from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..database import get_db
from ..models import FailureNotification, ANPStatus, FPSOFailureEmailList, Equipment, EquipmentStatus
from ..schemas.phase3 import (
    FailureNotificationCreate,
    FailureNotificationUpdate,
    FailureNotificationApproval,
    FailureNotification as FailureNotificationSchema,
    FPSOFailureEmailListCreate,
    FPSOFailureEmailList as FPSOFailureEmailListSchema
)
from ..dependencies import get_current_user_fpso
from ..services.failures_service import FailuresService

router = APIRouter(prefix="/api/failures", tags=["failures"])

@router.get("", response_model=List[FailureNotificationSchema])
def get_failures(
    skip: int = 0,
    limit: int = 100,
    anp_status: Optional[str] = None,
    equipment_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user_data = Depends(get_current_user_fpso)
):
    """Get all failure notifications with optional ANP status filter"""
    query = db.query(FailureNotification)
    
    if current_user_data["fpso_name"]:
        query = query.filter(FailureNotification.fpso_name == current_user_data["fpso_name"])
    if anp_status:
        query = query.filter(FailureNotification.anp_status == anp_status)
    if equipment_id:
        query = query.filter(FailureNotification.equipment_id == equipment_id)
    
    return query.offset(skip).limit(limit).all()

@router.get("/{failure_id}", response_model=FailureNotificationSchema)
def get_failure(
    failure_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific failure notification by ID"""
    failure = db.query(FailureNotification).filter(FailureNotification.id == failure_id).first()
    if not failure:
        raise HTTPException(status_code=404, detail="Failure notification not found")
    return failure

@router.post("", response_model=FailureNotificationSchema)
def create_failure(
    failure: FailureNotificationCreate,
    db: Session = Depends(get_db),
    current_user_data = Depends(get_current_user_fpso)
):
    """Create a new failure notification in Draft mode"""
    return FailuresService.create_failure(db, failure, current_user_data["fpso_name"])

@router.post("/{failure_id}/approve", response_model=FailureNotificationSchema)
def approve_failure(
    failure_id: int,
    approval: FailureNotificationApproval,
    db: Session = Depends(get_db),
    current_user_data = Depends(get_current_user_fpso)
):
    """Approve a failure notification - triggers automatic email distribution"""
    return FailuresService.approve_failure(db, failure_id, approval, current_user_data["fpso_name"])

@router.put("/{failure_id}/anp-submit", response_model=FailureNotificationSchema)
def submit_to_anp(
    failure_id: int,
    db: Session = Depends(get_db),
    current_user_data = Depends(get_current_user_fpso)
):
    """Submit failure notification (records data for future XML generation)"""
    return FailuresService.submit_to_anp(db, failure_id, current_user_data["fpso_name"])

# Email List Endpoints
@router.get("/config/emails", response_model=List[FPSOFailureEmailListSchema])
def get_email_lists(fpso_name: Optional[str] = None, db: Session = Depends(get_db), current_user_data = Depends(get_current_user_fpso)):
    query = db.query(FPSOFailureEmailList)
    filter_fpso = current_user_data["fpso_name"] if current_user_data["fpso_name"] else fpso_name
    if filter_fpso:
        query = query.filter(FPSOFailureEmailList.fpso_name == filter_fpso)
    return query.all()

@router.post("/config/emails", response_model=FPSOFailureEmailListSchema)
def add_email_to_list(entry: FPSOFailureEmailListCreate, db: Session = Depends(get_db), current_user_data = Depends(get_current_user_fpso)):
    return FailuresService.add_email_to_list(db, entry, current_user_data["fpso_name"])

@router.get("/anp-pending", response_model=List[FailureNotificationSchema])
def get_anp_pending(db: Session = Depends(get_db), current_user_data = Depends(get_current_user_fpso)):
    """Get all pending ANP submissions"""
    query = db.query(FailureNotification).filter(
        FailureNotification.anp_status == ANPStatus.PENDING.value
    )
    if current_user_data["fpso_name"]:
        query = query.filter(FailureNotification.fpso_name == current_user_data["fpso_name"])
    return query.all()
