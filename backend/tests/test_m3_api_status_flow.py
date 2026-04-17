import pytest
from datetime import date, timedelta
from app.models import SampleStatus

class TestM3StatusFlowIntegration:
    """
    Simula o ciclo de vida HTTP do endpoint `/update-status`.
    Sensor do Harness assegurando que os 'Dias de Prazo (SLA)' 
    sejam calculados e gravados no Banco de Dados em cada etapa.
    """

    def test_api_sample_transit_to_disembark(self, client, db_session):
        # 1. Setup Sample Point
        sp_res = client.post("/api/chemical/sample-points", json={
            "fase": "Prod", "number": "SP-COMPLEX", "fpso_name": "FPSO Flow", "system": "Gas", "fluid": "Gas"
        })
        sp_id = sp_res.json()["id"]

        # 2. Setup Base Sample (Fiscal Onshore)
        sample_payload = {
            "sample_id": "TEST-FLOW-01",
            "type": "Chromatography",
            "sample_point_id": sp_id,
            "local": "Onshore",
            "planned_date": (date.today() - timedelta(days=5)).isoformat()
        }
        sample_res = client.post("/api/chemical/samples", json=sample_payload)
        s_id = sample_res.json()["id"]

        # 3. Trigger /update-status (Simulando o Fiel apertando 'Coleta Realizada')
        update_payload = {
            "status": SampleStatus.DISEMBARK_PREP.value,
            "user": "Fiel de Metrologia",
            "comments": "Coletado e asinado",
            "event_date": date.today().isoformat()
        }
        res = client.post(f"/api/chemical/samples/{s_id}/update-status", json=update_payload)
        
        assert res.status_code == 200, "Falha na rota REST de Update Status."
        updated_sample = res.json()
        assert updated_sample["status"] == SampleStatus.DISEMBARK_PREP.value

        # --- A Magia do SLA Backend Acontecendo ---
        # Se for Onshore Fiscal, disembark_days = 10, lab_days = 20, report_days = 25
        t = date.today()
        expected_disembark = (t + timedelta(days=10)).isoformat()
        expected_lab = (t + timedelta(days=20)).isoformat()
        expected_report = (t + timedelta(days=25)).isoformat()

        assert updated_sample["disembark_expected_date"] == expected_disembark, "Backend não ativou a matriz para Disembark!"
        assert updated_sample["lab_expected_date"] == expected_lab, "Backend não ativou a matriz para Warehouse!"
        assert updated_sample["report_expected_date"] == expected_report, "Backend não ativou a janela máxima do Relatório!"
