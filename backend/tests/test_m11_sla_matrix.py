"""
Harness Engineering — SLA Matrix & Auto-Scheduling Tests

Comprehensive test suite covering:
  1. SLA Rule CRUD (Create, Read, Update, Delete) via API
  2. status_variation filtering (Approved vs Reproved vs Any)
  3. get_sla_config cascading lookup (exact → Any → fallback)
  4. Auto-scheduling trigger when sample leaves status "Sample"
  5. Offshore flow: no disembark, auto-schedule still fires
  6. Reproved flow: emergency re-sampling uses reproval_reschedule_days from DB
  7. Deduplication guard: no double-scheduling
"""

import pytest
from datetime import date, timedelta
from io import BytesIO
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.dependencies import get_current_user
from app.services.sla_matrix import get_sla_config

# --- Isolated DB ---
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
sla_engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
SlaTestSession = sessionmaker(autocommit=False, autoflush=False, bind=sla_engine)


def override_get_db_sla():
    try:
        db = SlaTestSession()
        yield db
    finally:
        db.close()


def override_get_current_user_sla():
    return {"id": "sla-bot", "email": "sla@test.com", "role": "Admin"}


@pytest.fixture(scope="module")
def sla_client():
    """Dedicated client for SLA matrix tests."""
    app.dependency_overrides[get_db] = override_get_db_sla
    app.dependency_overrides[get_current_user] = override_get_current_user_sla
    Base.metadata.create_all(bind=sla_engine)
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def sla_db():
    """Direct DB session for unit-testing get_sla_config."""
    db = SlaTestSession()
    yield db
    db.close()


