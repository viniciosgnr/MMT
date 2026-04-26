import pytest
from datetime import datetime
from app.models import EquipmentStatus

def test_failures_lifecycle_and_filters(client, db_session, equipment_factory):
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
    
    # 3. Test Filters
    list_res = client.get(f"/api/failures?equipment_id={eq['id']}")
    assert len(list_res.json()) >= 1
    
    # 4. Approve Failure
    app_res = client.post(f"/api/failures/{failure_id}/approve", json={"approved_by": "Senior Auditor"})
    assert app_res.status_code == 200
    
    # 5. Submit to ANP
    sub_res = client.put(f"/api/failures/{failure_id}/anp-submit")
    assert sub_res.status_code == 200
    
    # 6. Test Error Cases
    # 404
    res_404 = client.get("/api/failures/9999")
    assert res_404.status_code == 404
    
    # Not approved yet for ANP
    fail_2 = client.post("/api/failures", json=failure_payload).json()["id"]
    res_400 = client.put(f"/api/failures/{fail_2}/anp-submit")
    assert res_400.status_code == 400

def test_failures_rbac_and_decommissioned(client, db_session, equipment_factory):
    from app.dependencies import get_current_user_fpso
    from app.main import app

    # Case: Decommissioned Equipment
    eq_dec = equipment_factory(fpso_name="FPSO Harness", status=EquipmentStatus.DECOMMISSIONED.value)
    res_dec = client.post("/api/failures", json={
        "equipment_id": eq_dec["id"],
        "tag": "62-FT-8888",
        "fpso_name": "FPSO Harness",
        "failure_date": "2026-06-01T10:00:00",
        "description": "Fail",
        "impact": "Low",
        "corrective_action": "None",
        "responsible": "X"
    })
    assert res_dec.status_code == 400
    assert "Decommissioned" in res_dec.json()["detail"]

    # Case: RBAC 403 (Wrong FPSO)
    app.dependency_overrides[get_current_user_fpso] = lambda: {"user": {"username": "tech-01"}, "fpso_name": "FPSO A"}
    try:
        # User is in FPSO A, equipment is in FPSO Harness
        res_403 = client.post("/api/failures", json={
            "equipment_id": eq_dec["id"],
            "tag": "62-FT-1001",
            "fpso_name": "FPSO Harness",
            "failure_date": "2026-06-01T10:00:00",
            "description": "Fail",
            "impact": "Low",
            "corrective_action": "None",
            "responsible": "X"
        })
        assert res_403.status_code == 403
    finally:
        del app.dependency_overrides[get_current_user_fpso]

def test_failures_email_configs(client, db_session):
    res = client.post("/api/failures/config/emails", json={
        "fpso_name": "FPSO Harness",
        "email": "audit@sbmoffshore.com",
        "is_active": 1
    })
    assert res.status_code == 200
    
    list_res = client.get("/api/failures/config/emails?fpso_name=FPSO Harness")
    assert any(e["email"] == "audit@sbmoffshore.com" for e in list_res.json())

def test_alerts_filters_and_read(client, db_session):
    # 1. Create multiple alerts
    client.post("/api/alerts", json={
        "type": "Compliance", "severity": "High", "title": "A1", "message": "M1", "fpso_name": "FPSO Harness", "tag_number": "T1"
    })
    client.post("/api/alerts", json={
        "type": "Maintenance", "severity": "Low", "title": "A2", "message": "M2", "fpso_name": "FPSO Harness", "tag_number": "T2"
    })
    
    # 2. Test Filters
    res = client.get("/api/alerts?severity=High&alert_type=Compliance")
    assert len(res.json()) >= 1
    assert res.json()[0]["severity"] == "High"
    
    res2 = client.get("/api/alerts?tag_number=T2")
    assert len(res2.json()) >= 1
    assert res2.json()[0]["tag_number"] == "T2"

    # 3. Test unread count
    count_res = client.get("/api/alerts/unread-count")
    assert count_res.json()["unread_count"] >= 2

def test_alerts_config_flow(client, db_session):
    config_payload = {
        "fpso_name": "FPSO Harness",
        "alert_type": "Critical",
        "rule_config": "{\"limit\": 10}",
        "notify_email": True,
        "notify_whatsapp": True,
        "notify_in_app": True,
        "recipients": [{"user_name": "Admin", "email": "a@b.com", "receive_in_app": True}]
    }
    client.post("/api/alerts/configs", json=config_payload)
    
    configs = client.get("/api/alerts/configs")
    assert any(c["alert_type"] == "Critical" for c in configs.json())

def test_alerts_acknowledge_recheck(client, db_session):
    alert = client.post("/api/alerts", json={
        "type": "C", "severity": "H", "title": "T", "message": "M", "fpso_name": "FPSO Harness"
    }).json()
    
    res = client.put(f"/api/alerts/{alert['id']}/acknowledge", json={
        "acknowledged_by": "User", "run_recheck": True, "justification": "Fixed"
    })
    assert res.status_code == 200
    assert res.json()["run_recheck"] == 1
