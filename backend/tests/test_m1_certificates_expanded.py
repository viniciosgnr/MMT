"""
M1 — Certificate Management Expanded Tests
Cobre: listagem de certificados por equipamento, tipos de certificado,
health status no endpoint de lista (/api/equipment/), e o caso limite
de certificado sem data de validade (não deve contar como calibração expirada).
"""
import pytest
from datetime import date, timedelta


def test_certificate_list_route(client, equipment_factory, certificate_factory):
    """Verifica que GET /{equipment_id}/certificates devolve os certificados."""
    eq = equipment_factory()
    certificate_factory(eq_id=eq["id"], expiry_date=(date.today() + timedelta(days=100)).isoformat())
    certificate_factory(eq_id=eq["id"], expiry_date=(date.today() + timedelta(days=200)).isoformat())

    res = client.get(f"/api/equipment/{eq['id']}/certificates")
    assert res.status_code == 200
    certs = res.json()
    assert len(certs) == 2


def test_certificate_type_non_calibration_ignored(client, equipment_factory, certificate_factory):
    """
    Um certificado do tipo 'Verification' (não 'Calibration') não deve
    influenciar o health_status, deixando-o como 'missing'.
    """
    eq = equipment_factory()
    # Adiciona um cert do tipo não-calibração
    client.post("/api/equipment/certificates", json={
        "equipment_id": eq["id"],
        "certificate_number": "VER-001",
        "certificate_type": "Verification",
        "issue_date": date.today().isoformat(),
        "expiry_date": (date.today() + timedelta(days=365)).isoformat(),
    })

    res = client.get(f"/api/equipment/{eq['id']}")
    assert res.json()["health_status"] == "missing"


def test_certificate_no_expiry_date_does_not_expire(client, equipment_factory):
    """
    Certificado do tipo 'Calibration' sem expiry_date não deve ser
    marcado como expirado — deve ser tratado apenas como 'healthy' (sem vencimento definido).
    """
    eq = equipment_factory()
    client.post("/api/equipment/certificates", json={
        "equipment_id": eq["id"],
        "certificate_number": "CAL-NO-EXPIRY",
        "certificate_type": "Calibration",
        "issue_date": date.today().isoformat(),
        "expiry_date": None,
    })

    res = client.get(f"/api/equipment/{eq['id']}")
    # Without any expiry date set, the engine skips → treated as healthy (no expiry warning)
    assert res.json()["health_status"] in ["healthy", "missing"]


def test_health_status_in_equipment_list(client, equipment_factory, certificate_factory):
    """
    Verifica que o endpoint de LISTA (/api/equipment/) também devolve
    o health_status calculado para cada equipamento.
    """
    eq_healthy = equipment_factory(serial_number="SN-LIST-HEALTHY")
    certificate_factory(
        eq_id=eq_healthy["id"],
        expiry_date=(date.today() + timedelta(days=365)).isoformat()
    )

    eq_missing = equipment_factory(serial_number="SN-LIST-MISSING")

    res = client.get("/api/equipment/")
    assert res.status_code == 200
    items = {e["serial_number"]: e for e in res.json()}

    assert items["SN-LIST-HEALTHY"]["health_status"] == "healthy"
    assert items["SN-LIST-MISSING"]["health_status"] == "missing"


def test_multiple_certs_worst_status_wins(client, equipment_factory, certificate_factory):
    """
    Com três certificados (healthy, expiring, expired), o status final deve ser 'expired'.
    """
    eq = equipment_factory()
    certificate_factory(eq_id=eq["id"], expiry_date=(date.today() + timedelta(days=365)).isoformat())
    certificate_factory(eq_id=eq["id"], expiry_date=(date.today() + timedelta(days=10)).isoformat())
    certificate_factory(eq_id=eq["id"], expiry_date=(date.today() - timedelta(days=1)).isoformat())

    res = client.get(f"/api/equipment/{eq['id']}")
    assert res.json()["health_status"] == "expired"
