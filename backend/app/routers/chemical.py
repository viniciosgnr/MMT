from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, date, timedelta
from .. import models, database
from ..schemas import chemical as schemas
from ..dependencies import get_current_user

router = APIRouter(
    prefix="/api/chemical",
    tags=["chemical"],
)

# --- Sample Points (M3 Configuration) ---

@router.post("/sample-points", response_model=schemas.SamplePoint)
def create_sample_point(sp: schemas.SamplePointCreate, db: Session = Depends(database.get_db), current_user = Depends(get_current_user)):
    db_sp = models.SamplePoint(**sp.model_dump())
    db.add(db_sp)
    db.commit()
    db.refresh(db_sp)
    return db_sp

@router.get("/sample-points", response_model=List[schemas.SamplePoint])
def list_sample_points(fpso_name: Optional[str] = None, db: Session = Depends(database.get_db)):
    query = db.query(models.SamplePoint)
    if fpso_name:
        query = query.filter(models.SamplePoint.fpso_name == fpso_name)
    return query.all()

@router.post("/sample-points/{sp_id}/link-meters")
def link_meters(sp_id: int, tag_ids: List[int], db: Session = Depends(database.get_db), current_user = Depends(get_current_user)):
    db.query(models.InstrumentTag).filter(models.InstrumentTag.id.in_(tag_ids)).update({"sample_point_id": sp_id})
    db.commit()
    return {"message": f"{len(tag_ids)} meters linked to sample point"}

# --- Sampling Campaigns ---

@router.post("/campaigns", response_model=schemas.SamplingCampaign)
def create_campaign(campaign: schemas.SamplingCampaignCreate, db: Session = Depends(database.get_db), current_user = Depends(get_current_user)):
    db_campaign = models.SamplingCampaign(**campaign.model_dump())
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign

@router.get("/campaigns", response_model=List[schemas.SamplingCampaign])
def list_campaigns(fpso_name: Optional[str] = None, status: Optional[str] = None, db: Session = Depends(database.get_db)):
    query = db.query(models.SamplingCampaign)
    if fpso_name:
        query = query.filter(models.SamplingCampaign.fpso_name == fpso_name)
    if status:
        query = query.filter(models.SamplingCampaign.status == status)
    return query.all()

# --- Samples & Lifecycle (M3 Core) ---

@router.post("/samples", response_model=schemas.Sample)
def create_sample(sample: schemas.SampleCreate, db: Session = Depends(database.get_db), current_user = Depends(get_current_user)):
    # Verify sample point
    sp = db.query(models.SamplePoint).filter(models.SamplePoint.id == sample.sample_point_id).first()
    if not sp:
        raise HTTPException(status_code=404, detail="Sample point not found")
        
    db_sample = models.Sample(
        **sample.model_dump(),
        status=models.SampleStatus.PLANNED,
        type=sp.fluid_type
    )
    db.add(db_sample)
    db.commit()
    db.refresh(db_sample)
    
    # Log initial status
    history = models.SampleStatusHistory(
        sample_id=db_sample.id,
        status=models.SampleStatus.PLANNED,
        comments="Sample planned automatically or manually."
    )
    db.add(history)
    db.commit()
    
    return db_sample

@router.get("/samples", response_model=List[schemas.Sample])
def list_samples(
    fpso_name: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(database.get_db)
):
    query = db.query(models.Sample).join(models.SamplePoint)
    if fpso_name:
        query = query.filter(models.SamplePoint.fpso_name == fpso_name)
    if status:
        query = query.filter(models.Sample.status == status)
    return query.all()

@router.get("/samples/{sample_id}", response_model=schemas.Sample)
def get_sample(sample_id: int, db: Session = Depends(database.get_db)):
    sample = db.query(models.Sample).filter(models.Sample.id == sample_id).first()
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    return sample

@router.post("/check-slas")
def check_sampling_slas(db: Session = Depends(database.get_db)):
    """Scans active samples and creates alerts for SLA violations."""
    from datetime import date, timedelta
    from ..models import Alert, AlertSeverity, SampleStatus
    
    today = date.today()
    alerts_created = 0
    
    # 1. Check Samples that are 'Sampled' but missing report for > 15 days
    overdue_reports = db.query(models.Sample).filter(
        models.Sample.status == SampleStatus.SAMPLED.value,
        models.Sample.sampling_date <= today - timedelta(days=15)
    ).all()
    
    for s in overdue_reports:
        # Check if alert already exists for this sample/type
        existing = db.query(Alert).filter(Alert.tag_number == s.sample_id, Alert.type == "Lab Report Overdue").first()
        if not existing:
            alert = Alert(
                tag_number=s.sample_id,
                fpso_name=s.sample_point.fpso_name,
                severity=AlertSeverity.HIGH.value,
                type="Lab Report Overdue",
                description=f"Sample {s.sample_id} was taken on {s.sampling_date} but lab report is missing (>15 days).",
                acknowledged=0,
                created_at=datetime.utcnow()
            )
            db.add(alert)
            alerts_created += 1
            
    # 2. Check Reports Issued but not Approved for > 3 days
    pending_validation = db.query(models.Sample).filter(
        models.Sample.status == SampleStatus.REPORT_ISSUED.value,
        models.Sample.report_issue_date <= today - timedelta(days=3)
    ).all()
    
    for s in pending_validation:
        existing = db.query(Alert).filter(Alert.tag_number == s.sample_id, Alert.type == "Validation Pending").first()
        if not existing:
            alert = Alert(
                tag_number=s.sample_id,
                fpso_name=s.sample_point.fpso_name,
                severity=AlertSeverity.MEDIUM.value,
                type="Validation Pending",
                description=f"Lab report for {s.sample_id} was issued on {s.report_issue_date} but remains unvalidated (>3 days).",
                acknowledged=0,
                created_at=datetime.utcnow()
            )
            db.add(alert)
            alerts_created += 1
            
    db.commit()
    return {"message": "SLA check completed", "alerts_created": alerts_created}

