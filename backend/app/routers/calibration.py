from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime
import json
from .. import models, database
from ..schemas import calibration as schemas
from ..dependencies import get_current_user

router = APIRouter(
    prefix="/api/calibration",
    tags=["calibration"],
)

# Campaign Endpoints
@router.post("/campaigns", response_model=schemas.CalibrationCampaign)
def create_campaign(campaign: schemas.CalibrationCampaignCreate, db: Session = Depends(database.get_db), current_user = Depends(get_current_user)):
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
    db: Session = Depends(database.get_db)
):
    query = db.query(models.CalibrationCampaign)
    if fpso_name:
        query = query.filter(models.CalibrationCampaign.fpso_name == fpso_name)
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
def create_task(task: schemas.CalibrationTaskCreate, db: Session = Depends(database.get_db), current_user = Depends(get_current_user)):
    db_task = models.CalibrationTask(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.get("/tasks", response_model=List[schemas.CalibrationTask])
def list_tasks(
    campaign_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db)
):
    query = db.query(models.CalibrationTask)
    if campaign_id:
        query = query.filter(models.CalibrationTask.campaign_id == campaign_id)
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
    current_user = Depends(get_current_user)
):
    """Transition task from PENDING to PLANNED."""
    task = db.query(models.CalibrationTask).filter(models.CalibrationTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.status = models.CalibrationTaskStatus.SCHEDULED.value
    task.plan_date = date.today()
    if plan_data.procurement_ids:
        task.spare_procurement_ids = json.dumps(plan_data.procurement_ids)
    
    db.commit()
    db.refresh(task)
    return {"message": "Calibration planned successfully", "task_id": task.id, "status": task.status}

@router.post("/tasks/{task_id}/execute")
def execute_calibration(
    task_id: int,
    exec_data: schemas.CalibrationExecutionData,
    db: Session = Depends(database.get_db),
    current_user = Depends(get_current_user)
):
    """Record calibration execution with temporary completion date."""
    task = db.query(models.CalibrationTask).filter(models.CalibrationTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.status = models.CalibrationTaskStatus.EXECUTED.value
    task.exec_date = exec_data.execution_date
    task.calibration_type = exec_data.calibration_type
    task.temporary_completion_date = exec_data.completion_date
    task.is_temporary = 1
    task.seal_number = exec_data.seal_number
    task.seal_installation_date = exec_data.seal_date
    task.seal_location = exec_data.seal_location
    
    # Also record seal in history
    seal = models.SealHistory(
        tag_id=task.equipment.installations[0].tag_id if task.equipment.installations else None,
        seal_number=exec_data.seal_number,
        seal_type=exec_data.seal_type or "Wire",
        seal_location=exec_data.seal_location,
        installation_date=exec_data.seal_date,
        installed_by="System",  # TODO: Get from auth
        is_active=1
    )
    db.add(seal)
    
    db.commit()
    db.refresh(task)
    return {"message": "Calibration executed successfully", "task_id": task.id, "status": task.status}

# M2 MVP: Seal Management Endpoints

@router.post("/seals", response_model=schemas.SealHistoryRead)
def record_seal_installation(
    seal_data: schemas.SealInstallationData,
    db: Session = Depends(database.get_db),
    current_user = Depends(get_current_user)
):
    """Record a new seal installation."""
    # Deactivate previous seal if exists
    previous_seal = db.query(models.SealHistory).filter(
        models.SealHistory.tag_id == seal_data.tag_id,
        models.SealHistory.is_active == 1
    ).first()
    
    if previous_seal:
        previous_seal.is_active = 0
        previous_seal.removal_date = seal_data.installation_date
        previous_seal.removed_by = seal_data.installed_by
        previous_seal.removal_reason = seal_data.removal_reason or "Calibration"
    
    # Create new seal record
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
    current_user = Depends(get_current_user)
):
    """Upload certificate metadata and mark task as definitively complete."""
    task = db.query(models.CalibrationTask).filter(models.CalibrationTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update task with certificate info
    task.certificate_number = certificate_data.certificate_number
    task.certificate_issued_date = certificate_data.issue_date
    task.is_temporary = 0
    task.definitive_completion_date = certificate_data.issue_date
    task.certificate_ca_status = "pending"
    
    # Update or create result
    if not task.results:
        result = models.CalibrationResult(
            task_id=task_id,
            standard_reading=certificate_data.standard_reading or 0.0,
            equipment_reading=certificate_data.equipment_reading or 0.0,
            uncertainty=certificate_data.uncertainty
        )
        db.add(result)
    else:
        result = task.results
        if certificate_data.uncertainty:
            result.uncertainty = certificate_data.uncertainty
        if certificate_data.standard_reading:
            result.standard_reading = certificate_data.standard_reading
        if certificate_data.equipment_reading:
            result.equipment_reading = certificate_data.equipment_reading
    
    db.commit()
    return {"message": "Certificate uploaded successfully", "task_id": task.id}

@router.post("/tasks/{task_id}/certificate/validate")
def validate_certificate(
    task_id: int,
    db: Session = Depends(database.get_db),
    current_user = Depends(get_current_user)
):
    """Run CA validation rules on certificate data."""
    task = db.query(models.CalibrationTask).filter(models.CalibrationTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    validation_results = []
    issues = []
    
    # Rule 1: Certificate number exists
    if not task.certificate_number:
        issues.append("Certificate number is missing")
    else:
        validation_results.append({
            "rule": "Certificate Number Exists",
            "status": "pass",
            "value": task.certificate_number
        })
    
    # Rule 2: Certificate issued within RTM time limit (30 days)
    if task.certificate_issued_date and task.exec_date:
        days_diff = (task.certificate_issued_date - task.exec_date).days
        if days_diff > 30:
            issues.append(f"Certificate issued {days_diff} days after calibration (limit: 30 days)")
            validation_results.append({
                "rule": "RTM Time Limit",
                "status": "fail",
                "value": f"{days_diff} days"
            })
        else:
            validation_results.append({
                "rule": "RTM Time Limit",
                "status": "pass",
                "value": f"{days_diff} days"
            })
    
    # Rule 3: Tag number matches (basic check)
    if task.certificate_number and task.tag:
        # Extract tag from certificate number (format: AAA-BBB-CC-DDD)
        # For now, just check if tag is mentioned
        if task.tag.replace("-", "") not in task.certificate_number.replace("-", ""):
            issues.append(f"Certificate number may not match tag {task.tag}")
    
    # Store validation results
    result = task.results
    if result:
        result.ca_validated_at = datetime.utcnow()
        result.ca_validated_by = "System"  # TODO: Get from auth
        result.ca_validation_rules = json.dumps(validation_results)
        result.ca_issues = json.dumps(issues) if issues else None
        task.certificate_ca_status = "approved" if not issues else "pending"
        db.commit()
    
    return {
        "validation_results": validation_results,
        "issues": issues,
        "status": "approved" if not issues else "pending"
    }

# Result Endpoints (existing)
@router.post("/tasks/{task_id}/results", response_model=schemas.CalibrationResult)
def submit_results(task_id: int, result: schemas.CalibrationResultBase, db: Session = Depends(database.get_db), current_user = Depends(get_current_user)):
    # Check if task exists
    task = db.query(models.CalibrationTask).filter(models.CalibrationTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Create result
    db_result = models.CalibrationResult(task_id=task_id, **result.dict())
    db.add(db_result)
    
    # Update task status
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
    current_user = Depends(get_current_user)
):
    """Generate a compliant certificate number: AAA-BBB-CC-DDD."""
    task = db.query(models.CalibrationTask).filter(models.CalibrationTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # 1. Get FPSO Trigram
    # Assuming task -> campaign -> fpso_name OR task -> equipment -> installation -> fpso
    # Fallback to a default if logic fails (MVP)
    fpso_name = "Unknown"
    if task.campaign:
        fpso_name = task.campaign.fpso_name
    
    # Simple mapping
    trigrams = {
        "Cidade de Angra dos Reis": "CDA",
        "Cidade de Ilhabela": "CDI",
        "Cidade de Maricá": "CDM",
        "Cidade de Saquarema": "CDS",
        "Cidade de Paraty": "CDP",
        "Espirito Santo": "ESS",
        "Anchieta": "ATD",
        "Capixaba": "ADG",
        "Sepetiba": "SEP"
    }
    
    # Try partial match or exact
    aaa = "XXX"
    for name, trigram in trigrams.items():
        if name in fpso_name:
            aaa = trigram
            break
            
    # 2. Get Sequence
    year = datetime.now().year
    yy = str(year)[-2:]
    
    # Find max sequence for this year and type
    # Using a LIKE query to find matching patterns
    pattern = f"{aaa}-{cert_type}-{yy}-%"
    
    last_cert = db.query(models.CalibrationTask).filter(
        models.CalibrationTask.certificate_number.like(pattern)
    ).order_by(models.CalibrationTask.certificate_number.desc()).first()
    
    seq = 1
    if last_cert and last_cert.certificate_number:
        # Extract DDD
        try:
            parts = last_cert.certificate_number.split('-')
            if len(parts) == 4:
                seq = int(parts[3]) + 1
        except:
            pass # Fallback to 1
            
    ddd = f"{seq:03d}"
    
    cert_number = f"{aaa}-{cert_type}-{yy}-{ddd}"
    
    return {"certificate_number": cert_number}

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
    
    # Simple CSV construction
    output = "Tag ID,Seal Number,Type,Location,Installed,Removed,Status\n"
    for s in seals:
        output += f"{s.tag_id},{s.seal_number},{s.seal_type},{s.seal_location},{s.installation_date},{s.removal_date},{'Active' if s.is_active else 'Inactive'}\n"
        
    # In a real app, return StreamingResponse
    return {"csv_content": output, "count": len(seals)}
