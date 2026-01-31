from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
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

@router.post("/upload")
async def upload_reports(
    files: List[UploadFile] = File(...),
    report_type_id: int = Form(...),
    title_prefix: str = Form(""),
    report_date: str = Form(...),
    fpso_name: Optional[str] = Form(None),
    metering_system: Optional[str] = Form(None),
    serial_number: Optional[str] = Form(None),
    uploaded_by: str = Form("Marcos G."),
    db: Session = Depends(get_db)
):
    """Bulk upload utility for historical reports"""
    uploaded_reports = []
    
    # Parse date
    dt_report = datetime.fromisoformat(report_date.replace("Z", "+00:00"))

    for file in files:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        
        # Save file locally
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Create database record
        db_report = HistoricalReport(
            report_type_id=report_type_id,
            title=f"{title_prefix} {file.filename}".strip(),
            file_url=f"/uploads/historical/{file.filename}",
            file_name=file.filename,
            file_size=os.path.getsize(file_path),
            report_date=dt_report,
            fpso_name=fpso_name,
            metering_system=metering_system,
            serial_number=serial_number,
            uploaded_by=uploaded_by
        )
        db.add(db_report)
        uploaded_reports.append(db_report)
        
    db.commit()
    return {"message": f"Successfully uploaded {len(files)} files"}

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
