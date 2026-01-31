from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Alert, AlertSeverity
from ..schemas.phase3 import AlertCreate, AlertAcknowledge, Alert as AlertSchema
from datetime import datetime

router = APIRouter(prefix="/api/alerts", tags=["alerts"])

@router.get("", response_model=List[AlertSchema])
def get_alerts(
    skip: int = 0,
    limit: int = 100,
    severity: str = None,
    acknowledged: bool = None,
    db: Session = Depends(get_db)
):
    """Get all alerts with optional filters"""
    query = db.query(Alert)
    
    if severity:
        query = query.filter(Alert.severity == severity)
    
    if acknowledged is not None:
        query = query.filter(Alert.acknowledged == (1 if acknowledged else 0))
    
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
    """Acknowledge an alert"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.acknowledged = 1
    alert.acknowledged_by = ack.acknowledged_by
    alert.acknowledged_at = datetime.utcnow()
    db.commit()
    db.refresh(alert)
    return alert

@router.get("/unread-count")
def get_unread_count(db: Session = Depends(get_db)):
    """Get count of unacknowledged alerts"""
    count = db.query(Alert).filter(Alert.acknowledged == 0).count()
    return {"unread_count": count}
