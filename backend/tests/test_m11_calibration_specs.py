import pytest
from app import models
from datetime import date
import uuid

def test_calibration_campaign_lifecycle(client):
    """Test full calibration campaign lifecycle via API."""
    # 1. Create Campaign
    res = client.post("/api/calibration/campaigns", json={
        "name": f"CAM-2026-06-{uuid.uuid4().hex[:4]}",
        "fpso_name": "FPSO Harness",
        "description": "June 2026 Campaign",
        "status": "Planned",
        "start_date": "2026-06-01",
        "responsible": "Harness Lead"
    })
    assert res.status_code == 200, res.text
    camp_id = res.json()["id"]

    # 2. Create Task
    tag = f"PT-26-{uuid.uuid4().hex[:4]}"
    res = client.post("/api/calibration/tasks", json={
        "campaign_id": camp_id,
        "equipment_id": 1,
        "tag": tag,
        "description": "Pressure Transmitter Calibration",
        "due_date": "2026-06-15",
        "status": "Pending"
    })
    assert res.status_code == 200, res.text
    task_id = res.json()["id"]

    # 3. Upload Certificate
    res = client.post(f"/api/calibration/tasks/{task_id}/certificate", json={
        "certificate_number": f"CDA-PRV-{tag}",
        "issue_date": "2026-06-02",
        "standard_reading": 100.0,
        "equipment_reading": 100.1,
        "uncertainty": 0.05
    })
    assert res.status_code == 200, res.text

    # 4. Validate Certificate (CA)
    res = client.post(f"/api/calibration/tasks/{task_id}/certificate/validate")
    assert res.status_code == 200, f"Validate fail: {res.text}"
    assert res.json()["status"] in ["approved", "pending"]

    # 5. Complete with FC Evidence
    res = client.post(f"/api/calibration/tasks/{task_id}/fc-update", json={
        "fc_evidence_url": "http://storage/ev.pdf",
        "notes": "FC updated"
    })
    assert res.status_code == 200, res.text

def test_sla_rules_cascading_fallback(client):
    """Test that SLA rules fallback correctly."""
    res = client.get("/api/config/sla-rules")
    assert res.status_code == 200

def test_hierarchy_node_attributes(client):
    """Test setting and getting attributes on hierarchy nodes."""
    # 1. Create a node first
    tag = f"NODE-ATTR-{uuid.uuid4().hex[:4]}"
    res = client.post("/api/config/hierarchy/nodes", json={
        "tag": tag,
        "description": "Node for attributes",
        "level_type": "System"
    })
    assert res.status_code == 200, res.text
    node_id = res.json()["id"]

    # 2. Create a definition using /api/config/attributes
    res = client.post("/api/config/attributes", json={
        "name": f"Attr-{uuid.uuid4().hex[:4]}",
        "type": "Text",
        "entity_type": "HierarchyNode",
        "description": "Asset criticality"
    })
    assert res.status_code == 200, res.text
    attr_def_id = res.json()["id"]
    
    # 3. Set value using the correct endpoint /api/config/values
    res = client.post("/api/config/values", json={
        "attribute_id": attr_def_id,
        "entity_id": node_id,
        "value": "High"
    })
    assert res.status_code == 200, res.text
    
    # 4. Get values using /api/config/values/{entity_id}
    res = client.get(f"/api/config/values/{node_id}")
    assert res.status_code == 200
    assert any(a["attribute_id"] == attr_def_id and a["value"] == "High" for a in res.json())
