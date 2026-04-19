"""
Harness Engineering — Cross-Module Integration (M1 + M11 + M3)
Verifica a integração entre Ativos, Hierarquia e Análise Química.
"""
import pytest
from datetime import datetime

def test_equipment_to_chemical_samples_link(client, equipment_factory, tag_factory, sample_factory, installation_factory):
    """
    Verifica se amostras químicas podem ser filtradas por ID de Equipamento físico (M1 -> M3).
    """
    # 1. Create Equipment and Tag
    eq = equipment_factory(serial_number="EQ-CH-01")
    tag = tag_factory(tag_number="TAG-CH-01")
    
    # 2. Install Equipment on Tag
    installation_factory(eq_id=eq["id"], t_id=tag["id"])
    
    # 3. Create Sample for that Tag (Meter)
    # We need a sample point first
    sp = client.post("/api/chemical/sample-points", json={
        "tag_number": "SP-CH-01",
        "description": "Sample Point for integration",
        "fpso_name": "FPSO Harness"
    }).json()
    
    # 3. Link Tag (Meter) to Sample Point (Required for filtering logic)
    res = client.post(f"/api/chemical/sample-points/{sp['id']}/link-meters", json=[tag["id"]])
    assert res.status_code == 200

    sample = sample_factory(sample_point_id=sp["id"], meter_id=tag["id"])
    
    # 4. Query samples by equipment_id
    res = client.get(f"/api/chemical/samples?equipment_id={eq['id']}")
    assert res.status_code == 200
    samples = res.json()
    assert len(samples) == 1
    assert samples[0]["id"] == sample["id"]

def test_hierarchy_updates_on_installation(client, equipment_factory, tag_factory, installation_factory):
    """
    Verifica se a instalação de um equipamento (M1) reflete na hierarquia (M11).
    Note: M11 tree is dynamic based on tags, so this verifies if tag exists.
    """
    eq = equipment_factory(serial_number="EQ-HI-01")
    # Tag must follow the pattern TXX-FT-XXXX to appear in the tree
    tag = tag_factory(tag_number="T80-FT-8001", classification="Fiscal")
    
    # Install equipment
    installation_factory(eq_id=eq["id"], t_id=tag["id"])
    
    # Get Tree
    res = client.get("/api/config/hierarchy/tree")
    assert res.status_code == 200
    tree = res.json()
    
    # Find the tag in the tree
    fpso = tree[0]
    meters = [c for c in fpso["children"] if c["level_type"] == "Metering Point"]
    target_node = next((m for m in meters if m["tag"] == "T80-FT-8001"), None)
    
    assert target_node is not None
    # Verify classification attribute propagation
    assert target_node["attributes"]["classification"] == "Fiscal"

def test_equipment_history_cross_link(client, equipment_factory, tag_factory, installation_factory):
    """
    Verifica se o histórico de instalações (M1) rastreia corretamente as movimentações.
    """
    eq = equipment_factory(serial_number="EQ-HIST-01")
    tag_a = tag_factory(tag_number="TAG-A")
    tag_b = tag_factory(tag_number="TAG-B")
    
    # Install in Tag A
    inst1 = installation_factory(eq_id=eq["id"], t_id=tag_a["id"])
    
    # Move to Tag B (Remove 1, Install 2)
    client.post(f"/api/equipment/remove/{inst1['id']}")
    installation_factory(eq_id=eq["id"], t_id=tag_b["id"])
    
    # Verify history
    res = client.get(f"/api/equipment/{eq['id']}/history")
    assert res.status_code == 200
    history = res.json()
    assert len(history) == 2
    
    # Most recent should be active and on Tag B
    assert history[0]["tag_id"] == tag_b["id"]
    assert history[0]["is_active"] == 1
    
    # Older should be inactive and on Tag A
    assert history[1]["tag_id"] == tag_a["id"]
    assert history[1]["is_active"] == 0
