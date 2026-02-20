from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
import os
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
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

# --- Dashboard Stats (M3 Redesign) ---

# Step-to-card grouping
STEP_GROUPS = {
    "sampling": ["Planned", "Sampled"],
    "disembark": ["Disembark preparation", "Disembark logistics"],
    "logistics": ["Warehouse", "Logistics to vendor", "Delivered at vendor"],
    "report": ["Report issued", "Report under validation", "Report approved/reproved"],
    "fc_update": ["Flow computer updated"],
}

@router.get("/dashboard-stats")
def get_dashboard_stats(fpso_name: Optional[str] = None, db: Session = Depends(database.get_db)):
    """Returns grouped step counts with urgency classification for the 5 dashboard cards."""
    today = date.today()
    tomorrow = today + timedelta(days=1)
    
    query = db.query(models.Sample).outerjoin(models.SamplePoint)
    if fpso_name:
        query = query.filter(models.SamplePoint.fpso_name == fpso_name)
    
    # Exclude completed samples from active dashboard
    active_samples = query.filter(
        models.Sample.status != models.SampleStatus.FLOW_COMPUTER_UPDATED.value
    ).all()
    
    # Also get completed for FC Update card
    completed_samples = query.filter(
        models.Sample.status == models.SampleStatus.FLOW_COMPUTER_UPDATED.value
    ).all()
    
    all_samples = active_samples + completed_samples
    
    result = {}
    for group_key, statuses in STEP_GROUPS.items():
        group_samples = [s for s in all_samples if s.status in statuses]
        
        # Build sub-step breakdown
        steps = []
        for status_name in statuses:
            step_samples = [s for s in group_samples if s.status == status_name]
            overdue = sum(1 for s in step_samples if s.due_date and s.due_date < today)
            due_today = sum(1 for s in step_samples if s.due_date and s.due_date == today)
            due_tomorrow = sum(1 for s in step_samples if s.due_date and s.due_date == tomorrow)
            others = len(step_samples) - overdue - due_today - due_tomorrow
            
            steps.append({
                "name": status_name,
                "total": len(step_samples),
                "overdue": overdue,
                "due_today": due_today,
                "due_tomorrow": due_tomorrow,
                "others": others,
            })
        
        # Aggregate totals for the card
        total_overdue = sum(s["overdue"] for s in steps)
        total_due_today = sum(s["due_today"] for s in steps)
        total_due_tomorrow = sum(s["due_tomorrow"] for s in steps)
        total_others = sum(s["others"] for s in steps)
        
        result[group_key] = {
            "total": sum(s["total"] for s in steps),
            "overdue": total_overdue,
            "due_today": total_due_today,
            "due_tomorrow": total_due_tomorrow,
            "others": total_others,
            "steps": steps,
        }
    
    return result

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
        type=sp.fluid_type,
        due_date=(sample.planned_date or date.today()) + timedelta(days=7)
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
    equipment_id: Optional[int] = None,
    db: Session = Depends(database.get_db)
):
    query = db.query(models.Sample).outerjoin(models.SamplePoint)
    
    if fpso_name:
        query = query.filter(models.SamplePoint.fpso_name == fpso_name)
    if status:
        query = query.filter(models.Sample.status == status)
        
    if equipment_id:
        # M1 -> M3 Integration: Find samples relevant to the equipment's current location (Tag)
        # 1. Get active installation
        active_install = db.query(models.EquipmentTagInstallation).filter(
            models.EquipmentTagInstallation.equipment_id == equipment_id,
            models.EquipmentTagInstallation.is_active == 1
        ).first()
        
        if active_install:
            # 2. Get Tag and its Sample Point
            tag = db.query(models.InstrumentTag).filter(models.InstrumentTag.id == active_install.tag_id).first()
            if tag and tag.sample_point_id:
                query = query.filter(models.Sample.sample_point_id == tag.sample_point_id)
            else:
                # Installed but Tag has no sample point -> No samples
                return []
        else:
            # Not installed -> No associated process samples
            return []
            
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
                fpso_name=s.sample_point.fpso_name if s.sample_point else "Unknown",
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
                fpso_name=s.sample_point.fpso_name if s.sample_point else "Unknown",
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
        sampling_dt = update.event_date or date.today()
        sample.sampling_date = sampling_dt
        # Auto-calculate expected dates: 10-10-5-5 pattern
        sample.disembark_expected_date = sampling_dt + timedelta(days=10)
        sample.lab_expected_date = sampling_dt + timedelta(days=20)  # +10+10
        sample.report_expected_date = sampling_dt + timedelta(days=25)  # +10+10+5
        sample.fc_expected_date = sampling_dt + timedelta(days=30)  # +10+10+5+5
        
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

    # Handle additional tracking fields from update
    if update.osm_id is not None:
        sample.osm_id = update.osm_id
    if update.laudo_number is not None:
        sample.laudo_number = update.laudo_number
    if update.mitigated is not None:
        sample.mitigated = update.mitigated

    sample.status = update.status
    
    # Set due_date = expected date of the NEXT milestone (10-10-5-5 pattern)
    # The due_date answers: "by when does this sample need to reach the next phase?"
    #   Planned              → planned_date           (when sampling should happen)
    #   Sampled..Logistics   → disembark_expected_date (+10d, when disembark must complete)
    #   Warehouse..Logistics → lab_expected_date       (+20d, when lab delivery must happen)
    #   Delivered at vendor  → report_expected_date    (+25d, delivery done, waiting for report)
    #   Report issued..Valid → report_expected_date    (+25d, report phase in progress)
    #   Report approved      → fc_expected_date        (+30d, report done, waiting for FC)
    #   FC Updated           → fc_expected_date        (+30d, final deadline)
    PHASE_DUE = {
        "Planned": "planned_date",
        "Sampled": "disembark_expected_date",
        "Disembark preparation": "disembark_expected_date",
        "Disembark logistics": "disembark_expected_date",
        "Warehouse": "lab_expected_date",
        "Logistics to vendor": "lab_expected_date",
        "Delivered at vendor": "report_expected_date",
        "Report issued": "report_expected_date",
        "Report under validation": "report_expected_date",
        "Report approved/reproved": "fc_expected_date",
        "Flow computer updated": "fc_expected_date",
    }
    
    if update.due_date:
        sample.due_date = update.due_date
    else:
        phase_field = PHASE_DUE.get(update.status)
        if phase_field:
            sample.due_date = getattr(sample, phase_field, None)
        else:
            sample.due_date = None
    
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


