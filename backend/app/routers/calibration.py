from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime
import json
import csv
import io
from .. import models, database
from ..services.calibration_service import CalibrationService
from ..schemas import calibration as schemas
from ..dependencies import get_current_user_fpso

router = APIRouter(
    prefix="/api/calibration",
    tags=["calibration"],
)

# Campaign Endpoints
@router.post("/campaigns", response_model=schemas.CalibrationCampaign)
def create_campaign(campaign: schemas.CalibrationCampaignCreate, db: Session = Depends(database.get_db), current_user_data = Depends(get_current_user_fpso)):
    if current_user_data["fpso_name"] and campaign.fpso_name != current_user_data["fpso_name"]:
        raise HTTPException(status_code=403, detail="Forbidden: You can only create campaigns for your current FPSO.")
    db_campaign = models.CalibrationCampaign(**campaign.dict())
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign

@router.get("/campaigns", response_model=List[schemas.CalibrationCampaign])
def list_campaigns(
    fpso_name: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user_data = Depends(get_current_user_fpso)
):
    query = db.query(models.CalibrationCampaign)
    filter_fpso = current_user_data["fpso_name"] if current_user_data["fpso_name"] else fpso_name
    if filter_fpso:
        query = query.filter(models.CalibrationCampaign.fpso_name == filter_fpso)
    if status:
        query = query.filter(models.CalibrationCampaign.status == status)
    campaigns = query.offset(skip).limit(limit).all()
    return campaigns

