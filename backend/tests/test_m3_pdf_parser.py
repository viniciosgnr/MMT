"""
Harness Engineering — M3 PDF Parser: Exhaustive Extraction Tests
Cobre: detect_report_type, tag extraction, boletim, sampling_date,
PVT (density, RS, FE), CRO (O2, relative_density_real), Brazilian float parsing.
"""
import pytest
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.pdf_parser import (
    detect_report_type,
    _extract_tag_point,
    _extract_boletim,
    _extract_sampling_date,
    _parse_br_float,
    extract_cro,
    extract_pvt,
)


class TestBrazilianFloatParsing:
    """Testa a conversão de vírgula brasileira para float Python."""

    def test_normal_value(self):
        assert _parse_br_float("875,39") == 875.39

    def test_integer_value(self):
        assert _parse_br_float("100") == 100.0

    def test_small_decimal(self):
        assert _parse_br_float("0,032") == 0.032

    def test_none_on_empty(self):
        assert _parse_br_float("") is None

    def test_none_on_garbage(self):
        assert _parse_br_float("abc") is None


class TestReportTypeDetection:
    """Testa a classificação automática CRO vs PVT."""

    def test_detects_cro_by_concentracao_molar(self):
        assert detect_report_type("Concentração Molar\nDados do FPSO") == "CRO"

    def test_detects_cro_by_cromatografia(self):
        assert detect_report_type("Laudo de cromatografia de gases") == "CRO"

    def test_detects_cro_by_composicao_gas(self):
        assert detect_report_type("Composição do Gás Natural") == "CRO"

    def test_detects_pvt_by_fator_encolhimento(self):
        assert detect_report_type("Fator de Encolhimento\n0,84") == "PVT"

    def test_detects_pvt_by_rgo(self):
        assert detect_report_type("Dados de RGO ou RS do ponto") == "PVT"

    def test_detects_pvt_by_massa_especifica(self):
        assert detect_report_type("Massa específica absoluta do óleo") == "PVT"

    def test_detects_pvt_by_prefix(self):
        assert detect_report_type("PVT Sepetiba/26-16901\nOutros dados") == "PVT"

    def test_detects_cro_by_prefix(self):
        assert detect_report_type("CRO Sepetiba/26-16988\nOutros dados") == "CRO"

    def test_returns_unknown_for_garbage(self):
        assert detect_report_type("Texto totalmente irrelevante sem marcadores") == "UNKNOWN"


class TestTagPointExtraction:
    """Testa a extração do ponto de amostragem (Tag AP)."""

    def test_standard_tag_with_mro(self):
        text = "Dados da coleta: 662-AP-2233 / P-02 (MRO-16)\nFim"
        assert _extract_tag_point(text) == "662-AP-2233 / P-02 (MRO-16)"

    def test_standard_tag_without_mro(self):
        text = "Ponto: 771-AP-0602 / P-02\nFim"
        tag = _extract_tag_point(text)
        assert tag is not None
        assert "AP-0602" in tag

    def test_returns_none_for_no_tag(self):
        assert _extract_tag_point("Sem nenhuma informação de Tag") is None


class TestBoletimExtraction:
    """Testa a extração do número do Boletim."""

    def test_pvt_boletim(self):
        text = "Boletim de Resultado de Análise N°\nPVT Sepetiba/26-16901\nOutros dados"
        boletim = _extract_boletim(text)
        assert boletim is not None
        assert "PVT" in boletim

    def test_cro_boletim(self):
        text = "Boletim de Resultado de Análise N°\nCRO Sepetiba/26-16988\nOutros dados"
        boletim = _extract_boletim(text)
        assert boletim is not None
        assert "CRO" in boletim

    def test_fallback_pvt_pattern(self):
        text = "Dados diversos PVT Sepetiba/26-16901 finais"
        boletim = _extract_boletim(text)
        assert boletim is not None

    def test_returns_none_for_no_boletim(self):
        assert _extract_boletim("Texto sem boletim nenhum") is None


