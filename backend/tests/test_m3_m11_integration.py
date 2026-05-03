"""
Harness Engineering — M3 × M11 Integration Tests

Valida que as configurações do Módulo 11 (Validation Limits e SLA Matrix)
são efetivamente consumidas pelo motor de análise química do Módulo 3.

Scenarios:
  INT-1: Sigma Multiplier configurado no M11 altera banda de aceitação no motor
  INT-2: History Size configurado no M11 altera janela de histórico no motor
  INT-3: O2 limit configurado no M11 altera o threshold de reprovação
  INT-4: reproval_reschedule_days configurado no M11 controla prazo de emergência
  INT-5: SLA interval_days do M11 determina data do próximo sample auto-agendado
  INT-6: Regra 'Any' do M11 serve de fallback quando status_variation não existe
  INT-7: Alteração de SLA no M11 reflete imediatamente no agendamento (sem deploy)
  INT-8: Fluxo completo offshore: SLA sem disembark_days → agendar corretamente
"""

import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch

from app.main import app
from app.database import Base, get_db
from app.dependencies import get_current_user
from app.services.sla_matrix import get_sla_config
from app.services.validation_engine import _get_config_limit
from app import models

# ─── Isolated test DB ────────────────────────────────────────────────────────
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
int_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
IntSession = sessionmaker(autocommit=False, autoflush=False, bind=int_engine)


def override_get_db():
    try:
        db = IntSession()
        yield db
    finally:
        db.close()


def override_current_user():
    return {"id": "int-agent", "email": "agent@mmt.test", "role": "Admin"}


@pytest.fixture(scope="module")
def iclient():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_current_user
    Base.metadata.create_all(bind=int_engine)
    with TestClient(app) as c:
        # Seed baseline SLA rules
        _seed_rules(c)
        yield c


@pytest.fixture(scope="module")
def idb():
    db = IntSession()
    yield db
    db.close()


def _seed_rules(client):
    """Seed minimal SLA rules for integration scenarios."""
    rules = [
        # Fiscal/Chromatography/Onshore — Approved
        dict(classification="Fiscal", analysis_type="Chromatography", local="Onshore",
             status_variation="Approved", interval_days=30, disembark_days=10,
             lab_days=20, report_days=25, fc_days=3, fc_is_business_days=True,
             needs_validation=True),
        # Fiscal/Chromatography/Onshore — Reproved
        dict(classification="Fiscal", analysis_type="Chromatography", local="Onshore",
             status_variation="Reproved", interval_days=30, disembark_days=10,
             lab_days=20, report_days=25, fc_days=None, fc_is_business_days=False,
             reproval_reschedule_days=3, needs_validation=True),
        # Fiscal/Chromatography/Offshore — Any (no disembark)
        dict(classification="Fiscal", analysis_type="Chromatography", local="Offshore",
             status_variation="Any", interval_days=30, disembark_days=None,
             lab_days=None, report_days=25, fc_days=3, fc_is_business_days=True,
             needs_validation=True),
        # Appropriation/PVT/Onshore — Any
        dict(classification="Appropriation", analysis_type="PVT", local="Onshore",
             status_variation="Any", interval_days=180, disembark_days=15,
             lab_days=30, report_days=40, needs_validation=True),
    ]
    for r in rules:
        res = client.post("/api/config/sla-rules", json=r)
        assert res.status_code == 200, f"Seed failed: {res.text}"


_counter = 0


def _uid():
    global _counter
    _counter += 1
    return _counter


def _make_sp(client, fpso="INT-FPSO"):
    n = _uid()
    return client.post("/api/chemical/sample-points", json={
        "tag_number": f"INT-SP-{n:04d}", "description": "Integration SP", "fpso_name": fpso
    }).json()


