from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
import os
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, or_, and_, exists
from typing import List, Optional
from datetime import datetime, date, timedelta
from .. import models, database
from ..schemas import chemical as schemas
from ..dependencies import get_current_user
from ..services.sla_matrix import get_sla_config
from ..services.pdf_parser import parse_pdf_bytes
from ..services.validation_engine import validate_report

router = APIRouter(
    prefix="/api/chemical",
    tags=["chemical"],
)

# --- Sample Points & Meters (M3 Configuration) ---

from pydantic import BaseModel
class MeterWithSamplePoints(BaseModel):
    id: int
    tag_number: str
    description: Optional[str] = None
    classification: Optional[str] = None
    sample_points: List[schemas.SamplePoint] = []
    
    class Config:
        from_attributes = True

@router.get("/meters", response_model=List[MeterWithSamplePoints])
def list_meters(fpso_name: Optional[str] = None, db: Session = Depends(database.get_db)):
    query = db.query(models.InstrumentTag).options(joinedload(models.InstrumentTag.sample_points))
    # Note: InstrumentTag fpso_name filtering could be complex if it depends on install,
    # but for now we just return all tags that act as metering points for M3
    return query.all()

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
    sp = db.query(models.SamplePoint).filter(models.SamplePoint.id == sp_id).first()
    if not sp:
        raise HTTPException(status_code=404, detail="Sample point not found")
    meters = db.query(models.InstrumentTag).filter(models.InstrumentTag.id.in_(tag_ids)).all()
    sp.meters.extend([m for m in meters if m not in sp.meters])
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
    "sampling": ["Plan", "Sample"],
    "disembark": ["Disembark preparation", "Disembark logistics"],
    "logistics": ["Warehouse", "Logistics to vendor", "Deliver at vendor"],
    "report": ["Report issue", "Report under validation", "Report approve/reprove"],
    "fc_update": ["Flow computer update"],
}

