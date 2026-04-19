import pytest
from datetime import date, timedelta
from app.models import Sample, SampleStatus, SamplePoint

class TestM3AlertDetectionSystem:
    """
    Testes de Integração críticos para a varredura automática de Background (/check-slas).
    Responsável por gerar os alarmes (Alerts) para gerentes via e-mail/Dashboard.
    """

    def test_overdue_lab_report_alert_trigger(self, client, db_session):
        # 1. Manually inject a rotten sample directly into the SQLite mocked database
        # Sample collected 16 days ago (threshold is > 15 days without lab report)
        sp = SamplePoint(description="Auto", tag_number="SP-BAD", fpso_name="FPSO Alerts")
        db_session.add(sp)
        db_session.commit()

        bad_date = date.today() - timedelta(days=16)
        rotten_sample = Sample(
            sample_id="EMG-DANGER-001",
            sample_point_id=sp.id,
            status=SampleStatus.SAMPLE.value,
            sampling_date=bad_date,
            is_active=1
        )
        db_session.add(rotten_sample)
        db_session.commit()

        # 2. Ping the REST api to scan SLAs (Isso na prática roda num cron job / webhook)
        res = client.post("/api/chemical/check-slas")
        assert res.status_code == 200
        
        data = res.json()
        assert "alerts_created" in data
        assert data["alerts_created"] >= 1, "Crítico: O Varredor de Background CEGO para amostragens vencidas há mais de 15 dias!"

        # 3. Ping it AGAIN, it should NOT create duplicate alerts for the same offense
        res2 = client.post("/api/chemical/check-slas")
        assert res2.json()["alerts_created"] == 0, "O Varredor não é idempotente! Ele inundaria o DB de alarmes repetidos."
