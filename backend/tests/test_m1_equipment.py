"""
Harness Engineering — Module 1 (Asset Inventory) Core Tests
Verifica o registro de equipamentos físicos, criação de tags e o fluxo de instalação.
"""
import pytest
from datetime import datetime

def test_equipment_crud(client):
    """Verifica o CRUD básico de equipamentos."""
    payload = {
        "serial_number": "SN-TEST-001",
        "model": "Rosemount 3051",
        "manufacturer": "Emerson",
        "equipment_type": "Pressure Transmitter",
        "fpso_name": "FPSO CDI",
        "status": "Active"
    }
    # Create
    res = client.post("/api/equipment/", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["serial_number"] == "SN-TEST-001"
    eq_id = data["id"]

    # Read All
    res = client.get("/api/equipment/")
    assert res.status_code == 200
    assert any(e["id"] == eq_id for e in res.json())

    # Read One
    res = client.get(f"/api/equipment/{eq_id}")
    assert res.status_code == 200
    assert res.json()["serial_number"] == "SN-TEST-001"

def test_instrument_tag_crud(client):
    """Verifica o CRUD de Tags de instrumentação."""
    payload = {
        "tag_number": "62-PT-1001",
        "description": "Pressure Transmitter for Separator A",
        "area": "Process",
        "service": "High Pressure"
    }
    # Create
    res = client.post("/api/equipment/tags", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["tag_number"] == "62-PT-1001"
    tag_id = data["id"]

    # Read All
    res = client.get("/api/equipment/tags")
    assert res.status_code == 200
    assert any(t["id"] == tag_id for t in res.json())

def test_equipment_installation_workflow(client, equipment_factory, tag_factory):
    """Verifica o ciclo de vida de instalação e remoção de equipamentos."""
    eq = equipment_factory(serial_number="SN-INST-01")
    tag = tag_factory(tag_number="TAG-INST-01")

    # 1. Install
    install_payload = {
        "equipment_id": eq["id"],
        "tag_id": tag["id"],
        "installed_by": "Test Engineer",
        "installation_date": datetime.utcnow().isoformat()
    }
    res = client.post("/api/equipment/install", json=install_payload)
    assert res.status_code == 200
    install_data = res.json()
    assert install_data["is_active"] == 1
    install_id = install_data["id"]

    # 2. Verify tag is occupied
    res = client.get("/api/equipment/tags/available")
    assert res.status_code == 200
    # TAG-INST-01 should be in available list (meaning it has an active installation)
    assert any(t["id"] == tag["id"] for t in res.json())

    # 3. Try to install another equipment on same tag (should fail)
    eq2 = equipment_factory(serial_number="SN-INST-02")
    install_payload_2 = {
        "equipment_id": eq2["id"],
        "tag_id": tag["id"],
        "installed_by": "Another Engineer"
    }
    res = client.post("/api/equipment/install", json=install_payload_2)
    assert res.status_code == 400
    assert "already occupied" in res.json()["detail"]

    # 4. Remove equipment
    res = client.post(f"/api/equipment/remove/{install_id}")
    assert res.status_code == 200
    assert res.json()["status"] == "success"

    # 5. Verify history
    res = client.get(f"/api/equipment/{eq['id']}/history")
    assert res.status_code == 200
    history = res.json()
    assert len(history) == 1
    assert history[0]["is_active"] == 0
    assert history[0]["removal_date"] is not None