@router.post("/samples/{sample_id}/update-status", response_model=schemas.Sample)
def update_sample_status(sample_id: int, update: schemas.SampleStatusUpdate, db: Session = Depends(database.get_db), current_user = Depends(get_current_user)):
    sample = db.query(models.Sample).filter(models.Sample.id == sample_id).first()
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    
    # Audit History
    history = models.SampleStatusHistory(
        sample_id=sample.id,
        status=update.status,
        comments=update.comments,
        user=update.user
    )
    db.add(history)
    
    # Auto-update dates based on status
    if update.status == models.SampleStatus.SAMPLED:
        sample.sampling_date = update.event_date or date.today()
        # M3.1: Close IFS WO and open new one
        print(f"DEBUG: Closing IFS WO for {sample.sample_id}. Opening next in {sample.sample_point.sampling_interval_days} days.")
        # Forecast next sample
        next_planned = date.today() + timedelta(days=sample.sample_point.sampling_interval_days)
        # In a real app, we'd create a new 'Planned' Sample here or a WO record
        
    elif update.status == models.SampleStatus.DISEMBARK_LOGISTICS:
        sample.disembark_date = update.event_date or date.today()
    elif update.status == models.SampleStatus.DELIVERED_AT_VENDOR:
        sample.delivery_date = update.event_date or date.today()
    elif update.status == models.SampleStatus.REPORT_ISSUED:
        sample.report_issue_date = update.event_date or date.today()
        if update.url:
            sample.lab_report_url = update.url
            
    elif update.status == models.SampleStatus.REPORT_APPROVED_REPROVED:
        sample.validation_status = update.validation_status
        if update.url:
            sample.validation_report_url = update.url
            
    elif update.status == models.SampleStatus.FLOW_COMPUTER_UPDATED:
        sample.fc_update_date = datetime.utcnow()
        if update.url:
            sample.fc_evidence_url = update.url

    sample.status = update.status
    db.commit()
    db.refresh(sample)
    return sample

# --- Validation Logic (M3.1.1.1) ---

@router.get("/samples/{sample_id}/validate")
def perform_sbm_validation(sample_id: int, db: Session = Depends(database.get_db)):
    """Implements SBM algorithm: Avg + Std Dev of previous samples."""
    sample = db.query(models.Sample).filter(models.Sample.id == sample_id).first()
    if not sample or not sample.results:
        raise HTTPException(status_code=400, detail="No results found for validation")
    
    results_summary = []
    
    for res in sample.results:
        # Get historical data for this parameter and sample point
        history = db.query(models.SampleResult.value).join(models.Sample).filter(
            models.Sample.sample_point_id == sample.sample_point_id,
            models.SampleResult.parameter == res.parameter,
            models.Sample.status == models.SampleStatus.FLOW_COMPUTER_UPDATED,
            models.Sample.id != sample.id
        ).order_by(models.Sample.sampling_date.desc()).limit(10).all()
        
        history_values = [h[0] for h in history]
        
        if len(history_values) < 3:
            results_summary.append({
                "parameter": res.parameter,
                "status": "Inconclusive (Need 3+ samples)",
                "avg": sum(history_values)/len(history_values) if history_values else 0,
                "std": 0
            })
            continue
            
        avg = sum(history_values) / len(history_values)
        std = (sum((v - avg)**2 for v in history_values) / len(history_values))**0.5
        
        # Check if current value is within 2 STDs
        is_valid = (avg - 2*std) <= res.value <= (avg + 2*std)
        
        results_summary.append({
            "parameter": res.parameter,
            "status": "Pass" if is_valid else "Fail",
            "current": res.value,
            "avg": avg,
            "std": std,
            "range": [avg - 2*std, avg + 2*std]
        })
        
    return {
        "sample_id": sample.sample_id,
        "overall_status": "Approved" if all(r["status"] != "Fail" for r in results_summary) else "Reproved",
        "parameters": results_summary
    }

# --- Results ---

@router.post("/samples/{sample_id}/results", response_model=schemas.SampleResult)
def add_sample_result(sample_id: int, result: schemas.SampleResultBase, db: Session = Depends(database.get_db), current_user = Depends(get_current_user)):
    db_result = models.SampleResult(sample_id=sample_id, **result.model_dump())
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result