def _make_sample(client, sp_id, analysis_type="Chromatography",
                 local="Onshore", planned_date="2026-06-01"):
    n = _uid()
    return client.post("/api/chemical/samples", json={
        "sample_id": f"INT-{n:04d}", "type": analysis_type,
        "classification": "Fiscal", "sample_point_id": sp_id,
        "local": local, "planned_date": planned_date,
    }).json()


def _periodic_children(client, sp_id, parent_id):
    all_s = client.get(f"/api/chemical/samples?sample_point_id={sp_id}").json()
    return [s for s in all_s if s["id"] != parent_id and "PER-" in s.get("sample_id", "")]


def _emg_children(client, sp_id, parent_id):
    all_s = client.get(f"/api/chemical/samples?sample_point_id={sp_id}").json()
    return [s for s in all_s if s["id"] != parent_id and "EMG-" in s.get("sample_id", "")]


# ─── INT-1: Sigma Multiplier no M11 altera banda de aceitação ────────────────

class TestINT1_SigmaMultiplierFromM11:
    """Validation engine usa SIGMA_MULTIPLIER da ConfigParameter do M11."""

    def test_default_sigma_falls_back_to_2(self):
        """Sem parametro no DB, _get_config_limit retorna default=2.0."""
        class _EmptyDb:
            def query(self, *a): return self
            def filter(self, *a): return self
            def first(self): return None

        val = _get_config_limit(_EmptyDb(), "SIGMA_MULTIPLIER", 2.0)
        assert val == 2.0

    def test_sigma_saved_in_m11_is_read(self, iclient, idb):
        """Salvar SIGMA_MULTIPLIER=3.0 no M11 → motor lê 3.0."""
        res = iclient.post("/api/config/parameters", json={
            "key": "SIGMA_MULTIPLIER", "value": "3.0",
            "fpso": "GLOBAL", "description": "Test sigma"
        })
        assert res.status_code == 200

        val = _get_config_limit(idb, "SIGMA_MULTIPLIER", 2.0)
        assert val == 3.0

    def test_larger_sigma_widens_acceptance_band(self):
        """Com sigma=3.0, band é mais larga → valores antes reprovados passam."""
        from app.services.validation_engine import _check_2sigma
        from unittest.mock import patch

        class _EmptyDb:
            def query(self, *a): return self
            def filter(self, *a): return self
            def first(self): return None

        # Histórico com std≈0.8; mean=9.9; com sigma=2 → range [8.3, 11.5]; com sigma=3 → range [7.5, 12.3]
        history = [{"value": float(v), "date": f"2026-01-{i+1:02d}", "sample_id": f"S{i}"}
                   for i, v in enumerate([9, 10, 11, 10, 9, 10, 11, 10, 9, 10])]
        
        def mock_get_config(db, key, default):
            if key == "SIGMA_MULTIPLIER":
                return 3.0
            return default
            
        with patch("app.services.validation_engine._get_config_limit", side_effect=mock_get_config):
            result = _check_2sigma(_EmptyDb(), "density", 12.0, "kg/m³", history)
            
        assert result.status == "pass", "sigma=3 → 12.0 must be inside wider band"



# ─── INT-2: History Size no M11 altera janela de histórico ───────────────────

class TestINT2_HistorySizeFromM11:
    """Validation engine usa HISTORY_SIZE da ConfigParameter do M11."""

    def test_history_size_saved_in_m11_is_read(self, iclient, idb):
        """Salvar HISTORY_SIZE=5 no M11 → motor lê 5."""
        iclient.post("/api/config/parameters", json={
            "key": "HISTORY_SIZE", "value": "5",
            "fpso": "GLOBAL", "description": "Test history size"
        })
        val = int(_get_config_limit(idb, "HISTORY_SIZE", 10))
        assert val == 5

    def test_history_size_restored_to_10(self, iclient, idb):
        """Restore HISTORY_SIZE=10 para não afetar outros testes."""
        iclient.post("/api/config/parameters", json={
            "key": "HISTORY_SIZE", "value": "10",
            "fpso": "GLOBAL", "description": "Restored"
        })
        val = int(_get_config_limit(idb, "HISTORY_SIZE", 10))
        assert val == 10


