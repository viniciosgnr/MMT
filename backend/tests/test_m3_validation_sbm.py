"""
Harness Engineering — M3 SBM Validation & Parameter History Tests

ENDPOINTS COBERTOS (PREVIAMENTE NÃO TESTADOS):
1. GET /samples/{id}/validate — SBM algorithm (Avg + 2σ)
2. GET /sample-points/{id}/parameter-history — History chart data
3. Validation with insufficient history (Inconclusive)
4. Validation with pass/fail scenarios

Skills:
- fastapi-pro → TestClient, Factory from conftest
- python-testing-patterns → AAA, parametrize
"""
import pytest
from datetime import date
from app.models import SampleStatus


class TestSBMValidation:
    """Testa o endpoint GET /samples/{id}/validate (SBM algorithm)."""

    def _setup_sp(self, client, sp_num="SP-VAL"):
        res = client.post("/api/chemical/sample-points", json={
            "fase": "Prod", "number": sp_num, "fpso_name": "FPSO Validation",
            "system": "Oil", "fluid": "Oil"
        })
        return res.json()["id"]

    def _create_sample(self, client, sp_id, sid, status=None):
        res = client.post("/api/chemical/samples", json={
            "sample_id": sid, "type": "Chromatography",
            "sample_point_id": sp_id, "local": "Onshore",
            "planned_date": date.today().isoformat()
        })
        s_id = res.json()["id"]
        if status:
            client.post(f"/api/chemical/samples/{s_id}/update-status", json={
                "status": status, "user": "TestBot", "comments": "Setup",
                "event_date": date.today().isoformat()
            })
        return s_id

    def _add_result(self, client, s_id, param, value, unit="kg/m³"):
        return client.post(f"/api/chemical/samples/{s_id}/results", json={
            "parameter": param, "value": value, "unit": unit
        })

    def test_validate_no_results_returns_400(self, client):
        """Validate sem resultados deve retornar 400."""
        sp_id = self._setup_sp(client, "SP-VAL-NORES")
        s_id = self._create_sample(client, sp_id, "VAL-NORES-01")
        res = client.get(f"/api/chemical/samples/{s_id}/validate")
        assert res.status_code == 400

    def test_validate_with_insufficient_history(self, client):
        """Com < 3 amostras históricas, status deve ser 'Inconclusive'."""
        sp_id = self._setup_sp(client, "SP-VAL-INC")
        s_id = self._create_sample(client, sp_id, "VAL-INC-01")
        self._add_result(client, s_id, "density", 875.0)

        res = client.get(f"/api/chemical/samples/{s_id}/validate")
        assert res.status_code == 200
        data = res.json()
        assert any("Inconclusive" in p.get("status", "") for p in data["parameters"])

    def test_validate_with_history_pass(self, client):
        """Com histórico suficiente e valor dentro de 2σ → Pass."""
        sp_id = self._setup_sp(client, "SP-VAL-PASS")

        # Cria 4 amostras históricas com valores similares (baixo desvio)
        for i in range(4):
            sid = self._create_sample(
                client, sp_id, f"VAL-HIST-{i}",
                status=SampleStatus.FLOW_COMPUTER_UPDATE.value
            )
            self._add_result(client, sid, "density", 875.0 + i * 0.1)

        # Cria amostra atual com valor próximo da média
        current_id = self._create_sample(client, sp_id, "VAL-CURRENT")
        self._add_result(client, current_id, "density", 875.2)

        res = client.get(f"/api/chemical/samples/{current_id}/validate")
        assert res.status_code == 200
        data = res.json()
        assert data["overall_status"] == "Approved"

    def test_validate_with_history_fail(self, client):
        """Valor fora de 2σ → Fail → overall_status = 'Reproved'."""
        sp_id = self._setup_sp(client, "SP-VAL-FAIL")

        # Histórico estável em ~875
        for i in range(4):
            sid = self._create_sample(
                client, sp_id, f"VAL-FAIL-HIST-{i}",
                status=SampleStatus.FLOW_COMPUTER_UPDATE.value
            )
            self._add_result(client, sid, "density", 875.0 + i * 0.05)

        # Amostra atual com valor absurdo (960) — muito fora de 2σ
        current_id = self._create_sample(client, sp_id, "VAL-FAIL-CURR")
        self._add_result(client, current_id, "density", 960.0)

        res = client.get(f"/api/chemical/samples/{current_id}/validate")
        assert res.status_code == 200
        data = res.json()
        assert data["overall_status"] == "Reproved"

    def test_validate_multiple_parameters(self, client):
        """Validação com múltiplos parâmetros — todos precisam ser avaliados."""
        sp_id = self._setup_sp(client, "SP-VAL-MULTI")

        for i in range(4):
            sid = self._create_sample(
                client, sp_id, f"VAL-MULTI-{i}",
                status=SampleStatus.FLOW_COMPUTER_UPDATE.value
            )
            self._add_result(client, sid, "density", 875.0 + i * 0.1)
            self._add_result(client, sid, "rs", 88.0 + i * 0.05, "m³/m³")

        current_id = self._create_sample(client, sp_id, "VAL-MULTI-CURR")
        self._add_result(client, current_id, "density", 875.2)
        self._add_result(client, current_id, "rs", 88.1, "m³/m³")

        res = client.get(f"/api/chemical/samples/{current_id}/validate")
        assert res.status_code == 200
        assert len(res.json()["parameters"]) == 2

    def test_validate_response_structure(self, client):
        """Resposta deve ter sample_id, overall_status, parameters com avg/std/range."""
        sp_id = self._setup_sp(client, "SP-VAL-STRUCT")

        for i in range(4):
            sid = self._create_sample(
                client, sp_id, f"VAL-STR-{i}",
                status=SampleStatus.FLOW_COMPUTER_UPDATE.value
            )
            self._add_result(client, sid, "density", 875.0 + i * 0.1)

        current_id = self._create_sample(client, sp_id, "VAL-STR-CURR")
        self._add_result(client, current_id, "density", 875.3)

        res = client.get(f"/api/chemical/samples/{current_id}/validate")
        data = res.json()
        assert "sample_id" in data
        assert "overall_status" in data
        assert "parameters" in data
        for p in data["parameters"]:
            assert "parameter" in p
            assert "status" in p
            assert "avg" in p