class TestSamplingDateExtraction:
    """Testa a extração da data de coleta."""

    def test_fpso_date_pattern(self):
        text = "FPSO Cidade de Sepetiba\n17/01/2026\nOutros dados"
        d = _extract_sampling_date(text)
        assert d == "17/01/2026"

    def test_returns_none_for_no_date(self):
        assert _extract_sampling_date("Sem data nenhuma disponível") is None


class TestPvtExtraction:
    """Testa a extração completa de valores PVT."""

    MOCK_PVT_TEXT = (
        "Boletim de Resultado de Análise N°\n"
        "PVT Sepetiba/26-16901\n"
        "FPSO Cidade de Sepetiba\n"
        "10/03/2026\n"
        "Pressão e Volume:\n"
        "662-AP-2233 / P-02 (MRO-16)\n"
        "Massa específica absoluta do óleo morto - 20 °C\n"
        "875,39\n"
        "kg/m³\n"
        "RGO ou RS\n"
        "88,0571\n"
        "m³ STD gás/STD óleo morto\n"
        "FE\n"
        "0,8241\n"
        "-\n"
    )

    def test_pvt_density(self):
        r = extract_pvt(self.MOCK_PVT_TEXT)
        assert r.density == 875.39

    def test_pvt_rs(self):
        r = extract_pvt(self.MOCK_PVT_TEXT)
        assert r.rs == 88.0571

    def test_pvt_fe(self):
        r = extract_pvt(self.MOCK_PVT_TEXT)
        assert r.fe == 0.8241

    def test_pvt_boletim_extracted(self):
        r = extract_pvt(self.MOCK_PVT_TEXT)
        assert r.boletim is not None
        assert "PVT" in r.boletim

    def test_pvt_tag_point_extracted(self):
        r = extract_pvt(self.MOCK_PVT_TEXT)
        assert r.tag_point is not None
        assert "662-AP-2233" in r.tag_point

    def test_pvt_sampling_date_extracted(self):
        r = extract_pvt(self.MOCK_PVT_TEXT)
        assert r.sampling_date == "10/03/2026"

    def test_pvt_missing_values_graceful(self):
        """Parser não deve crashar com texto sem valores PVT."""
        r = extract_pvt("Texto vazio sem nenhum marcador PVT")
        assert r.density is None
        assert r.rs is None
        assert r.fe is None


class TestCroExtraction:
    """Testa a extração completa de valores CRO (Cromatografia)."""

    MOCK_CRO_TEXT = (
        "Boletim de Resultado de Análise N°\n"
        "CRO Sepetiba/26-16988\n"
        "FPSO Cidade de Sepetiba\n"
        "17/01/2026\n"
        "771-AP-0602 / P-02 (MRO-16)\n"
        "Contaminantes:\n"
        "O2\n"
        "Oxigênio\n"
        "1A\n"
        "0,032\n"
        "Condição Padrão:\n"
        "Densidade Relativa do Gás Real\n"
        "1B\n"
        "1,0509\n"
        "-\n"
    )

    def test_cro_o2(self):
        r = extract_cro(self.MOCK_CRO_TEXT)
        assert r.o2 == 0.032

    def test_cro_relative_density(self):
        r = extract_cro(self.MOCK_CRO_TEXT)
        assert r.relative_density_real == 1.0509

    def test_cro_boletim_extracted(self):
        r = extract_cro(self.MOCK_CRO_TEXT)
        assert r.boletim is not None
        assert "CRO" in r.boletim

    def test_cro_tag_point_extracted(self):
        r = extract_cro(self.MOCK_CRO_TEXT)
        assert r.tag_point is not None

    def test_cro_sampling_date_extracted(self):
        r = extract_cro(self.MOCK_CRO_TEXT)
        assert r.sampling_date == "17/01/2026"

    def test_cro_missing_values_graceful(self):
        """Parser não deve crashar com texto sem valores CRO."""
        r = extract_cro("Texto vazio sem marcadores de cromatografia")
        assert r.o2 is None
        assert r.relative_density_real is None
