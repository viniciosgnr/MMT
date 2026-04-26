"""
Harness Engineering RBAC Tests — Phase 2 Security Hardening.

Verifies that users can only access data for their assigned FPSO,
and endpoints properly extract 'fpso_name' from the auth token.
"""
from app.dependencies import get_current_user, get_current_user_fpso

def test_equipment_read_enforces_fpso_scoping(client, equipment_factory, db_session):
    """Test that a user only sees equipment belonging to their FPSO."""
    
    # Create two equipments for different FPSOs
    eq_harness = equipment_factory(fpso_name="FPSO Harness", serial_number="SN-HARNESS-1")
    eq_other = equipment_factory(fpso_name="FPSO Other", serial_number="SN-OTHER-1")
    
    # Override get_current_user_fpso directly for this test
    app = client.app
    original_override = app.dependency_overrides.get(get_current_user_fpso)
    
    app.dependency_overrides[get_current_user_fpso] = lambda: {
        "user": {"id": "fpso-user", "role": "HarnessAdmin"},
        "fpso_name": "FPSO Harness"
    }
    
    try:
        res = client.get("/api/equipment/")
        assert res.status_code == 200
        data = res.json()
        
        # Should only see the FPSO Harness equipment
        assert any(e["serial_number"] == "SN-HARNESS-1" for e in data)
        assert not any(e["serial_number"] == "SN-OTHER-1" for e in data)
    finally:
        # Restore previous override state
        if original_override:
            app.dependency_overrides[get_current_user_fpso] = original_override
        else:
            del app.dependency_overrides[get_current_user_fpso]


def test_available_tags_forces_user_fpso(client, equipment_factory, tag_factory, installation_factory):
    """Test that available tags query prioritizes the user's FPSO over query params."""
    
    # Setup: Tag with equipment in FPSO Harness
    eq_harness = equipment_factory(fpso_name="FPSO Harness")
    tag_harness = tag_factory(tag_number="TAG-HARNESS")
    installation_factory(eq_harness["id"], tag_harness["id"])
    
    app = client.app
    original_override = app.dependency_overrides.get(get_current_user_fpso)
    
    # A user from FPSO harness
    app.dependency_overrides[get_current_user_fpso] = lambda: {
        "user": {"id": "test"}, 
        "fpso_name": "FPSO Harness"
    }
    try:
        # Even if they request tags from FPSO Other, RBAC forces their scope
        res = client.get("/api/equipment/tags/available?fpso_name=FPSO Other")
        assert res.status_code == 200
        
        tags = res.json()
        # Should return TAG-HARNESS, ignoring the malicious 'FPSO Other' query param
        assert len(tags) >= 1
        assert any(t["tag_number"] == "TAG-HARNESS" for t in tags)
    finally:
        if original_override:
            app.dependency_overrides[get_current_user_fpso] = original_override
        else:
            del app.dependency_overrides[get_current_user_fpso]
