from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from ..database import get_db
from ..models import PlannedActivity
from ..dependencies import get_current_user
from ..schemas.phase3 import (
    PlannedActivityCreate,
    PlannedActivityUpdate,
    PlannedActivityMitigate,
    PlannedActivity as PlannedActivitySchema
)

router = APIRouter(prefix="/api/planning", tags=["planning"])

@router.get("/activities", response_model=List[PlannedActivitySchema])
def get_activities(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status: Optional[str] = None,
    fpso_name: Optional[str] = None,
    activity_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get planned activities with comprehensive filters"""
    query = db.query(PlannedActivity)
    
    if start_date:
        query = query.filter(PlannedActivity.scheduled_date >= start_date)
    if end_date:
        query = query.filter(PlannedActivity.scheduled_date <= end_date)
    if status:
        query = query.filter(PlannedActivity.status == status)
    if fpso_name:
        query = query.filter(PlannedActivity.fpso_name == fpso_name)
    if activity_type:
        query = query.filter(PlannedActivity.type == activity_type)
    
    return query.order_by(PlannedActivity.scheduled_date).all()

@router.post("/activities", response_model=PlannedActivitySchema)
def create_activity(
    activity: PlannedActivityCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new planned activity"""
    db_activity = PlannedActivity(**activity.model_dump())
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    return db_activity

@router.put("/activities/{activity_id}", response_model=PlannedActivitySchema)
def update_activity(
    activity_id: int,
    activity: PlannedActivityUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update a planned activity"""
    db_activity = db.query(PlannedActivity).filter(PlannedActivity.id == activity_id).first()
    if not db_activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    for key, value in activity.model_dump(exclude_unset=True).items():
        setattr(db_activity, key, value)
    
    db.commit()
    db.refresh(db_activity)
    return db_activity

@router.post("/activities/{activity_id}/mitigate", response_model=PlannedActivitySchema)
def mitigate_activity(
    activity_id: int,
    mitigation: PlannedActivityMitigate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Mark an activity as mitigated with a new due date"""
    db_activity = db.query(PlannedActivity).filter(PlannedActivity.id == activity_id).first()
    if not db_activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    db_activity.status = "Mitigated"
    db_activity.mitigation_reason = mitigation.reason
    db_activity.mitigation_attachment_url = mitigation.attachment_url
    db_activity.new_due_date = mitigation.new_due_date
    db_activity.mitigated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_activity)
    return db_activity

@router.delete("/activities/{activity_id}")
def cancel_activity(activity_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Cancel a planned activity"""
    activity = db.query(PlannedActivity).filter(PlannedActivity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    activity.status = "Cancelled"
    db.commit()
    return {"message": "Activity cancelled successfully"}
