from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..database import get_db
from ..models import FailureNotification, ANPStatus, FPSOFailureEmailList
from ..schemas.phase3 import (
    FailureNotificationCreate,
    FailureNotificationUpdate,
    FailureNotificationApproval,
    FailureNotification as FailureNotificationSchema,
    FPSOFailureEmailListCreate,
    FPSOFailureEmailList as FPSOFailureEmailListSchema
)

router = APIRouter(prefix="/api/failures", tags=["failures"])

@router.get("", response_model=List[FailureNotificationSchema])
def get_failures(
    skip: int = 0,
    limit: int = 100,
    anp_status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all failure notifications with optional ANP status filter"""
    query = db.query(FailureNotification)
    
    if anp_status:
        query = query.filter(FailureNotification.anp_status == anp_status)
    
    return query.offset(skip).limit(limit).all()

@router.post("", response_model=FailureNotificationSchema)
def create_failure(
    failure: FailureNotificationCreate,
    db: Session = Depends(get_db)
):
    """Create a new failure notification in Draft mode"""
    db_failure = FailureNotification(**failure.model_dump(), status="Draft")
    db.add(db_failure)
    db.commit()
    db.refresh(db_failure)
    return db_failure

@router.post("/{failure_id}/approve", response_model=FailureNotificationSchema)
def approve_failure(
    failure_id: int,
    approval: FailureNotificationApproval,
    db: Session = Depends(get_db)
):
    """Approve a failure notification - triggers automatic email distribution"""
    db_failure = db.query(FailureNotification).filter(FailureNotification.id == failure_id).first()
    if not db_failure:
        raise HTTPException(status_code=404, detail="Failure notification not found")
    
    db_failure.status = "Approved"
    db_failure.approved_by = approval.approved_by
    db_failure.approved_at = datetime.utcnow()
    
    # Trigger Email Simulation
    recipients = db.query(FPSOFailureEmailList).filter(
        FPSOFailureEmailList.fpso_name == db_failure.fpso_name,
        FPSOFailureEmailList.is_active == 1
    ).all()
    
    # Mock email sending logic
    print(f"DEBUG: Triggering email distribution for approved report {db_failure.id}")
    for rec in recipients:
        print(f"DEBUG: Mock sending PDF/Excel report to {rec.email}")

    db.commit()
    db.refresh(db_failure)
    return db_failure

@router.put("/{failure_id}/anp-submit", response_model=FailureNotificationSchema)
def submit_to_anp(
    failure_id: int,
    db: Session = Depends(get_db)
):
    """Submit failure notification (records data for future XML generation)"""
    failure = db.query(FailureNotification).filter(FailureNotification.id == failure_id).first()
    if not failure:
        raise HTTPException(status_code=404, detail="Failure notification not found")
    
    if failure.status != "Approved":
        raise HTTPException(status_code=400, detail="Only approved notifications can be submitted")

    failure.anp_submitted_date = datetime.utcnow()
    failure.anp_status = ANPStatus.SUBMITTED.value
    failure.status = "Submitted"
    db.commit()
    db.refresh(failure)
    return failure

# Email List Endpoints
@router.get("/config/emails", response_model=List[FPSOFailureEmailListSchema])
def get_email_lists(fpso_name: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(FPSOFailureEmailList)
    if fpso_name:
        query = query.filter(FPSOFailureEmailList.fpso_name == fpso_name)
    return query.all()

@router.post("/config/emails", response_model=FPSOFailureEmailListSchema)
def add_email_to_list(entry: FPSOFailureEmailListCreate, db: Session = Depends(get_db)):
    db_entry = FPSOFailureEmailList(**entry.model_dump())
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry

@router.get("/anp-pending", response_model=List[FailureNotificationSchema])
def get_anp_pending(db: Session = Depends(get_db)):
    """Get all pending ANP submissions"""
    return db.query(FailureNotification).filter(
        FailureNotification.anp_status == ANPStatus.PENDING.value
    ).all()