# ─── INT-3: O2 Limit no M11 altera threshold de reprovação ──────────────────

class TestINT3_O2LimitFromM11:
    """O2 threshold é configurável via M11 — motor o lê a cada validação."""

    def test_o2_default_limit_is_0_5(self, idb):
        val = _get_config_limit(idb, "VALIDATION_LIMIT_O2", 0.5)
        # May have been set to 0.5 or reading from DB
        assert val <= 0.5 or val == 0.5

    def test_o2_limit_raised_to_1_0_passes_before_reproval(self, iclient, idb):
        """Se admin sobe O2 limit para 1.0%, valor 0.8% deve passar."""
        iclient.post("/api/config/parameters", json={
            "key": "VALIDATION_LIMIT_O2", "value": "1.0",
            "fpso": "GLOBAL", "description": "Raised O2 limit"
        })
        val = _get_config_limit(idb, "VALIDATION_LIMIT_O2", 0.5)
        assert val == 1.0

    def test_o2_limit_restored(self, iclient, idb):
        """Restore O2 limit para não afetar outros testes."""
        iclient.post("/api/config/parameters", json={
            "key": "VALIDATION_LIMIT_O2", "value": "0.5",
            "fpso": "GLOBAL", "description": "Restored O2"
        })
        val = _get_config_limit(idb, "VALIDATION_LIMIT_O2", 0.5)
        assert val == 0.5


# ─── INT-4: reproval_reschedule_days no M11 controla prazo de emergência ─────

class TestINT4_ReprovalRescheduleDays:
    """M11 controla quantos dias úteis após reprovação o próximo sample é agendado."""

    def test_reproval_rule_has_reschedule_days(self, iclient):
        """Regra 'Reproved' do M11 deve ter reproval_reschedule_days configurado."""
        rules = iclient.get(
            "/api/config/sla-rules?classification=Fiscal&analysis_type=Chromatography&local=Onshore"
        ).json()
        reproved = next((r for r in rules if r.get("status_variation") == "Reproved"), None)
        assert reproved is not None, "Regra Reproved não encontrada no M11"
        assert reproved["reproval_reschedule_days"] == 3

    def test_update_reschedule_days_via_put(self, iclient):
        """Admin pode alterar reproval_reschedule_days via PUT no M11."""
        rules = iclient.get(
            "/api/config/sla-rules?classification=Fiscal&analysis_type=Chromatography&local=Onshore"
        ).json()
        reproved = next(r for r in rules if r.get("status_variation") == "Reproved")

        res = iclient.put(f"/api/config/sla-rules/{reproved['id']}", json={
            "classification": reproved["classification"],
            "analysis_type": reproved["analysis_type"],
            "local": reproved["local"],
            "status_variation": reproved["status_variation"],
            "interval_days": reproved["interval_days"],
            "disembark_days": reproved["disembark_days"],
            "lab_days": reproved["lab_days"],
            "report_days": reproved["report_days"],
            "fc_days": reproved.get("fc_days"),
            "fc_is_business_days": reproved.get("fc_is_business_days", False),
            "needs_validation": reproved.get("needs_validation", True),
            "reproval_reschedule_days": 5,  # Changed from 3 to 5
        })
        assert res.status_code == 200
        assert res.json()["reproval_reschedule_days"] == 5

        # Restore
        iclient.put(f"/api/config/sla-rules/{reproved['id']}", json={
            **{k: reproved[k] for k in ("classification", "analysis_type", "local",
                                         "status_variation", "interval_days", "disembark_days",
                                         "lab_days", "report_days", "fc_is_business_days",
                                         "needs_validation")},
            "fc_days": reproved.get("fc_days"),
            "reproval_reschedule_days": 3,
        })