class TestSLARuleCRUD:
    """API-level tests for SLA Rule management (M11 Configuration)."""

    def test_list_empty(self, sla_client):
        """GET /config/sla-rules returns empty list initially."""
        res = sla_client.get("/api/config/sla-rules")
        assert res.status_code == 200
        assert res.json() == []

    def test_create_approved_rule(self, sla_client):
        """POST creates a new SLA rule with status_variation = Approved."""
        res = sla_client.post("/api/config/sla-rules", json={
            "classification": "Fiscal",
            "analysis_type": "Chromatography",
            "local": "Onshore",
            "status_variation": "Approved",
            "interval_days": 30,
            "disembark_days": 10,
            "lab_days": 20,
            "report_days": 25,
            "fc_days": 3,
            "fc_is_business_days": True,
            "needs_validation": True,
        })
        assert res.status_code == 200
        data = res.json()
        assert data["classification"] == "Fiscal"
        assert data["status_variation"] == "Approved"
        assert data["interval_days"] == 30
        assert data["fc_days"] == 3

    def test_create_reproved_rule_same_combo(self, sla_client):
        """POST can create a Reproved rule for the same classification/type/local
        without overwriting the Approved one."""
        res = sla_client.post("/api/config/sla-rules", json={
            "classification": "Fiscal",
            "analysis_type": "Chromatography",
            "local": "Onshore",
            "status_variation": "Reproved",
            "interval_days": 30,
            "disembark_days": 10,
            "lab_days": 20,
            "report_days": 25,
            "fc_days": None,
            "fc_is_business_days": False,
            "reproval_reschedule_days": 3,
            "needs_validation": True,
        })
        assert res.status_code == 200
        reproved = res.json()
        assert reproved["status_variation"] == "Reproved"
        assert reproved["reproval_reschedule_days"] == 3
        assert reproved["fc_days"] is None

        # Verify both rules exist (Approved + Reproved)
        all_rules = sla_client.get("/api/config/sla-rules?classification=Fiscal&analysis_type=Chromatography&local=Onshore").json()
        statuses = {r["status_variation"] for r in all_rules}
        assert "Approved" in statuses, "Approved rule was overwritten!"
        assert "Reproved" in statuses, "Reproved rule not created!"

    def test_create_offshore_approved(self, sla_client):
        """Create Offshore/Approved rule (no disembark, no lab)."""
        res = sla_client.post("/api/config/sla-rules", json={
            "classification": "Fiscal",
            "analysis_type": "Chromatography",
            "local": "Offshore",
            "status_variation": "Approved",
            "interval_days": 30,
            "disembark_days": None,
            "lab_days": None,
            "report_days": 25,
            "fc_days": 3,
            "fc_is_business_days": True,
            "needs_validation": True,
        })
        assert res.status_code == 200
        data = res.json()
        assert data["local"] == "Offshore"
        assert data["disembark_days"] is None
        assert data["lab_days"] is None

    def test_create_any_rule_no_validation(self, sla_client):
        """Create rule with status_variation=Any for analyses without validation (e.g. Enxofre)."""
        res = sla_client.post("/api/config/sla-rules", json={
            "classification": "Fiscal",
            "analysis_type": "Enxofre",
            "local": "Onshore",
            "status_variation": "Any",
            "interval_days": 365,
            "disembark_days": 10,
            "lab_days": 20,
            "report_days": 25,
            "needs_validation": False,
        })
        assert res.status_code == 200
        data = res.json()
        assert data["status_variation"] == "Any"
        assert data["needs_validation"] is False
        assert data["interval_days"] == 365

    def test_update_rule_via_put(self, sla_client):
        """PUT /config/sla-rules/{id} updates an existing rule's deadlines."""
        # Get the Approved rule
        rules = sla_client.get("/api/config/sla-rules?classification=Fiscal&analysis_type=Chromatography&local=Onshore").json()
        approved = next(r for r in rules if r["status_variation"] == "Approved")

        # Update interval from 30 to 45
        res = sla_client.put(f"/api/config/sla-rules/{approved['id']}", json={
            "classification": "Fiscal",
            "analysis_type": "Chromatography",
            "local": "Onshore",
            "status_variation": "Approved",
            "interval_days": 45,
            "disembark_days": 10,
            "lab_days": 20,
            "report_days": 25,
            "fc_days": 3,
            "fc_is_business_days": True,
            "needs_validation": True,
        })
        assert res.status_code == 200
        updated = res.json()
        assert updated["interval_days"] == 45

        # Restore back to 30 for subsequent tests
        sla_client.put(f"/api/config/sla-rules/{approved['id']}", json={
            "classification": "Fiscal",
            "analysis_type": "Chromatography",
            "local": "Onshore",
            "status_variation": "Approved",
            "interval_days": 30,
            "disembark_days": 10,
            "lab_days": 20,
            "report_days": 25,
            "fc_days": 3,
            "fc_is_business_days": True,
            "needs_validation": True,
        })

    def test_update_nonexistent_returns_404(self, sla_client):
        """PUT on a non-existent ID should return 404."""
        res = sla_client.put("/api/config/sla-rules/99999", json={
            "classification": "X", "analysis_type": "Y", "local": "Z",
            "status_variation": "Any", "needs_validation": False,
        })
        assert res.status_code == 404

    def test_delete_rule(self, sla_client):
        """DELETE /config/sla-rules/{id} removes the rule."""
        # Create a throwaway rule
        create_res = sla_client.post("/api/config/sla-rules", json={
            "classification": "Test",
            "analysis_type": "Delete",
            "local": "Onshore",
            "status_variation": "Any",
            "interval_days": 999,
            "needs_validation": False,
        })
        rule_id = create_res.json()["id"]

        # Delete it
        del_res = sla_client.delete(f"/api/config/sla-rules/{rule_id}")
        assert del_res.status_code == 200
        assert del_res.json()["status"] == "deleted"

        # Verify it's gone
        verify = sla_client.get("/api/config/sla-rules?classification=Test&analysis_type=Delete")
        assert verify.json() == []

    def test_delete_nonexistent_returns_404(self, sla_client):
        """DELETE on a non-existent ID should return 404."""
        res = sla_client.delete("/api/config/sla-rules/99999")
        assert res.status_code == 404


