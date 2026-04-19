import pytest
from datetime import datetime, date, timedelta

def test_equipment_health_status_missing(client, equipment_factory):
    """Verifica que equipamento sem certificados tem status 'missing'."""
    eq = equipment_factory()
    res = client.get(f"/api/equipment/{eq['id']}")
    assert res.json()["health_status"] == "missing"

def test_equipment_health_status_healthy(client, equipment_factory, certificate_factory):
    """Verifica status 'healthy' com certificado válido."""
    eq = equipment_factory()
    certificate_factory(eq_id=eq["id"], expiry_date=(date.today() + timedelta(days=365)).isoformat())
    
    res = client.get(f"/api/equipment/{eq['id']}")
    assert res.json()["health_status"] == "healthy"

def test_equipment_health_status_expiring(client, equipment_factory, certificate_factory):
    """Verifica status 'expiring' quando o certificado vence em menos de 30 dias."""
    eq = equipment_factory()
    # Expira em 15 dias
    exp_date = (date.today() + timedelta(days=15)).isoformat()
    certificate_factory(eq_id=eq["id"], expiry_date=exp_date)
    
    res = client.get(f"/api/equipment/{eq['id']}")
    assert res.json()["health_status"] == "expiring"

def test_equipment_health_status_expired(client, equipment_factory, certificate_factory):
    """Verifica status 'expired' quando o certificado já venceu."""
    eq = equipment_factory()
    # Venceu ontem
    exp_date = (date.today() - timedelta(days=1)).isoformat()
    certificate_factory(eq_id=eq["id"], expiry_date=exp_date)
    
    res = client.get(f"/api/equipment/{eq['id']}")
    assert res.json()["health_status"] == "expired"

def test_equipment_health_status_priority_expired(client, equipment_factory, certificate_factory):
    """Verifica que 'expired' tem prioridade sobre 'expiring'."""
    eq = equipment_factory()
    # Um expirando e um expirado
    certificate_factory(eq_id=eq["id"], expiry_date=(date.today() + timedelta(days=10)).isoformat())
    certificate_factory(eq_id=eq["id"], expiry_date=(date.today() - timedelta(days=5)).isoformat())
    
    res = client.get(f"/api/equipment/{eq['id']}")
    assert res.json()["health_status"] == "expired"