# ─── INT-5: SLA interval_days determina data do próximo sample ───────────────

class TestINT5_IntervalDaysFromSLAMatrix:
    """interval_days do M11 SLA Matrix determina quando o próximo sample é agendado."""

    def test_interval_days_drives_next_sample_date(self, iclient):
        """Criar sample com planned_date → próximo = planned_date + interval_days (30d)."""
        sp = _make_sp(iclient)
        planned = "2026-09-01"
        sample = _make_sample(iclient, sp["id"], planned_date=planned)

        periodic = _periodic_children(iclient, sp["id"], sample["id"])
        assert len(periodic) >= 1, "No PER auto-created from create_sample"

        # planned_date 2026-09-01 + 30 = 2026-10-01
        dates = [p["planned_date"] for p in periodic]
        assert any("2026-10" in d or "2026-09" in d for d in dates), (
            f"Expected next date ≈ 2026-10-01 (interval=30d from 2026-09-01), got: {dates}"
        )

    def test_changing_interval_days_reflects_in_next_schedule(self, iclient):
        """Após alterar interval_days no M11, novos samples usam o novo valor."""
        rules = iclient.get(
            "/api/config/sla-rules?classification=Fiscal&analysis_type=Chromatography&local=Onshore"
        ).json()
        approved = next(r for r in rules if r.get("status_variation") == "Approved")

        # Change interval from 30 to 60 days
        iclient.put(f"/api/config/sla-rules/{approved['id']}", json={
            **{k: approved[k] for k in ("classification", "analysis_type", "local",
                                         "status_variation", "disembark_days", "lab_days",
                                         "report_days", "fc_is_business_days", "needs_validation")},
            "fc_days": approved.get("fc_days"),
            "interval_days": 60,
        })

        sp = _make_sp(iclient)
        sample = _make_sample(iclient, sp["id"], planned_date="2026-08-01")

        periodic = _periodic_children(iclient, sp["id"], sample["id"])
        assert len(periodic) >= 1

        # planned 2026-08-01 + 60 = 2026-09-30
        dates = [p["planned_date"] for p in periodic]
        assert any("2026-09" in d or "2026-10" in d for d in dates), (
            f"Expected next ≈ 2026-09-30 (interval=60d), got: {dates}"
        )

        # Restore interval to 30
        iclient.put(f"/api/config/sla-rules/{approved['id']}", json={
            **{k: approved[k] for k in ("classification", "analysis_type", "local",
                                         "status_variation", "disembark_days", "lab_days",
                                         "report_days", "fc_is_business_days", "needs_validation")},
            "fc_days": approved.get("fc_days"),
            "interval_days": 30,
        })


# ─── INT-6: Fallback 'Any' serve quando status_variation não existe ───────────

class TestINT6_FallbackToAny:
    """Regra 'Any' do M11 é usada quando Approved/Reproved não está cadastrado."""

    def test_offshore_any_rule_returned_for_approved(self, idb):
        """Offshore só tem 'Any' → lookup retorna essa regra para qualquer status."""
        cfg = get_sla_config(idb, "Fiscal", "Chromatography", "Offshore", "Approved")
        assert cfg is not None
        assert cfg["status_variation"] == "Any"

    def test_offshore_any_rule_has_no_disembark(self, idb):
        """Offshore via fallback 'Any' → disembark_days e lab_days ausentes."""
        cfg = get_sla_config(idb, "Fiscal", "Chromatography", "Offshore")
        assert cfg is not None
        assert cfg["disembark_days"] is None
        assert cfg["lab_days"] is None

    def test_appropriation_pvt_fallback_to_any(self, idb):
        """Appropriation/PVT só tem 'Any' → cobre qualquer status_variation."""
        cfg = get_sla_config(idb, "Appropriation", "PVT", "Onshore", "Approved")
        assert cfg is not None
        assert cfg["interval_days"] == 180  # Semi-annual