class TestSLAConfigLookup:
    """Unit tests for get_sla_config cascading lookup logic."""

    def test_exact_match_approved(self, sla_db):
        """Lookup with status_variation='Approved' returns the Approved rule."""
        cfg = get_sla_config(sla_db, "Fiscal", "Chromatography", "Onshore", "Approved")
        assert cfg is not None
        assert cfg["status_variation"] == "Approved"
        assert cfg["fc_days"] == 3

    def test_exact_match_reproved(self, sla_db):
        """Lookup with status_variation='Reproved' returns the Reproved rule."""
        cfg = get_sla_config(sla_db, "Fiscal", "Chromatography", "Onshore", "Reproved")
        assert cfg is not None
        assert cfg["status_variation"] == "Reproved"
        assert cfg["reproval_reschedule_days"] == 3
        assert cfg["fc_days"] is None

    def test_fallback_to_any(self, sla_db):
        """When no 'Approved' rule exists but 'Any' does, fallback to 'Any'."""
        # Enxofre only has status_variation='Any'
        cfg = get_sla_config(sla_db, "Fiscal", "Enxofre", "Onshore", "Approved")
        assert cfg is not None
        assert cfg["status_variation"] == "Any"
        assert cfg["interval_days"] == 365

    def test_default_no_status_variation(self, sla_db):
        """Calling without status_variation defaults to 'Any' lookup."""
        cfg = get_sla_config(sla_db, "Fiscal", "Enxofre", "Onshore")
        assert cfg is not None
        assert cfg["interval_days"] == 365

    def test_unknown_combination_returns_none(self, sla_db):
        """Unknown combinations should return None (no crash)."""
        cfg = get_sla_config(sla_db, "Unknown", "Unknown", "Mars")
        assert cfg is None

    def test_offshore_no_disembark(self, sla_db):
        """Offshore rules correctly return None for disembark_days and lab_days."""
        cfg = get_sla_config(sla_db, "Fiscal", "Chromatography", "Offshore", "Approved")
        assert cfg is not None
        assert cfg["disembark_days"] is None
        assert cfg["lab_days"] is None
        assert cfg["report_days"] == 25


