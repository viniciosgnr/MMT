from datetime import datetime, date
from sqlalchemy.orm import Session
from fastapi import HTTPException
from ..models import PlannedActivity
from ..schemas.phase3 import PlannedActivityCreate, PlannedActivityUpdate, PlannedActivityMitigate

class PlanningService:
    @staticmethod
    def create_activity(db: Session, activity: PlannedActivityCreate, user_fpso: str = None):
        if user_fpso and activity.fpso_name != user_fpso:
            raise HTTPException(status_code=403, detail="Forbidden: You can only create activities for your current FPSO.")
        db_activity = PlannedActivity(**activity.model_dump())
        db.add(db_activity)
        db.commit()
        db.refresh(db_activity)
        return db_activity

    @staticmethod
    def update_activity(db: Session, activity_id: int, activity: PlannedActivityUpdate, user_fpso: str = None):
        db_activity = db.query(PlannedActivity).filter(PlannedActivity.id == activity_id).first()
        if not db_activity:
            raise HTTPException(status_code=404, detail="Activity not found")
        if user_fpso and db_activity.fpso_name != user_fpso:
            raise HTTPException(status_code=403, detail="Forbidden: You can only update activities for your current FPSO.")
        
        for key, value in activity.model_dump(exclude_unset=True).items():
            setattr(db_activity, key, value)
        
        db.commit()
        db.refresh(db_activity)
        return db_activity

    @staticmethod
    def mitigate_activity(db: Session, activity_id: int, mitigation: PlannedActivityMitigate, user_fpso: str = None):
        db_activity = db.query(PlannedActivity).filter(PlannedActivity.id == activity_id).first()
        if not db_activity:
            raise HTTPException(status_code=404, detail="Activity not found")
        if user_fpso and db_activity.fpso_name != user_fpso:
            raise HTTPException(status_code=403, detail="Forbidden: You can only mitigate activities for your current FPSO.")
        
        db_activity.status = "Mitigated"
        db_activity.mitigation_reason = mitigation.reason
        db_activity.mitigation_attachment_url = mitigation.attachment_url
        db_activity.new_due_date = mitigation.new_due_date
        db_activity.mitigated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_activity)
        return db_activity

    @staticmethod
    def cancel_activity(db: Session, activity_id: int, user_fpso: str = None):
        db_activity = db.query(PlannedActivity).filter(PlannedActivity.id == activity_id).first()
        if not db_activity:
            raise HTTPException(status_code=404, detail="Activity not found")
        if user_fpso and db_activity.fpso_name != user_fpso:
            raise HTTPException(status_code=403, detail="Forbidden: You can only cancel activities for your current FPSO.")
            
        db_activity.status = "Cancelled"
        db.commit()
        return {"message": "Activity cancelled successfully"}
