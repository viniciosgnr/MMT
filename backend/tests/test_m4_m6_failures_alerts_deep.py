import pytest
from datetime import datetime

def test_failures_and_approval_workflow(client, db_session, equipment_factory):
    # 1. Setup - Equipment for FPSO Harness
    eq = equipment_factory(fpso_name="FPSO Harness")
    
    # 2. Create Failure Notification (Draft)
    failure_payload = {
        "equipment_id": eq["id"],
        "tag": "62-FT-1001",
        "fpso_name": "FPSO Harness",
        "failure_date": "2026-06-01T10:00:00",
        "description": "Total loss of signal",
        "impact": "High",
        "estimated_volume_impact": 500.5,
        "corrective_action": "Replace electronics board",
        "responsible": "Main Specialist"
    }
    
    res = client.post("/api/failures", json=failure_payload)
    assert res.status_code == 200
    failure_id = res.json()["id"]
    assert res.json()["status"] == "Draft"
    
    # 3. Approve Failure
    approval_payload = {
        "approved_by": "Senior Auditor"
    }
    app_res = client.post(f"/api/failures/{failure_id}/approve", json=approval_payload)
    assert app_res.status_code == 200
    assert app_res.json()["status"] == "Approved"
    
    # 4. Submit to ANP
    sub_res = client.put(f"/api/failures/{failure_id}/anp-submit")
    assert sub_res.status_code == 200
    assert sub_res.json()["status"] == "Submitted"
    assert sub_res.json()["anp_status"] == "Submitted"

def test_alerts_and_configs(client, db_session):
    # 1. Setup - Create Alert Configuration
    config_payload = {
        "fpso_name": "FPSO Harness",
        "alert_type": "Compliance",
        "rule_config": "{\"o2_max\": 500}",
        "notify_email": True,
        "notify_whatsapp": False,
        "notify_in_app": True,
        "recipients": [
            {"user_name": "Alert Bot", "email": "alerts@harness.com", "receive_in_app": True}
        ]
    }
    
    cfg_res = client.post("/api/alerts/configs", json=config_payload)
    assert cfg_res.status_code == 200
    
    # 2. Create Alert manually (simulated trigger)
    alert_payload = {
        "type": "Compliance",
        "severity": "High",
        "title": "Unauthorized Access",
        "message": "Detection of unauthorized tag edit",
        "fpso_name": "FPSO Harness",
        "tag_number": "62-PT-1001"
    }
    res = client.post("/api/alerts", json=alert_payload)
    assert res.status_code == 200
    alert_id = res.json()["id"]
    
    # 3. Acknowledge Alert
    ack_payload = {
        "acknowledged_by": "Admin",
        "justification": "Checked and verified",
        "linked_event_type": "Audit",
        "linked_event_id": 123,
        "run_recheck": False
    }
    ack_res = client.put(f"/api/alerts/{alert_id}/acknowledge", json=ack_payload)
    assert ack_res.status_code == 200
    assert ack_res.json()["acknowledged"] == 1
    
    # 4. Verify unread count
    count_res = client.get("/api/alerts/unread-count")
    assert count_res.status_code == 200
    # Assuming there are other alerts from other tests, just check if it's a dict
    assert "unread_count" in count_res.json()
