"""
M1 — Equipment Filtering & Available Tags Tests
Cobre: filtragem de equipamentos por serial_number e equipment_type,
e filtragem de tags disponíveis por fpso_name e equipment_type.
"""
import pytest


def test_filter_equipment_by_serial_number(client, equipment_factory):
    """Verifica filtragem de equipamentos por serial_number (ilike)."""
    equipment_factory(serial_number="ROSEMOUNT-3051")
    equipment_factory(serial_number="VORTEX-7700")

    res = client.get("/api/equipment/?serial_number=ROSEMOUNT")
    assert res.status_code == 200
    result = res.json()
    assert len(result) >= 1
    assert all("ROSEMOUNT" in e["serial_number"].upper() for e in result)


def test_filter_equipment_by_type(client, equipment_factory):
    """Verifica filtragem de equipamentos por equipment_type exato."""
    equipment_factory(serial_number="SN-FLOW-001", equipment_type="Flow Computer")
    equipment_factory(serial_number="SN-PRESS-001", equipment_type="Pressure Transmitter")

    res = client.get("/api/equipment/?equipment_type=Flow Computer")
    assert res.status_code == 200
    result = res.json()
    assert len(result) >= 1
    assert all(e["equipment_type"] == "Flow Computer" for e in result)


def test_filter_equipment_by_serial_and_type_combined(client, equipment_factory):
    """Verifica filtragem combinada de serial + tipo."""
    equipment_factory(serial_number="MULTI-FC-001", equipment_type="Flow Computer")
    equipment_factory(serial_number="MULTI-PT-001", equipment_type="Pressure Transmitter")

    res = client.get("/api/equipment/?serial_number=MULTI&equipment_type=Flow Computer")
    assert res.status_code == 200
    result = res.json()
    assert len(result) >= 1
    assert all(e["equipment_type"] == "Flow Computer" for e in result)
    assert all("MULTI" in e["serial_number"] for e in result)


def test_available_tags_filtered_by_fpso(client, equipment_factory, tag_factory, installation_factory):
    """Verifica que tags disponíveis podem ser filtradas pelo FPSO do equipamento instalado."""
    eq_cdi = equipment_factory(serial_number="AVAIL-CDI-01", fpso_name="FPSO CDI")
    eq_other = equipment_factory(serial_number="AVAIL-OTH-01", fpso_name="FPSO Other")
    tag_cdi = tag_factory(tag_number="TAG-AVAIL-CDI")
    tag_other = tag_factory(tag_number="TAG-AVAIL-OTH")

    installation_factory(eq_id=eq_cdi["id"], t_id=tag_cdi["id"])
    installation_factory(eq_id=eq_other["id"], t_id=tag_other["id"])

    res = client.get("/api/equipment/tags/available?fpso_name=FPSO CDI")
    assert res.status_code == 200
    result = res.json()
    ids = [t["id"] for t in result]
    assert tag_cdi["id"] in ids
    assert tag_other["id"] not in ids


def test_available_tags_filtered_by_equipment_type(client, equipment_factory, tag_factory, installation_factory):
    """Verifica filtragem de tags disponíveis por tipo de equipamento instalado."""
    eq_fc = equipment_factory(serial_number="AVAIL-FC-01", equipment_type="Flow Computer")
    eq_pt = equipment_factory(serial_number="AVAIL-PT-01", equipment_type="Pressure Transmitter")
    tag_fc = tag_factory(tag_number="TAG-FC-01")
    tag_pt = tag_factory(tag_number="TAG-PT-01")

    installation_factory(eq_id=eq_fc["id"], t_id=tag_fc["id"])
    installation_factory(eq_id=eq_pt["id"], t_id=tag_pt["id"])

    res = client.get("/api/equipment/tags/available?equipment_type=Flow Computer")
    assert res.status_code == 200
    result = res.json()
    ids = [t["id"] for t in result]
    assert tag_fc["id"] in ids
    assert tag_pt["id"] not in ids


def test_equipment_not_found_returns_404(client):
    """Verifica que GET /api/equipment/99999 retorna 404."""
    res = client.get("/api/equipment/99999")
    assert res.status_code == 404


def test_tag_filter_by_number(client, tag_factory):
    """Verifica filtragem de tags por tag_number (ilike)."""
    tag_factory(tag_number="T62-FT-FILTER-01")
    tag_factory(tag_number="T62-PT-OTHER-01")

    res = client.get("/api/equipment/tags?tag_number=FILTER")
    assert res.status_code == 200
    result = res.json()
    assert len(result) >= 1
    assert all("FILTER" in t["tag_number"] for t in result)
