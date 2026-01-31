from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from .. import models, database
from ..schemas import calibration as schemas

router = APIRouter(
    prefix="/api/calibration",
    tags=["calibration"],
)

# Campaign Endpoints
@router.post("/campaigns", response_model=schemas.CalibrationCampaign)
def create_campaign(campaign: schemas.CalibrationCampaignCreate, db: Session = Depends(database.get_db)):
    db_campaign = models.CalibrationCampaign(**campaign.dict())
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign

@router.get("/campaigns", response_model=List[schemas.CalibrationCampaign])
def list_campaigns(
    fpso_name: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db)
):
    query = db.query(models.CalibrationCampaign)
    if fpso_name:
        query = query.filter(models.CalibrationCampaign.fpso_name == fpso_name)
    if status:
        query = query.filter(models.CalibrationCampaign.status == status)
    campaigns = query.offset(skip).limit(limit).all()
    return campaigns

@router.get("/campaigns/{campaign_id}", response_model=schemas.CalibrationCampaign)
def get_campaign(campaign_id: int, db: Session = Depends(database.get_db)):
    campaign = db.query(models.CalibrationCampaign).filter(models.CalibrationCampaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign

# Task Endpoints
@router.post("/tasks", response_model=schemas.CalibrationTask)
def create_task(task: schemas.CalibrationTaskCreate, db: Session = Depends(database.get_db)):
    db_task = models.CalibrationTask(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.get("/tasks", response_model=List[schemas.CalibrationTask])
def list_tasks(
    campaign_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db)
):
    query = db.query(models.CalibrationTask)
    if campaign_id:
        query = query.filter(models.CalibrationTask.campaign_id == campaign_id)
    if status:
        query = query.filter(models.CalibrationTask.status == status)
    tasks = query.offset(skip).limit(limit).all()
    return tasks

@router.get("/tasks/{task_id}", response_model=schemas.CalibrationTask)
def get_task(task_id: int, db: Session = Depends(database.get_db)):
    task = db.query(models.CalibrationTask).filter(models.CalibrationTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

# Result Endpoints
@router.post("/tasks/{task_id}/results", response_model=schemas.CalibrationResult)
def submit_results(task_id: int, result: schemas.CalibrationResultBase, db: Session = Depends(database.get_db)):
    # Check if task exists
    task = db.query(models.CalibrationTask).filter(models.CalibrationTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Create result
    db_result = models.CalibrationResult(task_id=task_id, **result.dict())
    db.add(db_result)
    
    # Update task status
    task.status = models.CalibrationTaskStatus.EXECUTED.value
    task.exec_date = date.today()
    
    db.commit()
    db.refresh(db_result)
    return db_result

@router.get("/tasks/{task_id}/results", response_model=schemas.CalibrationResult)
def get_results(task_id: int, db: Session = Depends(database.get_db)):
    result = db.query(models.CalibrationResult).filter(models.CalibrationResult.task_id == task_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Results not found")
    return result
