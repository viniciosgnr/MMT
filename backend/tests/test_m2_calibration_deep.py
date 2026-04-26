import pytest
from app.models import Equipment, CalibrationTask, CalibrationTaskStatus, CalibrationTaskType
from datetime import date

def test_plan_calibration(client, db_session, equipment_factory):
    equipment = equipment_factory()
    task = CalibrationTask(
        equipment_id=equipment["id"],
        tag="TAG-01",
        description="Test Task",
        due_date=date.today(),
        type=CalibrationTaskType.CALIBRATION.value,
        status=CalibrationTaskStatus.PENDING.value
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    payload = {
        "procurement_ids": [123, 456],
        "notes": "Planning notes"
    }

    res = client.post(f"/api/calibration/tasks/{task.id}/plan", json=payload)
    assert res.status_code == 200
    
    db_session.refresh(task)
    assert task.status == CalibrationTaskStatus.SCHEDULED.value
    assert "123" in task.spare_procurement_ids

def test_execute_calibration(client, db_session, equipment_factory):
    equipment = equipment_factory()
    task = CalibrationTask(
        equipment_id=equipment["id"],
        tag="TAG-02",
        description="Test Task",
        due_date=date.today(),
        type=CalibrationTaskType.CALIBRATION.value,
        status=CalibrationTaskStatus.SCHEDULED.value
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    payload = {
        "execution_date": "2026-06-01",
        "completion_date": "2026-06-01",
        "calibration_type": "in-situ",
        "seal_number": "SEAL-001",
        "seal_date": "2026-06-01",
        "seal_location": "Terminal Block"
    }

    res = client.post(f"/api/calibration/tasks/{task.id}/execute", json=payload)
    assert res.status_code == 200

    db_session.refresh(task)
    assert task.status == CalibrationTaskStatus.EXECUTED.value
    assert task.seal_number == "SEAL-001"

def test_upload_certificate(client, db_session, equipment_factory):
    equipment = equipment_factory()
    task = CalibrationTask(
        equipment_id=equipment["id"],
        tag="TAG-03",
        description="Test Task",
        due_date=date.today(),
        type=CalibrationTaskType.CALIBRATION.value,
        status=CalibrationTaskStatus.EXECUTED.value
    )
    db_session.add(task)
    db_session.commit()

    payload = {
        "certificate_number": "CERT-2026-001",
        "issue_date": "2026-06-05",
        "uncertainty": 0.05,
        "standard_reading": 10.0,
        "equipment_reading": 10.01
    }

    res = client.post(f"/api/calibration/tasks/{task.id}/certificate", json=payload)
    assert res.status_code == 200

    db_session.refresh(task)
    assert task.certificate_number == "CERT-2026-001"
    assert task.certificate_ca_status == "pending"

def test_validate_certificate(client, db_session, equipment_factory):
    equipment = equipment_factory()
    # To pass validation, cert number should contain the tag (normalized)
    task = CalibrationTask(
        equipment_id=equipment["id"],
        tag="TAG04",
        description="Test Task",
        due_date=date.today(),
        type=CalibrationTaskType.CALIBRATION.value,
        status=CalibrationTaskStatus.EXECUTED.value,
        certificate_number="CERT-TAG04-001",
        certificate_issued_date=date(2026, 6, 5),
        exec_date=date(2026, 6, 1)
    )
    db_session.add(task)
    db_session.commit()

    res = client.post(f"/api/calibration/tasks/{task.id}/certificate/validate")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "approved"

def test_fc_update(client, db_session, equipment_factory):
    equipment = equipment_factory()
    task = CalibrationTask(
        equipment_id=equipment["id"],
        tag="TAG-05",
        description="Test Task",
        due_date=date.today(),
        status=CalibrationTaskStatus.EXECUTED.value
    )
    db_session.add(task)
    db_session.commit()

    payload = {
        "fc_evidence_url": "https://storage.mmt/fc-screenshot-1.png",
        "notes": "Applied correction factor"
    }

    res = client.post(f"/api/calibration/tasks/{task.id}/fc-update", json=payload)
    assert res.status_code == 200

    db_session.refresh(task)
    assert task.status == "Completed"

def test_fail_task(client, db_session, equipment_factory):
    equipment = equipment_factory()
    task = CalibrationTask(
        equipment_id=equipment["id"],
        tag="TAG-06",
        description="Test Task",
        due_date=date.today(),
        status=CalibrationTaskStatus.PENDING.value
    )
    db_session.add(task)
    db_session.commit()

    # The router path is /tasks/{task_id}/fail
    # It takes reason as a string but typically FastAPI expects it as a query param if not in body
    # Let's check router sig: def fail_task(task_id: int, reason: str, ...)
    # If it's a required string and not Pydantic, it's a query param.
    res = client.post(f"/api/calibration/tasks/{task.id}/fail?reason=DamagedDuringCalibration")
    assert res.status_code == 200
    assert "notification_id" in res.json()

def test_generate_certificate_number(client, db_session, equipment_factory):
    # 1. Create Campaign
    from app.models import CalibrationCampaign
    from datetime import date
    camp = CalibrationCampaign(name="Campaign 2026", fpso_name="Cidade de Saquarema", start_date=date(2026,1,1), responsible="Admin")
    db_session.add(camp)
    db_session.flush()

    # 2. Create Task linked to campaign
    eq = equipment_factory()
    task = CalibrationTask(
        campaign_id=camp.id,
        equipment_id=eq["id"],
        tag="T-TRIG-01",
        description="D",
        due_date=date.today(),
        status="Pending"
    )
    db_session.add(task)
    db_session.commit()

    from app.services.calibration_service import CalibrationService
    res = CalibrationService.generate_certificate_number(db_session, task.id, "PRV")
    # CDS is Saquarema trigram
    assert "CDS-PRV" in res["certificate_number"]

    # 3. Test sequence increment
    task.certificate_number = res["certificate_number"]
    db_session.commit()
    
    res2 = CalibrationService.generate_certificate_number(db_session, task.id, "PRV")
    # Should be seq 002 if 001 was extracted
    if "-001" in res["certificate_number"]:
        assert "-002" in res2["certificate_number"]

def test_generate_certificate_number_404(db_session):
    from app.services.calibration_service import CalibrationService
    import pytest
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as excinfo:
        CalibrationService.generate_certificate_number(db_session, 99999)
    assert excinfo.value.status_code == 404

def test_generate_certificate_number_various_fpsos(db_session, equipment_factory):
    from app.models import CalibrationCampaign, CalibrationTask
    from app.services.calibration_service import CalibrationService
    from datetime import date
    fpsos = ["Cidade de Angra dos Reis", "Anchieta", "Sepetiba", "Unknown FPSO"]
    for name in fpsos:
        camp = CalibrationCampaign(name=f"C-{name}", fpso_name=name, start_date=date.today(), responsible="R")
        db_session.add(camp)
        db_session.flush()
        eq = equipment_factory()
        task = CalibrationTask(campaign_id=camp.id, equipment_id=eq["id"], tag="T", due_date=date.today())
        db_session.add(task)
        db_session.commit()
        res = CalibrationService.generate_certificate_number(db_session, task.id)
        assert res["certificate_number"] is not None

def test_generate_certificate_number_bad_parts(db_session, equipment_factory):
    from app.models import CalibrationTask
    from app.services.calibration_service import CalibrationService
    from datetime import date
    eq = equipment_factory()
    task = CalibrationTask(equipment_id=eq["id"], tag="T", due_date=date.today(), certificate_number="BAD-FORMAT")
    db_session.add(task)
    db_session.commit()
    res = CalibrationService.generate_certificate_number(db_session, task.id)
    assert "-001" in res["certificate_number"]


