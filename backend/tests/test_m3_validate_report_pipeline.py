from sqlalchemy.pool import StaticPool
"""
Harness Engineering — P0 Test: Validate Report Pipeline

Covers the ENTIRE PDF upload → parse → validate → store → response pipeline
(chemical.py lines 597-678). This is the most critical untested path in M3.

Uses its own isolated SQLite DB to avoid module-scope conflicts.
"""

import pytest
from io import BytesIO
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.dependencies import get_current_user

# --- Isolated DB for Pipeline tests ---
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
pipe_engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
PipeTestSession = sessionmaker(autocommit=False, autoflush=False, bind=pipe_engine)


def override_get_db_pipe():
    try:
        db = PipeTestSession()
        yield db
    finally:
        db.close()


def override_get_current_user_pipe():
    return {"id": "pipe-bot", "email": "pipe@test.com", "role": "Admin"}


@pytest.fixture(scope="module")
def pipe_client():
    """Dedicated client for pipeline tests."""
    app.dependency_overrides[get_db] = override_get_db_pipe
    app.dependency_overrides[get_current_user] = override_get_current_user_pipe
    Base.metadata.create_all(bind=pipe_engine)
    with TestClient(app) as c:
        yield c
    import os
    try:
        os.remove("./test_pipeline.db")
    except OSError:
        pass


