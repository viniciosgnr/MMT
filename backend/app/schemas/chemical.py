from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List

# Campaign Schemas
class SamplingCampaignBase(BaseModel):
    name: str
    fpso_name: str
    start_date: date
    end_date: Optional[date] = None
    responsible: str
    description: Optional[str] = None

class SamplingCampaignCreate(SamplingCampaignBase):
    pass

class SamplingCampaign(SamplingCampaignBase):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

# Sample Schemas
class SampleBase(BaseModel):
    sample_id: str
    type: str
    collection_date: date
    location: str
    cylinder_location: Optional[str] = None
    responsible: str
    notes: Optional[str] = None

class SampleCreate(SampleBase):
    campaign_id: int

class Sample(SampleBase):
    id: int
    campaign_id: int
    status: str
    lab_report_url: Optional[str]
    compliance_status: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# Result Schemas
class SampleResultBase(BaseModel):
    parameter: str
    value: float
    unit: str

class SampleResultCreate(SampleResultBase):
    sample_id: int

class SampleResult(SampleResultBase):
    id: int
    sample_id: int
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
