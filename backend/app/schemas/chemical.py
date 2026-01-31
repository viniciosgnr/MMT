from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List

# Sample Point Schemas (New)
class SamplePointBase(BaseModel):
    tag_number: str
    description: str
    fpso_name: str
    fluid_type: str
    is_operational: int = 1
    sampling_interval_days: int = 30
    validation_method_implemented: int = 0

class SamplePointCreate(SamplePointBase):
    pass

class SamplePoint(SamplePointBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

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

# Status History Schema (New)
class SampleStatusHistoryBase(BaseModel):
    status: str
    comments: Optional[str] = None
    user: Optional[str] = None

class SampleStatusHistory(SampleStatusHistoryBase):
    id: int
    sample_id: int
    entered_at: datetime

    class Config:
        from_attributes = True

# Sample Schemas
class SampleBase(BaseModel):
    sample_id: str
    type: str # Gas, Oil, Water
    responsible: str
    sample_point_id: int
    notes: Optional[str] = None

class SampleCreate(SampleBase):
    campaign_id: Optional[int] = None
    planned_date: Optional[date] = None

class SampleStatusUpdate(BaseModel):
    status: str
    comments: Optional[str] = None
    user: Optional[str] = None
    # For logistics steps
    event_date: Optional[date] = None 
    # For validation/FC steps
    url: Optional[str] = None
    validation_status: Optional[str] = None

class Sample(SampleBase):
    id: int
    campaign_id: Optional[int]
    status: str
    
    planned_date: Optional[date]
    sampling_date: Optional[date]
    disembark_date: Optional[date]
    delivery_date: Optional[date]
    report_issue_date: Optional[date]
    fc_update_date: Optional[datetime]
    
    lab_report_url: Optional[str]
    validation_status: Optional[str]
    validation_report_url: Optional[str]
    fc_evidence_url: Optional[str]
    
    created_at: datetime
    sample_point: Optional[SamplePoint] = None
    history: List[SampleStatusHistory] = []

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
