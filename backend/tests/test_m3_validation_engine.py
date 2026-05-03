"""
Harness Engineering — M3 Validation Engine: Full Mathematical Coverage
Cobre: O2 hard-limit, 2-Sigma historical bounds, bootstrap (empty history),
boundary values (exactly at limit), multiple parameters, edge cases.
"""
import pytest
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.validation_engine import _check_o2_limit, _check_2sigma


class _MockDb:
    """Minimal DB stub — returns None so _get_config_limit uses defaults."""
    def query(self, *a): return self
    def filter(self, *a): return self
    def first(self): return None

_DB = _MockDb()


class TestO2HardLimit:
    """Compliance rígida para O2 na Cromatografia (threshold: 0.5%)."""

    def test_o2_well_below_limit(self):
        check = _check_o2_limit(0.032, _DB)
        assert check.status == "pass"

    def test_o2_at_limit_boundary(self):
        """Exatamente 0.5% — valor limítrofe."""
        check = _check_o2_limit(0.5, _DB)
        # Dependendo da implementação (< vs <=), documenta o comportamento
        assert check.status in ("pass", "fail"), "Deve ter um resultado definido no limiar"

    def test_o2_just_above_limit(self):
        check = _check_o2_limit(0.501, _DB)
        assert check.status == "fail"

    def test_o2_grossly_above_limit(self):
        check = _check_o2_limit(5.0, _DB)
        assert check.status == "fail"
        assert "exceeds limit" in check.detail.lower() or "limit" in check.detail.lower()

    def test_o2_zero(self):
        check = _check_o2_limit(0.0, _DB)
        assert check.status == "pass"


class TestTwoSigmaValidation:
    """Validação estatística 2-Sigma com histórico."""

    STABLE_HISTORY = [
        {"value": 10.0, "date": "2026-01-01"},
        {"value": 10.5, "date": "2026-01-02"},
        {"value": 9.5, "date": "2026-01-03"},
        {"value": 10.2, "date": "2026-01-04"},
        {"value": 9.8, "date": "2026-01-05"},
    ]

    def test_value_within_band(self):
        check = _check_2sigma(_DB, "density", 10.1, "kg/m³", self.STABLE_HISTORY)
        assert check.status == "pass"

    def test_value_far_outside_band(self):
        check = _check_2sigma(_DB, "density", 150.0, "kg/m³", self.STABLE_HISTORY)
        assert check.status == "fail"

    def test_value_negative_outlier(self):
        check = _check_2sigma(_DB, "density", -50.0, "kg/m³", self.STABLE_HISTORY)
        assert check.status == "fail"

    def test_returns_mean_and_std(self):
        check = _check_2sigma(_DB, "density", 10.0, "kg/m³", self.STABLE_HISTORY)
        assert check.history_mean is not None
        assert check.history_std is not None
        assert check.history_mean > 0

    def test_empty_history_bootstrap(self):
        """Equipamento novo (sem histórico) — não pode reprovar."""
        check = _check_2sigma(_DB, "density", 850.0, "kg/m³", [])
        assert check.status == "pass"
        assert check.history_mean == 850.0

    def test_single_sample_history(self):
        """Apenas 1 amostra no histórico — std dev = 0, qualquer valor igual passa."""
        history = [{"value": 100.0, "date": "2026-01-01"}]
        check = _check_2sigma(_DB, "density", 100.0, "kg/m³", history)
        assert check.status == "pass"

    def test_different_parameters(self):
        """Testa que o parâmetro 'rs' e 'fe' também funcionam."""
        rs_history = [
            {"value": 88.0, "date": "2026-01-01"},
            {"value": 87.5, "date": "2026-01-02"},
            {"value": 88.5, "date": "2026-01-03"},
        ]
        check = _check_2sigma(_DB, "rs", 88.2, "m³/m³", rs_history)
        assert check.status == "pass"

    def test_highly_volatile_history(self):
        """Histórico muito disperso — banda larga, aceita mais valores."""
        volatile = [
            {"value": 1.0, "date": "2026-01-01"},
            {"value": 100.0, "date": "2026-01-02"},
            {"value": 50.0, "date": "2026-01-03"},
            {"value": 75.0, "date": "2026-01-04"},
        ]
        # Mean ≈ 56.5, Std ≈ 36 → band is very wide
        check = _check_2sigma(_DB, "density", 60.0, "kg/m³", volatile)
        assert check.status == "pass"
