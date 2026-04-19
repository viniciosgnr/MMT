from sqlalchemy.pool import StaticPool
"""
Harness Engineering — M3 Edge Cases & Auto-Scheduling Tests
Cobre as linhas não testadas de app/routers/chemical.py (aprox. 40% faltante).
Testa caminhos tristes (404), cálculo de datas úteis no Dashboard e criação
automática de amostras Periódicas e de Emergência.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, timedelta
import string
import random

from app.main import app
from app.database import Base, get_db
from app.dependencies import get_current_user
import app.models as db_models
from app.models import SamplePoint, Sample, SampleStatus, SampleResult, InstrumentTag, SamplingCampaign, SampleStatusHistory
from app.schemas.chemical import SampleStatusUpdate

@pytest.fixture(scope="module")
def setup_db(db_session):
    # Create sample point
    sp_tag = f"662-AP-{random.randint(1000, 9999)}"
    sp = SamplePoint(
        tag_number=sp_tag,
        fpso_name="FPSO M3 Edge Tests",
        description="Edge Test Sample Point"
    )
    db_session.add(sp)
    db_session.commit()
    db_session.refresh(sp)
    
    yield db_session, sp

class TestChemicalSadPaths:
    """Tests 404s and sad paths in chemical.py endpoints."""
    
    def test_link_meters_404(self, client):
        res = client.post("/api/chemical/sample-points/999999/link-meters", json=[1, 2, 3])
        assert res.status_code == 404
        assert "Sample point not found" in res.json()["detail"]
        
    def test_update_status_404(self, client):
        update_data = {"status": "Plan"}
        res = client.post("/api/chemical/samples/999999/update-status", json=update_data)
        assert res.status_code == 404
        assert "Sample not found" in res.json()["detail"]
        
    def test_legacy_validation_endpoint_400(self, client, setup_db):
        db, sp = setup_db
        # Sample without results
        sample = Sample(
            sample_id="NO-RESULTS-001",
            type="PVT",
            category="Gas",
            status="Sample",
            sample_point_id=sp.id
        )
        db.add(sample)
        db.commit()
        db.refresh(sample)
        
        res = client.get(f"/api/chemical/samples/{sample.id}/validate")
        assert res.status_code == 400
        assert "No results found" in res.json()["detail"]

class TestCampaignsExisted:
    """Testes de Criação de Campanhas de Amostragem (linhas 66-70)"""
    
    def test_create_campaign(self, client):
        payload = {
            "name": "Campaign Edge Test Q3",
            "fpso_name": "FPSO M3 Edge Tests",
            "start_date": "2026-08-01",
            "end_date": "2026-08-30",
            "responsible": "Admin"
        }
        res = client.post("/api/chemical/campaigns", json=payload)
        assert res.status_code == 200
        assert res.json()["name"] == "Campaign Edge Test Q3"
        assert res.json()["id"] > 0

class TestAutoSchedulingLogic:
    """Testa agendamento automático Periódico e Emergencial nas mudanças de status."""
    
    def test_schedule_next_periodic_on_disembark(self, client, setup_db):
        """When status changes to DISEMBARK_PREP, a new periodic sample should be spawned."""
        db, sp = setup_db
        
        sample = Sample(
            sample_id="AUTO-PER-001",
            type="PVT",
            category="Oil",
            status="Sample",
            sample_point_id=sp.id,
            local="Onshore",
            sampling_date=date.today()
        )
        db.add(sample)
        db.commit()
        db.refresh(sample)
        
        # update status to Disembark preparation
        payload = {
            "status": "Disembark preparation",
            "event_date": str(date.today()),
            "local": "Onshore"
        }
        res = client.post(f"/api/chemical/samples/{sample.id}/update-status", json=payload)
        assert res.status_code == 200
        updated = res.json()
        assert updated["status"] == "Disembark preparation"
        assert updated["disembark_expected_date"] is not None
        
        # Verify periodic daughter was spawned
        per_sample = db.query(Sample).filter(Sample.sample_id.like(f"%-PER-{sample.id}-%")).first()
        assert per_sample is not None
        assert per_sample.status == "Sample"
        assert per_sample.type == "PVT"
        assert per_sample.planned_date is not None
        
    def test_schedule_emergency_on_reprovado(self, client, setup_db):
        """When validation_status is Reprovado, an emergency sample is created 3 business days later."""
        db, sp = setup_db
        
        sample = Sample(
            sample_id="AUTO-EMG-001",
            type="CRO",
            category="Gas",
            status="Report under validation",
            sample_point_id=sp.id,
            report_issue_date=date(2026, 4, 15)  # E.g. Wednesday
        )
        db.add(sample)
        db.commit()
        db.refresh(sample)
        
        payload = {
            "status": "Report approve/reprove",
            "validation_status": "Reprovado"
        }
        res = client.post(f"/api/chemical/samples/{sample.id}/update-status", json=payload)
        assert res.status_code == 200
        
        # Verify emergency daughter was spawned
        emg_sample = db.query(Sample).filter(Sample.sample_id.like(f"%-EMG-{sample.id}-%")).first()
        assert emg_sample is not None
        assert emg_sample.status == "Sample"
        
        # 3 business days logic from Wednesday (4/15) is Mon (4/20)
        assert emg_sample.planned_date.isoformat().startswith("2026-04-20")

class TestDashboardUrgencyTriggers:
    """Testa lógicas de contagem das urgências usando os triggers do get_dashboard_stats."""
    
    def test_get_dashboard_stats_trigger_urgency(self, client, setup_db):
        db, sp = setup_db
        
        # We need samples at specific steps with overdue dates on the TRIGGER properties
        yesterday = date.today() - timedelta(days=1)
        today = date.today()
        tomorrow = date.today() + timedelta(days=1)

        samples = [
            # Sampling trigger is planned_date
            Sample(sample_id=f"DASH-1", status="Plan", planned_date=yesterday, sample_point_id=sp.id),
            Sample(sample_id=f"DASH-2", status="Sample", planned_date=today, sample_point_id=sp.id),
            # Disembark trigger is disembark_expected_date
            Sample(sample_id=f"DASH-3", status="Disembark preparation", disembark_expected_date=tomorrow, sample_point_id=sp.id)
        ]
        
        db.bulk_save_objects(samples)
        db.commit()

        res = client.get("/api/chemical/dashboard-stats")
        assert res.status_code == 200
        data = res.json()
        
        # We expect "sampling" card to have:
        # overdue = 1 (planned_date < today)
        # due_today = 1 (planned_date == today)
        sampling_group = data.get("sampling", {})
        assert sampling_group.get("overdue", 0) >= 1
        assert sampling_group.get("due_today", 0) >= 1
        
        # "disembark" card shouldn't have overdue related to these, but due_tomorrow = 1
        disembark_group = data.get("disembark", {})
        assert disembark_group.get("due_tomorrow", 0) >= 1
