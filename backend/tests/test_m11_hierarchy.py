"""
Harness Engineering — Module 11 (Asset Hierarchy) Core Tests
Verifica a geração dinâmica da árvore de ativos e o CRUD de nós da hierarquia.
"""
import pytest

def test_hierarchy_node_crud(client):
    """Verifica o CRUD básico de nós da hierarquia (M11)."""
    payload = {
        "tag": "SYSTEM-01",
        "description": "Production System",
        "level_type": "System"
    }
    # Create
    res = client.post("/api/config/hierarchy/nodes", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["tag"] == "SYSTEM-01"
    node_id = data["id"]

    # Read All (dynamic + static nodes)
    res = client.get("/api/config/hierarchy/nodes")
    assert res.status_code == 200
    # Note: the router returns all HierarchyNode objects from DB
    assert any(n["id"] == node_id for n in res.json())

    # Delete
    res = client.delete(f"/api/config/hierarchy/nodes/{node_id}")
    assert res.status_code == 200
    assert res.json()["status"] == "success"

def test_dynamic_tree_generation(client, tag_factory):
    """Verifica a montagem dinâmica da árvore FPSO -> Meter -> Category -> Sensor."""
    
    # 1. Create a Meter Tag (FT) with classification to trigger dynamic logic
    meter_tag = tag_factory(
        tag_number="T62-FT-1103", # One of the mapped tags in METER_TO_SAMPLE_POINT
        description="Liquid Meter",
        classification="Fiscal"
    )

    # 2. Create the linked Sample Point tag (AP)
    tag_factory(
        tag_number="T62-AP-1002", # The target AP for T62-FT-1103
        description="Sample Point Liquid"
    )

    # 3. Create linked sensors (PT/TT)
    tag_factory(tag_number="T62-PT-1103", description="Pressure Sensor")
    tag_factory(tag_number="T62-TT-1103", description="Temperature Sensor")

    # 4. Get the Tree
    res = client.get("/api/config/hierarchy/tree")
    assert res.status_code == 200
    tree = res.json()
    
    # Root should be the FPSO
    assert len(tree) == 1
    fpso = tree[0]
    assert fpso["level_type"] == "FPSO"
    
    # Check for Meter node
    meters = [c for c in fpso["children"] if c["level_type"] == "Metering Point"]
    assert any(m["tag"] == "T62-FT-1103" for m in meters)
    
    meter_node = next(m for m in meters if m["tag"] == "T62-FT-1103")
    
    # Check for Categories (Pressure, Temperature, Fluid Properties)
    cats = {c["tag"]: c for c in meter_node["children"]}
    assert "Pressure" in cats
    assert "Temperature" in cats
    assert "Fluid Properties" in cats
    
    # Check for specific instruments in categories
    pressure_sensors = [c["tag"] for c in cats["Pressure"]["children"]]
    assert "T62-PT-1103" in pressure_sensors

    fluid_properties_nodes = [c["tag"] for c in cats["Fluid Properties"]["children"]]
    assert "T62-AP-1002" in fluid_properties_nodes