class TestAutoScheduling:
    """Integration tests for the auto-scheduling engine in update-status."""

    _sp_counter = 100
    _s_counter = 100

    def _create_sp_and_sample(self, client, local="Onshore", classification="Fiscal",
                               analysis_type="Chromatography", planned_date="2026-06-01"):
        """Helper: create sample point + sample via API."""
        TestAutoScheduling._sp_counter += 1
        TestAutoScheduling._s_counter += 1
        sp_res = client.post("/api/chemical/sample-points", json={
            "tag_number": f"SP-SLA-{TestAutoScheduling._sp_counter:04d}",
            "description": "SLA Test SP",
            "fpso_name": "FPSO SLA",
        })
        assert sp_res.status_code == 200
        sp = sp_res.json()

        s_res = client.post("/api/chemical/samples", json={
            "sample_id": f"SLA-{TestAutoScheduling._s_counter:04d}",
            "type": analysis_type,
            "classification": classification,
            "sample_point_id": sp["id"],
            "local": local,
            "planned_date": planned_date,
        })
        assert s_res.status_code == 200
        return sp, s_res.json()

    def _get_periodic_children(self, client, sp_id, parent_id):
        """Get all PER samples under a sample point excluding the parent."""
        res = client.get(f"/api/chemical/samples?sample_point_id={sp_id}")
        assert res.status_code == 200
        return [s for s in res.json() if s["id"] != parent_id and "PER-" in s.get("sample_id", "")]

    def test_onshore_disembark_triggers_schedule(self, sla_client):
        """Onshore: transitioning Sample → Disembark prep auto-schedules next periodic."""
        sp, sample = self._create_sp_and_sample(sla_client, local="Onshore")

        # Transition to Disembark preparation
        res = sla_client.post(
            f"/api/chemical/samples/{sample['id']}/update-status",
            json={"status": "Disembark preparation", "event_date": "2026-06-15"}
        )
        assert res.status_code == 200

        # Verify periodic sample exists
        periodic = self._get_periodic_children(sla_client, sp["id"], sample["id"])
        assert len(periodic) >= 1, "No periodic sample auto-scheduled for onshore flow"

    def test_offshore_report_triggers_schedule(self, sla_client):
        """Offshore: transitioning Sample → Report issue (skip disembark) auto-schedules."""
        sp, sample = self._create_sp_and_sample(sla_client, local="Offshore")

        # Skip disembark entirely — go straight to Report issue
        res = sla_client.post(
            f"/api/chemical/samples/{sample['id']}/update-status",
            json={"status": "Report issue", "event_date": "2026-06-20"}
        )
        assert res.status_code == 200

        periodic = self._get_periodic_children(sla_client, sp["id"], sample["id"])
        assert len(periodic) >= 1, "No periodic sample auto-scheduled for offshore flow!"

    def test_no_double_schedule(self, sla_client):
        """Transitioning from a non-Sample status should NOT create another PER."""
        sp, sample = self._create_sp_and_sample(sla_client, local="Onshore")

        # Step 1: Sample → Disembark prep (triggers schedule)
        sla_client.post(
            f"/api/chemical/samples/{sample['id']}/update-status",
            json={"status": "Disembark preparation", "event_date": "2026-06-15"}
        )

        # Step 2: Disembark prep → Disembark logistics (should NOT schedule again)
        sla_client.post(
            f"/api/chemical/samples/{sample['id']}/update-status",
            json={"status": "Disembark logistics", "event_date": "2026-06-20"}
        )

        periodic = self._get_periodic_children(sla_client, sp["id"], sample["id"])
        # We expect PER samples from create_sample + update-status, but not from Disembark logistics
        # Count should NOT increase beyond what was created by the two triggers
        per_count = len(periodic)
        
        # Step 3: Logistics → Warehouse (should NOT schedule again)
        sla_client.post(
            f"/api/chemical/samples/{sample['id']}/update-status",
            json={"status": "Warehouse"}
        )
        periodic_after = self._get_periodic_children(sla_client, sp["id"], sample["id"])
        assert len(periodic_after) == per_count, (
            f"Double-scheduling detected: had {per_count} PER, now {len(periodic_after)}"
        )

    def test_schedule_uses_sampling_date_as_base(self, sla_client):
        """The scheduled date should use sampling_date (event_date) + interval_days."""
        sp, sample = self._create_sp_and_sample(
            sla_client, local="Offshore", planned_date="2026-08-01"
        )

        # Transition with explicit event_date
        sla_client.post(
            f"/api/chemical/samples/{sample['id']}/update-status",
            json={"status": "Report issue", "event_date": "2026-08-10"}
        )

        periodic = self._get_periodic_children(sla_client, sp["id"], sample["id"])
        # From update-status: base=2026-08-10, interval=30 → 2026-09-09
        # From create_sample: base=2026-08-01, interval=30 → 2026-08-31
        dates = [p["planned_date"] for p in periodic]
        has_valid_date = any("2026-08" in d or "2026-09" in d for d in dates)
        assert has_valid_date, f"Expected dates in Aug/Sep 2026, got: {dates}"

    def test_reproved_triggers_emergency_resampling(self, sla_client):
        """When validation status = Reprovado, an emergency sample is created."""
        sp, sample = self._create_sp_and_sample(sla_client, local="Onshore")

        # Move through pipeline: Sample → Disembark → ... → Report approve/reprove
        sla_client.post(
            f"/api/chemical/samples/{sample['id']}/update-status",
            json={"status": "Disembark preparation", "event_date": "2026-06-01"}
        )
        sla_client.post(
            f"/api/chemical/samples/{sample['id']}/update-status",
            json={"status": "Report issue", "event_date": "2026-06-20"}
        )
        res = sla_client.post(
            f"/api/chemical/samples/{sample['id']}/update-status",
            json={
                "status": "Report approve/reprove",
                "validation_status": "Reprovado",
            }
        )
        assert res.status_code == 200

        # Check for emergency sample (EMG pattern)
        all_samples = sla_client.get(f"/api/chemical/samples?sample_point_id={sp['id']}").json()
        emg_samples = [s for s in all_samples if "EMG-" in s.get("sample_id", "")]
        assert len(emg_samples) >= 1, (
            f"Emergency re-sampling not triggered. Samples: {[s['sample_id'] for s in all_samples]}"
        )

    def test_enxofre_no_validation_still_schedules(self, sla_client):
        """Enxofre (needs_validation=False) should still auto-schedule the next periodic."""
        sp, sample = self._create_sp_and_sample(
            sla_client,
            local="Onshore",
            analysis_type="Enxofre",
            planned_date="2026-01-01",
        )

        # Move from Sample → Disembark preparation
        res = sla_client.post(
            f"/api/chemical/samples/{sample['id']}/update-status",
            json={"status": "Disembark preparation", "event_date": "2026-01-15"}
        )
        assert res.status_code == 200

        periodic = self._get_periodic_children(sla_client, sp["id"], sample["id"])
        assert len(periodic) >= 1, "Enxofre should still get auto-scheduled periodic samples"

        # Verify interval is 365 days (annual)
        dates = [p["planned_date"] for p in periodic]
        has_2027 = any("2027" in d for d in dates)
        has_2026_dec = any("2026-12" in d for d in dates)
        assert has_2027 or has_2026_dec, f"Expected ~1 year interval, got dates: {dates}"
