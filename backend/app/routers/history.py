from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel
import os
import shutil
from ..database import get_db
from ..models import HistoricalReport, ReportType
from ..dependencies import get_current_user_fpso
from ..services.history_service import HistoryService
from ..schemas.phase3 import (
    HistoricalReport as HistoricalReportSchema,
    ReportType as ReportTypeSchema,
    ReportTypeCreate,
    BulkReportUpload
)

router = APIRouter(prefix="/api/reports", tags=["reports"])

UPLOAD_DIR = "uploads/historical"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("", response_model=List[HistoricalReportSchema])
def get_reports(
    report_type_id: Optional[int] = None,
    fpso_name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user_data = Depends(get_current_user_fpso)
):
    query = db.query(HistoricalReport)
    if report_type_id:
        query = query.filter(HistoricalReport.report_type_id == report_type_id)
        
    filter_fpso = current_user_data["fpso_name"] if current_user_data["fpso_name"] else fpso_name
    if filter_fpso:
        query = query.filter(HistoricalReport.fpso_name == filter_fpso)
        
    return query.order_by(HistoricalReport.report_date.desc()).all()


@router.post("/upload")
def upload_reports(
    payload: BulkReportUpload,
    db: Session = Depends(get_db),
    current_user_data = Depends(get_current_user_fpso)
):
    """Bulk upload utility for historical reports (Supabase Storage)"""
    user = current_user_data["user"]
    username = user.get("username") if isinstance(user, dict) else getattr(user, 'username', 'System')
    return HistoryService.upload_reports(db, payload, current_user_data["fpso_name"], username)

# Report Types (Managed by Admin in 6.2)
@router.get("/types", response_model=List[ReportTypeSchema])
def get_report_types(db: Session = Depends(get_db)):
    return db.query(ReportType).filter(ReportType.is_active == 1).all()

@router.post("/types", response_model=ReportTypeSchema)
def create_report_type(rt: ReportTypeCreate, db: Session = Depends(get_db), current_user_data = Depends(get_current_user_fpso)):
    return HistoryService.create_report_type(db, rt)
