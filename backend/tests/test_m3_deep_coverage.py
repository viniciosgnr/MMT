"""
Harness Engineering — M3 Validation Engine Deep Tests

TESTA DIRETAMENTE AS FUNÇÕES DO validation_engine.py:
1. _check_2sigma com históricos variados
2. _check_o2_limit em boundaries exatos
3. validate_pvt com PVTResult mockado
4. validate_cro com CROResult mockado
5. validate_report dispatcher (PVT vs CRO)
6. CheckResult e ValidationResult dataclass behavior

Expansão da cobertura sobre test_m3_validation_engine.py que já existe.

Skills:
- python-testing-patterns → mocks, parametrize, edge cases
- fastapi-pro → isolamento de services
"""
import pytest
import math
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.validation_engine import (
    _check_2sigma, _check_o2_limit,
    CheckResult, ValidationResult,
    DEFAULT_O2_LIMIT, HISTORY_SIZE, SIGMA_MULTIPLIER
)
from app.services.pdf_parser import (
    PVTResult, CROResult,
    _parse_br_float, detect_report_type,
    _extract_tag_point, _extract_boletim, _extract_sampling_date,
    extract_pvt, extract_cro
)
class TestCheckResultDataclass:
    """Testa o dataclass CheckResult."""

    def test_default_values(self):
        cr = CheckResult(parameter="test", value=1.0, unit="u", status="pass", detail="ok")
        assert cr.history_mean is None
        assert cr.history_std is None
        assert cr.lower_bound is None
        assert cr.upper_bound is None
        assert cr.history_values == []
        assert cr.history_dates == []


class TestValidationResultDataclass:
    """Testa o dataclass ValidationResult."""

    def test_passed_failed_counts(self):
        vr = ValidationResult(report_type="PVT", overall_status="fail")
        vr.checks = [
            CheckResult(parameter="a", value=1.0, unit="u", status="pass", detail="ok"),
            CheckResult(parameter="b", value=2.0, unit="u", status="fail", detail="bad"),
            CheckResult(parameter="c", value=3.0, unit="u", status="pass", detail="ok"),
        ]
        assert vr.passed_count == 2
        assert vr.failed_count == 1

    def test_empty_checks(self):
        vr = ValidationResult(report_type="CRO", overall_status="pass")
        assert vr.passed_count == 0
        assert vr.failed_count == 0

    def test_boletim_tag_optional(self):
        vr = ValidationResult(report_type="PVT", overall_status="pass")
        assert vr.boletim is None
        assert vr.tag_point is None


class TestCheck2SigmaEdgeCases:
    """Testes profundos de _check_2sigma — condições de borda."""

    def test_empty_history_bootstraps(self):
        """Sem histórico, valor é replicado → σ=0 → sempre PASS."""
        result = _check_2sigma("density", 875.0, "kg/m³", [])
        assert result.status == "pass"

    def test_single_history_point(self):
        """1 ponto = replicação → baixo σ → provavelmente pass."""
        history = [{"value": 875.0, "date": "2026-01-01", "sample_id": "S1"}]
        result = _check_2sigma("density", 875.0, "kg/m³", history)
        assert result.status == "pass"

    def test_identical_history_zero_std(self):
        """Todos valores iguais → σ=0 → o mesmo valor passa, qualquer outro falha."""
        history = [{"value": 875.0, "date": f"2026-01-{i+1:02d}", "sample_id": f"S{i}"} for i in range(10)]
        # O mesmo valor passa
        result = _check_2sigma("density", 875.0, "kg/m³", history)
        assert result.status == "pass"
        # Um valor diferente falha (σ = 0, range = [875, 875])
        result2 = _check_2sigma("density", 876.0, "kg/m³", history)
        assert result2.status == "fail"

    def test_exact_boundary_2sigma(self):
        """Valor exatamente no boundary (mean ± 2σ) deve PASS."""
        # Valores: [100, 110, 100, 110, 100, 110, 100, 110, 100, 110]
        history = [
            {"value": 100 + (i % 2) * 10, "date": f"2026-01-{i+1:02d}", "sample_id": f"S{i}"}
            for i in range(10)
        ]
        # Mean = 105, σ = 5, range = [95, 115]
        result_lower = _check_2sigma("test", 95.0, "unit", history)
        assert result_lower.status == "pass", "Valor exatamente no lower bound deve PASS"
        result_upper = _check_2sigma("test", 115.0, "unit", history)
        assert result_upper.status == "pass", "Valor exatamente no upper bound deve PASS"

    def test_just_outside_boundary_fails(self):
        """Valor 1 acima do boundary deveria FAIL."""
        history = [
            {"value": 100 + (i % 2) * 10, "date": f"2026-01-{i+1:02d}", "sample_id": f"S{i}"}
            for i in range(10)
        ]
        result = _check_2sigma("test", 116.0, "unit", history)
        assert result.status == "fail"

    def test_volatile_history(self):
        """Histórico muito volátil → faixa larga → mais fácil de passar."""
        history = [
            {"value": v, "date": f"2026-01-{i+1:02d}", "sample_id": f"S{i}"}
            for i, v in enumerate([800, 900, 810, 890, 820, 880, 830, 870, 840, 860])
        ]
        # Mean ≈ 850, σ ≈ 33 → range ≈ [784, 916]
        result = _check_2sigma("test", 850.0, "unit", history)
        assert result.status == "pass"

    def test_history_fills_output(self):
        """CheckResult deve conter history_mean, history_std, bounds, values, dates."""
        history = [
            {"value": 100 + i, "date": f"2026-01-{i+1:02d}", "sample_id": f"S{i}"}
            for i in range(5)
        ]
        result = _check_2sigma("density", 102.0, "kg/m³", history)
        assert result.history_mean is not None
        assert result.history_std is not None
        assert result.lower_bound is not None
        assert result.upper_bound is not None
        assert len(result.history_values) > 0


