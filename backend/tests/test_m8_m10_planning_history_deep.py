import pytest
from datetime import date, datetime

def test_planning_lifecycle(client, db_session):
    # 1. Create activity
    payload = {
        "title": "Monthly Instrumentation Audit",
        "description": "Full check of fiscal systems",
        "scheduled_date": "2026-06-15T00:00:00",
        "type": "Metrological Audit",
        "fpso_name": "FPSO Harness",
        "status": "Planned",
        "responsible": "Inspector X"
    }
    res = client.post("/api/planning/activities", json=payload)
    assert res.status_code == 200
    activity_id = res.json()["id"]

    # 2. Update activity
    upd_payload = {"description": "Mandatory audit"}
    res = client.put(f"/api/planning/activities/{activity_id}", json=upd_payload)
    assert res.status_code == 200
    assert res.json()["description"] == "Mandatory audit"

    # 3. Mitigate activity
    mit_payload = {
        "reason": "Wait for spare parts",
        "new_due_date": "2026-07-01T00:00:00",
        "attachment_url": "https://storage/mitigation.pdf"
    }
    res = client.post(f"/api/planning/activities/{activity_id}/mitigate", json=mit_payload)
    assert res.status_code == 200
    assert res.json()["status"] == "Mitigated"

    # 4. Cancel activity
    del_res = client.delete(f"/api/planning/activities/{activity_id}")
    assert del_res.status_code == 200

def test_historical_reports(client, db_session):
    # 1. Create Unique Report Type
    import uuid
    unique_name = f"Log-{uuid.uuid4().hex[:6]}"
    rt_res = client.post("/api/reports/types", json={"name": unique_name, "description": "Daily logs"})
    assert rt_res.status_code == 200
    rt_id = rt_res.json()["id"]

    # 2. Bulk Upload reports
    payload = {
        "report_type_id": rt_id,
        "report_date": "2026-06-01",
        "fpso_name": "FPSO Harness",
        "title_prefix": "DAILY-CONF",
        "metering_system": "B01",
        "serial_number": "SN123",
        "files": [
            {"filename": "log_a.pdf", "file_url": "/s3/a.pdf", "file_size": 1024},
            {"filename": "log_b.rv", "file_url": "/s3/b.rv", "file_size": 2048}
        ]
    }
    res = client.post("/api/reports/upload", json=payload)
    assert res.status_code == 200

    # 3. List reports with filter and verify uploaded_by
    res = client.get(f"/api/reports?report_type_id={rt_id}")
    assert res.status_code == 200
    reports = res.json()
    assert len(reports) == 2
    for r in reports:
        assert r["uploaded_by"] is not None
        assert isinstance(r["uploaded_by"], str)
