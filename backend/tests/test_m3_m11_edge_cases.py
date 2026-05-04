import pytest
from app import models

def test_create_sample_point_not_found(client):
    """Test creating a sample for a non-existent point."""
    res = client.post("/api/chemical/samples", json={
        "sample_id": "S-FAIL",
        "sample_point_id": 9999,
        "type": "PVT",
        "local": "Onshore",
        "planned_date": "2026-05-01"
    })
    assert res.status_code == 404

def test_update_status_sample_not_found(client):
    """Test updating status of a non-existent sample."""
    res = client.post("/api/chemical/samples/9999/status", json={
        "status": "Sample",
        "comments": "Test"
    })
    assert res.status_code == 404

def test_get_samples_with_filters(client):
    """Test sample listing with various filters."""
    res = client.get("/api/chemical/samples?status=Sample&sample_type=PVT")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_sla_rules_crud_and_fallbacks(client):
    """Test SLA rules CRUD and fallback logic."""
    # 1. Create rule
    res = client.post("/api/config/sla-rules", json={
        "module": "chemical",
        "classification": "Fiscal",
        "local": "Onshore",
        "analysis_type": "PVT",
        "interval_days": 30,
        "lab_days": 10,
        "report_days": 5
    })
    assert res.status_code == 200
    rule_id = res.json()["id"]

    # 2. Get with filters
    res = client.get("/api/config/sla-rules?classification=Fiscal&local=Onshore")
    assert res.status_code == 200
    rules = res.json()
    assert any(r["id"] == rule_id for r in rules)

    # 3. Delete
    res = client.delete(f"/api/config/sla-rules/{rule_id}")
    assert res.status_code == 200
    
    res = client.get("/api/config/sla-rules")
    rules = res.json()
    assert not any(r["id"] == rule_id for r in rules)

def test_chemical_filters_deep(client):
    """Test deep filtering in chemical module."""
    # 1. Create SP for different FPSOs
    import uuid
    tag_a = f"SP-A-{uuid.uuid4().hex[:4]}"
    res_a = client.post("/api/chemical/sample-points", json={"tag_number": tag_a, "fpso_name": "FPSO A", "description": "Test SP"})
    assert res_a.status_code == 200, res_a.text
    sp_a = res_a.json()
    
    # Filter SP by FPSO
    res = client.get("/api/chemical/sample-points?fpso_name=FPSO A")
    assert all(sp["fpso_name"] == "FPSO A" for sp in res.json())

    # 2. Filter Samples by multiple criteria
    client.post("/api/chemical/samples", json={
        "sample_id": "S-FILTER-1", "sample_point_id": sp_a["id"], "type": "PVT", "local": "Onshore", "planned_date": "2026-01-01"
    })
    # New samples start at 'Sample' status
    res = client.get(f"/api/chemical/samples?status=Sample&sample_type=PVT")
    assert res.status_code == 200
    samples = res.json()
    assert len(samples) >= 1
    assert any(s["sample_id"] == "S-FILTER-1" for s in samples)

def test_hierarchy_crud_system(client):
    """Test hierarchy node CRUD."""
    res = client.post("/api/config/hierarchy/nodes", json={
        "tag": "SYSTEM-01",
        "description": "New System",
        "level_type": "System"
    })
    assert res.status_code == 200
    node_id = res.json()["id"]

    res = client.get(f"/api/config/hierarchy/nodes")
    assert any(n["id"] == node_id for n in res.json())