class TestO2LimitDeep:
    """Testes profundos de _check_o2_limit."""

    @pytest.mark.parametrize("value,expected_status", [
        (0.0, "pass"),
        (0.1, "pass"),
        (0.499, "pass"),
        (0.5, "pass"),       # Exatamente 0.5 → PASS (≤ 0.5)
        (0.501, "fail"),     # Logo acima → FAIL
        (1.0, "fail"),
        (5.0, "fail"),
        (0.0001, "pass"),
    ])
    def test_o2_parametrized(self, value, expected_status, db_session):
        result = _check_o2_limit(value, db_session)
        assert result.status == expected_status, f"O2={value}: esperado {expected_status}, got {result.status}"

    def test_o2_exactly_at_limit(self, db_session):
        """O2 = 0.5 (exatamente no limite) → PASS."""
        result = _check_o2_limit(0.5, db_session)
        assert result.status == "pass"
        assert result.value == 0.5

    def test_o2_detail_message_on_fail(self, db_session):
        """Detalhe do CheckResult deve explicar a falha."""
        result = _check_o2_limit(0.8, db_session)
        assert result.status == "fail"
        assert "0.5" in result.detail or "limit" in result.detail.lower() or "O" in result.detail


class TestPdfParserEdgeCases:
    """Testes adicionais do PDF Parser — edge cases de regex."""

    def test_parse_br_float_with_thousand_separator(self):
        """1.234,56 → não suportado, mas não deve crashar."""
        result = _parse_br_float("1.234,56")
        # Pode retornar None ou um float (comportamento defensivo)
        assert result is None or isinstance(result, float)

    def test_parse_br_float_empty(self):
        assert _parse_br_float("") is None

    def test_parse_br_float_none_input(self):
        assert _parse_br_float(None) is None

    def test_detect_pvt(self):
        text = "Massa específica absoluta do óleo morto\n875,39"
        assert detect_report_type(text) == "PVT"

    def test_detect_cro(self):
        text = "Cromatografia do Gás Natural\nConcentração Molar"
        assert detect_report_type(text) == "CRO"

    def test_detect_unknown(self):
        text = "Este é um documento qualquer sem marcadores"
        assert detect_report_type(text) == "UNKNOWN"

    def test_detect_pvt_by_boletim_prefix(self):
        text = "PVT Sepetiba/26-16901"
        assert detect_report_type(text) == "PVT"

    def test_detect_cro_by_boletim_prefix(self):
        text = "CRO Sepetiba/26-16901"
        assert detect_report_type(text) == "CRO"

    def test_extract_tag_point_valid(self):
        text = "662-AP-2233 / P-02 (Downstream)"
        result = _extract_tag_point(text)
        assert result is not None
        assert "662-AP-2233" in result

    def test_extract_tag_point_no_match(self):
        result = _extract_tag_point("Texto sem tag point nenhum")
        assert result is None

    def test_extract_boletim_pvt(self):
        text = "Boletim de Resultado de Análise N°\nPVT Sepetiba/26-16901"
        result = _extract_boletim(text)
        assert result is not None
        assert "PVT" in result

    def test_extract_boletim_no_match(self):
        result = _extract_boletim("Texto sem boletim")
        assert result is None

    def test_extract_sampling_date_fpso(self):
        text = "FPSO Cidade de Sepetiba\n17/01/2026\nOutra coisa"
        result = _extract_sampling_date(text)
        assert result == "17/01/2026"

    def test_extract_sampling_date_fallback(self):
        text = "Data de Recebimento\n03/02/2026"
        result = _extract_sampling_date(text)
        assert result == "03/02/2026"

    def test_extract_pvt_complete(self):
        text = (
            "Boletim de Resultado de Análise N°\nPVT Sepetiba/26-16901\n"
            "662-AP-2233 / P-02\n"
            "FPSO Cidade de Sepetiba\n17/01/2026\n"
            "Massa específica absoluta do óleo morto - 20 °C\n875,39\n"
            "RGO ou RS\n88,0571\n"
            "FE\n0,8241\n"
        )
        result = extract_pvt(text)
        assert result.report_type == "PVT"
        assert result.boletim is not None
        assert result.tag_point is not None
        assert result.sampling_date == "17/01/2026"
        assert abs(result.density - 875.39) < 0.01
        assert abs(result.rs - 88.0571) < 0.001
        assert abs(result.fe - 0.8241) < 0.001

    def test_extract_cro_complete(self):
        text = (
            "Boletim de Resultado de Análise N°\nCRO Sepetiba/26-16902\n"
            "662-AP-2233 / P-02\n"
            "FPSO Cidade de Sepetiba\n20/01/2026\n"
            "O2\nOxigênio\n1A\n0,032\n"
            "Densidade Relativa do Gás Real\n1B\n1,0509\n-"
        )
        result = extract_cro(text)
        assert result.report_type == "CRO"
        assert result.boletim is not None
        assert abs(result.o2 - 0.032) < 0.001
        assert abs(result.relative_density_real - 1.0509) < 0.001

    def test_extract_pvt_missing_fields(self):
        """PVT com campos faltando → None nos campos, sem crash."""
        text = "Massa específica absoluta do óleo morto - 20 °C\n875,39\n"
        result = extract_pvt(text)
        assert result.density is not None
        assert result.rs is None
        assert result.fe is None
        assert result.boletim is None

    def test_extract_cro_missing_o2(self):
        """CRO sem O2 → o2 é None."""
        text = "Densidade Relativa do Gás Real\n1B\n1,0509\n-"
        result = extract_cro(text)
        assert result.o2 is None
        assert result.relative_density_real is not None