# --- Report Validation (PDF Extraction + 2σ Analysis) ---

@router.post("/samples/{sample_id}/validate-report", response_model=schemas.ValidationResponse)
async def validate_report_endpoint(
    sample_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user = Depends(get_current_user),
):
    """Upload a lab report PDF, extract values, store them, and run validation."""
    from ..services.pdf_parser import parse_pdf_bytes
    from ..services.validation_engine import validate_report

    sample = db.query(models.Sample).filter(models.Sample.id == sample_id).first()
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")

    # Read and parse PDF
    pdf_bytes = await file.read()
    try:
        extracted = parse_pdf_bytes(pdf_bytes, filename=file.filename or "")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Run validation against historical data
    validation = validate_report(extracted, sample, db)

    # Store extracted values as SampleResult rows
    # First, remove any previous results from this sample (re-validation)
    db.query(models.SampleResult).filter(models.SampleResult.sample_id == sample_id).delete()

    for check in validation.checks:
        db_result = models.SampleResult(
            sample_id=sample_id,
            parameter=check.parameter,
            value=check.value,
            unit=check.unit,
            validation_status=check.status,
            validation_detail=check.detail,
            history_mean=check.history_mean,
            history_std=check.history_std,
            source_pdf=file.filename,
        )
        db.add(db_result)

    # Update the sample's validation_status based on overall result
    sample.validation_status = validation.overall_status
    # Save the PDF to disk so it can be viewed later
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "reports")
    os.makedirs(uploads_dir, exist_ok=True)
    # Use a unique filename to avoid collisions
    from datetime import datetime as _dt
    safe_name = f"{sample_id}_{int(_dt.now().timestamp())}_{file.filename}"
    pdf_path = os.path.join(uploads_dir, safe_name)
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)
    sample.lab_report_url = f"/uploads/reports/{safe_name}"

    db.commit()

    return schemas.ValidationResponse(
        report_type=validation.report_type,
        overall_status=validation.overall_status,
        boletim=validation.boletim,
        tag_point=validation.tag_point,
        checks=[
            schemas.ValidationCheck(
                parameter=c.parameter,
                value=c.value,
                unit=c.unit,
                status=c.status,
                detail=c.detail,
                history_mean=c.history_mean,
                history_std=c.history_std,
                lower_bound=c.lower_bound,
                upper_bound=c.upper_bound,
                history_values=c.history_values,
                history_dates=c.history_dates,
            )
            for c in validation.checks
        ],
        passed_count=validation.passed_count,
        failed_count=validation.failed_count,
    )


@router.get("/samples/{sample_id}/lab-results", response_model=List[schemas.SampleResult])
def get_lab_results(
    sample_id: int,
    db: Session = Depends(database.get_db),
):
    """Get stored lab results (extracted PDF values) for a sample."""
    results = (
        db.query(models.SampleResult)
        .filter(models.SampleResult.sample_id == sample_id)
        .order_by(models.SampleResult.id)
        .all()
    )
    return results


@router.get("/sample-points/{point_id}/parameter-history", response_model=List[schemas.ParameterHistoryItem])
def get_parameter_history(
    point_id: int,
    parameter: str = Query(..., description="Parameter name: density, rs, fe, o2, density_abs_op, density_abs_std"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(database.get_db),
):
    """Get last N values of a parameter for a sample point (for history chart)."""
    results = (
        db.query(models.SampleResult, models.Sample)
        .join(models.Sample, models.SampleResult.sample_id == models.Sample.id)
        .filter(
            models.Sample.sample_point_id == point_id,
            models.SampleResult.parameter == parameter,
        )
        .order_by(desc(models.SampleResult.created_at))
        .limit(limit)
        .all()
    )

    return [
        schemas.ParameterHistoryItem(
            value=sr.value,
            date=s.sampling_date.isoformat() if s.sampling_date else str(sr.created_at),
            sample_id=s.sample_id or "",
        )
        for sr, s in results
    ]
