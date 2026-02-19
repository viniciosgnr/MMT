from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List

# Sample Point Schemas (New)
class SamplePointBase(BaseModel):
    tag_number: str
    description: str
    fpso_name: str
    is_operational: int = 1
    sampling_interval_days: int = 30
    validation_method_implemented: int = 0

class SamplePointCreate(SamplePointBase):
    pass

class SamplePoint(SamplePointBase):
    id: int
    created_at: Optional[datetime] = None

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
    type: str # Fiscal, Gas Lift, Poço CG, Poço PVT
    responsible: Optional[str] = None
    sample_point_id: Optional[int] = None
    osm_id: Optional[str] = None  # Identificação OSM
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
    # User-defined deadline for the next step
    due_date: Optional[date] = None
    # Additional tracking fields
    osm_id: Optional[str] = None
    laudo_number: Optional[str] = None
    mitigated: Optional[int] = None

class Sample(SampleBase):
    id: int
    campaign_id: Optional[int]
    status: str
    laudo_number: Optional[str] = None
    mitigated: Optional[int] = 0
    
    # SLA Dates — Expected (Previsto)
    planned_date: Optional[date] = None
    disembark_expected_date: Optional[date] = None
    lab_expected_date: Optional[date] = None
    report_expected_date: Optional[date] = None
    fc_expected_date: Optional[date] = None
    
    # SLA Dates — Actual (Realizado)
    sampling_date: Optional[date] = None
    disembark_date: Optional[date] = None
    delivery_date: Optional[date] = None
    report_issue_date: Optional[date] = None
    fc_update_date: Optional[datetime] = None
    due_date: Optional[date] = None
    
    lab_report_url: Optional[str] = None
    validation_status: Optional[str] = None
    validation_report_url: Optional[str] = None
    fc_evidence_url: Optional[str] = None
    
    created_at: Optional[datetime] = None
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
    validation_status: Optional[str] = None
    validation_detail: Optional[str] = None
    history_mean: Optional[float] = None
    history_std: Optional[float] = None
    source_pdf: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Validation Response Schemas
class ValidationCheck(BaseModel):
    parameter: str
    value: float
    unit: str
    status: str  # "pass", "fail", "warning", "insufficient_data"
    detail: str
    history_mean: Optional[float] = None
    history_std: Optional[float] = None
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    history_values: List[float] = []
    history_dates: List[str] = []

class ValidationResponse(BaseModel):
    report_type: str
    overall_status: str  # "Approved" / "Reproved"
    boletim: Optional[str] = None
    tag_point: Optional[str] = None
    checks: List[ValidationCheck] = []
    passed_count: int = 0
    failed_count: int = 0

class ParameterHistoryItem(BaseModel):
    value: float
    date: str
    sample_id: str
