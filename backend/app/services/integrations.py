from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from .. import models, schemas
from ..models import (
    CalibrationTask, 
    CalibrationResult, 
    FailureNotification, 
    Equipment, 
    SamplePoint,
    Sample,
    SampleStatus
)

class IntegrationService:
    """
    Centralizes logic that crosses module boundaries to prevents circular dependencies
    and ensure business rules are consistent.
    """

    @staticmethod
    def trigger_failure_from_calibration(db: Session, task_id: int, reason: str, user: str) -> int:
        """
        M2 -> M9: When a calibration fails, auto-create a draft Failure Notification.
        Returns the ID of the created notification.
        """
        task = db.query(CalibrationTask).filter(CalibrationTask.id == task_id).first()
        if not task:
            return None

        # Check if one already exists for this failure to avoid duplicates? 
        # For now, we assume every failure needs a new record or manual check.

        equipment = task.equipment
        
        # Create detailed description
        description = f"Generated automatically from Calibration Task #{task.id}.\n"
        description += f"Equipment: {equipment.serial_number} / {task.tag}\n"
        description += f"Reason: {reason}\n"

        notification = FailureNotification(
            equipment_id=equipment.id,
            tag=task.tag,
            fpso_name=task.campaign.fpso_name if task.campaign else "Unknown",
            failure_date=datetime.utcnow(),
            description=description,
            impact="Medium", # Default
            responsible=user,
            cause="Calibration Failed",
            corrective_action="Investigate calibration failure and re-calibrate if necessary.",
            status="Draft"
        )
        
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        return notification.id

    @staticmethod
    def update_equipment_status_from_sync(db: Session, tag_number: str, value: float, timestamp: datetime):
        """
        M5 -> M1: Update equipment 'Last Seen' or Status based on live data.
        """
        # Find tag
        tag = db.query(models.InstrumentTag).filter(models.InstrumentTag.tag_number == tag_number).first()
        if not tag:
            return

        # Find installed equipment
        # Assuming current active installation
        installation = db.query(models.EquipmentTagInstallation).filter(
            models.EquipmentTagInstallation.tag_id == tag.id,
            models.EquipmentTagInstallation.is_active == 1
        ).first()

        if installation and installation.equipment:
             # Logic to update status if value indicates error? 
             # For MVP, maybe just logging "Last Data Received" if we had that field.
             # Or auto-detect "Maintenance" mode if value is specific?
             pass

    @staticmethod
    def process_sync_job_impact(db: Session, job_id: int):
        """
        M5 -> M1/M2: Analyze a completed sync job for business impacts.
        Detects 'Bad' quality data and flags related equipment/tasks.
        """
        job = db.query(models.SyncJob).filter(models.SyncJob.id == job_id).first()
        if not job:
            return "Job not found"

        # Get data points with Bad quality
        bad_data = db.query(models.OperationalData).filter(
            models.OperationalData.job_id == job_id,
            models.OperationalData.quality != "Good"
        ).all()

        impact_count = 0
        for data in bad_data:
            # 1. Find Tag
            tag = db.query(models.InstrumentTag).filter(models.InstrumentTag.tag_number == data.tag_number).first()
            if not tag:
                continue
                
            # 2. Find Equipment (M1)
            install = db.query(models.EquipmentTagInstallation).filter(
                models.EquipmentTagInstallation.tag_id == tag.id,
                models.EquipmentTagInstallation.is_active == 1
            ).first()
            
            if install and install.equipment:
                # 3. M1 link found. Check M2 (Calibration)
                # Find open task
                task = db.query(models.CalibrationTask).filter(
                    models.CalibrationTask.equipment_id == install.equipment.id,
                    models.CalibrationTask.status.in_(["Planned", "In Progress"])
                ).first()
                
                if task:
                    # Append note to task (M5 -> M2)
                    note = f"\n[System] Sync Alert: Bad data quality received on {data.timestamp}. Value: {data.value} {data.unit}"
                    if task.remarks:
                        task.remarks += note
                    else:
                        task.remarks = note
                    db.add(task)
                    impact_count += 1

        db.commit()
        return f"Impact analysis complete. {impact_count} tasks updated with sync alerts."
