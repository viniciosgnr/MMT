import pytest
import io
import uuid
import os
from datetime import date, datetime, timedelta
from app.services.export_service import ExportService
from app.schemas.export import ExportRequest
from app import models

def test_export_deep_zip_generation(client, db_session):
    # Setup EVERYTHING inside db_session for consistency
    root = models.HierarchyNode(tag="FPSO Harness", description="Root FPSO", level_type="FP")
    db_session.add(root)
    db_session.flush()
    
    sub_node = models.HierarchyNode(tag="SUB-01", description="Sub System", level_type="System", parent_id=root.id)
    db_session.add(sub_node)
    
    tag = models.InstrumentTag(tag_number="62-FT-DEEP", description="Deep Tag", hierarchy_node_id=sub_node.id)
    db_session.add(tag)
    
    eq = models.Equipment(serial_number="SN-DEEP-01", equipment_type="Flowmeter", fpso_name="FPSO Harness", status="Active")
    db_session.add(eq)
    db_session.flush()
    
    task = models.CalibrationTask(
        tag=tag.tag_number, equipment_id=eq.id, type="Calibration", status="Completed",
        exec_date=date.today(), description="Test task"
    )
    db_session.add(task)
    db_session.flush()
    
    # Link result to task specifically to ensure res.task is valid
    res = models.CalibrationResult(
        task_id=task.id, certificate_url="http://s3/cert.pdf",
        uncertainty_report_url="http://s3/unc.pdf", fc_evidence_url="http://s3/ev.png",
        created_at=datetime.utcnow()
    )
    db_session.add(res)
    
    # Create Installation History for CHANGES
    hist = models.InstallationHistory(
        equipment_id=eq.id, fpso_name="FPSO Harness", 
        installation_date=datetime.utcnow(),
        location=tag.tag_number, reason="REMOVAL", 
        installed_by="Deep Test Bot", notes="Testing changes export"
    )
    db_session.add(hist)
    
    # ADDED: Sampling for full M12 coverage
    sp = models.SamplePoint(tag_number="SP-DEEP-01", description="SP1", fpso_name="FPSO Harness")
    db_session.add(sp)
    db_session.flush()
    
    sample = models.Sample(
        sample_id="SMP-DEEP-01", sample_point_id=sp.id, sampling_date=datetime.utcnow(),
        lab_report_url="http://s3/lab.pdf", notes="Evidence notes"
    )
    db_session.add(sample)
    db_session.commit()

    # Trigger Export with WIDE date range
    job_id = str(uuid.uuid4())
    ExportService.export_jobs[job_id] = {"status": "PENDING"}
    
    now = datetime.utcnow()
    request = ExportRequest(
        fpso_name="FPSO Harness",
        fpso_nodes=[root.id],
        start_date=now - timedelta(days=30),
        end_date=now + timedelta(days=30),
        file_types=["CERTS", "UNCERTAINTY", "EVIDENCE", "CHANGES", "SAMPLING"],
        format="ZIP"
    )
    
    ExportService.generate_export_zip(job_id, request, db_session)
    
    if ExportService.export_jobs[job_id]["status"] == "FAILED":
        print(f"DEBUG: Export Job failed with: {ExportService.export_jobs[job_id].get('message')}")
    
    assert ExportService.export_jobs[job_id]["status"] == "COMPLETED"
    
    # Cleanup temp file if exists
    path = ExportService.export_jobs[job_id].get("file_path")
    if path and os.path.exists(path):
        os.remove(path)

def test_export_suffix_branches():
    assert ExportService.get_suffix("Flowmeter", "Calibration") == "P"
    assert ExportService.get_suffix("Pressure Transmitter", "Calibration") == "S"
    assert ExportService.get_suffix("Orifice Plate", "Check") == "OP"
    assert ExportService.get_suffix("Straight Run", "Cleaning") == "SR"
    assert ExportService.get_suffix(None, "REMOVAL") == "R"
    assert ExportService.get_suffix(None, "UNAVAILABLE") == "UN"
    assert ExportService.get_suffix(None, "AVAILABLE") == "AV"
    assert ExportService.get_suffix("Generic", "Normal") == ""

def test_export_error_handling(db_session):
    job_id = "fail-job"
    ExportService.export_jobs[job_id] = {"status": "PENDING"}
    ExportService.generate_export_zip(job_id, None, db_session)
    assert ExportService.export_jobs[job_id]["status"] == "FAILED"
