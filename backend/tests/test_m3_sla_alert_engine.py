"""
Harness Engineering — P0 Test: SLA Alert Engine

Covers check_sampling_slas (chemical.py lines 263-316) — the core safety
mechanism that prevents $250K ANP fines by creating alerts for overdue
samples and pending validations.

Uses direct DB manipulation via its own fixtures for proper isolation.
"""

import pytest
from datetime import date, datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.dependencies import get_current_user
from app import models

# --- Isolated DB for SLA tests ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_sla.db"
sla_engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SLATestSession = sessionmaker(autocommit=False, autoflush=False, bind=sla_engine)


def override_get_db_sla():
    try:
        db = SLATestSession()
        yield db
    finally:
        db.close()


def override_get_current_user_sla():
    return {"id": "sla-bot", "email": "sla@test.com", "role": "Admin"}


@pytest.fixture(scope="module")
def sla_client():
    """Dedicated client with its own DB for SLA tests."""
    app.dependency_overrides[get_db] = override_get_db_sla
    app.dependency_overrides[get_current_user] = override_get_current_user_sla
    Base.metadata.create_all(bind=sla_engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=sla_engine)
    # Clean up the file-based DB
    import os
    try:
        os.remove("./test_sla.db")
    except OSError:
        pass


@pytest.fixture(scope="module")
def sla_db():
    db = SLATestSession()
    yield db
    db.close()


class TestSLAAlertEngine:
    """Integration tests for POST /api/chemical/check-slas."""

    def _create_sample_point(self, client):
        """Create a sample point via the API."""
        TestSLAAlertEngine._sp_counter = getattr(TestSLAAlertEngine, '_sp_counter', 0) + 1
        res = client.post("/api/chemical/sample-points", json={
            "tag_number": f"SP-SLA-{TestSLAAlertEngine._sp_counter:04d}",
            "description": "SLA Test SP",
            "fpso_name": "FPSO SLA-Test",
        })
        assert res.status_code == 200, f"SP creation failed: {res.text}"
        return res.json()

    def _create_sample(self, client, sp_id):
        """Create a sample via the API."""
        TestSLAAlertEngine._s_counter = getattr(TestSLAAlertEngine, '_s_counter', 0) + 1
        res = client.post("/api/chemical/samples", json={
            "sample_id": f"SLA-SAMPLE-{TestSLAAlertEngine._s_counter:04d}",
            "type": "Chromatography",
            "sample_point_id": sp_id,
            "local": "Onshore",
            "planned_date": "2026-06-01",
        })
        assert res.status_code == 200, f"Sample creation failed: {res.text}"
        return res.json()

    def _force_sample_state(self, sla_db, sample_id, status, sampling_date=None, report_date=None):
        """Directly update sample state in DB for precise scenario control."""
        sample = sla_db.query(models.Sample).filter(models.Sample.id == sample_id).first()
        sample.status = status
        if sampling_date:
            sample.sampling_date = sampling_date
        if report_date:
            sample.report_issue_date = report_date
        sla_db.commit()

    def test_creates_alert_for_overdue_report(self, sla_client, sla_db):
        """Sample stuck in 'Sample' for >15 days → Alert created."""
        sp = self._create_sample_point(sla_client)
        sample = self._create_sample(sla_client, sp["id"])
        self._force_sample_state(
            sla_db, sample["id"], "Sample",
            sampling_date=date.today() - timedelta(days=20),
        )

        response = sla_client.post("/api/chemical/check-slas")

        assert response.status_code == 200
        assert response.json()["alerts_created"] >= 1

    def test_no_duplicate_alerts(self, sla_client, sla_db):
        """Running check-slas twice should NOT create duplicate alerts."""
        sp = self._create_sample_point(sla_client)
        sample = self._create_sample(sla_client, sp["id"])
        self._force_sample_state(
            sla_db, sample["id"], "Sample",
            sampling_date=date.today() - timedelta(days=20),
        )

        sla_client.post("/api/chemical/check-slas")
        response = sla_client.post("/api/chemical/check-slas")

        assert response.json()["alerts_created"] == 0

    def test_creates_alert_for_pending_validation(self, sla_client, sla_db):
        """Report issued >3 days ago but still pending validation → Alert."""
        sp = self._create_sample_point(sla_client)
        sample = self._create_sample(sla_client, sp["id"])
        self._force_sample_state(
            sla_db, sample["id"], "Report issue",
            report_date=date.today() - timedelta(days=5),
        )

        response = sla_client.post("/api/chemical/check-slas")

        assert response.status_code == 200
        assert response.json()["alerts_created"] >= 1

    def test_no_alert_for_recent_samples(self, sla_client, sla_db):
        """Sample taken today → 0 alerts (within SLA window)."""
        sp = self._create_sample_point(sla_client)
        sample = self._create_sample(sla_client, sp["id"])
        self._force_sample_state(
            sla_db, sample["id"], "Sample",
            sampling_date=date.today(),
        )

        response = sla_client.post("/api/chemical/check-slas")

        assert response.status_code == 200
        assert response.json()["alerts_created"] == 0

    def test_no_alert_for_recent_reports(self, sla_client, sla_db):
        """Report issued today → 0 alerts (within validation window)."""
        sp = self._create_sample_point(sla_client)
        sample = self._create_sample(sla_client, sp["id"])
        self._force_sample_state(
            sla_db, sample["id"], "Report issue",
            report_date=date.today(),
        )

        response = sla_client.post("/api/chemical/check-slas")

        assert response.status_code == 200
        assert response.json()["alerts_created"] == 0
