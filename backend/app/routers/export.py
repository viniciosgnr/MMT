from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import zipfile
import io
import os
from datetime import datetime
from .. import models, database
from ..dependencies import get_current_user_fpso
from ..services.export_service import ExportService
from ..schemas.export import ExportRequest, ExportJobStatus, FILE_TYPE_MAP

router = APIRouter(
    prefix="/api/export",
    tags=["export"],
)

@router.post("/prepare")
async def prepare_export(request: ExportRequest, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db), current_user_data = Depends(get_current_user_fpso)):
    if current_user_data["fpso_name"]:
        request.fpso_name = current_user_data["fpso_name"]
    job_id = f"job_{datetime.utcnow().timestamp()}"
    ExportService.export_jobs[job_id] = {"status": "PENDING", "progress": 0}
    
    background_tasks.add_task(ExportService.generate_export_zip, job_id, request, db)
    return {"job_id": job_id}

@router.get("/status/{job_id}", response_model=ExportJobStatus)
async def get_status(job_id: str):
    if job_id not in ExportService.export_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, **ExportService.export_jobs[job_id]}

@router.get("/download/{job_id}")
async def download_zip(job_id: str):
    if job_id not in ExportService.export_jobs or ExportService.export_jobs[job_id]["status"] != "COMPLETED":
        raise HTTPException(status_code=404, detail="File not ready")
    
    file_path = ExportService.export_jobs[job_id].get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
        
    return FileResponse(file_path, filename="MMT_Audit_Export.zip", media_type="application/zip")
