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
from ..dependencies import get_current_user_fpso
from ..services.alerts_service import AlertsService

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
    db: Session = Depends(get_db),
    current_user_data = Depends(get_current_user_fpso)
):
    """Get all alerts with extensive filters"""
    query = db.query(Alert)
    
    if severity:
        query = query.filter(Alert.severity == severity)
    
    if acknowledged is not None:
        query = query.filter(Alert.acknowledged == (1 if acknowledged else 0))

    filter_fpso = current_user_data["fpso_name"] if current_user_data["fpso_name"] else fpso_name
    if filter_fpso:
        query = query.filter(Alert.fpso_name == filter_fpso)

    if tag_number:
        query = query.filter(Alert.tag_number == tag_number)

    if alert_type:
        query = query.filter(Alert.type == alert_type)
    
    return query.order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()

@router.post("", response_model=AlertSchema)
def create_alert(alert: AlertCreate, db: Session = Depends(get_db), current_user_data = Depends(get_current_user_fpso)):
    """Create a new alert"""
    if current_user_data["fpso_name"] and alert.fpso_name != current_user_data["fpso_name"]:
        raise HTTPException(status_code=403, detail="Forbidden: You can only create alerts for your current FPSO.")
    db_alert = Alert(**alert.model_dump())
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert

@router.put("/{alert_id}/acknowledge", response_model=AlertSchema)
def acknowledge_alert(
    alert_id: int,
    ack: AlertAcknowledge,
    db: Session = Depends(get_db),
    current_user_data = Depends(get_current_user_fpso)
):
    """Acknowledge an alert with justification and linking"""
    return AlertsService.acknowledge_alert(db, alert_id, ack, current_user_data["fpso_name"])

@router.get("/unread-count")
def get_unread_count(db: Session = Depends(get_db), current_user_data = Depends(get_current_user_fpso)):
    """Get count of unacknowledged alerts"""
    query = db.query(Alert).filter(Alert.acknowledged == 0)
    if current_user_data["fpso_name"]:
        query = query.filter(Alert.fpso_name == current_user_data["fpso_name"])
    return {"unread_count": query.count()}

# Configuration Endpoints
@router.get("/configs", response_model=List[ConfigSchema])
def get_alert_configs(db: Session = Depends(get_db), current_user_data = Depends(get_current_user_fpso)):
    query = db.query(AlertConfiguration)
    if current_user_data["fpso_name"]:
        query = query.filter(AlertConfiguration.fpso_name == current_user_data["fpso_name"])
    return query.all()

@router.post("/configs", response_model=ConfigSchema)
def create_alert_config(config: AlertConfigurationCreate, db: Session = Depends(get_db), current_user_data = Depends(get_current_user_fpso)):
    return AlertsService.create_alert_config(db, config, current_user_data["fpso_name"])
