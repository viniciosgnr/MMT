import pytest
import io
from datetime import date, datetime

def test_sync_source_and_ingestion(client, db_session):
    # 1. Create Source
    source_payload = {
        "name": "Omni 6000 - Unit 1",
        "type": "FLOW_COMPUTER",
        "fpso": "FPSO Harness",
        "connection_details": "{\"ip\": \"10.1.1.5\"}"
    }
    res = client.post("/api/sync/sources", json=source_payload)
    assert res.status_code == 200
    source_id = res.json()["id"]

    # 2. Ingest Data
    ingest_payload = {
        "source_id": source_id,
        "data": [
            {
                "tag_number": "62-FT-1101",
                "value": 1250.5,
                "timestamp": "2026-06-01T12:00:00",
                "unit": "m3/h",
                "quality": "Good"
            }
        ]
    }
    res = client.post("/api/sync/ingest", json=ingest_payload)
    assert res.status_code == 200
    assert "job_id" in res.json()

    # 3. Check status
    res = client.get("/api/sync/status")
    assert res.status_code == 200
    status = [s for s in res.json() if s["module_name"] == "Omni 6000 - Unit 1"]
    assert len(status) == 1
    assert status[0]["records_synced"] == 1

def test_sync_file_upload(client, db_session):
    # Create Source
    source_res = client.post("/api/sync/sources", json={
        "name": "USB Manual Dump",
        "type": "MANUAL_FILE",
        "fpso": "FPSO Harness"
    })
    source_id = source_res.json()["id"]

    # CSV Content
    csv_content = "tag,value,timestamp,unit,quality\n62-PT-1001,45.2,2026-06-01T10:00:00,bar,Good\n62-TT-1001,25.5,2026-06-01T10:05:00,C,Good"
    file = ("sync_dump.csv", csv_content.encode())
    
    res = client.post(f"/api/sync/upload?source_id={source_id}", files={"file": file})
    assert res.status_code == 200
    assert res.json()["records"] == 2

def test_export_flow(client, db_session, hierarchy_factory):
    # 1. Setup - Hierarchy for scoping
    node = hierarchy_factory(tag="EXP-01", description="Export Root", fpso_name="FPSO Harness")
    node_id = node["id"]

    # 2. Start Export Job
    export_payload = {
        "fpso_name": "FPSO Harness",
        "fpso_nodes": [node_id],
        "start_date": "2026-01-01T00:00:00",
        "end_date": "2026-12-31T23:59:59",
        "file_types": ["CERTS", "SAMPLING", "CHANGES"],
        "format": "ZIP"
    }
    
    # Path is /api/export/prepare
    res = client.post("/api/export/prepare", json=export_payload)
    assert res.status_code == 200
    job_id = res.json()["job_id"]

    # 3. Check Status
    res = client.get(f"/api/export/status/{job_id}")
    assert res.status_code == 200
    assert res.json()["status"] in ["PENDING", "PROCESSING", "COMPLETED"]