@router.get("/campaigns/{campaign_id}", response_model=schemas.CalibrationCampaign)
def get_campaign(campaign_id: int, db: Session = Depends(database.get_db)):
    campaign = db.query(models.CalibrationCampaign).filter(models.CalibrationCampaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign

# Task Endpoints
@router.post("/tasks", response_model=schemas.CalibrationTask)
def create_task(task: schemas.CalibrationTaskCreate, db: Session = Depends(database.get_db), current_user_data = Depends(get_current_user_fpso)):
    if current_user_data["fpso_name"]:
        # enforce fpso scoping on task creation by checking campaign fpso
        campaign = db.query(models.CalibrationCampaign).filter(models.CalibrationCampaign.id == task.campaign_id).first()
        if campaign and campaign.fpso_name != current_user_data["fpso_name"]:
            raise HTTPException(status_code=403, detail="Forbidden: You can only create tasks for campaigns in your FPSO.")
    db_task = models.CalibrationTask(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.get("/tasks", response_model=List[schemas.CalibrationTask])
def list_tasks(
    campaign_id: Optional[int] = None,
    equipment_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db)
):
    query = db.query(models.CalibrationTask)
    if campaign_id:
        query = query.filter(models.CalibrationTask.campaign_id == campaign_id)
    if equipment_id:
        query = query.filter(models.CalibrationTask.equipment_id == equipment_id)
    if status:
        query = query.filter(models.CalibrationTask.status == status)
    tasks = query.offset(skip).limit(limit).all()
    return tasks

@router.get("/tasks/{task_id}", response_model=schemas.CalibrationTask)
def get_task(task_id: int, db: Session = Depends(database.get_db)):
    task = db.query(models.CalibrationTask).filter(models.CalibrationTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

# M2 MVP: Status Transition Endpoints

@router.post("/tasks/{task_id}/plan")
def plan_calibration(
    task_id: int,
    plan_data: schemas.CalibrationPlanData,
    db: Session = Depends(database.get_db),
    current_user_data = Depends(get_current_user_fpso)
):
    """Transition task from PENDING to PLANNED."""
    return CalibrationService.plan_calibration(db, task_id, plan_data)

@router.post("/tasks/{task_id}/execute")
def execute_calibration(
    task_id: int,
    exec_data: schemas.CalibrationExecutionData,
    db: Session = Depends(database.get_db),
    current_user_data = Depends(get_current_user_fpso)
):
    """Record calibration execution with temporary completion date."""
    user = current_user_data["user"]
    user_id = user.get("id") if isinstance(user, dict) else user.id if user else "System"
    return CalibrationService.execute_calibration(db, task_id, exec_data, user_id)

# M2 MVP: Seal Management Endpoints

@router.post("/seals", response_model=schemas.SealHistoryRead)
def record_seal_installation(
    seal_data: schemas.SealInstallationData,
    db: Session = Depends(database.get_db),
    current_user_data = Depends(get_current_user_fpso)
):
    """Record a new seal installation."""
    previous_seal = db.query(models.SealHistory).filter(
        models.SealHistory.tag_id == seal_data.tag_id,
        models.SealHistory.is_active == 1
    ).first()
    
    if previous_seal:
        previous_seal.is_active = 0
        previous_seal.removal_date = seal_data.installation_date
        previous_seal.removed_by = seal_data.installed_by
        previous_seal.removal_reason = seal_data.removal_reason or "Calibration"
    
    new_seal = models.SealHistory(**seal_data.dict())
    db.add(new_seal)
    db.commit()
    db.refresh(new_seal)
    
    return new_seal

@router.get("/tags/{tag_id}/seals", response_model=List[schemas.SealHistoryRead])
def get_tag_seal_history(
    tag_id: int,
    db: Session = Depends(database.get_db)
):
    """Get seal history for a specific tag."""
    seals = db.query(models.SealHistory).filter(
        models.SealHistory.tag_id == tag_id
    ).order_by(models.SealHistory.installation_date.desc()).all()
    
    return seals

@router.get("/seals/active", response_model=List[schemas.SealHistoryRead])
def get_active_seals(
    tag_ids: Optional[str] = None,  # Comma-separated tag IDs
    db: Session = Depends(database.get_db)
):
    """Get currently active seals, optionally filtered by tag IDs."""
    query = db.query(models.SealHistory).filter(models.SealHistory.is_active == 1)
    
    if tag_ids:
        tag_id_list = [int(x) for x in tag_ids.split(",")]
        query = query.filter(models.SealHistory.tag_id.in_(tag_id_list))
    
    seals = query.order_by(models.SealHistory.installation_date.desc()).all()
    return seals

# M2 MVP: Certificate Management Endpoints

@router.post("/tasks/{task_id}/certificate")
def upload_certificate(
    task_id: int,
    certificate_data: schemas.CertificateData,
    db: Session = Depends(database.get_db),
    current_user_data = Depends(get_current_user_fpso)
):
    """Upload certificate metadata and mark task as definitively complete."""
    return CalibrationService.upload_certificate(db, task_id, certificate_data)

@router.post("/tasks/{task_id}/certificate/validate")
def validate_certificate(
    task_id: int,
    db: Session = Depends(database.get_db),
    current_user_data = Depends(get_current_user_fpso)
):
    """Run CA validation rules on certificate data."""
    user = current_user_data["user"]
    user_id = user.get("id") if isinstance(user, dict) else user.id if user else "System"
    return CalibrationService.validate_certificate(db, task_id, user_id)

@router.post("/tasks/{task_id}/fc-update")
def complete_calibration_fc(
    task_id: int,
    fc_data: schemas.FCUpdateData,
    db: Session = Depends(database.get_db),
    current_user_data = Depends(get_current_user_fpso)
):
    """Record Flow Computer evidence upload and formalize task completion."""
    return CalibrationService.complete_calibration_fc(db, task_id, fc_data)

@router.post("/tasks/{task_id}/fail")
def fail_task(
    task_id: int,
    reason: str,
    db: Session = Depends(database.get_db),
    current_user_data = Depends(get_current_user_fpso)
):
    """
    Explicitly fail a calibration task (M2 -> M9 Integration).
    Triggers creation of a Failure Notification.
    """
    user = current_user_data["user"]
    username = user.get("username") if isinstance(user, dict) else user.username if hasattr(user, 'username') else "System"
    return CalibrationService.fail_task(db, task_id, reason, username)

# Result Endpoints (existing)
@router.post("/tasks/{task_id}/results", response_model=schemas.CalibrationResult)
def submit_results(task_id: int, result: schemas.CalibrationResultBase, db: Session = Depends(database.get_db), current_user_data = Depends(get_current_user_fpso)):
    task = db.query(models.CalibrationTask).filter(models.CalibrationTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db_result = models.CalibrationResult(task_id=task_id, **result.dict())
    db.add(db_result)
    
    task.status = models.CalibrationTaskStatus.EXECUTED.value
    task.exec_date = date.today()
    
    db.commit()
    db.refresh(db_result)
    return db_result

@router.get("/tasks/{task_id}/results", response_model=schemas.CalibrationResult)
def get_results(task_id: int, db: Session = Depends(database.get_db)):
    result = db.query(models.CalibrationResult).filter(models.CalibrationResult.task_id == task_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Results not found")
    return result

# M2 MVP: Advanced Features

@router.post("/tasks/{task_id}/certificate/generate")
def generate_certificate_number(
    task_id: int,
    cert_type: str = "PRV", # PRV, LT, SMP
    db: Session = Depends(database.get_db),
    current_user_data = Depends(get_current_user_fpso)
):
    """Generate a compliant certificate number: AAA-BBB-CC-DDD."""
    return CalibrationService.generate_certificate_number(db, task_id, cert_type)

@router.get("/seals/export")
def export_seal_report(
    tag_ids: Optional[str] = None,
    db: Session = Depends(database.get_db)
):
    """Export seal report for selected tags (CSV for MVP)."""
    # ... logic to build CSV ...
    query = db.query(models.SealHistory)
    if tag_ids:
        tids = [int(x) for x in tag_ids.split(',')]
        query = query.filter(models.SealHistory.tag_id.in_(tids))
        
    seals = query.all()
    
    # Build and stream CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Tag ID", "Seal Number", "Type", "Location", "Installed", "Removed", "Installed By", "Reason", "Status"])
    for s in seals:
        writer.writerow([
            s.tag_id, s.seal_number, s.seal_type, s.seal_location,
            s.installation_date, s.removal_date or "",
            s.installed_by, s.removal_reason or "",
            "Active" if s.is_active else "Inactive"
        ])
        
    response = StreamingResponse(iter([output.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=seal_history_export.csv"
    return response
