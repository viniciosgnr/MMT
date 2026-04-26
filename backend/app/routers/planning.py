from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from ..database import get_db
from ..models import PlannedActivity
from ..dependencies import get_current_user_fpso
from ..services.planning_service import PlanningService
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
    db: Session = Depends(get_db),
    current_user_data = Depends(get_current_user_fpso)
):
    """Get planned activities with comprehensive filters"""
    query = db.query(PlannedActivity)
    
    if start_date:
        query = query.filter(PlannedActivity.scheduled_date >= start_date)
    if end_date:
        query = query.filter(PlannedActivity.scheduled_date <= end_date)
    if status:
        query = query.filter(PlannedActivity.status == status)
        
    filter_fpso = current_user_data["fpso_name"] if current_user_data["fpso_name"] else fpso_name
    if filter_fpso:
        query = query.filter(PlannedActivity.fpso_name == filter_fpso)
        
    if activity_type:
        query = query.filter(PlannedActivity.type == activity_type)
    
    return query.order_by(PlannedActivity.scheduled_date).all()

@router.post("/activities", response_model=PlannedActivitySchema)
def create_activity(
    activity: PlannedActivityCreate,
    db: Session = Depends(get_db),
    current_user_data = Depends(get_current_user_fpso)
):
    """Create a new planned activity"""
    return PlanningService.create_activity(db, activity, current_user_data["fpso_name"])

@router.put("/activities/{activity_id}", response_model=PlannedActivitySchema)
def update_activity(
    activity_id: int,
    activity: PlannedActivityUpdate,
    db: Session = Depends(get_db),
    current_user_data = Depends(get_current_user_fpso)
):
    """Update a planned activity"""
    return PlanningService.update_activity(db, activity_id, activity, current_user_data["fpso_name"])

@router.post("/activities/{activity_id}/mitigate", response_model=PlannedActivitySchema)
def mitigate_activity(
    activity_id: int,
    mitigation: PlannedActivityMitigate,
    db: Session = Depends(get_db),
    current_user_data = Depends(get_current_user_fpso)
):
    """Mark an activity as mitigated with a new due date"""
    return PlanningService.mitigate_activity(db, activity_id, mitigation, current_user_data["fpso_name"])

@router.delete("/activities/{activity_id}")
def cancel_activity(activity_id: int, db: Session = Depends(get_db), current_user_data = Depends(get_current_user_fpso)):
    """Cancel a planned activity"""
    return PlanningService.cancel_activity(db, activity_id, current_user_data["fpso_name"])
