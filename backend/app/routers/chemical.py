from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, database
from ..schemas import chemical as schemas

router = APIRouter(
    prefix="/api/chemical",
    tags=["chemical"],
)

# Campaign Endpoints
@router.post("/campaigns", response_model=schemas.SamplingCampaign)
def create_campaign(campaign: schemas.SamplingCampaignCreate, db: Session = Depends(database.get_db)):
    db_campaign = models.SamplingCampaign(**campaign.dict())
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign

@router.get("/campaigns", response_model=List[schemas.SamplingCampaign])
def list_campaigns(
    fpso_name: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db)
):
    query = db.query(models.SamplingCampaign)
    if fpso_name:
        query = query.filter(models.SamplingCampaign.fpso_name == fpso_name)
    if status:
        query = query.filter(models.SamplingCampaign.status == status)
    campaigns = query.offset(skip).limit(limit).all()
    return campaigns

# Sample Endpoints
@router.post("/samples", response_model=schemas.Sample)
def create_sample(sample: schemas.SampleCreate, db: Session = Depends(database.get_db)):
    # Check if sample_id already exists
    existing = db.query(models.Sample).filter(models.Sample.sample_id == sample.sample_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Sample ID already exists")
    
    db_sample = models.Sample(**sample.dict())
    db.add(db_sample)
    db.commit()
    db.refresh(db_sample)
    return db_sample

@router.get("/samples", response_model=List[schemas.Sample])
def list_samples(
    campaign_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db)
):
    query = db.query(models.Sample)
    if campaign_id:
        query = query.filter(models.Sample.campaign_id == campaign_id)
    if status:
        query = query.filter(models.Sample.status == status)
    samples = query.offset(skip).limit(limit).all()
    return samples

@router.get("/samples/{sample_id}", response_model=schemas.Sample)
def get_sample(sample_id: int, db: Session = Depends(database.get_db)):
    sample = db.query(models.Sample).filter(models.Sample.id == sample_id).first()
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    return sample

@router.put("/samples/{sample_id}/status")
def update_sample_status(sample_id: int, status: str, db: Session = Depends(database.get_db)):
    sample = db.query(models.Sample).filter(models.Sample.id == sample_id).first()
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    
    sample.status = status
    db.commit()
    return {"message": "Status updated successfully"}

# Result Endpoints
@router.post("/samples/{sample_id}/results", response_model=schemas.SampleResult)
def add_result(sample_id: int, result: schemas.SampleResultBase, db: Session = Depends(database.get_db)):
    # Check if sample exists
    sample = db.query(models.Sample).filter(models.Sample.id == sample_id).first()
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    
    db_result = models.SampleResult(sample_id=sample_id, **result.dict())
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result

@router.get("/samples/{sample_id}/results", response_model=List[schemas.SampleResult])
def get_results(sample_id: int, db: Session = Depends(database.get_db)):
    results = db.query(models.SampleResult).filter(models.SampleResult.sample_id == sample_id).all()
    return results
