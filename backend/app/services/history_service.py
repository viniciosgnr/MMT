from sqlalchemy.orm import Session
from fastapi import HTTPException
from ..models import HistoricalReport, ReportType
from ..schemas.phase3 import BulkReportUpload, ReportTypeCreate

class HistoryService:
    @staticmethod
    def upload_reports(db: Session, payload: BulkReportUpload, user_fpso: str = None, username: str = "System"):
        if user_fpso and payload.fpso_name != user_fpso:
            raise HTTPException(status_code=403, detail="Forbidden: You can only upload reports for your current FPSO.")
        uploaded_reports = []
        for file in payload.files:
            db_report = HistoricalReport(
                report_type_id=payload.report_type_id,
                title=f"{payload.title_prefix} {file.filename}".strip(),
                file_url=file.file_url,
                file_name=file.filename,
                file_size=file.file_size,
                report_date=payload.report_date,
                fpso_name=payload.fpso_name,
                metering_system=payload.metering_system,
                serial_number=payload.serial_number,
                uploaded_by=username
            )
            db.add(db_report)
            uploaded_reports.append(db_report)
        db.commit()
        return {"message": f"Successfully registered {len(payload.files)} files"}

    @staticmethod
    def create_report_type(db: Session, rt: ReportTypeCreate):
        db_rt = ReportType(**rt.model_dump())
        db.add(db_rt)
        db.commit()
        db.refresh(db_rt)
        return db_rt
