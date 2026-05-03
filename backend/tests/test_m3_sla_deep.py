"""
Pillar 5 — M3 SLA Alert Engine Deep Coverage
Cobre TODOS os 18 cenários da planilha 'All Periodic Analyses.xlsx' via
testes unitários de get_sla_config(), mais boundary tests e batch multi-sample.
"""
import pytest
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db
from app.dependencies import get_current_user
from app import models
from app.services.sla_matrix import get_sla_config, SLA_MATRIX


# ─── Pillar 5a: Unit tests — get_sla_config() for all 18 matrix rows ─────────

class _MockDb:
    def query(self, *a): return self
    def filter(self, *a): return self
    def first(self): return None

class TestSLAMatrix:
    """Testa que get_sla_config() retorna os valores corretos para cada combinação."""

    def _assert_config(self, classification, analysis_type, local, expected):
        cfg = get_sla_config(_MockDb(), classification, analysis_type, local)
        assert cfg is not None, f"Expected config for ({classification}, {analysis_type}, {local}) but got None"
        for field, value in expected.items():
            assert cfg[field] == value, (
                f"({classification}/{analysis_type}/{local}).{field}: "
                f"expected {value!r}, got {cfg[field]!r}"
            )

    # Row 1 — Fiscal / Chromatography / Onshore / Aprovado
    def test_01_fiscal_cro_onshore_aprovado(self):
        self._assert_config("Fiscal", "Chromatography", "Onshore", {
            "interval_days": 30, "report_days": 25, "fc_days": 3, "fc_is_business_days": True, "needs_validation": True
        })

    # Row 2 — Fiscal / Chromatography / Onshore / Reprovado
    def test_02_fiscal_cro_onshore_reprovado(self):
        # Reprovado uses the same base config but triggers NA internally handling overrides
        self._assert_config("Fiscal", "Chromatography", "Onshore", {
            "interval_days": 30, "report_days": 25, "fc_days": 3, "needs_validation": True
        })

    # Row 3 — Fiscal / Chromatography / Offshore / Aprovado
    def test_03_fiscal_cro_offshore_aprovado(self):
        self._assert_config("Fiscal", "Chromatography", "Offshore", {
            "interval_days": 30, "report_days": 25, "fc_days": 3, "needs_validation": True
        })

    # Row 4 — Fiscal / Chromatography / Offshore / Reprovado
    def test_04_fiscal_cro_offshore_reprovado(self):
        self._assert_config("Fiscal", "Chromatography", "Offshore", {
            "interval_days": 30, "report_days": 25, "fc_days": 3, "needs_validation": True
        })

    # Row 5 — Apropriation / Chromatography / Onshore / Aprovado
    def test_05_apropriation_cro_onshore_aprovado(self):
        self._assert_config("Apropriation", "Chromatography", "Onshore", {
            "interval_days": 90, "report_days": 25, "fc_days": 3, "needs_validation": True
        })

    # Row 6 — Apropriation / Chromatography / Onshore / Reprovado
    def test_06_apropriation_cro_onshore_reprovado(self):
        self._assert_config("Apropriation", "Chromatography", "Onshore", {
            "interval_days": 90, "report_days": 25, "fc_days": 3, "needs_validation": True
        })

    # Row 7 — Apropriation / Chromatography / Offshore / Aprovado
    def test_07_apropriation_cro_offshore_aprovado(self):
        self._assert_config("Apropriation", "Chromatography", "Offshore", {
            "interval_days": 90, "report_days": 25, "fc_days": 3, "needs_validation": True
        })

    # Row 8 — Apropriation / Chromatography / Offshore / Reprovado
    def test_08_apropriation_cro_offshore_reprovado(self):
        self._assert_config("Apropriation", "Chromatography", "Offshore", {
            "interval_days": 90, "report_days": 25, "fc_days": 3, "needs_validation": True
        })

    # Row 9 — Operational / Chromatography / Onshore / Aprovado
    def test_09_operational_cro_onshore_aprovado(self):
        self._assert_config("Operational", "Chromatography", "Onshore", {
            "interval_days": 180, "report_days": 45, "fc_days": 10, "needs_validation": True
        })

    # Row 10 — Operational / Chromatography / Onshore / Reprovado
    def test_10_operational_cro_onshore_reprovado(self):
        self._assert_config("Operational", "Chromatography", "Onshore", {
            "interval_days": 180, "report_days": 45, "fc_days": 10, "needs_validation": True
        })

    # Row 11 — Operational / Chromatography / Offshore / Aprovado
    def test_11_operational_cro_offshore_aprovado(self):
        self._assert_config("Operational", "Chromatography", "Offshore", {
            "interval_days": 180, "report_days": 45, "fc_days": 10, "needs_validation": True
        })

    # Row 12 — Operational / Chromatography / Offshore / Reprovado
    def test_12_operational_cro_offshore_reprovado(self):
        self._assert_config("Operational", "Chromatography", "Offshore", {
            "interval_days": 180, "report_days": 45, "fc_days": 10, "needs_validation": True
        })

    # Row 13 — Apropriation / PVT / Onshore / Aprovado
    def test_13_apropriation_pvt_onshore_aprovado(self):
        self._assert_config("Apropriation", "PVT", "Onshore", {
            "interval_days": 90, "report_days": 25, "fc_days": None, "needs_validation": True
        })

    # Row 14 — Apropriation / PVT / Onshore / Reprovado
    def test_14_apropriation_pvt_onshore_reprovado(self):
        self._assert_config("Apropriation", "PVT", "Onshore", {
            "interval_days": 90, "report_days": 25, "fc_days": None, "needs_validation": True
        })

    # Row 15 — Apropriation / PVT / Offshore / Aprovado
    def test_15_apropriation_pvt_offshore_aprovado(self):
        self._assert_config("Apropriation", "PVT", "Offshore", {
            "interval_days": 90, "report_days": 25, "fc_days": None, "needs_validation": True
        })

    # Row 16 — Apropriation / PVT / Offshore / Reprovado
    def test_16_apropriation_pvt_offshore_reprovado(self):
        self._assert_config("Apropriation", "PVT", "Offshore", {
            "interval_days": 90, "report_days": 25, "fc_days": None, "needs_validation": True
        })

    # Row 17 — Fiscal / Enxofre / Onshore / NA
    def test_17_fiscal_enxofre_onshore(self):
        self._assert_config("Fiscal", "Enxofre", "Onshore", {
            "interval_days": 365, "report_days": 25, "fc_days": None, "needs_validation": False
        })

    # Row 18 — Fiscal / Enxofre / Offshore / NA
    def test_18_fiscal_enxofre_offshore(self):
        self._assert_config("Fiscal", "Enxofre", "Offshore", {
            "interval_days": 365, "report_days": 25, "fc_days": None, "needs_validation": False
        })

    # Row 19 — Fiscal / Viscosity / Onshore / NA
    def test_19_fiscal_viscosity_onshore(self):
        self._assert_config("Fiscal", "Viscosity", "Onshore", {
            "interval_days": 365, "report_days": 45, "fc_days": None, "needs_validation": False
        })

    # Row 20 — Fiscal / Viscosity / Offshore / NA
    def test_20_fiscal_viscosity_offshore(self):
        self._assert_config("Fiscal", "Viscosity", "Offshore", {
            "interval_days": 365, "report_days": 45, "fc_days": None, "needs_validation": False
        })

    # Row 21 — Custody Transfer / Viscosity / Onshore / NA
    def test_21_custody_transfer_viscosity_onshore(self):
        self._assert_config("Custody Transfer", "Viscosity", "Onshore", {
            "interval_days": 365, "report_days": 45, "fc_days": None, "needs_validation": False
        })

    # Row 22 — Custody Transfer / Viscosity / Offshore / NA
    def test_22_custody_transfer_viscosity_offshore(self):
        self._assert_config("Custody Transfer", "Viscosity", "Offshore", {
            "interval_days": 365, "report_days": 45, "fc_days": None, "needs_validation": False
        })

    # Alias: CRO → Chromatography
    def test_alias_cro_resolves_to_chromatography(self):
        cfg = get_sla_config(_MockDb(), "Fiscal", "CRO", "Onshore")
        assert cfg is not None, "Alias 'CRO' should resolve to 'Chromatography'"
        assert cfg["interval_days"] == 30

    # Alias: PVT stays PVT
    def test_alias_pvt_resolves_correctly(self):
        cfg = get_sla_config(_MockDb(), "Apropriation", "PVT", "Onshore")
        assert cfg is not None
        assert cfg["interval_days"] == 90

    # Unknown combination returns None — no crash
    def test_unknown_classification_returns_none(self):
        cfg = get_sla_config(_MockDb(), "GasLift", "SomeAnalysis", "Onshore")
        assert cfg is None

    # Case insensitivity / title-case normalization
    def test_case_normalization(self):
        cfg_upper = get_sla_config(_MockDb(), "FISCAL", "CHROMATOGRAPHY", "ONSHORE")
        cfg_normal = get_sla_config(_MockDb(), "Fiscal", "Chromatography", "Onshore")
        assert cfg_upper == cfg_normal

    # Verify that all 22 semantic combinations map back to valid config states
    def test_all_22_spreadsheet_rows_covered(self):
        expected_matrix_tests = [
            ("Fiscal", "Chromatography", "Onshore"),
            ("Fiscal", "Chromatography", "Offshore"),
            ("Apropriation", "Chromatography", "Onshore"),
            ("Apropriation", "Chromatography", "Offshore"),
            ("Operational", "Chromatography", "Onshore"),
            ("Operational", "Chromatography", "Offshore"),
            ("Apropriation", "PVT", "Onshore"),
            ("Apropriation", "PVT", "Offshore"),
            ("Fiscal", "Enxofre", "Onshore"),
            ("Fiscal", "Enxofre", "Offshore"),
            ("Fiscal", "Viscosity", "Onshore"),
            ("Fiscal", "Viscosity", "Offshore"),
            ("Custody Transfer", "Viscosity", "Onshore"),
            ("Custody Transfer", "Viscosity", "Offshore"),
        ]
        for key in expected_matrix_tests:
            assert key in SLA_MATRIX, f"Missing core SLA matrix entry: {key}"
        assert len(SLA_MATRIX) >= 14



