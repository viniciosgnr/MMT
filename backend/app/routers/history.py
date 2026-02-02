from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel
import os
import shutil
from ..database import get_db
from ..models import HistoricalReport, ReportType
from ..schemas.phase3 import (
    HistoricalReport as HistoricalReportSchema,
    ReportType as ReportTypeSchema,
    ReportTypeCreate
)

router = APIRouter(prefix="/api/reports", tags=["reports"])

UPLOAD_DIR = "uploads/historical"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("", response_model=List[HistoricalReportSchema])
def get_reports(
    report_type_id: Optional[int] = None,
    fpso_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(HistoricalReport)
    if report_type_id:
        query = query.filter(HistoricalReport.report_type_id == report_type_id)
    if fpso_name:
        query = query.filter(HistoricalReport.fpso_name == fpso_name)
    return query.order_by(HistoricalReport.report_date.desc()).all()


class FileUploadMetadata(BaseModel):
    filename: str
    file_url: str
    file_size: int

class BulkReportUpload(BaseModel):
    report_type_id: int
    title_prefix: Optional[str] = ""
    report_date: date
    fpso_name: Optional[str] = None
    metering_system: Optional[str] = None
    serial_number: Optional[str] = None
    files: List[FileUploadMetadata]

@router.post("/upload")
def upload_reports(
    payload: BulkReportUpload,
    db: Session = Depends(get_db)
):
    """Bulk upload utility for historical reports (Supabase Storage)"""
    uploaded_reports = []
    
    for file in payload.files:
        # Create database record
        db_report = HistoricalReport(
            report_type_id=payload.report_type_id,
            title=f"{payload.title_prefix} {file.filename}".strip(),
            file_url=file.file_url, # Full Supabase URL or relative path
            file_name=file.filename,
            file_size=file.file_size,
            report_date=payload.report_date,
            fpso_name=payload.fpso_name,
            metering_system=payload.metering_system,
            serial_number=payload.serial_number,
            uploaded_by="Current User" # Should get from auth
        )
        db.add(db_report)
        uploaded_reports.append(db_report)
        
    db.commit()
    return {"message": f"Successfully registered {len(payload.files)} files"}

# Report Types (Managed by Admin in 6.2)
@router.get("/types", response_model=List[ReportTypeSchema])
def get_report_types(db: Session = Depends(get_db)):
    return db.query(ReportType).filter(ReportType.is_active == 1).all()

@router.post("/types", response_model=ReportTypeSchema)
def create_report_type(rt: ReportTypeCreate, db: Session = Depends(get_db)):
    db_rt = ReportType(**rt.model_dump())
    db.add(db_rt)
    db.commit()
    db.refresh(db_rt)
    return db_rt
