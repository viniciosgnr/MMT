import pytest
from app.models import MaintenanceColumn, MaintenanceLabel, MaintenanceCard

def test_maintenance_flow_complete(client, db_session, equipment_factory, tag_factory):
    # 1. Setup - Create Column
    col_res = client.post("/api/maintenance/columns", json={"name": "Backlog", "order": 1})
    assert col_res.status_code == 200
    col_id = col_res.json()["id"]

    # 2. Setup - Create Labels
    lab_res1 = client.post("/api/maintenance/labels", json={"name": "Urgent", "color": "#FF0000"})
    lab_res2 = client.post("/api/maintenance/labels", json={"name": "Onshore", "color": "#00FF00"})
    label1_id = lab_res1.json()["id"]
    label2_id = lab_res2.json()["id"]

    # 3. Setup - Get Equipment and Tag
    eq = equipment_factory(fpso_name="FPSO Harness")
    tag = tag_factory()

    # 4. Create Card with full associations
    card_payload = {
        "title": "Repair Flow Meter",
        "description": "Bearing replacement",
        "column_id": col_id,
        "fpso": "FPSO Harness",
        "status": "Todo",
        "responsible": "John Doe",
        "label_ids": [label1_id, label2_id],
        "equipment_ids": [eq["id"]],
        "tag_ids": [tag["id"]]
    }
    
    res = client.post("/api/maintenance/cards", json=card_payload)
    assert res.status_code == 200, f"Card creation failed: {res.text}"
    card = res.json()
    assert len(card["labels"]) == 2
    assert len(card["linked_equipments"]) == 1
    card_id = card["id"]

    # 5. Create another card to test connections
    card2_res = client.post("/api/maintenance/cards", json={
        "title": "Sub-task",
        "column_id": col_id,
        "fpso": "FPSO Harness",
        "connected_card_ids": [card_id]
    })
    assert card2_res.status_code == 200
    card2 = card2_res.json()
    assert len(card2["connections"]) == 1

    # 6. Update Card (Exercise update branches)
    update_payload = {
        "status": "In Progress",
        "label_ids": [label1_id], # Remove one label
        "equipment_ids": [],      # Clear equipment
        "connected_card_ids": [card2["id"]] # Connect back to card 2
    }
    upd_res = client.patch(f"/api/maintenance/cards/{card_id}", json=update_payload)
    assert upd_res.status_code == 200
    updated_card = upd_res.json()
    assert len(updated_card["labels"]) == 1
    assert len(updated_card["linked_equipments"]) == 0
    assert len(updated_card["connections"]) == 1

    # 7. Comments
    comm_res = client.post(f"/api/maintenance/cards/{card_id}/comments", json={
        "text": "Starting now",
        "author": "Harness Tester"
    })
    assert comm_res.status_code == 200
    comm_id = comm_res.json()["id"]

    del_comm_res = client.delete(f"/api/maintenance/comments/{comm_id}")
    assert del_comm_res.status_code == 200

    # 8. List and Filter
    list_res = client.get(f"/api/maintenance/cards?fpso=FPSO Harness&status=In Progress")
    assert list_res.status_code == 200
    # The filter in router uses current_user_data["fpso_name"] if present.
    # Since we set it to "FPSO Harness", it should match.
    assert len(list_res.json()) >= 1

def test_maintenance_error_cases(client):
    from app.dependencies import get_current_user_fpso
    from app.main import app
    
    # Mock user tied to FPSO A to test 403 rejection
    app.dependency_overrides[get_current_user_fpso] = lambda: {"user": {"username": "tech-01"}, "fpso_name": "FPSO A"}
    
    try:
        # Wrong FPSO
        res = client.post("/api/maintenance/cards", json={
            "title": "Forbidden Card",
            "column_id": 1,
            "fpso": "FPSO B"
        })
        assert res.status_code == 403
    finally:
        del app.dependency_overrides[get_current_user_fpso]

    # Not Found
    res = client.patch("/api/maintenance/cards/9999", json={"status": "Done"})
    assert res.status_code == 404
