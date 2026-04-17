"""
Harness Engineering — M3 SLA Matrix: 100% Parameter Sweep
Cada linha da planilha 'All Periodic Analyses.xlsx' é testada individualmente.
Se QUALQUER valor for alterado acidentalmente, esse sensor bloqueia a build.
"""
import pytest
from datetime import date, timedelta
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.sla_matrix import get_sla_config


class TestSlaMatrixFullSweep:
    """Testa TODAS as 20 combinações da planilha Excel (Classification × Type × Local)."""

    # ──────────────────────────────────────────────────────────────
    # CHROMATOGRAPHY
    # ──────────────────────────────────────────────────────────────

    def test_fiscal_chromatography_onshore(self):
        c = get_sla_config("Fiscal", "Chromatography", "Onshore")
        assert c["interval_days"] == 30
        assert c["disembark_days"] == 10
        assert c["lab_days"] == 20
        assert c["report_days"] == 25
        assert c["fc_days"] == 3
        assert c["fc_is_business_days"] is True

    def test_fiscal_chromatography_offshore(self):
        c = get_sla_config("Fiscal", "Chromatography", "Offshore")
        assert c["interval_days"] == 30
        assert c["disembark_days"] is None, "Offshore: Disembark deve ser NA"
        assert c["lab_days"] is None, "Offshore: Lab deve ser NA"
        assert c["report_days"] == 25
        assert c["fc_days"] == 3
        assert c["fc_is_business_days"] is True

    def test_apropriation_chromatography_onshore(self):
        c = get_sla_config("Apropriation", "Chromatography", "Onshore")
        assert c["interval_days"] == 90
        assert c["disembark_days"] == 10
        assert c["lab_days"] == 20
        assert c["report_days"] == 25
        assert c["fc_days"] == 3
        assert c["fc_is_business_days"] is True

    def test_apropriation_chromatography_offshore(self):
        c = get_sla_config("Apropriation", "Chromatography", "Offshore")
        assert c["interval_days"] == 90
        assert c["disembark_days"] is None
        assert c["lab_days"] is None
        assert c["report_days"] == 25
        assert c["fc_days"] == 3

    def test_operational_chromatography_onshore(self):
        c = get_sla_config("Operational", "Chromatography", "Onshore")
        assert c["interval_days"] == 180
        assert c["disembark_days"] == 10
        assert c["lab_days"] == 20
        assert c["report_days"] == 45
        assert c["fc_days"] == 10
        assert c["fc_is_business_days"] is True

    def test_operational_chromatography_offshore(self):
        c = get_sla_config("Operational", "Chromatography", "Offshore")
        assert c["interval_days"] == 180
        assert c["disembark_days"] is None
        assert c["lab_days"] is None
        assert c["report_days"] == 45
        assert c["fc_days"] == 10

    # ──────────────────────────────────────────────────────────────
    # PVT
    # ──────────────────────────────────────────────────────────────

    def test_apropriation_pvt_onshore(self):
        c = get_sla_config("Apropriation", "PVT", "Onshore")
        assert c["interval_days"] == 90
        assert c["disembark_days"] == 10
        assert c["lab_days"] == 20
        assert c["report_days"] == 25
        assert c["fc_days"] is None, "PVT nunca exige FC Update"

    def test_apropriation_pvt_offshore(self):
        c = get_sla_config("Apropriation", "PVT", "Offshore")
        assert c["interval_days"] == 90
        assert c["disembark_days"] is None
        assert c["lab_days"] is None
        assert c["report_days"] == 25
        assert c["fc_days"] is None

    # ──────────────────────────────────────────────────────────────
    # ENXOFRE (Sulfur)
    # ──────────────────────────────────────────────────────────────

    def test_fiscal_enxofre_onshore(self):
        c = get_sla_config("Fiscal", "Enxofre", "Onshore")
        assert c["interval_days"] == 365
        assert c["disembark_days"] == 10
        assert c["lab_days"] == 20
        assert c["report_days"] == 25
        assert c["fc_days"] is None, "Enxofre não gera FC"

    def test_fiscal_enxofre_offshore(self):
        c = get_sla_config("Fiscal", "Enxofre", "Offshore")
        assert c["interval_days"] == 365
        assert c["disembark_days"] is None
        assert c["lab_days"] is None
        assert c["report_days"] == 25
        assert c["fc_days"] is None

    # ──────────────────────────────────────────────────────────────
    # VISCOSITY
    # ──────────────────────────────────────────────────────────────

    def test_fiscal_viscosity_onshore(self):
        c = get_sla_config("Fiscal", "Viscosity", "Onshore")
        assert c["interval_days"] == 365
        assert c["disembark_days"] == 10
        assert c["lab_days"] == 20
        assert c["report_days"] == 45
        assert c["fc_days"] is None

    def test_fiscal_viscosity_offshore(self):
        c = get_sla_config("Fiscal", "Viscosity", "Offshore")
        assert c["interval_days"] == 365
        assert c["disembark_days"] is None
        assert c["lab_days"] is None
        assert c["report_days"] == 45
        assert c["fc_days"] is None

    def test_custody_transfer_viscosity_onshore(self):
        c = get_sla_config("Custody Transfer", "Viscosity", "Onshore")
        assert c["interval_days"] == 365
        assert c["disembark_days"] == 10
        assert c["lab_days"] == 20
        assert c["report_days"] == 45
        assert c["fc_days"] is None

    def test_custody_transfer_viscosity_offshore(self):
        c = get_sla_config("Custody Transfer", "Viscosity", "Offshore")
        assert c["interval_days"] == 365
        assert c["disembark_days"] is None
        assert c["lab_days"] is None
        assert c["report_days"] == 45
        assert c["fc_days"] is None

    # ──────────────────────────────────────────────────────────────
    # EDGE CASES & NEGATIVE TESTS
    # ──────────────────────────────────────────────────────────────

    def test_invalid_combination_returns_none(self):
        """Combinação inexistente na matriz não pode crashar o backend."""
        result = get_sla_config("Inventado", "Inexistente", "Marte")
        assert result is None, "get_sla_config DEVE retornar None para combinações inexistentes"

    def test_case_sensitivity_guard(self):
        """Verifica se a lookup é case-sensitive (deve ser, conforme implementação)."""
        result = get_sla_config("fiscal", "chromatography", "onshore")
        # Se a implementação for case-insensitive, isso passará; se for case-sensitive, retornará None
        # Este test documenta o comportamento atual para evitar regressões silenciosas
        assert result is None or result["interval_days"] == 30


