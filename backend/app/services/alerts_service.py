from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException
from ..models import Alert, AlertConfiguration, AlertRecipient
from ..schemas.phase3 import AlertCreate, AlertAcknowledge, AlertConfigurationCreate

class AlertsService:
    @staticmethod
    def acknowledge_alert(db: Session, alert_id: int, ack: AlertAcknowledge, user_fpso: str = None):
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        if user_fpso and alert.fpso_name != user_fpso:
            raise HTTPException(status_code=403, detail="Forbidden: You can only acknowledge alerts for your current FPSO.")
        
        alert.acknowledged = 1
        alert.acknowledged_by = ack.acknowledged_by
        alert.acknowledged_at = datetime.utcnow()
        alert.justification = ack.justification
        alert.linked_event_type = ack.linked_event_type
        alert.linked_event_id = ack.linked_event_id
        alert.run_recheck = 1 if ack.run_recheck else 0
        
        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def create_alert_config(db: Session, config: AlertConfigurationCreate, user_fpso: str = None):
        if user_fpso and config.fpso_name != user_fpso:
            raise HTTPException(status_code=403, detail="Forbidden: You can only configure alerts for your current FPSO.")
        db_config = AlertConfiguration(
            fpso_name=config.fpso_name,
            alert_type=config.alert_type,
            rule_config=config.rule_config,
            notify_email=1 if config.notify_email else 0,
            notify_whatsapp=1 if config.notify_whatsapp else 0,
            notify_in_app=1 if config.notify_in_app else 0
        )
        db.add(db_config)
        db.commit()
        db.refresh(db_config)
        
        for r in config.recipients:
            db_recipient = AlertRecipient(
                config_id=db_config.id,
                **r.model_dump()
            )
            db.add(db_recipient)
        
        db.commit()
        db.refresh(db_config)
        return db_config