class TestValidateReportPipeline:
    """Integration tests for POST /api/chemical/samples/{id}/validate-report."""

    _sp_counter = 0
    _s_counter = 0

    def _create_sp_and_sample(self, client, extra_sample_kw=None):
        """Create sample point + sample via API."""
        TestValidateReportPipeline._sp_counter += 1
        TestValidateReportPipeline._s_counter += 1
        sp_res = client.post("/api/chemical/sample-points", json={
            "tag_number": f"SP-PIPE-{TestValidateReportPipeline._sp_counter:04d}",
            "description": "Pipeline Test SP",
            "fpso_name": "FPSO Pipeline",
        })
        assert sp_res.status_code == 200, f"SP creation failed: {sp_res.text}"
        sp = sp_res.json()

        sample_data = {
            "sample_id": f"PIPE-{TestValidateReportPipeline._s_counter:04d}",
            "type": "Chromatography",
            "sample_point_id": sp["id"],
            "local": "Onshore",
            "planned_date": "2026-06-01",
        }
        if extra_sample_kw:
            sample_data.update(extra_sample_kw)
        s_res = client.post("/api/chemical/samples", json=sample_data)
        assert s_res.status_code == 200, f"Sample creation failed: {s_res.text}"
        return sp, s_res.json()

    def _mock_parse_result(self, report_type="CRO"):
        """Create a mock parsed result for patching parse_pdf_bytes."""
        if report_type == "CRO":
            from app.services.pdf_parser import CROResult
            return CROResult(
                report_type="CRO",
                boletim="CRO Test/26-001",
                tag_point="662-AP-2233 / P-02",
                o2=0.032,
                relative_density_real=1.0509,
            )
        else:
            from app.services.pdf_parser import PVTResult
            return PVTResult(
                report_type="PVT",
                boletim="PVT Test/26-001",
                tag_point="662-AP-2233 / P-02",
                density=875.39,
                rs=88.0571,
                fe=0.8241,
            )

    def _upload_pdf(self, client, sample_id, mock_result, filename="test_report.pdf"):
        """Helper to upload a fake PDF with mocked parsing and file I/O."""
        from unittest.mock import mock_open
        fake_pdf = BytesIO(b"%PDF-1.4 fake content")
        with patch("app.services.pdf_parser.parse_pdf_bytes", return_value=mock_result), \
             patch("builtins.open", mock_open()), \
             patch("os.makedirs"):
            response = client.post(
                f"/api/chemical/samples/{sample_id}/validate-report",
                files={"file": (filename, fake_pdf, "application/pdf")},
            )
        return response

    # --- P0 Tests ---

    def test_cro_upload_happy_path(self, pipe_client):
        """CRO mock result → 200 + checks returned."""
        _, sample = self._create_sp_and_sample(pipe_client)
        mock = self._mock_parse_result("CRO")
        response = self._upload_pdf(pipe_client, sample["id"], mock)

        assert response.status_code == 200
        data = response.json()
        assert data["report_type"] == "CRO"
        assert data["overall_status"] in ("Approved", "Reproved")
        assert data["boletim"] == "CRO Test/26-001"
        assert len(data["checks"]) >= 1
        assert data["passed_count"] + data["failed_count"] == len(data["checks"])

    def test_pvt_upload_happy_path(self, pipe_client):
        """PVT report → density, RS, FE checks."""
        from unittest.mock import mock_open
        _, sample = self._create_sp_and_sample(pipe_client)
        mock = self._mock_parse_result("PVT")
        fake_pdf = BytesIO(b"%PDF-1.4 fake pvt")
        with patch("app.services.pdf_parser.parse_pdf_bytes", return_value=mock), \
             patch("builtins.open", mock_open()), \
             patch("os.makedirs"):
            response = pipe_client.post(
                f"/api/chemical/samples/{sample['id']}/validate-report",
                files={"file": ("pvt_report.pdf", fake_pdf, "application/pdf")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["report_type"] == "PVT"
        params = [c["parameter"] for c in data["checks"]]
        assert "density" in params

    def test_invalid_pdf_returns_400(self, pipe_client):
        """Garbage bytes → ValueError → 400."""
        _, sample = self._create_sp_and_sample(pipe_client)
        fake_pdf = BytesIO(b"NOT A PDF AT ALL")
        with patch(
            "app.services.pdf_parser.parse_pdf_bytes",
            side_effect=ValueError("Unknown report type"),
        ):
            response = pipe_client.post(
                f"/api/chemical/samples/{sample['id']}/validate-report",
                files={"file": ("garbage.pdf", fake_pdf, "application/pdf")},
            )

        assert response.status_code == 400
        assert "Unknown report type" in response.json()["detail"]

    def test_sample_not_found_returns_404(self, pipe_client):
        """Upload to nonexistent sample → 404."""
        url = "/api/chemical/samples/99999/validate-report"
        fake_pdf = BytesIO(b"%PDF-1.4 fake")
        response = pipe_client.post(
            url, files={"file": ("test.pdf", fake_pdf, "application/pdf")},
        )
        assert response.status_code == 404

    def test_results_stored_in_database(self, pipe_client):
        """After upload, SampleResult rows should exist in DB."""
        _, sample = self._create_sp_and_sample(pipe_client)
        mock = self._mock_parse_result("CRO")
        self._upload_pdf(pipe_client, sample["id"], mock)

        results = pipe_client.get(f"/api/chemical/samples/{sample['id']}/lab-results")
        assert results.status_code == 200
        data = results.json()
        assert len(data) >= 1
        assert data[0]["source_pdf"] == "test_report.pdf"

    def test_reupload_replaces_previous_results(self, pipe_client):
        """Upload twice → old results deleted, count stays the same (not doubled)."""
        _, sample = self._create_sp_and_sample(pipe_client)
        mock = self._mock_parse_result("CRO")

        self._upload_pdf(pipe_client, sample["id"], mock)
        first_results = pipe_client.get(f"/api/chemical/samples/{sample['id']}/lab-results").json()
        first_count = len(first_results)

        self._upload_pdf(pipe_client, sample["id"], mock)
        second_results = pipe_client.get(f"/api/chemical/samples/{sample['id']}/lab-results").json()

        # Results should have same count (not doubled from re-upload)
        assert len(second_results) == first_count, \
            f"Expected {first_count} results after re-upload, got {len(second_results)}"

    def test_validation_status_updates_sample(self, pipe_client):
        """After upload, sample.validation_status should reflect overall result."""
        _, sample = self._create_sp_and_sample(pipe_client)
        mock = self._mock_parse_result("CRO")
        self._upload_pdf(pipe_client, sample["id"], mock)

        sample_data = pipe_client.get(f"/api/chemical/samples/{sample['id']}").json()
        assert sample_data["validation_status"] in ("Approved", "Reproved")
        assert sample_data["lab_report_url"] is not None
        assert "test_report.pdf" in sample_data["lab_report_url"]