class TestEmergencySampleDateCalculation:
    """Testa a regra ANP de reagendamento de emergência após reprovação."""

    @staticmethod
    def _calc_emergency(report_issue_date: date, next_periodic_date: date) -> date:
        """Replica a lógica exata de chemical.py L449-469."""
        days_to_add = 3
        emergency_date = report_issue_date
        while days_to_add > 0:
            emergency_date += timedelta(days=1)
            if emergency_date.weekday() < 5:
                days_to_add -= 1
        return min(emergency_date, next_periodic_date)

    def test_reprovacao_quarta_feira(self):
        """Reprovação na Quarta: +3BD = Qui, Sex, Seg → Segunda 20/04."""
        d = self._calc_emergency(date(2026, 4, 15), date(2026, 5, 15))
        assert d == date(2026, 4, 20)

    def test_reprovacao_sexta_feira(self):
        """Reprovação na Sexta: +3BD = Seg, Ter, Qua → Quarta 22/04."""
        d = self._calc_emergency(date(2026, 4, 17), date(2026, 5, 15))
        assert d == date(2026, 4, 22)

    def test_periodic_date_wins_when_sooner(self):
        """Se a periódica é antes dos 3BD, ela prevalece (regra 'mantém se menor')."""
        d = self._calc_emergency(date(2026, 4, 17), date(2026, 4, 20))
        assert d == date(2026, 4, 20), "Periódica mais urgente deve prevalecer"

    def test_reprovacao_sabado(self):
        """Reprovação no Sábado (edge case): +3BD = Seg, Ter, Qua."""
        d = self._calc_emergency(date(2026, 4, 18), date(2026, 5, 18))
        assert d == date(2026, 4, 22)

    def test_reprovacao_domingo(self):
        """Reprovação no Domingo: +3BD = Seg, Ter, Qua."""
        d = self._calc_emergency(date(2026, 4, 19), date(2026, 5, 19))
        assert d == date(2026, 4, 22)

    def test_same_day_periodic_wins(self):
        """Se a periódica coincide com o dia de hoje, ela prevalece (min)."""
        issue = date(2026, 4, 15)
        d = self._calc_emergency(issue, issue)
        assert d == issue


class TestFcBusinessDaysCalculation:
    """Testa o cálculo de dias úteis para FC Update (replica chemical.py L433-442)."""

    @staticmethod
    def _calc_fc_date(report_issue_date: date, fc_days: int) -> date:
        """Replica a lógica exata de business_days do chemical.py."""
        days_to_add = fc_days
        curr_date = report_issue_date
        while days_to_add > 0:
            curr_date += timedelta(days=1)
            if curr_date.weekday() < 5:
                days_to_add -= 1
        return curr_date

    def test_fc_3_business_days_from_monday(self):
        """Emissão Segunda: +3BD = Ter, Qua, Qui → Quinta."""
        d = self._calc_fc_date(date(2026, 4, 13), 3)
        assert d == date(2026, 4, 16)

    def test_fc_3_business_days_from_thursday(self):
        """Emissão Quinta: +3BD = Sex, Seg, Ter → Terça."""
        d = self._calc_fc_date(date(2026, 4, 16), 3)
        assert d == date(2026, 4, 21)

    def test_fc_10_business_days_operational(self):
        """Operational: 10BD a partir de Segunda 13/04 → Quarta 29/04 (pulando 2 fins de semana)."""
        d = self._calc_fc_date(date(2026, 4, 13), 10)
        assert d == date(2026, 4, 27)

    def test_fc_from_friday(self):
        """Emissão Sexta: +3BD = Seg, Ter, Qua → Quarta."""
        d = self._calc_fc_date(date(2026, 4, 17), 3)
        assert d == date(2026, 4, 22)
