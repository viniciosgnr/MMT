from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List

# Campaign Schemas
class CalibrationCampaignBase(BaseModel):
    name: str
    fpso_name: str
    start_date: date
    end_date: Optional[date] = None
    responsible: str
    description: Optional[str] = None

class CalibrationCampaignCreate(CalibrationCampaignBase):
    pass

class CalibrationCampaign(CalibrationCampaignBase):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

# Task Schemas
class CalibrationTaskBase(BaseModel):
    tag: str
    description: str
    type: str
    due_date: date
    plan_date: Optional[date] = None

class CalibrationTaskCreate(CalibrationTaskBase):
    campaign_id: Optional[int] = None
    equipment_id: int

class CalibrationTask(CalibrationTaskBase):
    id: int
    campaign_id: Optional[int]
    equipment_id: int
    exec_date: Optional[date]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

# Result Schemas
class CalibrationResultBase(BaseModel):
    standard_reading: float
    equipment_reading: float
    uncertainty: Optional[float] = None
    notes: Optional[str] = None

class CalibrationResultCreate(CalibrationResultBase):
    task_id: int

class CalibrationResult(CalibrationResultBase):
    id: int
    task_id: int
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    certificate_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
