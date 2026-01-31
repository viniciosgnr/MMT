from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# M9 - Failure Notification Schemas

class FailureNotificationBase(BaseModel):
    equipment_id: Optional[int] = None
    tag: str
    fpso_name: str
    failure_date: datetime
    restoration_date: Optional[datetime] = None
    description: str
    impact: str
    estimated_volume_impact: float = 0.0
    volume_unit: str = "m3"
    cause: Optional[str] = None
    corrective_action: str
    responsible: str
    anp_notification_number: Optional[str] = None
    anp_classification: Optional[str] = None
    anp_deadline: Optional[datetime] = None

class FailureNotificationCreate(FailureNotificationBase):
    pass

class FailureNotificationUpdate(BaseModel):
    restoration_date: Optional[datetime] = None
    description: Optional[str] = None
    impact: Optional[str] = None
    estimated_volume_impact: Optional[float] = None
    cause: Optional[str] = None
    corrective_action: Optional[str] = None
    anp_status: Optional[str] = None
    anp_submitted_date: Optional[datetime] = None
    status: Optional[str] = None

class FailureNotificationApproval(BaseModel):
    approved_by: str

class FailureNotification(FailureNotificationBase):
    id: int
    status: str
    anp_status: str
    anp_submitted_date: Optional[datetime] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Email List Schemas
class FPSOFailureEmailListBase(BaseModel):
    fpso_name: str
    email: str
    is_active: int = 1

class FPSOFailureEmailListCreate(FPSOFailureEmailListBase):
    pass

class FPSOFailureEmailList(FPSOFailureEmailListBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

# M1 - Installation History Schemas

class InstallationHistoryBase(BaseModel):
    equipment_id: int
    fpso_name: str
    installation_date: datetime
    removal_date: Optional[datetime] = None
    location: str
    reason: str
    notes: Optional[str] = None
    installed_by: str

class InstallationHistoryCreate(InstallationHistoryBase):
    pass

class InstallationHistory(InstallationHistoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# M5 - Sync Status Schemas

class SyncStatusBase(BaseModel):
    module_name: str
    last_sync: datetime
    status: str
    records_synced: int = 0
    error_message: Optional[str] = None

class SyncStatusCreate(SyncStatusBase):
    pass

class SyncStatus(SyncStatusBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# M5 - Advanced Sync Schemas
class SyncSourceBase(BaseModel):
    name: str
    type: str # FLOW_COMPUTER, AVEVA_PI, MANUAL_FILE
    fpso: str
    connection_details: Optional[str] = None
    is_active: int = 1

class SyncSourceCreate(SyncSourceBase):
    pass

class SyncSource(SyncSourceBase):
    id: int
    class Config:
        from_attributes = True

class SyncJobBase(BaseModel):
    source_id: int
    status: str
    records_processed: int = 0
    error_log: Optional[str] = None

class SyncJobCreate(SyncJobBase):
    start_time: Optional[datetime] = None

class SyncJob(SyncJobBase):
    id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    class Config:
        from_attributes = True

class OperationalDataIngest(BaseModel):
    tag_number: str
    value: float
    timestamp: datetime
    unit: Optional[str] = None
    quality: Optional[str] = "Good"

class DataIngestionPayload(BaseModel):
    source_id: int
    data: list[OperationalDataIngest]

# M6 - Alert Schemas

class AlertBase(BaseModel):
    type: str
    severity: str
    title: str
    message: str
    equipment_id: Optional[int] = None

class AlertCreate(AlertBase):
    pass

class AlertAcknowledge(BaseModel):
    acknowledged_by: str

class Alert(AlertBase):
    id: int
    created_at: datetime
    acknowledged: int
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# M8 - Planning Schemas

class PlannedActivityBase(BaseModel):
    type: str
    title: str
    description: Optional[str] = None
    equipment_id: Optional[int] = None
    tag_id: Optional[int] = None
    fpso_name: str
    scheduled_date: datetime
    duration_hours: int = 1
    responsible: str
    status: str = "Planned"

class PlannedActivityCreate(PlannedActivityBase):
    pass

class PlannedActivityUpdate(BaseModel):
    status: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    mitigation_reason: Optional[str] = None
    mitigation_attachment_url: Optional[str] = None
    new_due_date: Optional[datetime] = None

class PlannedActivityMitigate(BaseModel):
    reason: str
    attachment_url: Optional[str] = None
    new_due_date: datetime

class PlannedActivity(PlannedActivityBase):
    id: int
    completed_at: Optional[datetime] = None
    mitigation_reason: Optional[str] = None
    mitigation_attachment_url: Optional[str] = None
    new_due_date: Optional[datetime] = None
    mitigated_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

# M10 - Historical Report Schemas
class ReportTypeBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: int = 1

class ReportTypeCreate(ReportTypeBase):
    pass

class ReportType(ReportTypeBase):
    id: int
    class Config:
        from_attributes = True

class HistoricalReportBase(BaseModel):
    report_type_id: int
    title: str
    report_date: datetime
    fpso_name: Optional[str] = None
    metering_system: Optional[str] = None
    serial_number: Optional[str] = None

class HistoricalReportCreate(HistoricalReportBase):
    pass

class HistoricalReport(HistoricalReportBase):
    id: int
    file_url: str
    file_name: str
    file_size: int
    uploaded_by: str
    uploaded_at: datetime
    report_type: ReportType

    class Config:
        from_attributes = True
