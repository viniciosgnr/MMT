from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException
from ..models import FailureNotification, ANPStatus, FPSOFailureEmailList, Equipment, EquipmentStatus
from ..schemas.phase3 import FailureNotificationCreate, FailureNotificationApproval, FPSOFailureEmailListCreate

class FailuresService:
    @staticmethod
    def create_failure(db: Session, failure: FailureNotificationCreate, user_fpso: str = None):
        equipment = db.query(Equipment).filter(Equipment.id == failure.equipment_id).first()
        if not equipment:
            raise HTTPException(status_code=404, detail="Equipment not found")
        if user_fpso and equipment.fpso_name != user_fpso:
            raise HTTPException(status_code=403, detail="Forbidden: You can only register failures for your current FPSO.")
        
        if equipment.status == EquipmentStatus.DECOMMISSIONED.value:
            raise HTTPException(status_code=400, detail="Cannot register failure for Decommissioned equipment")
        
        db_failure = FailureNotification(**failure.model_dump(), status="Draft")
        db.add(db_failure)
        db.commit()
        db.refresh(db_failure)
        return db_failure

    @staticmethod
    def approve_failure(db: Session, failure_id: int, approval: FailureNotificationApproval, user_fpso: str = None):
        db_failure = db.query(FailureNotification).filter(FailureNotification.id == failure_id).first()
        if not db_failure:
            raise HTTPException(status_code=404, detail="Failure notification not found")
        if user_fpso and db_failure.fpso_name != user_fpso:
            raise HTTPException(status_code=403, detail="Forbidden: You can only approve failures for your current FPSO.")
        
        db_failure.status = "Approved"
        db_failure.approved_by = approval.approved_by
        db_failure.approved_at = datetime.utcnow()
        
        recipients = db.query(FPSOFailureEmailList).filter(
            FPSOFailureEmailList.fpso_name == db_failure.fpso_name,
            FPSOFailureEmailList.is_active == 1
        ).all()
        
        print(f"DEBUG: Triggering email distribution for approved report {db_failure.id}")
        for rec in recipients:
            print(f"DEBUG: Mock sending PDF/Excel report to {rec.email}")

        db.commit()
        db.refresh(db_failure)
        return db_failure

    @staticmethod
    def submit_to_anp(db: Session, failure_id: int, user_fpso: str = None):
        failure = db.query(FailureNotification).filter(FailureNotification.id == failure_id).first()
        if not failure:
            raise HTTPException(status_code=404, detail="Failure notification not found")
        if user_fpso and failure.fpso_name != user_fpso:
            raise HTTPException(status_code=403, detail="Forbidden: You can only submit failures for your current FPSO.")
        
        if failure.status != "Approved":
            raise HTTPException(status_code=400, detail="Only approved notifications can be submitted")

        failure.anp_submitted_date = datetime.utcnow()
        failure.anp_status = ANPStatus.SUBMITTED.value
        failure.status = "Submitted"
        db.commit()
        db.refresh(failure)
        return failure
    
    @staticmethod
    def add_email_to_list(db: Session, entry: FPSOFailureEmailListCreate, user_fpso: str = None):
        if user_fpso and entry.fpso_name != user_fpso:
            raise HTTPException(status_code=403, detail="Forbidden: You can only configure email lists for your current FPSO.")
        db_entry = FPSOFailureEmailList(**entry.model_dump())
        db.add(db_entry)
        db.commit()
        db.refresh(db_entry)
        return db_entry
