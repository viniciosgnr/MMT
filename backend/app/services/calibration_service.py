from datetime import date, datetime
import json
from sqlalchemy.orm import Session
from fastapi import HTTPException
from .. import models
from ..schemas import calibration as schemas
from .integrations import IntegrationService

class CalibrationService:
    @staticmethod
    def plan_calibration(db: Session, task_id: int, plan_data: schemas.CalibrationPlanData):
        task = db.query(models.CalibrationTask).filter(models.CalibrationTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        task.status = models.CalibrationTaskStatus.SCHEDULED.value
        task.plan_date = date.today()
        if plan_data.procurement_ids:
            task.spare_procurement_ids = json.dumps(plan_data.procurement_ids)
        db.commit()
        db.refresh(task)
        return {"message": "Calibration planned successfully", "task_id": task.id, "status": task.status}

    @staticmethod
    def execute_calibration(db: Session, task_id: int, exec_data: schemas.CalibrationExecutionData, user_id: str):
        task = db.query(models.CalibrationTask).filter(models.CalibrationTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        task.status = models.CalibrationTaskStatus.EXECUTED.value
        task.exec_date = exec_data.execution_date
        task.calibration_type = exec_data.calibration_type
        task.temporary_completion_date = exec_data.completion_date
        task.is_temporary = 1
        task.seal_number = exec_data.seal_number
        task.seal_installation_date = exec_data.seal_date
        task.seal_location = exec_data.seal_location
        
        seal = models.SealHistory(
            tag_id=task.equipment.installations[0].tag_id if task.equipment.installations else None,
            seal_number=exec_data.seal_number,
            seal_type=exec_data.seal_type or "Wire",
            seal_location=exec_data.seal_location,
            installation_date=exec_data.seal_date,
            installed_by=user_id,
            is_active=1
        )
        db.add(seal)
        db.commit()
        db.refresh(task)
        return {"message": "Calibration executed successfully", "task_id": task.id, "status": task.status}

    @staticmethod
    def upload_certificate(db: Session, task_id: int, certificate_data: schemas.CertificateData):
        task = db.query(models.CalibrationTask).filter(models.CalibrationTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        task.certificate_number = certificate_data.certificate_number
        task.certificate_issued_date = certificate_data.issue_date
        task.is_temporary = 0
        task.definitive_completion_date = certificate_data.issue_date
        task.certificate_ca_status = "pending"
        
        if not task.results:
            result = models.CalibrationResult(
                task_id=task_id,
                standard_reading=certificate_data.standard_reading or 0.0,
                equipment_reading=certificate_data.equipment_reading or 0.0,
                uncertainty=certificate_data.uncertainty
            )
            db.add(result)
        else:
            result = task.results
            if certificate_data.uncertainty:
                result.uncertainty = certificate_data.uncertainty
            if certificate_data.standard_reading:
                result.standard_reading = certificate_data.standard_reading
            if certificate_data.equipment_reading:
                result.equipment_reading = certificate_data.equipment_reading
        
        db.commit()
        return {"message": "Certificate uploaded successfully", "task_id": task.id}

    @staticmethod
    def validate_certificate(db: Session, task_id: int, user_id: str):
        task = db.query(models.CalibrationTask).filter(models.CalibrationTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        validation_results = []
        issues = []
        
        if not task.certificate_number:
            issues.append("Certificate number is missing")
        else:
            validation_results.append({
                "rule": "Certificate Number Exists",
                "status": "pass",
                "value": task.certificate_number
            })
        
        if task.certificate_issued_date and task.exec_date:
            days_diff = (task.certificate_issued_date - task.exec_date).days
            if days_diff > 30:
                issues.append(f"Certificate issued {days_diff} days after calibration (limit: 30 days)")
                validation_results.append({
                    "rule": "RTM Time Limit",
                    "status": "fail",
                    "value": f"{days_diff} days"
                })
            else:
                validation_results.append({
                    "rule": "RTM Time Limit",
                    "status": "pass",
                    "value": f"{days_diff} days"
                })
        
        if task.certificate_number and task.tag:
            if task.tag.replace("-", "") not in task.certificate_number.replace("-", ""):
                issues.append(f"Certificate number may not match tag {task.tag}")
        
        result = task.results
        if result:
            result.ca_validated_at = datetime.utcnow()
            result.ca_validated_by = user_id
            result.ca_validation_rules = json.dumps(validation_results)
            result.ca_issues = json.dumps(issues) if issues else None
        
        task.certificate_ca_status = "approved" if not issues else "pending"
        task.certificate_ca_notes = "\n".join(issues) if issues else None
        db.commit()
        
        return {
            "validation_results": validation_results,
            "issues": issues,
            "status": "approved" if not issues else "pending"
        }

    @staticmethod
    def complete_calibration_fc(db: Session, task_id: int, fc_data: schemas.FCUpdateData):
        task = db.query(models.CalibrationTask).filter(models.CalibrationTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
            
        result = task.results
        if not result:
            result = models.CalibrationResult(
                task_id=task_id, 
                standard_reading=0.0, 
                equipment_reading=0.0
            )
            db.add(result)
            
        result.fc_evidence_url = fc_data.fc_evidence_url
        if fc_data.notes:
            result.notes = (result.notes or "") + "\nFC Notes: " + fc_data.notes
            
        task.status = "Completed"
            
        db.commit()
        return {"message": "Flow Computer evidence updated successfully", "task_id": task_id}

    @staticmethod
    def fail_task(db: Session, task_id: int, reason: str, username: str):
        task = db.query(models.CalibrationTask).filter(models.CalibrationTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        notification_id = IntegrationService.trigger_failure_from_calibration(
            db, task_id, reason, username
        )
        return {
            "message": "Task flagged as failed. Notification created.",
            "notification_id": notification_id
        }

    @staticmethod
    def generate_certificate_number(db: Session, task_id: int, cert_type: str = "PRV"):
        task = db.query(models.CalibrationTask).filter(models.CalibrationTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        fpso_name = "Unknown"
        if task.campaign:
            fpso_name = task.campaign.fpso_name
        
        trigrams = {
            "Cidade de Angra dos Reis": "CDA",
            "Cidade de Ilhabela": "CDI",
            "Cidade de Maricá": "CDM",
            "Cidade de Saquarema": "CDS",
            "Cidade de Paraty": "CDP",
            "Espirito Santo": "ESS",
            "Anchieta": "ATD",
            "Capixaba": "ADG",
            "Sepetiba": "SEP"
        }
        
        aaa = "XXX"
        for name, trigram in trigrams.items():
            if name in fpso_name:
                aaa = trigram
                break
                
        year = datetime.now().year
        yy = str(year)[-2:]
        pattern = f"{aaa}-{cert_type}-{yy}-%"
        last_cert = db.query(models.CalibrationTask).filter(
            models.CalibrationTask.certificate_number.like(pattern)
        ).order_by(models.CalibrationTask.certificate_number.desc()).first()
        
        seq = 1
        if last_cert and last_cert.certificate_number:
            try:
                parts = last_cert.certificate_number.split('-')
                if len(parts) == 4:
                    seq = int(parts[3]) + 1
            except:
                pass
                
        ddd = f"{seq:03d}"
        cert_number = f"{aaa}-{cert_type}-{yy}-{ddd}"
        return {"certificate_number": cert_number}
