from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import SyncStatus, SyncStatusEnum, SyncSource, SyncJob, OperationalData
from ..services.integrations import IntegrationService
from ..dependencies import get_current_user_fpso
from ..services.sync_service import SyncService
from ..schemas.phase3 import (
    SyncStatus as SyncStatusSchema, 
    SyncSource as SyncSourceSchema, 
    SyncSourceCreate,
    SyncJob as SyncJobSchema,
    DataIngestionPayload
)
from datetime import datetime
import json
import csv
import io

router = APIRouter(prefix="/api/sync", tags=["sync"])

# --- Source Management ---

@router.get("/sources", response_model=List[SyncSourceSchema])
def get_sync_sources(db: Session = Depends(get_db)):
    return db.query(SyncSource).all()

@router.post("/sources", response_model=SyncSourceSchema)
def create_sync_source(source: SyncSourceCreate, db: Session = Depends(get_db), current_user_data = Depends(get_current_user_fpso)):
    return SyncService.create_sync_source(db, source)

# --- Data Ingestion (Automatic) ---

@router.post("/ingest")
def ingest_data(payload: DataIngestionPayload, db: Session = Depends(get_db)):
    """Automated ingestion for Flow Computers and AVEVA PI."""
    return SyncService.ingest_data(db, payload)

# --- Manual File Upload (USB Workflow) ---

@router.post("/upload")
async def upload_sync_file(
    source_id: int, 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user_data = Depends(get_current_user_fpso)
):
    """Manual upload for data dumps gathered via USB offshore."""
    content = await file.read()
    return await SyncService.upload_sync_file(db, source_id, content, file.filename)

# --- Monitoring ---

@router.get("/jobs", response_model=List[SyncJobSchema])
def get_sync_jobs(limit: int = 20, db: Session = Depends(get_db)):
    return db.query(SyncJob).order_by(SyncJob.start_time.desc()).limit(limit).all()

@router.get("/status", response_model=List[SyncStatusSchema])
def get_sync_status(db: Session = Depends(get_db)):
    """Get aggregated synchronization status for all sources"""
    return db.query(SyncStatus).all()