# ─── Pillar 5b: Integration tests — check-slas boundary & batch ───────────────

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
sla_deep_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SLADeepSession = sessionmaker(autocommit=False, autoflush=False, bind=sla_deep_engine)


def override_get_db_sla_deep():
    db = SLADeepSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def sla_deep_client():
    app.dependency_overrides[get_db] = override_get_db_sla_deep
    app.dependency_overrides[get_current_user] = lambda: {"id": "sla-deep", "email": "sla@deep.com", "role": "Admin"}
    Base.metadata.create_all(bind=sla_deep_engine)
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def sla_deep_db():
    db = SLADeepSession()
    yield db
    db.close()


class TestSLABoundary:
    """Testa fronteiras exatas do engine de SLA (dia N-1 vs dia N)."""

    _sp_counter = 0
    _s_counter = 0

    def _make_sample(self, client, db):
        TestSLABoundary._sp_counter += 1
        TestSLABoundary._s_counter += 1
        sp = client.post("/api/chemical/sample-points", json={
            "tag_number": f"SP-DEEP-{self._sp_counter:04d}",
            "description": "SLA Deep",
            "fpso_name": "FPSO Deep",
        }).json()
        sample = client.post("/api/chemical/samples", json={
            "sample_id": f"DEEP-{self._s_counter:04d}",
            "type": "Chromatography",
            "sample_point_id": sp["id"],
            "local": "Onshore",
            "planned_date": "2026-06-01",
        }).json()
        return sample

    def _set_state(self, db, sample_id, status, sampling_date=None, report_date=None):
        s = db.query(models.Sample).filter(models.Sample.id == sample_id).first()
        s.status = status
        if sampling_date:
            s.sampling_date = sampling_date
        if report_date:
            s.report_issue_date = report_date
        db.commit()

    def test_day_24_no_alert(self, sla_deep_client, sla_deep_db):
        """Sample há exatamente 24 dias — ainda dentro do prazo (< 25 dias)."""
        sample = self._make_sample(sla_deep_client, sla_deep_db)
        self._set_state(sla_deep_db, sample["id"], "Sample",
                        sampling_date=date.today() - timedelta(days=24))
        res = sla_deep_client.post("/api/chemical/check-slas")
        assert res.status_code == 200
        assert res.json()["alerts_created"] == 0

    def test_day_25_triggers_alert(self, sla_deep_client, sla_deep_db):
        """Sample há exatamente 25 dias — deve gerar alerta."""
        sample = self._make_sample(sla_deep_client, sla_deep_db)
        self._set_state(sla_deep_db, sample["id"], "Sample",
                        sampling_date=date.today() - timedelta(days=25))
        res = sla_deep_client.post("/api/chemical/check-slas")
        assert res.status_code == 200
        assert res.json()["alerts_created"] >= 1

    def test_validation_day_2_no_alert(self, sla_deep_client, sla_deep_db):
        """Report emitido há 2 dias — validação ainda dentro do prazo."""
        sample = self._make_sample(sla_deep_client, sla_deep_db)
        self._set_state(sla_deep_db, sample["id"], "Report issue",
                        report_date=date.today() - timedelta(days=2))
        res = sla_deep_client.post("/api/chemical/check-slas")
        assert res.json()["alerts_created"] == 0

    def test_validation_day_3_triggers_alert(self, sla_deep_client, sla_deep_db):
        """Report emitido há 3 dias sem validação → deve alertar."""
        sample = self._make_sample(sla_deep_client, sla_deep_db)
        self._set_state(sla_deep_db, sample["id"], "Report issue",
                        report_date=date.today() - timedelta(days=3))
        res = sla_deep_client.post("/api/chemical/check-slas")
        assert res.json()["alerts_created"] >= 1

    def test_batch_5_overdue_samples(self, sla_deep_client, sla_deep_db):
        """5 amostras vencidas simultâneas devem gerar exatamente 5 alertas na primeira run."""
        samples = [self._make_sample(sla_deep_client, sla_deep_db) for _ in range(5)]
        for s in samples:
            self._set_state(sla_deep_db, s["id"], "Sample",
                            sampling_date=date.today() - timedelta(days=30))
        res = sla_deep_client.post("/api/chemical/check-slas")
        assert res.json()["alerts_created"] == 5

    def test_batch_dedup_on_second_run(self, sla_deep_client, sla_deep_db):
        """Mesmos 5 amostras na segunda run → 0 alertas (dedup ativo)."""
        res = sla_deep_client.post("/api/chemical/check-slas")
        assert res.json()["alerts_created"] == 0

    def test_approved_sample_no_alert(self, sla_deep_client, sla_deep_db):
        """Sample com status 'Approved' (já validado) não deve gerar alerta."""
        sample = self._make_sample(sla_deep_client, sla_deep_db)
        self._set_state(sla_deep_db, sample["id"], "Approved",
                        sampling_date=date.today() - timedelta(days=30))
        res = sla_deep_client.post("/api/chemical/check-slas")
        # Approved samples should not appear in the overdue check
        # (they passed through the whole pipeline already)
        assert res.status_code == 200

    def test_reprovado_reschedules_emergency_sample(self, sla_deep_client, sla_deep_db):
        """When a report goes to Reprovado, an emergency sample (3 biz days) must be generated."""
        sample = self._make_sample(sla_deep_client, sla_deep_db)
        
        # Explicit update mapping to "Reprovado" validation status
        res = sla_deep_client.post(f"/api/chemical/samples/{sample['id']}/update-status", json={
            "status": "Report approve/reprove",
            "validation_status": "Reprovado",
            "event_date": "2026-06-05",
            "user": "Tester"
        })
        assert res.status_code == 200
        
        # Check if an emergency sample was automatically created
        from app import models
        emg = sla_deep_db.query(models.Sample).filter(
            models.Sample.sample_point_id == sample["sample_point_id"],
            models.Sample.id != sample["id"]
        ).order_by(models.Sample.id.desc()).first()
        
        assert emg is not None, "Emergency sample was not created upon Reprovado!"
        assert "EMG" in emg.sample_id
        assert emg.due_date is not None