class TestParameterHistory:
    """Testa GET /sample-points/{id}/parameter-history."""

    def _setup(self, client, sp_num="SP-HIST"):
        sp = client.post("/api/chemical/sample-points", json={
            "fase": "Prod", "number": sp_num, "fpso_name": "FPSO History",
            "system": "Oil", "fluid": "Oil"
        })
        sp_id = sp.json()["id"]

        # Cria 5 amostras com resultados
        for i in range(5):
            s = client.post("/api/chemical/samples", json={
                "sample_id": f"HIST-{sp_num}-{i}", "type": "PVT",
                "sample_point_id": sp_id, "local": "Onshore",
                "planned_date": date.today().isoformat()
            })
            s_id = s.json()["id"]
            client.post(f"/api/chemical/samples/{s_id}/results", json={
                "parameter": "density", "value": 870 + i, "unit": "kg/m³"
            })
            client.post(f"/api/chemical/samples/{s_id}/results", json={
                "parameter": "rs", "value": 85 + i * 0.5, "unit": "m³/m³"
            })

        return sp_id

    def test_get_density_history(self, client):
        sp_id = self._setup(client, "SP-HIST-01")
        res = client.get(f"/api/chemical/sample-points/{sp_id}/parameter-history?parameter=density")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 5
        for item in data:
            assert "value" in item
            assert "date" in item
            assert "sample_id" in item

    def test_get_rs_history(self, client):
        sp_id = self._setup(client, "SP-HIST-02")
        res = client.get(f"/api/chemical/sample-points/{sp_id}/parameter-history?parameter=rs")
        assert res.status_code == 200
        assert len(res.json()) == 5

    def test_history_with_limit(self, client):
        sp_id = self._setup(client, "SP-HIST-03")
        res = client.get(f"/api/chemical/sample-points/{sp_id}/parameter-history?parameter=density&limit=3")
        assert res.status_code == 200
        assert len(res.json()) == 3

    def test_history_empty_for_unknown_param(self, client):
        sp_id = self._setup(client, "SP-HIST-04")
        res = client.get(f"/api/chemical/sample-points/{sp_id}/parameter-history?parameter=viscosity")
        assert res.status_code == 200
        assert len(res.json()) == 0

    def test_history_nonexistent_point(self, client):
        res = client.get("/api/chemical/sample-points/999999/parameter-history?parameter=density")
        assert res.status_code == 200
        assert len(res.json()) == 0
