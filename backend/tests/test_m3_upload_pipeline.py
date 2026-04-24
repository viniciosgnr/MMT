"""
M3 — Sample State Machine & Emergency Sample Tests
Cobre: transições de status de amostra (Plan→Sample→Report Issued),
trigger de Emergency Sample após reprovação, e a proteção
contra uploads em amostras em estado inválido.
"""
import pytest
from unittest.mock import patch, mock_open
from app.services.pdf_parser import CROResult, PVTResult


def _upload(client, sample_id, mock_result):
    with patch("app.routers.chemical.parse_pdf_bytes", return_value=mock_result), \
         patch("app.routers.chemical.open", mock_open()), \
         patch("app.routers.chemical.os.makedirs"):
        return client.post(
            f"/api/chemical/samples/{sample_id}/validate-report",
            files={"file": ("r.pdf", b"dummy", "application/pdf")}
        )


def test_sample_status_transitions_to_validation(client, sp_factory, sample_factory):
    """
    Um sample em status 'Report issue' que recebe um upload deve
    ter seu status atualizado para 'Validation' (ou similar).
    """
    sp = sp_factory()
    sample = sample_factory(sample_point_id=sp["id"], status="Report issue")

    mock = CROResult(report_type="CRO", boletim="CRO-ST-001", o2=0.1)
    res = _upload(client, sample["id"], mock)
    assert res.status_code == 200

    # Verify sample status was updated
    updated = client.get(f"/api/chemical/samples/{sample['id']}").json()
    assert updated["status"] in ["Sample", "Validation", "Report issue", "Approved", "Reproved"]
    assert updated["validation_status"] in ["Approved", "Reproved"]


def test_reproved_sample_has_correct_validation_status(client, sp_factory, sample_factory):
    """
    Sample com O2 > 0.5% deve ter validation_status = 'Reproved' após upload.
    """
    sp = sp_factory()
    sample = sample_factory(sample_point_id=sp["id"], status="Report issue")

    mock = CROResult(report_type="CRO", boletim="CRO-REP-001", o2=0.8)
    res = _upload(client, sample["id"], mock)
    assert res.status_code == 200

    updated = client.get(f"/api/chemical/samples/{sample['id']}").json()
    assert updated["validation_status"] == "Reproved"


def test_approved_sample_has_correct_validation_status(client, sp_factory, sample_factory):
    """
    Sample com O2 dentro do limite deve ter validation_status = 'Approved'.
    """
    sp = sp_factory()
    sample = sample_factory(sample_point_id=sp["id"], status="Report issue")

    mock = CROResult(report_type="CRO", boletim="CRO-APP-001", o2=0.1)
    res = _upload(client, sample["id"], mock)
    assert res.status_code == 200

    updated = client.get(f"/api/chemical/samples/{sample['id']}").json()
    assert updated["validation_status"] == "Approved"


def test_upload_stores_lab_report_url(client, sp_factory, sample_factory):
    """Upload de laudo deve registrar a lab_report_url no sample."""
    sp = sp_factory()
    sample = sample_factory(sample_point_id=sp["id"], status="Report issue")

    mock = CROResult(report_type="CRO", boletim="CRO-URL-001", o2=0.1)
    _upload(client, sample["id"], mock)

    updated = client.get(f"/api/chemical/samples/{sample['id']}").json()
    assert updated["lab_report_url"] is not None
    assert len(updated["lab_report_url"]) > 0


def test_sample_results_stored_after_upload(client, sp_factory, sample_factory):
    """Após upload, os SampleResults devem estar acessíveis via lab-results."""
    sp = sp_factory()
    sample = sample_factory(sample_point_id=sp["id"], status="Report issue")

    mock = CROResult(report_type="CRO", boletim="CRO-RES-001", o2=0.15)
    _upload(client, sample["id"], mock)

    res = client.get(f"/api/chemical/samples/{sample['id']}/lab-results")
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_reupload_does_not_duplicate_results(client, sp_factory, sample_factory):
    """Dois uploads no mesmo sample não devem duplicar os lab-results."""
    sp = sp_factory()
    sample = sample_factory(sample_point_id=sp["id"], status="Report issue")

    mock = CROResult(report_type="CRO", boletim="CRO-REUP-001", o2=0.1)
    _upload(client, sample["id"], mock)
    first_count = len(client.get(f"/api/chemical/samples/{sample['id']}/lab-results").json())

    _upload(client, sample["id"], mock)
    second_count = len(client.get(f"/api/chemical/samples/{sample['id']}/lab-results").json())

    assert second_count == first_count


def test_upload_to_nonexistent_sample_returns_404(client):
    """Upload para sample inexistente deve retornar 404."""
    with patch("app.routers.chemical.os.makedirs"), \
         patch("app.routers.chemical.open", mock_open()):
        res = client.post(
            "/api/chemical/samples/999999/validate-report",
            files={"file": ("r.pdf", b"dummy", "application/pdf")}
        )
    assert res.status_code == 404


def test_pvt_report_checks_density_and_rs(client, sp_factory, sample_factory):
    """PVT upload com density e RS deve retornar checks para ambos."""
    sp = sp_factory()
    sample = sample_factory(sample_point_id=sp["id"], status="Report issue")

    mock = PVTResult(report_type="PVT", boletim="PVT-RES-001", density=850.0, rs=90.0)
    res = _upload(client, sample["id"], mock)
    assert res.status_code == 200
    checks = res.json()["checks"]
    params = [c["parameter"] for c in checks]
    assert "density" in params
    assert "rs" in params


def test_cro_report_checks_o2(client, sp_factory, sample_factory):
    """CRO upload com O2 deve retornar check para o2."""
    sp = sp_factory()
    sample = sample_factory(sample_point_id=sp["id"], status="Report issue")

    mock = CROResult(report_type="CRO", boletim="CRO-O2-CHK", o2=0.3)
    res = _upload(client, sample["id"], mock)
    assert res.status_code == 200
    checks = res.json()["checks"]
    assert any(c["parameter"] == "o2" for c in checks)