@router.get("/dashboard-stats")
def get_dashboard_stats(fpso_name: Optional[str] = None, db: Session = Depends(database.get_db)):
    """Returns grouped step counts with urgency classification for the 5 dashboard cards.
    Card urgency (overdue/today/tomorrow) is driven by a specific trigger step's expected
    date field, checked against ALL samples in the card group — not just samples at that step."""
    today = date.today()
    tomorrow = today + timedelta(days=1)
    
    # Which expected date field drives each card's urgency color.
    # All samples in the group are checked against this field.
    CARD_TRIGGER_FIELD = {
        "sampling": "planned_date",              # Sample trigger
        "disembark": "disembark_expected_date",   # Disembark logistics trigger
        "logistics": "lab_expected_date",          # Deliver at vendor trigger
        "report": "report_expected_date",          # Report issue trigger
        "fc_update": "fc_expected_date",           # Flow computer update trigger
    }
    
    query = db.query(models.Sample).outerjoin(models.SamplePoint)
    if fpso_name:
        query = query.filter(models.SamplePoint.fpso_name == fpso_name)
    
    # Exclude completed samples from active dashboard
    active_samples = query.filter(
        models.Sample.status != models.SampleStatus.FLOW_COMPUTER_UPDATE.value
    ).all()
    
    # Also get completed for FC Update card
    completed_samples = query.filter(
        models.Sample.status == models.SampleStatus.FLOW_COMPUTER_UPDATE.value
    ).all()
    
    all_samples = active_samples + completed_samples
    
    result = {}
    for group_key, statuses in STEP_GROUPS.items():
        group_samples = [s for s in all_samples if s.status in statuses]
        trigger_field = CARD_TRIGGER_FIELD.get(group_key)
        
        # Build sub-step breakdown (uses due_date for per-step info)
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
        
        # Card-level urgency = ALL group samples checked against the trigger field
        card_overdue = 0
        card_due_today = 0
        card_due_tomorrow = 0
        if trigger_field:
            for s in group_samples:
                trigger_date = getattr(s, trigger_field, None)
                if trigger_date:
                    if trigger_date < today:
                        card_overdue += 1
                    elif trigger_date == today:
                        card_due_today += 1
                    elif trigger_date == tomorrow:
                        card_due_tomorrow += 1
        card_others = len(group_samples) - card_overdue - card_due_today - card_due_tomorrow
        
        result[group_key] = {
            "total": len(group_samples),
            "overdue": card_overdue,
            "due_today": card_due_today,
            "due_tomorrow": card_due_tomorrow,
            "others": card_others,
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
        
    category = "Operacional" if sample.type in ["Operacional", "Óleo - Densidade", "Óleo - Enxofre"] else "Coleta"
    
    db_sample = models.Sample(
        **sample.model_dump(exclude={"category"}),
        status=models.SampleStatus.SAMPLE,
        category=category,
        due_date=sample.planned_date
    )
    db.add(db_sample)
    db.commit()
    db.refresh(db_sample)
    
    # Log "Plan" step as completed (analysis starts at step 2 "Sample")
    plan_history = models.SampleStatusHistory(
        sample_id=db_sample.id,
        status=models.SampleStatus.PLAN,
        comments="Analysis planned — awaiting sample collection."
    )
    db.add(plan_history)
    
    sample_history = models.SampleStatusHistory(
        sample_id=db_sample.id,
        status=models.SampleStatus.SAMPLE,
        comments="Sample step started — awaiting collection."
    )
    db.add(sample_history)
    db.commit()
    
    return db_sample

@router.get("/samples", response_model=List[schemas.Sample])
def list_samples(
    fpso_name: Optional[str] = None,
    status: Optional[str] = None,
    sample_type: Optional[str] = None,
    equipment_id: Optional[int] = None,
    db: Session = Depends(database.get_db)
):
    query = db.query(models.Sample).outerjoin(models.SamplePoint).options(
        joinedload(models.Sample.sample_point),
        joinedload(models.Sample.meter),
        joinedload(models.Sample.well)
    )
    
    if fpso_name:
        query = query.filter(models.SamplePoint.fpso_name == fpso_name)
    if status:
        query = query.filter(models.Sample.status == status)
    if sample_type:
        query = query.filter(models.Sample.type == sample_type)
        
    if equipment_id:
        # --- Skill (backend-dev-guidelines): Unified Historical Traceability ---
        # M1 -> M3 Integration: Find samples linked to the equipment via its 
        # installation history. Handles both direct (meter_id) and indirect (SP) links.
        query = query.join(
            models.EquipmentTagInstallation,
            and_(
                models.EquipmentTagInstallation.equipment_id == equipment_id,
                models.Sample.created_at >= models.EquipmentTagInstallation.installation_date,
                or_(
                    models.EquipmentTagInstallation.removal_date.is_(None),
                    models.Sample.created_at <= models.EquipmentTagInstallation.removal_date
                )
            )
        )
        query = query.filter(
            or_(
                # Path A: Direct meter_id match
                models.Sample.meter_id == models.EquipmentTagInstallation.tag_id,
                # Path B: Indirect via SamplePoint (for samples missing meter_id but on correct SP)
                and_(
                    models.Sample.meter_id.is_(None),
                    exists().where(
                        and_(
                            models.meter_sample_link.c.sample_point_id == models.Sample.sample_point_id,
                            models.meter_sample_link.c.meter_id == models.EquipmentTagInstallation.tag_id
                        )
                    )
                )
            )
        )
            
    return query.all()

@router.get("/samples/{sample_id}", response_model=schemas.Sample)
def get_sample(sample_id: int, db: Session = Depends(database.get_db)):
    sample = db.query(models.Sample).filter(models.Sample.id == sample_id).first()
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    return sample

@router.post("/check-slas")
def check_sampling_slas(db: Session = Depends(database.get_db)):
    """Scans active samples and creates alerts for SLA violations dynamically using the 22-combination SLA matrix."""
    from datetime import date, timedelta
    from ..models import Alert, AlertSeverity, SampleStatus
    from ..services.sla_matrix import get_sla_config
    
    today = date.today()
    alerts_created = 0
    
    # 1. Fetch samples in statuses that have SLAs
    active_samples = db.query(models.Sample).filter(
        models.Sample.status.in_([SampleStatus.SAMPLE.value, SampleStatus.REPORT_ISSUE.value])
    ).all()
    
    for s in active_samples:
        classification = "Fiscal"
        if s.meter and hasattr(s.meter, 'classification') and s.meter.classification:
            classification = s.meter.classification
            
        cfg = get_sla_config(db, classification, s.type, s.local)
        if not cfg:
            continue
            
        if s.status == SampleStatus.SAMPLE.value and s.sampling_date:
            report_days = cfg.get("report_days")
            if report_days is not None:
                s_date = s.sampling_date.date() if hasattr(s.sampling_date, 'date') else s.sampling_date
                if s_date <= today - timedelta(days=report_days):
                    existing = db.query(Alert).filter(Alert.tag_number == s.sample_id, Alert.type == "Lab Report Overdue").first()
                    if not existing:
                        alert = Alert(
                            tag_number=s.sample_id,
                            fpso_name=s.sample_point.fpso_name if s.sample_point else "Unknown",
                            severity=AlertSeverity.HIGH.value,
                            type="Lab Report Overdue",
                            title="Lab Report Overdue",
                            message=f"Sample {s.sample_id} was taken on {s_date} but lab report is missing (>{report_days} days).",
                            acknowledged=0,
                            created_at=datetime.utcnow()
                        )
                        db.add(alert)
                        alerts_created += 1

        elif s.status == SampleStatus.REPORT_ISSUE.value and s.report_issue_date:
            fc_days = cfg.get("fc_days")
            if fc_days is not None:
                r_date = s.report_issue_date.date() if hasattr(s.report_issue_date, 'date') else s.report_issue_date
                if r_date <= today - timedelta(days=fc_days):
                    existing = db.query(Alert).filter(Alert.tag_number == s.sample_id, Alert.type == "Validation Pending").first()
                    if not existing:
                        alert = Alert(
                            tag_number=s.sample_id,
                            fpso_name=s.sample_point.fpso_name if s.sample_point else "Unknown",
                            severity=AlertSeverity.MEDIUM.value,
                            type="Validation Pending",
                            title="Validation Pending",
                            message=f"Lab report for {s.sample_id} was issued on {r_date} but remains unvalidated (>{fc_days} days).",
                            acknowledged=0,
                            created_at=datetime.utcnow()
                        )
                        db.add(alert)
                        alerts_created += 1
                        
    db.commit()
    return {"message": "SLA check completed", "alerts_created": alerts_created}


@router.patch("/samples/{sample_id}/due-date", response_model=schemas.Sample)
def override_due_date(
    sample_id: int,
    payload: dict,
    db: Session = Depends(database.get_db),
    current_user = Depends(get_current_user),
):
    """Manually override a sample's due_date ('Forçar Data Prevista')."""
    sample = db.query(models.Sample).filter(models.Sample.id == sample_id).first()
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    new_date = payload.get("due_date")
    if new_date:
        sample.due_date = date.fromisoformat(new_date)
    else:
        sample.due_date = None
    db.commit()
    db.refresh(sample)
    return sample

@router.post("/samples/{sample_id}/update-status", response_model=schemas.Sample)
def update_sample_status(sample_id: int, update: schemas.SampleStatusUpdate, db: Session = Depends(database.get_db), current_user = Depends(get_current_user)):
    # Use joinedload to eagerly load the meter so we can access meter.classification
    sample = db.query(models.Sample).options(joinedload(models.Sample.meter)).filter(models.Sample.id == sample_id).first()
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
    
    # Helper for auto-scheduling
    def schedule_next_periodic_sample(s: models.Sample, cfg: dict):
        base_date = s.sampling_date or date.today()
        p_date = base_date + timedelta(days=cfg["interval_days"])
        prefix = s.sample_id.split('-')[0] if '-' in s.sample_id else 'CDI'
        new_id = f"{prefix}-{p_date.strftime('%Y%m')}-PER-{s.id}-{int(datetime.utcnow().timestamp())}"
        new_sample = models.Sample(
            sample_id=new_id,
            type=s.type,
            category=s.category,
            status=models.SampleStatus.SAMPLE.value,
            responsible=s.responsible,
            sample_point_id=s.sample_point_id,
            meter_id=s.meter_id,
            well_id=s.well_id,
            validation_party=s.validation_party,
            is_active=1,
            local=s.local,
            planned_date=p_date,
            due_date=p_date,
            created_at=datetime.utcnow()
        )
        db.add(new_sample)
        # Log Plan as completed for auto-scheduled sample
        db.flush()
        plan_h = models.SampleStatusHistory(
            sample_id=new_sample.id,
            status=models.SampleStatus.PLAN.value,
            comments="Auto-scheduled periodic analysis — Plan completed."
        )
        sample_h = models.SampleStatusHistory(
            sample_id=new_sample.id,
            status=models.SampleStatus.SAMPLE.value,
            comments="Awaiting next sample collection."
        )
        db.add(plan_h)
        db.add(sample_h)

    # Apply local override EARLY if provided
    if update.local:
        sample.local = update.local

    meter_class = sample.meter.classification if sample.meter else "Fiscal"
    sla_config = get_sla_config(db, meter_class, sample.type, sample.local)
    
    def schedule_emergency_re_sampling(s: models.Sample, db: Session, cfg: Optional[dict]):
        # Try to get the Reproved-specific SLA rule for accurate reschedule days
        reproved_cfg = get_sla_config(db, meter_class, s.type, s.local, status_variation="Reproved")
        reschedule_days = 3  # default
        if reproved_cfg and reproved_cfg.get("reproval_reschedule_days"):
            reschedule_days = reproved_cfg["reproval_reschedule_days"]
        elif cfg and cfg.get("reproval_reschedule_days"):
            reschedule_days = cfg["reproval_reschedule_days"]
        
        # Schedule emergency sample N business days after emission/reproval
        base_date = s.report_issue_date or date.today()
        
        # Calculate N business days
        days_to_add = reschedule_days
        emergency_date = base_date
        while days_to_add > 0:
            emergency_date += timedelta(days=1)
            if emergency_date.weekday() < 5:  # 0-4 are Monday-Friday
                days_to_add -= 1

        # Per spec: "a data de coleta prevista mantém se menor"
        # Use the earlier of: emergency date OR next periodic planned date
        next_periodic_date = None
        if s.sampling_date and cfg and cfg.get("interval_days"):
            next_periodic_date = s.sampling_date + timedelta(days=cfg["interval_days"])
        
        final_date = emergency_date
        if next_periodic_date and next_periodic_date < emergency_date:
            final_date = next_periodic_date

        prefix = s.sample_id.split('-')[0] if '-' in s.sample_id else 'CDI'
        new_id = f"{prefix}-{datetime.now().strftime('%Y%m')}-EMG-{s.id}-{int(datetime.utcnow().timestamp())}"
        # Start at SAMPLE (step 2): Plan was completed automatically by the scheduler
        new_sample = models.Sample(
            sample_id=new_id,
            type=s.type,
            category=s.category,
            status=models.SampleStatus.SAMPLE.value,
            responsible=s.responsible,
            sample_point_id=s.sample_point_id,
            meter_id=s.meter_id,
            well_id=s.well_id,
            validation_party=s.validation_party,
            is_active=1,
            local=s.local,
            planned_date=final_date,
            due_date=final_date,
            created_at=datetime.utcnow()
        )
        db.add(new_sample)
        db.flush()
        # History: Plan completed automatically, now at Sample
        db.add(models.SampleStatusHistory(
            sample_id=new_sample.id,
            status=models.SampleStatus.PLAN.value,
            comments="Emergency re-sampling scheduled after report reproval — Plan completed by scheduler."
        ))
        db.add(models.SampleStatusHistory(
            sample_id=new_sample.id,
            status=models.SampleStatus.SAMPLE.value,
            comments=f"Awaiting emergency collection — scheduled {reschedule_days} business days after report emission."
        ))
        return new_sample

    # ---------------------------------------------------------------
    # AUTO-SCHEDULE: Trigger when sample LEAVES status "Sample" (step 2)
    # This fires for both Onshore (→ Disembark prep) and Offshore (→ Report issue)
    # ---------------------------------------------------------------
    if sample.status == models.SampleStatus.SAMPLE.value and update.status != models.SampleStatus.SAMPLE:
        sampling_dt = update.event_date or date.today()
        sample.sampling_date = sampling_dt

        # Guard: only schedule if no periodic child already exists for this sample
        existing_periodic = db.query(models.Sample).filter(
            models.Sample.sample_id.like(f"%-PER-{sample.id}-%")
        ).first()
        if not existing_periodic and sla_config and sla_config.get("interval_days"):
            schedule_next_periodic_sample(sample, sla_config)

        # Set/Clear expected dates based on SLA config
        if sla_config:
            # We use "is not None" because 0 days is a valid delay, but None means "no step"
            sample.disembark_expected_date = (sampling_dt + timedelta(days=sla_config["disembark_days"])) if sla_config.get("disembark_days") is not None else None
            sample.lab_expected_date = (sampling_dt + timedelta(days=sla_config["lab_days"])) if sla_config.get("lab_days") is not None else None
            sample.report_expected_date = (sampling_dt + timedelta(days=sla_config["report_days"])) if sla_config.get("report_days") is not None else None

    # Auto-update dates based on status
    if update.status == models.SampleStatus.DISEMBARK_PREP:
        if update.local:
            # If location changes during disembark prep, we MUST re-evaluate SLA and dates
            sample.local = update.local
            sla_config = get_sla_config(db, meter_class, sample.type, sample.local)
            if sla_config and sample.sampling_date:
                sample.disembark_expected_date = (sample.sampling_date + timedelta(days=sla_config["disembark_days"])) if sla_config.get("disembark_days") is not None else None
                sample.lab_expected_date = (sample.sampling_date + timedelta(days=sla_config["lab_days"])) if sla_config.get("lab_days") is not None else None
                sample.report_expected_date = (sample.sampling_date + timedelta(days=sla_config["report_days"])) if sla_config.get("report_days") is not None else None
                
    elif update.status == models.SampleStatus.DISEMBARK_LOGISTICS:
        sample.disembark_date = update.event_date or date.today()
    elif update.status == models.SampleStatus.DELIVER_AT_VENDOR:
        sample.delivery_date = update.event_date or date.today()
    elif update.status == models.SampleStatus.REPORT_ISSUE:
        sample.report_issue_date = update.event_date or date.today()
        if update.url:
            sample.lab_report_url = update.url
            
        # Calculate FC expected date based on report emission
        if sla_config and sla_config["fc_days"]:
            if sla_config["fc_is_business_days"]:
                days_to_add = sla_config["fc_days"]
                curr_date = sample.report_issue_date
                while days_to_add > 0:
                    curr_date += timedelta(days=1)
                    if curr_date.weekday() < 5:
                        days_to_add -= 1
                sample.fc_expected_date = curr_date
            else:
                sample.fc_expected_date = sample.report_issue_date + timedelta(days=sla_config["fc_days"])
    
    elif update.status == models.SampleStatus.REPORT_APPROVE_REPROVE:
        sample.validation_status = update.validation_status
        if update.url:
            sample.validation_report_url = update.url
        if update.validation_status == "Reprovado":
            schedule_emergency_re_sampling(sample, db, sla_config)
    
    elif update.status == models.SampleStatus.FLOW_COMPUTER_UPDATE:
        sample.fc_update_date = update.event_date or date.today()
        if update.url:
            sample.fc_evidence_url = update.url
        if update.validation_status:
            sample.validation_status = update.validation_status
        if update.validation_status == "Reprovado":
            schedule_emergency_re_sampling(sample, db, sla_config)
    
    # Handle additional tracking fields from update
    if update.osm_id is not None:
        sample.osm_id = update.osm_id
    if update.laudo_number is not None:
        sample.laudo_number = update.laudo_number
    if update.mitigated is not None:
        sample.mitigated = 1 if update.mitigated else 0

    sample.status = update.status
    
    # Calculate NEXT due_date dynamically based on skipped steps
    PHASE_DUE = {
        "Plan": "planned_date",
        "Sample": "planned_date",
        "Disembark preparation": "disembark_expected_date",
        "Disembark logistics": "disembark_expected_date",
        "Warehouse": "lab_expected_date",
        "Logistics to vendor": "lab_expected_date",
        "Deliver at vendor": "report_expected_date",
        "Report issue": "report_expected_date",
        "Report under validation": "report_expected_date",
        "Report approve/reprove": "fc_expected_date",
        "Flow computer update": "fc_expected_date",
    }
    
    # Always compute due_date from SLA matrix — no manual override
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
            models.Sample.status == models.SampleStatus.FLOW_COMPUTER_UPDATE,
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
    parameter: str = Query(..., description="Parameter name: density, rs, fe, o2, relative_density_real"),
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
