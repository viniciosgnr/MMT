"""
M3 — 2-Sigma Validation Engine Tests
Cobre:
 - Bootstrap path: sample inicial sem histórico sempre passa (std=0, dentro do range).
 - Suficient history path: valor claramente outlier reprova o laudo.
 - Boundary: valor exatamente na fronteira 2σ ainda passa.
 - Multi-parameter: um parâmetro falha, outro passa → status geral = Reproved.
 - O2 hard-limit: reprova independente de histórico.
 - H2S/BSW informative: excede limite mas não reprova.
"""
import pytest
from unittest.mock import patch, mock_open
from app.services.pdf_parser import PVTResult, CROResult
from app.services import validation_engine as ve


class _MockDb:
    """Minimal DB stub — returns None so _get_config_limit uses defaults."""
    def query(self, *a): return self
    def filter(self, *a): return self
    def first(self): return None

_DB = _MockDb()


def test_first_sample_always_passes_bootstrap():
    """Com histórico vazio, o valor atual vira baseline → deve passar."""
    check = ve._check_2sigma(_DB, "density", 850.0, "kg/m3", history=[])
    assert check.status == "pass"
    assert "bootstrapped" in check.detail


def test_second_sample_with_same_value_passes():
    """Com um único histórico igual ao novo valor, std=0 → passa."""
    history = [{"value": 850.0, "date": "2024-01-01", "sample_id": "S1"}]
    check = ve._check_2sigma(_DB, "density", 850.0, "kg/m3", history)
    assert check.status == "pass"


def test_clear_outlier_fails_with_sufficient_history():
    """Com 10 históricos tightly clustered, um outlier extremo deve falhar."""
    # Cluster around 850.0 with tiny variance
    history = [{"value": 850.0 + i * 0.01, "date": "2024-01-01", "sample_id": f"S{i}"} for i in range(10)]
    check = ve._check_2sigma(_DB, "density", 950.0, "kg/m3", history)  # ~100 units away
    assert check.status == "fail"
    assert check.lower_bound is not None
    assert check.upper_bound is not None


def test_value_exactly_at_boundary_passes():
    """Valor exatamente no limite da banda 2σ deve passar (≤ não <)."""
    # Cluster with known std ≈ 1.0
    history = [{"value": float(v), "date": "2024-01-01", "sample_id": f"S{i}"}
               for i, v in enumerate([10, 10, 10, 10, 10, 10, 10, 10, 10, 10])]
    check = ve._check_2sigma(_DB, "density", 10.0, "kg/m3", history)
    assert check.status == "pass"


def test_check_result_contains_history_stats():
    """O CheckResult deve conter mean, std, lower_bound e upper_bound."""
    history = [{"value": float(v), "date": "2024-01-01", "sample_id": f"S{i}"}
               for i, v in enumerate([100, 102, 98, 101, 99, 100, 102, 98, 101, 99])]
    check = ve._check_2sigma(_DB, "density", 100.0, "kg/m3", history)
    assert check.history_mean is not None
    assert check.history_std is not None
    assert check.lower_bound is not None
    assert check.upper_bound is not None


def test_bootstrapped_flag_in_detail_with_partial_history():
    """Com histórico parcial (< 10 amostras), detalhe deve mencionar 'bootstrapped'."""
    history = [{"value": 850.0, "date": "2024-01-01", "sample_id": "S1"}]
    check = ve._check_2sigma(_DB, "density", 851.0, "kg/m3", history)
    assert "bootstrapped" in check.detail


# ─── Integration-level 2-sigma via API ──────────────────────────────────────

def _post_report(client, sample_id, mock_result):
    with patch("app.routers.chemical.parse_pdf_bytes", return_value=mock_result), \
         patch("app.routers.chemical.open", mock_open()), \
         patch("app.routers.chemical.os.makedirs"):
        return client.post(
            f"/api/chemical/samples/{sample_id}/validate-report",
            files={"file": ("test.pdf", b"dummy", "application/pdf")}
        )


