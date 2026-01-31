from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

# Existing schemas
class CalibrationCampaignBase(BaseModel):
    name: str
    fpso_name: str
    start_date: date
    end_date: Optional[date] = None
    status: str
    responsible: str
    description: Optional[str] = None

class CalibrationCampaignCreate(CalibrationCampaignBase):
    pass

class CalibrationCampaign(CalibrationCampaignBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class CalibrationTaskBase(BaseModel):
    campaign_id: Optional[int] = None
    equipment_id: int
    tag: str
    description: str
    type: str = "Calibration"
    due_date: date

class CalibrationTaskCreate(CalibrationTaskBase):
    pass


class CalibrationTask(CalibrationTaskBase):
    id: int
    plan_date: Optional[date] = None
    exec_date: Optional[date] = None
    status: str
    created_at: datetime
    
    # M2 MVP fields
    calibration_type: Optional[str] = None
    temporary_completion_date: Optional[date] = None
    definitive_completion_date: Optional[date] = None
    is_temporary: int = 0
    seal_number: Optional[str] = None
    seal_installation_date: Optional[date] = None
    seal_location: Optional[str] = None
    spare_procurement_ids: Optional[str] = None
    certificate_number: Optional[str] = None
    certificate_issued_date: Optional[date] = None
    certificate_ca_status: Optional[str] = None
    certificate_ca_notes: Optional[str] = None

    class Config:
        from_attributes = True

class CalibrationResultBase(BaseModel):
    standard_reading: float
    equipment_reading: float
    uncertainty: Optional[float] = None
    notes: Optional[str] = None

class CalibrationResultCreate(CalibrationResultBase):
    pass

class CalibrationResult(CalibrationResultBase):
    id: int
    task_id: int
    uncertainty_report_url: Optional[str] = None
    fc_evidence_url: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    certificate_url: Optional[str] = None
    created_at: datetime
    
    # M2 MVP fields
    ca_validated_at: Optional[datetime] = None
    ca_validated_by: Optional[str] = None
    ca_validation_rules: Optional[str] = None
    ca_issues: Optional[str] = None
    certificate_pdf_path: Optional[str] = None
    certificate_xml_path: Optional[str] = None

    class Config:
        from_attributes = True

# M2 MVP - New Schemas

class CalibrationPlanData(BaseModel):
    """Data for planning a calibration."""
    procurement_ids: Optional[List[int]] = None
    notes: Optional[str] = None

class CalibrationExecutionData(BaseModel):
    """Data for executing a calibration."""
    execution_date: date
    completion_date: date
    calibration_type: str  # "in-situ" or "ex-situ"
    seal_number: str
    seal_date: date
    seal_location: str
    seal_type: Optional[str] = "Wire"

class CertificateData(BaseModel):
    """Certificate metadata."""
    certificate_number: str
    issue_date: date
    uncertainty: Optional[float] = None
    standard_reading: Optional[float] = None
    equipment_reading: Optional[float] = None

class SealInstallationData(BaseModel):
    """Data for recording a seal installation."""
    tag_id: int
    seal_number: str
    seal_type: str  # "Wire", "Plastic", "Lead"
    seal_location: str
    installation_date: date
    installed_by: str
    removal_reason: Optional[str] = None

class SealHistoryRead(BaseModel):
    """Seal history record."""
    id: int
    tag_id: int
    seal_number: str
    seal_type: str
    seal_location: str
    installation_date: date
    removal_date: Optional[date] = None
    installed_by: str
    removed_by: Optional[str] = None
    removal_reason: Optional[str] = None
    is_active: int
    created_at: datetime

    class Config:
        from_attributes = True
