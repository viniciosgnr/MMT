from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Alert, AlertSeverity, AlertConfiguration, AlertRecipient
from ..schemas.phase3 import (
    AlertCreate, 
    AlertAcknowledge, 
    Alert as AlertSchema,
    AlertConfiguration as ConfigSchema,
    AlertConfigurationCreate
)
from datetime import datetime

router = APIRouter(prefix="/api/alerts", tags=["alerts"])

@router.get("", response_model=List[AlertSchema])
def get_alerts(
    skip: int = 0,
    limit: int = 100,
    severity: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    fpso_name: Optional[str] = None,
    tag_number: Optional[str] = None,
    alert_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all alerts with extensive filters"""
    query = db.query(Alert)
    
    if severity:
        query = query.filter(Alert.severity == severity)
    
    if acknowledged is not None:
        query = query.filter(Alert.acknowledged == (1 if acknowledged else 0))

    if fpso_name:
        query = query.filter(Alert.fpso_name == fpso_name)

    if tag_number:
        query = query.filter(Alert.tag_number == tag_number)

    if alert_type:
        query = query.filter(Alert.type == alert_type)
    
    return query.order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()

@router.post("", response_model=AlertSchema)
def create_alert(alert: AlertCreate, db: Session = Depends(get_db)):
    """Create a new alert"""
    db_alert = Alert(**alert.model_dump())
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert

@router.put("/{alert_id}/acknowledge", response_model=AlertSchema)
def acknowledge_alert(
    alert_id: int,
    ack: AlertAcknowledge,
    db: Session = Depends(get_db)
):
    """Acknowledge an alert with justification and linking"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
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

@router.get("/unread-count")
def get_unread_count(db: Session = Depends(get_db)):
    """Get count of unacknowledged alerts"""
    count = db.query(Alert).filter(Alert.acknowledged == 0).count()
    return {"unread_count": count}

# Configuration Endpoints
@router.get("/configs", response_model=List[ConfigSchema])
def get_alert_configs(db: Session = Depends(get_db)):
    return db.query(AlertConfiguration).all()

@router.post("/configs", response_model=ConfigSchema)
def create_alert_config(config: AlertConfigurationCreate, db: Session = Depends(get_db)):
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