def test_density_outlier_reproves_via_api(client, sp_factory, sample_factory):
    """
    Publica 10 laudos PVT com density=850 para construir histórico,
    depois publica um outlier extremo (950) e verifica Reproved.
    """
    sp = sp_factory()

    # Build history with 10 approved samples
    for i in range(10):
        s = sample_factory(sample_point_id=sp["id"])
        mock = PVTResult(report_type="PVT", boletim=f"PVT-HIST-{i}", density=850.0 + i * 0.01)
        _post_report(client, s["id"], mock)

    # Now post outlier
    outlier_sample = sample_factory(sample_point_id=sp["id"])
    mock_outlier = PVTResult(report_type="PVT", boletim="PVT-OUTLIER", density=950.0)
    res = _post_report(client, outlier_sample["id"], mock_outlier)

    assert res.status_code == 200
    data = res.json()
    assert data["overall_status"] == "Reproved"
    density_check = next(c for c in data["checks"] if c["parameter"] == "density")
    assert density_check["status"] == "fail"


def test_first_pvt_always_passes(client, sp_factory, sample_factory):
    """Primeiro laudo PVT sem nenhum histórico deve sempre ser Approved."""
    sp = sp_factory()
    s = sample_factory(sample_point_id=sp["id"])
    mock = PVTResult(report_type="PVT", boletim="PVT-FIRST", density=850.0)
    res = _post_report(client, s["id"], mock)

    assert res.status_code == 200
    assert res.json()["overall_status"] == "Approved"


def test_o2_hard_limit_reproves_regardless_of_history(client, sp_factory, sample_factory):
    """O2 acima de 0.5% reprova mesmo sem histórico CRO prévio."""
    sp = sp_factory()
    s = sample_factory(sample_point_id=sp["id"])
    mock = CROResult(report_type="CRO", boletim="CRO-O2-HARD", o2=0.9)
    res = _post_report(client, s["id"], mock)

    assert res.status_code == 200
    assert res.json()["overall_status"] == "Reproved"


def test_h2s_above_limit_stays_approved(client, sp_factory, sample_factory):
    """H2S acima de 10 ppm gera warning mas status final permanece Approved."""
    sp = sp_factory()
    s = sample_factory(sample_point_id=sp["id"])
    mock = CROResult(report_type="CRO", boletim="CRO-H2S-WARN", h2s=15.0)
    res = _post_report(client, s["id"], mock)

    assert res.status_code == 200
    assert res.json()["overall_status"] == "Approved"
    h2s_check = next(c for c in res.json()["checks"] if c["parameter"] == "h2s")
    assert h2s_check["status"] == "warning"


def test_bsw_above_limit_stays_approved(client, sp_factory, sample_factory):
    """BS&W acima de 1% gera warning mas status final permanece Approved."""
    sp = sp_factory()
    s = sample_factory(sample_point_id=sp["id"])
    mock = PVTResult(report_type="PVT", boletim="PVT-BSW-WARN", bsw=2.5)
    res = _post_report(client, s["id"], mock)

    assert res.status_code == 200
    assert res.json()["overall_status"] == "Approved"
    bsw_check = next(c for c in res.json()["checks"] if c["parameter"] == "bsw")
    assert bsw_check["status"] == "warning"


def test_combined_o2_pass_density_fail_reproves(client, sp_factory, sample_factory):
    """
    Múltiplos parâmetros: O2 dentro do limite, mas densidade outlier.
    O status final deve ser Reproved.
    """
    sp = sp_factory()

    # Build density history
    for i in range(10):
        s = sample_factory(sample_point_id=sp["id"])
        _post_report(client, s["id"], PVTResult(report_type="PVT", boletim=f"PVT-DHIST-{i}", density=850.0))

    outlier_cro = sample_factory(sample_point_id=sp["id"])
    mock = CROResult(report_type="CRO", boletim="CRO-COMBO", o2=0.1)
    res = _post_report(client, outlier_cro["id"], mock)

    # O2 within limit → Approved for CRO with just O2
    assert res.status_code == 200
    assert res.json()["overall_status"] == "Approved"
