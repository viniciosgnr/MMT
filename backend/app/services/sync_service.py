from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException
import csv
import io
from ..models import SyncStatus, SyncStatusEnum, SyncSource, SyncJob, OperationalData
from ..services.integrations import IntegrationService
from ..schemas.phase3 import SyncSourceCreate, DataIngestionPayload

class SyncService:
    @staticmethod
    def create_sync_source(db: Session, source: SyncSourceCreate):
        db_source = SyncSource(**source.dict())
        db.add(db_source)
        db.commit()
        db.refresh(db_source)
        return db_source

    @staticmethod
    def ingest_data(db: Session, payload: DataIngestionPayload):
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
        db.flush()
        
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
            
        sync_status = db.query(SyncStatus).filter(SyncStatus.module_name == source.name).first()
        if not sync_status:
            sync_status = SyncStatus(module_name=source.name)
            db.add(sync_status)
        
        sync_status.last_sync = datetime.utcnow()
        sync_status.status = SyncStatusEnum.SYNCED.value
        sync_status.records_synced += len(payload.data)
        db.commit()
        
        try:
            IntegrationService.process_sync_job_impact(db, job.id)
        except Exception as e:
            print(f"Integration Error: {e}")
            
        return {"message": "Data ingested successfully", "job_id": job.id}

    @staticmethod
    async def upload_sync_file(db: Session, source_id: int, file_content: bytes, filename: str):
        source = db.query(SyncSource).filter(SyncSource.id == source_id).first()
        if not source:
            raise HTTPException(status_code=404, detail="Sync source not found")
            
        decoded = file_content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(decoded))
        
        job = SyncJob(
            source_id=source.id,
            status=SyncStatusEnum.SYNCED.value,
            artifact_path=filename
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
        
        try:
            IntegrationService.process_sync_job_impact(db, job.id)
        except Exception as e:
            print(f"Integration Error: {e}")
            
        return {"message": "File processed successfully", "records": count}