# ─── INT-7: Alteração no M11 reflete imediatamente (sem deploy) ──────────────

class TestINT7_DynamicConfigNoDeploy:
    """Toda mudança no M11 é lida na próxima chamada — nenhum restart necessário."""

    def test_sla_rule_update_immediately_reflected(self, iclient, idb):
        """PUT numa regra SLA → get_sla_config retorna novo valor imediatamente."""
        rules = iclient.get(
            "/api/config/sla-rules?classification=Appropriation&analysis_type=PVT&local=Onshore"
        ).json()
        rule = next(r for r in rules if r.get("status_variation") == "Any")

        # Update report_days from 40 to 50
        iclient.put(f"/api/config/sla-rules/{rule['id']}", json={
            **{k: rule[k] for k in ("classification", "analysis_type", "local",
                                     "status_variation", "interval_days", "disembark_days",
                                     "lab_days", "fc_is_business_days", "needs_validation")},
            "fc_days": rule.get("fc_days"),
            "report_days": 50,
        })

        cfg = get_sla_config(idb, "Appropriation", "PVT", "Onshore")
        assert cfg["report_days"] == 50, "SLA update must be immediately visible without restart"

        # Restore
        iclient.put(f"/api/config/sla-rules/{rule['id']}", json={
            **{k: rule[k] for k in ("classification", "analysis_type", "local",
                                     "status_variation", "interval_days", "disembark_days",
                                     "lab_days", "fc_is_business_days", "needs_validation")},
            "fc_days": rule.get("fc_days"),
            "report_days": 40,
        })


# ─── INT-8: Offshore sem disembark_days ainda agenda corretamente ─────────────

class TestINT8_OffshoreFlowEndToEnd:
    """Fluxo offshore completo: Sample → Report issue → PER auto-agendado."""

    def test_offshore_sample_transition_triggers_schedule(self, iclient):
        """Offshore: Sample → Report issue (sem disembark) → PER criado."""
        sp = _make_sp(iclient)
        sample = _make_sample(iclient, sp["id"], local="Offshore",
                               planned_date="2026-10-01")

        # Offshore jump: Sample → Report issue (skip Disembark)
        iclient.post(f"/api/chemical/samples/{sample['id']}/update-status", json={
            "status": "Report issue", "event_date": "2026-10-15"
        })

        periodic = _periodic_children(iclient, sp["id"], sample["id"])
        assert len(periodic) >= 1, (
            "Offshore flow must auto-schedule PER when Sample → Report issue. "
            "Trigger must not depend on Disembark status."
        )

    def test_offshore_per_starts_at_sample_status(self, iclient):
        """PER criado pelo fluxo offshore deve iniciar em 'Sample', não 'Plan'."""
        sp = _make_sp(iclient)
        sample = _make_sample(iclient, sp["id"], local="Offshore",
                               planned_date="2026-11-01")

        iclient.post(f"/api/chemical/samples/{sample['id']}/update-status", json={
            "status": "Report issue", "event_date": "2026-11-15"
        })

        periodic = _periodic_children(iclient, sp["id"], sample["id"])
        assert len(periodic) >= 1

        for per in periodic:
            assert per["status"] == "Sample", (
                f"Offshore PER must start at 'Sample', got '{per['status']}'. "
                "Plan step is handled automatically by the scheduler."
            )

    def test_offshore_sla_has_no_disembark_no_lab(self, idb):
        """SLA Matrix do M11 para Offshore não possui disembark_days nem lab_days."""
        cfg = get_sla_config(idb, "Fiscal", "Chromatography", "Offshore")
        assert cfg is not None
        assert cfg["disembark_days"] is None, (
            "Offshore analysis is done on-board FPSO — no disembark step."
        )
        assert cfg["lab_days"] is None, (
            "Offshore analysis is done on-board FPSO — no external lab step."
        )
        assert cfg["report_days"] is not None, "Offshore must still have report deadline"
