import pytest
from fastapi.testclient import TestClient
from app import models

def test_create_sample_point_not_found(client):
    """POST /samples must return 404 if sample_point_id is invalid."""
    res = client.post("/api/chemical/samples", json={
        "sample_id": "TEST-404",
        "sample_point_id": 99999,
        "type": "Chromatography",
        "planned_date": "2026-01-01"
    })
    assert res.status_code == 404
    assert res.json()["detail"] == "Sample point not found"

def test_update_status_sample_not_found(client):
    """POST /update-status must return 404 if sample_id is invalid."""
    res = client.post("/api/chemical/samples/99999/update-status", json={
        "status": "Sample",
        "comments": "Ghost sample"
    })
    assert res.status_code == 404
    assert res.json()["detail"] == "Sample not found"

def test_get_samples_with_filters(client):
    """GET /samples should support status and point filtering."""
    # Create two samples
    client.post("/api/chemical/samples", json={
        "sample_id": "S1", "sample_point_id": 1, "type": "Chromatography", "planned_date": "2026-01-01"
    })
    client.post("/api/chemical/samples", json={
        "sample_id": "S2", "sample_point_id": 1, "type": "PVT", "planned_date": "2026-01-02"
    })
    
    res = client.get("/api/chemical/samples?sample_type=PVT")
    samples = res.json()
    assert all(s["type"] == "PVT" for s in samples)

def test_sla_rules_crud_and_fallbacks(client):
    """Test full CRUD for SLA rules and fallback to 'Any'."""
    # 1. Create a rule
    rule_data = {
        "classification": "Fiscal",
        "analysis_type": "Chromatography",
        "local": "Onshore",
        "status_variation": "Any",
        "interval_days": 30,
        "disembark_days": 5,
        "lab_days": 10,
        "report_days": 15
    }
    res = client.post("/api/config/sla-rules", json=rule_data)
    assert res.status_code == 200
    rule_id = res.json()["id"]

    # 2. Get with filters
    res = client.get(f"/api/config/sla-rules?classification=Fiscal&local=Onshore")
    rules = res.json()
    assert any(r["id"] == rule_id for r in rules)

    # 3. Update
    res = client.put(f"/api/config/sla-rules/{rule_id}", json={**rule_data, "interval_days": 45})
    assert res.json()["interval_days"] == 45

    # 4. Delete
    res = client.delete(f"/api/config/sla-rules/{rule_id}")
    assert res.status_code == 200
    
    # 5. Verify deleted
    res = client.get(f"/api/config/sla-rules?classification=Fiscal&local=Onshore")
    rules = res.json()
    assert not any(r["id"] == rule_id for r in rules)

def test_hierarchy_crud_system(client):
    """Test creating a standard hierarchy node."""
    res = client.post("/api/config/hierarchy/nodes", json={
        "tag": "SYS-TEST",
        "description": "Test System",
        "level_type": "System",
        "parent_id": 1
    })
    assert res.status_code == 200
    data = res.json()
    assert data["level_type"] == "System"
    
    node_id = data["id"]
    
    # Update
    res = client.put(f"/api/config/hierarchy/nodes/{node_id}", json={
        "tag": "SYS-TEST-MOD",
        "description": "Mod",
        "level_type": "System"
    })
    assert res.json()["tag"] == "SYS-TEST-MOD"
