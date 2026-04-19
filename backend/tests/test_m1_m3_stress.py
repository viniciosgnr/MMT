"""
Harness Engineering — Deep Integration & Stress Testing (M1 + M3 + M11)
Testes avançados de rastreabilidade, concorrência e integridade de dados.
"""
import pytest
from datetime import datetime, timedelta
from app import models, database

def test_asset_swap_historical_traceability(client, equipment_factory, tag_factory, sample_factory, installation_factory):
    """
    Cenário: Equipamento A move-se de Tag X para Tag Y. 
    Amostras coletadas em Tag X enquanto A estava lá devem continuar vinculadas ao Equipamento A. 
    Amostras novas em Tag X (com Equipamento B) devem ser vinculadas a B.
    """
    # 1. Setup Assets
    eq_a = equipment_factory(serial_number="EQ-A")
    eq_b = equipment_factory(serial_number="EQ-B")
    tag_x = tag_factory(tag_number="TAG-X")
    tag_y = tag_factory(tag_number="TAG-Y")
    
    sp_x = client.post("/api/chemical/sample-points", json={
        "tag_number": "SP-X", "description": "SP X", "fpso_name": "FPSO Harness"
    }).json()
    sp_y = client.post("/api/chemical/sample-points", json={
        "tag_number": "SP-Y", "description": "SP Y", "fpso_name": "FPSO Harness"
    }).json()
    
    # Link Meters
    client.post(f"/api/chemical/sample-points/{sp_x['id']}/link-meters", json=[tag_x["id"]])
    client.post(f"/api/chemical/sample-points/{sp_y['id']}/link-meters", json=[tag_y["id"]])

    # 2. Stage 1: Eq A in Tag X (10 minutes ago)
    t1 = datetime.utcnow() - timedelta(minutes=10)
    inst_a1 = installation_factory(eq_id=eq_a["id"], t_id=tag_x["id"], installed_by="Harness")
    s1 = sample_factory(sample_point_id=sp_x["id"], meter_id=tag_x["id"], sample_id="S1-EQA-X")
    
    # Manual backdate in DB
    db = next(database.get_db())
    db.query(models.EquipmentTagInstallation).filter(models.EquipmentTagInstallation.id == inst_a1["id"]).update({"installation_date": t1})
    db.query(models.Sample).filter(models.Sample.id == s1["id"]).update({"created_at": t1 + timedelta(minutes=1)})
    db.commit()
    
    # 3. Stage 2: Move Eq A to Tag Y (5 minutes ago)
    t2 = datetime.utcnow() - timedelta(minutes=5)
    client.post(f"/api/equipment/remove/{inst_a1['id']}")
    db.query(models.EquipmentTagInstallation).filter(models.EquipmentTagInstallation.id == inst_a1["id"]).update({"removal_date": t2})
    
    inst_a2 = installation_factory(eq_id=eq_a["id"], t_id=tag_y["id"], installed_by="Harness")
    s2 = sample_factory(sample_point_id=sp_y["id"], meter_id=tag_y["id"], sample_id="S2-EQA-Y")
    
    db.query(models.EquipmentTagInstallation).filter(models.EquipmentTagInstallation.id == inst_a2["id"]).update({"installation_date": t2})
    db.query(models.Sample).filter(models.Sample.id == s2["id"]).update({"created_at": t2 + timedelta(minutes=1)})
    db.commit()
    
    # 4. Stage 3: Eq B in Tag X (1 minute ago)
    t3 = datetime.utcnow() - timedelta(minutes=1)
    inst_b = installation_factory(eq_id=eq_b["id"], t_id=tag_x["id"], installed_by="Harness")
    s3 = sample_factory(sample_point_id=sp_x["id"], meter_id=tag_x["id"], sample_id="S3-EQB-X")
    
    db.query(models.EquipmentTagInstallation).filter(models.EquipmentTagInstallation.id == inst_b["id"]).update({"installation_date": t3})
    db.query(models.Sample).filter(models.Sample.id == s3["id"]).update({"created_at": datetime.utcnow()})
    db.commit()

    # 5. Verification: Eq A should see S1 and S2
    res_a = client.get(f"/api/chemical/samples?equipment_id={eq_a['id']}")
    samples_a = [s["sample_id"] for s in res_a.json()]
    assert "S1-EQA-X" in samples_a
    assert "S2-EQA-Y" in samples_a
    assert "S3-EQB-X" not in samples_a

    # 6. Verification: Eq B should see only S3
    res_b = client.get(f"/api/chemical/samples?equipment_id={eq_b['id']}")
    samples_b = [s["sample_id"] for s in res_b.json()]
    assert "S3-EQB-X" in samples_b
    assert "S1-EQA-X" not in samples_b

def test_occupancy_guard_enforcement(client, equipment_factory, tag_factory, installation_factory):
    """Verifica se o sistema impede duas instalações ativas na mesma tag."""
    eq1 = equipment_factory(serial_number="EQ-1")
    eq2 = equipment_factory(serial_number="EQ-2")
    tag = tag_factory(tag_number="TAG-BUSY")
    
    # Install EQ1
    installation_factory(eq_id=eq1["id"], t_id=tag["id"])
    
    # Try install EQ2 on same tag (Should fail)
    install_payload = {
        "equipment_id": eq2["id"],
        "tag_id": tag["id"],
        "installed_by": "System Guard"
    }
    res = client.post("/api/equipment/install", json=install_payload)
    assert res.status_code == 400
    assert "occupied" in res.json()["detail"].lower()

def test_hierarchy_realtime_sync(client, tag_factory):
    """Verifica se mudanças no M1 refletem imediatamente no M11 Tree."""
    tag = tag_factory(tag_number="T44-FT-4444", description="Original Desc", classification="Fiscal")
    
    # Verify Tree
    res1 = client.get("/api/config/hierarchy/tree")
    fpso = res1.json()[0]
    node = next(m for m in fpso["children"] if m["tag"] == "T44-FT-4444")
    assert node["description"] == "Original Desc"
    
    # Update Tag in M1 (Include all mandatory fields for PUT)
    res = client.put(f"/api/equipment/tags/{tag['id']}", json={
        "tag_number": "T44-FT-4444", 
        "description": "Updated Desc"
    })
    assert res.status_code == 200
    
    # Verify Tree again
    res2 = client.get("/api/config/hierarchy/tree")
    fpso2 = res2.json()[0]
    node2 = next(m for m in fpso2["children"] if m["tag"] == "T44-FT-4444")
    assert node2["description"] == "Updated Desc"

def test_delete_protection_guards(client, tag_factory, sp_factory):
    """Verifica bloqueio de deleção para registros com dependências."""
    tag = tag_factory(tag_number="TAG-PROTECTED")
    sp = sp_factory(tag_number="SP-PROTECTED")
    
    # Link them
    client.post(f"/api/chemical/sample-points/{sp['id']}/link-meters", json=[tag["id"]])
    
    # Try to delete Tag with active link (Should fail or be blocked by constraint)
    # Note: Depending on implementation, it might fail with 400 or DB error 500.
    # We want a clean 400/409.
    res = client.delete(f"/api/equipment/tags/{tag['id']}")
    # If the system is robust, it returns 400.
    assert res.status_code in [400, 409] 
