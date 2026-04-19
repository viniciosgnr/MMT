"""
Harness Engineering — M3 Integration Tests: Full API Coverage
Cobre TODOS os endpoints do routers/chemical.py:
- POST /sample-points, GET /sample-points
- POST /samples, GET /samples, GET /samples/{id}
- POST /samples/{id}/update-status (full lifecycle traversal)
- PATCH /samples/{id}/due-date (override)
- GET /dashboard-stats
- POST /check-slas
- POST /samples/{id}/results
- GET /samples/{id}/lab-results
- GET /sample-points/{id}/parameter-history
"""
import pytest
from datetime import date, timedelta
from app.models import SampleStatus


class TestSamplePointCRUD:
    """Testa criação e listagem de pontos de amostragem."""

    def test_create_sample_point(self, client):
        res = client.post("/api/chemical/sample-points", json={
            "description": "Auto", "fase": "Prod", "tag_number": "SP-INT-001", "description": "Ponto Master",
            "fpso_name": "FPSO Sepetiba", "system": "Gas", "fluid": "Gas"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["fpso_name"] == "FPSO Sepetiba"
        assert data["tag_number"] == "SP-INT-001"
        assert "id" in data

    def test_list_sample_points_all(self, client):
        res = client.get("/api/chemical/sample-points")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_list_sample_points_filtered_by_fpso(self, client):
        res = client.get("/api/chemical/sample-points?fpso_name=FPSO Sepetiba")
        assert res.status_code == 200
        for sp in res.json():
            assert sp["fpso_name"] == "FPSO Sepetiba"


class TestSampleCreation:
    """Testa criação de amostras e auto-status."""

    def _create_sp(self, client, number="SP-AUTO"):
        res = client.post("/api/chemical/sample-points", json={
            "description": "Auto", "fase": "Prod", "tag_number": number, "description": "dummy_desc", "fpso_name": "FPSO Test", "system": "Oil", "fluid": "Oil"
        })
        return res.json()["id"]

    def test_create_sample_starts_at_sample_status(self, client):
        sp_id = self._create_sp(client, "SP-CREATE-01")
        res = client.post("/api/chemical/samples", json={
            "sample_id": "FULL-TEST-001", "type": "Chromatography",
            "sample_point_id": sp_id, "local": "Onshore",
            "planned_date": "2026-06-01"
        })
        assert res.status_code == 200
        assert res.json()["status"] == SampleStatus.SAMPLE.value

    def test_create_sample_operational_category(self, client):
        """Tipo 'Operacional' deve gerar categoria 'Operacional'."""
        sp_id = self._create_sp(client, "SP-CREATE-02")
        res = client.post("/api/chemical/samples", json={
            "sample_id": "OP-TEST-001", "type": "Operacional",
            "sample_point_id": sp_id, "local": "Onshore",
            "planned_date": "2026-06-01"
        })
        assert res.status_code == 200
        assert res.json()["category"] == "Operacional"

    def test_create_sample_chromatography_is_coleta(self, client):
        """Tipo 'Chromatography' deve gerar categoria 'Coleta'."""
        sp_id = self._create_sp(client, "SP-CREATE-03")
        res = client.post("/api/chemical/samples", json={
            "sample_id": "CRO-TEST-001", "type": "Chromatography",
            "sample_point_id": sp_id, "local": "Offshore",
            "planned_date": "2026-06-01"
        })
        assert res.status_code == 200
        assert res.json()["category"] == "Coleta"

    def test_create_sample_invalid_sp_returns_404(self, client):
        res = client.post("/api/chemical/samples", json={
            "sample_id": "FAIL-001", "type": "Chromatography",
            "sample_point_id": 999999, "local": "Onshore",
            "planned_date": "2026-06-01"
        })
        assert res.status_code == 404

    def test_get_sample_by_id(self, client):
        sp_id = self._create_sp(client, "SP-GET-01")
        create_res = client.post("/api/chemical/samples", json={
            "sample_id": "GET-TEST-001", "type": "Chromatography",
            "sample_point_id": sp_id, "local": "Onshore",
            "planned_date": "2026-06-01"
        })
        s_id = create_res.json()["id"]
        res = client.get(f"/api/chemical/samples/{s_id}")
        assert res.status_code == 200
        assert res.json()["sample_id"] == "GET-TEST-001"

    def test_get_sample_not_found(self, client):
        res = client.get("/api/chemical/samples/999999")
        assert res.status_code == 404

    def test_list_samples_all(self, client):
        res = client.get("/api/chemical/samples")
        assert res.status_code == 200
        assert isinstance(res.json(), list)


class TestStatusFlowLifecycle:
    """Testa a travessia completa do ciclo de vida de uma amostra."""

    def _setup_sample(self, client, sample_id="LIFECYCLE-001"):
        sp_res = client.post("/api/chemical/sample-points", json={
            "description": "Auto", "fase": "Prod", "tag_number": f"SP-{sample_id}", "description": "LIFECYCLE",
            "fpso_name": "FPSO Flow", "system": "Gas", "fluid": "Gas"
        })
        sp_id = sp_res.json()["id"]

        s_res = client.post("/api/chemical/samples", json={
            "sample_id": sample_id, "type": "Chromatography",
            "sample_point_id": sp_id, "local": "Onshore",
            "planned_date": date.today().isoformat()
        })
        return s_res.json()["id"]

    def _update_status(self, client, s_id, status, **kwargs):
        payload = {"status": status, "user": "TestBot", "comments": "Auto test", **kwargs}
        return client.post(f"/api/chemical/samples/{s_id}/update-status", json=payload)

    def test_sample_to_disembark_sets_sla_dates(self, client):
        """Ao coletar (Disembark prep), o backend DEVE calcular as datas SLA."""
        s_id = self._setup_sample(client, "SLA-DATES-01")
        today = date.today()

        res = self._update_status(client, s_id, SampleStatus.DISEMBARK_PREP.value,
                                  event_date=today.isoformat())
        assert res.status_code == 200
        data = res.json()

        # Fiscal Onshore: disembark=10, lab=20, report=25
        assert data["disembark_expected_date"] == (today + timedelta(days=10)).isoformat()
        assert data["lab_expected_date"] == (today + timedelta(days=20)).isoformat()
        assert data["report_expected_date"] == (today + timedelta(days=25)).isoformat()

    def test_disembark_logistics_sets_date(self, client):
        s_id = self._setup_sample(client, "DISEMBARK-LOG-01")
        self._update_status(client, s_id, SampleStatus.DISEMBARK_PREP.value,
                           event_date=date.today().isoformat())
        res = self._update_status(client, s_id, SampleStatus.DISEMBARK_LOGISTICS.value,
                                  event_date=date.today().isoformat())
        assert res.status_code == 200
        assert res.json()["disembark_date"] is not None

    def test_deliver_at_vendor_sets_date(self, client):
        s_id = self._setup_sample(client, "DELIVER-01")
        self._update_status(client, s_id, SampleStatus.DISEMBARK_PREP.value,
                           event_date=date.today().isoformat())
        res = self._update_status(client, s_id, SampleStatus.DELIVER_AT_VENDOR.value,
                                  event_date=date.today().isoformat())
        assert res.status_code == 200
        assert res.json()["delivery_date"] is not None

    def test_report_issue_sets_fc_expected(self, client):
        """Emissão de relatório deve calcular a data FC (3 dias úteis para Fiscal)."""
        s_id = self._setup_sample(client, "REPORT-FC-01")
        self._update_status(client, s_id, SampleStatus.DISEMBARK_PREP.value,
                           event_date=date.today().isoformat())
        res = self._update_status(client, s_id, SampleStatus.REPORT_ISSUE.value,
                                  event_date=date.today().isoformat())
        assert res.status_code == 200
        data = res.json()
        assert data["report_issue_date"] is not None
        assert data["fc_expected_date"] is not None, "FC expected date DEVE ser calculada na emissão do laudo!"

    def test_fc_update_sets_timestamp(self, client):
        s_id = self._setup_sample(client, "FC-UPD-01")
        self._update_status(client, s_id, SampleStatus.DISEMBARK_PREP.value,
                           event_date=date.today().isoformat())
        res = self._update_status(client, s_id, SampleStatus.FLOW_COMPUTER_UPDATE.value)
        assert res.status_code == 200
        assert res.json()["fc_update_date"] is not None


class TestOverrideDate:
    """Testa o endpoint PATCH de override manual de due_date."""

    def _setup(self, client, sid="OVERRIDE-001"):
        sp_res = client.post("/api/chemical/sample-points", json={
            "description": "Auto", "fase": "Prod", "tag_number": f"SP-{sid}", "fpso_name": "FPSO OV", "description": "OV",
            "system": "Gas", "fluid": "Gas"
        })
        s_res = client.post("/api/chemical/samples", json={
            "sample_id": sid, "type": "Chromatography",
            "sample_point_id": sp_res.json()["id"], "local": "Onshore",
            "planned_date": "2026-06-01"
        })
        return s_res.json()["id"]

    def test_override_due_date(self, client):
        s_id = self._setup(client, "OV-TEST-01")
        res = client.patch(f"/api/chemical/samples/{s_id}/due-date",
                          json={"due_date": "2026-12-25"})
        assert res.status_code == 200
        assert res.json()["due_date"] == "2026-12-25"

    def test_override_with_null_clears_date(self, client):
        s_id = self._setup(client, "OV-TEST-02")
        res = client.patch(f"/api/chemical/samples/{s_id}/due-date",
                          json={"due_date": None})
        assert res.status_code == 200
        assert res.json()["due_date"] is None

    def test_override_nonexistent_sample_404(self, client):
        res = client.patch("/api/chemical/samples/999999/due-date",
                          json={"due_date": "2026-12-25"})
        assert res.status_code == 404


class TestDashboard:
    """Testa o endpoint de estatísticas do Dashboard."""

    def test_dashboard_returns_all_groups(self, client):
        res = client.get("/api/chemical/dashboard-stats")
        assert res.status_code == 200
        data = res.json()
        for group in ["sampling", "disembark", "logistics", "report", "fc_update"]:
            assert group in data
            assert "total" in data[group]
            assert "overdue" in data[group]
            assert "due_today" in data[group]
            assert "due_tomorrow" in data[group]
            assert "steps" in data[group]

    def test_dashboard_with_fpso_filter(self, client):
        res = client.get("/api/chemical/dashboard-stats?fpso_name=FPSO Sepetiba")
        assert res.status_code == 200


class TestSampleResults:
    """Testa criação e consulta de resultados laboratoriais."""

    def _setup(self, client, sid="RESULT-001"):
        sp_res = client.post("/api/chemical/sample-points", json={
            "description": "Auto", "fase": "Prod", "tag_number": f"SP-{sid}", "description": "RESULT", "fpso_name": "FPSO Res",
            "system": "Oil", "fluid": "Oil"
        })
        s_res = client.post("/api/chemical/samples", json={
            "sample_id": sid, "type": "Chromatography",
            "sample_point_id": sp_res.json()["id"], "local": "Onshore",
            "planned_date": "2026-06-01"
        })
        return s_res.json()["id"]

    def test_add_result(self, client):
        s_id = self._setup(client, "RES-ADD-01")
        res = client.post(f"/api/chemical/samples/{s_id}/results", json={
            "parameter": "density", "value": 875.0, "unit": "kg/m³"
        })
        assert res.status_code == 200
        assert res.json()["parameter"] == "density"
        assert res.json()["value"] == 875.0

    def test_get_lab_results(self, client):
        s_id = self._setup(client, "RES-GET-01")
        client.post(f"/api/chemical/samples/{s_id}/results", json={
            "parameter": "o2", "value": 0.032, "unit": "%"
        })
        res = client.get(f"/api/chemical/samples/{s_id}/lab-results")
        assert res.status_code == 200
        results = res.json()
        assert len(results) >= 1
        assert results[0]["parameter"] == "o2"


class TestCheckSlas:
    """Testa a varredura Background de alertas SLA."""

    def test_check_slas_returns_200(self, client):
        res = client.post("/api/chemical/check-slas")
        assert res.status_code == 200
        assert "alerts_created" in res.json()
        assert "message" in res.json()
