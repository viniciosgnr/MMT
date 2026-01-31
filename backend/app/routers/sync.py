from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import SyncStatus, SyncStatusEnum, SyncSource, SyncJob, OperationalData
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
def create_sync_source(source: SyncSourceCreate, db: Session = Depends(get_db)):
    db_source = SyncSource(**source.dict())
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return db_source

# --- Data Ingestion (Automatic) ---

@router.post("/ingest")
def ingest_data(payload: DataIngestionPayload, db: Session = Depends(get_db)):
    """Automated ingestion for Flow Computers and AVEVA PI."""
    source = db.query(SyncSource).filter(SyncSource.id == payload.source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Sync source not found")

    job = SyncJob(
        source_id=source.id,
        status=SyncStatusEnum.SYNCED.value,
        records_processed=len(payload.data),
        end_time=datetime.utcnow()
    )
    db.add(job)
    db.flush() # Get Job ID

    for item in payload.data:
        data_point = OperationalData(
            job_id=job.id,
            tag_number=item.tag_number,
            value=item.value,
            timestamp=item.timestamp,
            unit=item.unit,
            quality=item.quality
        )
        db.add(data_point)
    
    # Update global status for the dashboard
    sync_status = db.query(SyncStatus).filter(SyncStatus.module_name == source.name).first()
    if not sync_status:
        sync_status = SyncStatus(module_name=source.name)
        db.add(sync_status)
    
    sync_status.last_sync = datetime.utcnow()
    sync_status.status = SyncStatusEnum.SYNCED.value
    sync_status.records_synced += len(payload.data)

    db.commit()
    return {"message": "Data ingested successfully", "job_id": job.id}

# --- Manual File Upload (USB Workflow) ---

@router.post("/upload")
async def upload_sync_file(
    source_id: int, 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    """Manual upload for data dumps gathered via USB offshore."""
    source = db.query(SyncSource).filter(SyncSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Sync source not found")

    content = await file.read()
    
    # Simple CSV parser for MVP
    decoded = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded))
    
    job = SyncJob(
        source_id=source.id,
        status=SyncStatusEnum.SYNCED.value,
        artifact_path=file.filename # Simplified for MVP
    )
    db.add(job)
    db.flush()

    count = 0
    for row in reader:
        try:
            data_point = OperationalData(
                job_id=job.id,
                tag_number=row.get("tag", "UNKNOWN"),
                value=float(row.get("value", 0)),
                timestamp=datetime.fromisoformat(row.get("timestamp", datetime.utcnow().isoformat())),
                unit=row.get("unit"),
                quality=row.get("quality", "Good")
            )
            db.add(data_point)
            count += 1
        except Exception:
            continue
    
    job.records_processed = count
    job.end_time = datetime.utcnow()
    
    db.commit()
    return {"message": "File processed successfully", "records": count}

# --- Monitoring ---

@router.get("/jobs", response_model=List[SyncJobSchema])
def get_sync_jobs(limit: int = 20, db: Session = Depends(get_db)):
    return db.query(SyncJob).order_by(SyncJob.start_time.desc()).limit(limit).all()

@router.get("/status", response_model=List[SyncStatusSchema])
def get_sync_status(db: Session = Depends(get_db)):
    """Get aggregated synchronization status for all sources"""
    return db.query(SyncStatus).all()
