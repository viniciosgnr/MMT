from sqlalchemy import Column, Integer, String, Date, DateTime, Float, ForeignKey, Enum, Text, Table
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime
import enum

# Enums
class EquipmentStatus(str, enum.Enum):
    ACTIVE = "Active"
    CALIBRATION = "Calibration"
    MAINTENANCE = "Maintenance"
    DECOMMISSIONED = "Decommissioned"

class CampaignStatus(str, enum.Enum):
    PLANNING = "Planning"
    ACTIVE = "Active"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

class CalibrationTaskStatus(str, enum.Enum):
    PENDING = "Pending"
    SCHEDULED = "Scheduled"
    EXECUTED = "Executed"
    OVERDUE = "Overdue"

class CalibrationTaskType(str, enum.Enum):
    CALIBRATION = "Calibration"
    VERIFICATION = "Verification"
    INSPECTION = "Inspection"

class SampleStatus(str, enum.Enum):
    PLAN = "Plan"
    SAMPLE = "Sample"
    DISEMBARK_PREP = "Disembark preparation"
    DISEMBARK_LOGISTICS = "Disembark logistics"
    WAREHOUSE = "Warehouse"
    LOGISTICS_TO_VENDOR = "Logistics to vendor"
    DELIVER_AT_VENDOR = "Deliver at vendor"
    REPORT_ISSUE = "Report issue"
    REPORT_UNDER_VALIDATION = "Report under validation"
    REPORT_APPROVE_REPROVE = "Report approve/reprove"
    FLOW_COMPUTER_UPDATE = "Flow computer update"

class MaintenanceStatus(str, enum.Enum):
    TO_SEND = "To Send"
    AT_VENDOR = "At Vendor"
    RETURNED = "Returned"

class ANPStatus(str, enum.Enum):
    PENDING = "Pending"
    SUBMITTED = "Submitted"
    APPROVED = "Approved"
    REJECTED = "Rejected"

class ANPClassification(str, enum.Enum):
    CRITICAL = "Critical"
    MAJOR = "Major"
    MINOR = "Minor"

class SyncStatusEnum(str, enum.Enum):
    SYNCED = "Synced"
    PENDING = "Pending"
    ERROR = "Error"

class AlertSeverity(str, enum.Enum):
    INFO = "Info"
    WARNING = "Warning"
    CRITICAL = "Critical"

class AlertType(str, enum.Enum):
    CALIBRATION = "Calibration"
    MAINTENANCE = "Maintenance"
    COMPLIANCE = "Compliance"
    SYSTEM = "System"

class ActivityType(str, enum.Enum):
    PLAN_CAL_INS = "Plan Calibration/Inspection"
    EXEC_CAL_INS = "Execute Calibration/Inspection"
    TAKE_SAMPLE = "Take Sample"
    ISSUE_REPORT = "Issue Report"
    ISSUE_CERT = "Issue Certificate"
    ISSUE_UNCERTAINTY = "Issue Uncertainty Calculation"
    UPDATE_FLOW_COMPUTER = "Update Flow Computer"
    CALIBRATION = "Calibration"
    SAMPLING = "Sampling"
    MAINTENANCE = "Maintenance"
    INSPECTION = "Inspection"

class ActivityStatus(str, enum.Enum):
    PLANNED = "Planned"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    MITIGATED = "Mitigated"
    OVERDUE = "Overdue"

# M1 - Equipment Management
class Equipment(Base):
    """Represents a physical device identified by a Serial Number."""
    __tablename__ = "equipments"

    id = Column(Integer, primary_key=True, index=True)
    serial_number = Column(String, unique=True, index=True)
    model = Column(String)
    manufacturer = Column(String, nullable=True)
    equipment_type = Column(String) # Pressure Transmitter, etc.
    specifications = Column(Text, nullable=True) # JSON with technical specs
    status = Column(String, default=EquipmentStatus.ACTIVE.value)
    
    # Calibration parameters
    calibration_frequency_months = Column(Integer, nullable=True)
    calculation_base = Column(String, default="Calibration Date") # Installation Date and/or Calibration Date
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    installations = relationship("EquipmentTagInstallation", back_populates="equipment")
    certificates = relationship("EquipmentCertificate", back_populates="equipment")
    calibration_tasks = relationship("CalibrationTask", back_populates="equipment")
    maintenance_records = relationship("MaintenanceRecord", back_populates="equipment")

meter_sample_link = Table(
    "meter_sample_link",
    Base.metadata,
    Column("meter_id", Integer, ForeignKey("instrument_tags.id"), primary_key=True),
    Column("sample_point_id", Integer, ForeignKey("sample_points.id"), primary_key=True)
)

class InstrumentTag(Base):
    """Represents a logical location/address on the process plant (P&ID Tag)."""
    __tablename__ = "instrument_tags"

    id = Column(Integer, primary_key=True, index=True)
    tag_number = Column(String, unique=True, index=True) # e.g., 62-PT-1101
    description = Column(String)
    area = Column(String, nullable=True)
    service = Column(String, nullable=True)
    classification = Column(String, nullable=True) # Fiscal, Custody Transfer, Operational, etc.
    
    # Hierarchy Link (M11)
    hierarchy_node_id = Column(Integer, ForeignKey("hierarchy_nodes.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    installations = relationship("EquipmentTagInstallation", back_populates="tag")
    # Link to Sample Point (M3 - Many to Many)
    sample_points = relationship("SamplePoint", secondary="meter_sample_link", back_populates="meters")
    seal_history = relationship("SealHistory", back_populates="tag")

class SealHistory(Base):
    """Tracks seal installation and removal history for tags (M2)."""
    __tablename__ = "seal_history"
    
    id = Column(Integer, primary_key=True, index=True)
    tag_id = Column(Integer, ForeignKey("instrument_tags.id"))
    
    seal_number = Column(String, index=True)
    seal_type = Column(String) # "Wire", "Plastic", "Lead"
    seal_location = Column(String) # "Terminal Block", "Transmitter Body", etc.
    
    installation_date = Column(Date)
    removal_date = Column(Date, nullable=True)
    
    installed_by = Column(String)
    removed_by = Column(String, nullable=True)
    removal_reason = Column(String, nullable=True) # "Calibration", "Maintenance", "Damage"
    
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tag = relationship("InstrumentTag", back_populates="seal_history")

class EquipmentTagInstallation(Base):
    """Tracks the history of which Equipment was installed on which Tag."""
    __tablename__ = "equipment_tag_installations"

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipments.id"))
    tag_id = Column(Integer, ForeignKey("instrument_tags.id"))
    
    installation_date = Column(DateTime, default=datetime.utcnow)
    removal_date = Column(DateTime, nullable=True)
    
    installed_by = Column(String)
    installation_report_path = Column(String, nullable=True)
    checklist_data = Column(Text, nullable=True) # JSON evidence
    
    # Status
    is_active = Column(Integer, default=1) # 1 if currently installed

    # Relationships
    equipment = relationship("Equipment", back_populates="installations")
    tag = relationship("InstrumentTag", back_populates="installations")

class EquipmentCertificate(Base):
    """Certificates issued to a Serial Number."""
    __tablename__ = "equipment_certificates"

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipments.id"))
    
    certificate_number = Column(String, index=True)
    issue_date = Column(Date)
    expiry_date = Column(Date, nullable=True)
    certificate_type = Column(String) # Calibration, Material, etc.
    file_path = Column(String)
    
    # Context (may be linked to a tag at issuance)
    tag_id = Column(Integer, ForeignKey("instrument_tags.id"), nullable=True)

    # Relationships
    equipment = relationship("Equipment", back_populates="certificates")

# M2 - Metrological Confirmation
class CalibrationCampaign(Base):
    __tablename__ = "calibration_campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    fpso_name = Column(String)
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    status = Column(String, default=CampaignStatus.PLANNING.value)
    responsible = Column(String)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tasks = relationship("CalibrationTask", back_populates="campaign")

class CalibrationTask(Base):
    __tablename__ = "calibration_tasks"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("calibration_campaigns.id"), nullable=True)
    equipment_id = Column(Integer, ForeignKey("equipments.id"))
    tag = Column(String)  # Denormalized for quick access
    description = Column(String)
    type = Column(String, default=CalibrationTaskType.CALIBRATION.value)
    due_date = Column(Date)
    plan_date = Column(Date, nullable=True)
    exec_date = Column(Date, nullable=True)
    status = Column(String, default=CalibrationTaskStatus.PENDING.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    campaign = relationship("CalibrationCampaign", back_populates="tasks")
    equipment = relationship("Equipment", back_populates="calibration_tasks")
    results = relationship("CalibrationResult", back_populates="task", uselist=False)

    # M2: Metrological Confirmation Fields
    calibration_type = Column(String, nullable=True)  # "in-situ" or "ex-situ"
    temporary_completion_date = Column(Date, nullable=True)
    definitive_completion_date = Column(Date, nullable=True)
    is_temporary = Column(Integer, default=0) # 1 if waiting for definitive documentation

    # Seal information
    seal_number = Column(String, nullable=True)
    seal_installation_date = Column(Date, nullable=True)
    seal_location = Column(String, nullable=True)
    
    # Spare management integration
    spare_procurement_ids = Column(Text, nullable=True) # JSON array

    # Certificate tracking
    certificate_number = Column(String, nullable=True, index=True)
    certificate_issued_date = Column(Date, nullable=True)
    certificate_ca_status = Column(String, nullable=True) # "pending", "approved", "rejected"
    certificate_ca_notes = Column(Text, nullable=True)

class CalibrationResult(Base):
    __tablename__ = "calibration_results"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("calibration_tasks.id"))
    standard_reading = Column(Float)
    equipment_reading = Column(Float)
    uncertainty = Column(Float, nullable=True)
    uncertainty_report_url = Column(String, nullable=True) # PDF for MMT-generated or uploaded uncertainty
    fc_evidence_url = Column(String, nullable=True) # Flow computer screenshot/raw data evidence
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    certificate_url = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # M2: Certificate CA & Storage
    ca_validated_at = Column(DateTime, nullable=True)
    ca_validated_by = Column(String, nullable=True)
    ca_validation_rules = Column(Text, nullable=True) # JSON
    ca_issues = Column(Text, nullable=True) # JSON array
    certificate_pdf_path = Column(String, nullable=True)
    certificate_xml_path = Column(String, nullable=True)

    # Relationships
    task = relationship("CalibrationTask", back_populates="results")

# M3 - Chemical Analysis
class SamplePoint(Base):
    """A physical point where samples are taken. Can be linked to multiple meters."""
    __tablename__ = "sample_points"

    id = Column(Integer, primary_key=True, index=True)
    tag_number = Column(String, unique=True, index=True) # e.g., 62-SP-1101
    description = Column(String)
    fpso_name = Column(String)
    is_operational = Column(Integer, default=1) # Operational vs others (affects SLA)
    sampling_interval_days = Column(Integer, default=30)
    validation_method_implemented = Column(Integer, default=0) # Boolean
    analysis_types = Column(Text, nullable=True) # JSON array of available analysis types
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    meters = relationship("InstrumentTag", secondary="meter_sample_link", back_populates="sample_points")
    samples = relationship("Sample", back_populates="sample_point")

class SamplingCampaign(Base):
    __tablename__ = "sampling_campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    fpso_name = Column(String)
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    status = Column(String, default=CampaignStatus.PLANNING.value)
    responsible = Column(String)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    samples = relationship("Sample", back_populates="campaign")

class Sample(Base):
    __tablename__ = "samples"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("sampling_campaigns.id"), nullable=True)
    sample_point_id = Column(Integer, ForeignKey("sample_points.id"))
    meter_id = Column(Integer, ForeignKey("instrument_tags.id"), nullable=True)
    well_id = Column(Integer, ForeignKey("wells.id"), nullable=True)
    sample_id = Column(String, unique=True, index=True) # Barcode or unique string
    
    # Process Details
    type = Column(String)  # Fiscal, Gas Lift, Poço CG, Poço PVT, Operacional, Óleo - Densidade, Óleo - Enxofre
    category = Column(String, default="Coleta")  # "Coleta" or "Operacional"
    status = Column(String, default=SampleStatus.SAMPLE.value)
    responsible = Column(String)
    osm_id = Column(String, nullable=True)  # Identificação OSM
    laudo_number = Column(String, nullable=True)  # Laudo Nº
    mitigated = Column(Integer, default=0)  # 0=Não, 1=Sim
    validation_party = Column(String, default="Client") # Client or SBM offshore
    is_active = Column(Integer, default=1) # 1=Active, 0=Inactive
    local = Column(String, default="Onshore") # Onshore or Offshore
    
    # SLA Dates — Expected (Previsto) auto-calculated: 10-10-5-5 days
    planned_date = Column(Date, nullable=True)  # Coleta Prevista
    disembark_expected_date = Column(Date, nullable=True)  # Desembarque Previsto (+10d from sampling)
    lab_expected_date = Column(Date, nullable=True)  # Laboratório Previsto (+10d from disembark)
    report_expected_date = Column(Date, nullable=True)  # Laudo Previsto (+5d from lab)
    fc_expected_date = Column(Date, nullable=True)  # CV Previsto (+5d from report)
    
    # SLA Dates — Actual (Realizado)
    sampling_date = Column(Date, nullable=True)  # Coleta Realizado
    disembark_date = Column(Date, nullable=True)  # Desembarque Realizado
    delivery_date = Column(Date, nullable=True)  # Laboratório Realizado
    report_issue_date = Column(Date, nullable=True)  # Laudo Realizado
    fc_update_date = Column(DateTime, nullable=True)  # CV Realizado
    due_date = Column(Date, nullable=True)  # Deadline for the current step
    
    # Results & Validation
    lab_report_url = Column(String, nullable=True)
    validation_status = Column(String, nullable=True) # Approved / Reproved
    validation_report_url = Column(String, nullable=True)
    fc_evidence_url = Column(String, nullable=True)
    
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    campaign = relationship("SamplingCampaign", back_populates="samples")
    sample_point = relationship("SamplePoint", back_populates="samples")
    meter = relationship("InstrumentTag")
    well = relationship("Well")
    results = relationship("SampleResult", back_populates="sample")
    history = relationship("SampleStatusHistory", back_populates="sample")

class SampleStatusHistory(Base):
    """Tracks every status change with specific comments as per spec."""
    __tablename__ = "sample_status_histories"

    id = Column(Integer, primary_key=True, index=True)
    sample_id = Column(Integer, ForeignKey("samples.id"))
    status = Column(String)
    entered_at = Column(DateTime, default=datetime.utcnow)
    comments = Column(Text, nullable=True)
    user = Column(String, nullable=True)

    # Relationships
    sample = relationship("Sample", back_populates="history")

class SampleResult(Base):
    __tablename__ = "sample_results"

    id = Column(Integer, primary_key=True, index=True)
    sample_id = Column(Integer, ForeignKey("samples.id"))
    parameter = Column(String)  # e.g., "density", "rs", "fe", "o2", "density_abs_op", "density_abs_std"
    value = Column(Float)
    unit = Column(String)
    
    # Validation fields (populated by validation engine)
    validation_status = Column(String, nullable=True)   # "pass", "fail", "warning", "insufficient_data"
    validation_detail = Column(String, nullable=True)    # e.g. "Within 2σ range [872.3 – 876.8]"
    history_mean = Column(Float, nullable=True)          # Mean of last 10 samples
    history_std = Column(Float, nullable=True)           # Std deviation of last 10
    source_pdf = Column(String, nullable=True)           # Original PDF filename
    
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    sample = relationship("Sample", back_populates="results")

# M4 - Onshore Maintenance
class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipments.id"))
    tag = Column(String)  # Denormalized
    description = Column(String)
    vendor = Column(String)
    vendor_contact = Column(String, nullable=True)
    sent_date = Column(Date)
    expected_return = Column(Date)
    actual_return = Column(Date, nullable=True)
    status = Column(String, default=MaintenanceStatus.TO_SEND.value)
    reason = Column(String)  # Calibration, Repair, Storage
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    equipment = relationship("Equipment", back_populates="maintenance_records")

# M1 - Installation History (Enhancement)
class InstallationHistory(Base):
    __tablename__ = "installation_history"

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipments.id"))
    fpso_name = Column(String)
    installation_date = Column(DateTime)
    removal_date = Column(DateTime, nullable=True)
    location = Column(String)
    reason = Column(String)  # Installation, Replacement, Maintenance, Removal
    notes = Column(Text, nullable=True)
    installed_by = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    equipment = relationship("Equipment")

# M5 - Synchronization Status & Data Ingestion
class SyncSource(Base):
    __tablename__ = "sync_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True) # e.g., "Cidade de Ilhabela - Omni 6000"
    type = Column(String) # "FLOW_COMPUTER", "AVEVA_PI", "MANUAL_FILE"
    fpso = Column(String, index=True)
    connection_details = Column(Text, nullable=True) # JSON config
    is_active = Column(Integer, default=1)
    
    jobs = relationship("SyncJob", back_populates="source")

class SyncJob(Base):
    __tablename__ = "sync_jobs"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sync_sources.id"))
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    status = Column(String, default=SyncStatusEnum.PENDING.value)
    records_processed = Column(Integer, default=0)
    error_log = Column(Text, nullable=True)
    artifact_path = Column(String, nullable=True) # For manual file dumps

    source = relationship("SyncSource", back_populates="jobs")

class OperationalData(Base):
    """Stores time-series data points from synced sources."""
    __tablename__ = "operational_data"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("sync_jobs.id"))
    tag_number = Column(String, index=True) # e.g. 62-FT-1101
    value = Column(Float)
    timestamp = Column(DateTime, index=True)
    unit = Column(String, nullable=True)
    quality = Column(String, default="Good") # Good, Bad, Uncertain

class SyncStatus(Base):
    """Aggregated status for the dashboard (M1 style)."""
    __tablename__ = "sync_status"

    id = Column(Integer, primary_key=True, index=True)
    module_name = Column(String, index=True)
    last_sync = Column(DateTime)
    status = Column(String, default=SyncStatusEnum.PENDING.value)
    records_synced = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# M6 - Alerts Management
class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, default=AlertType.SYSTEM.value) # e.g., System Configuration, Sampling
    severity = Column(String, default=AlertSeverity.INFO.value)
    title = Column(String)
    message = Column(Text)
    fpso_name = Column(String, index=True)
    tag_number = Column(String, nullable=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipments.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Acknowledgment
    acknowledged = Column(Integer, default=0)
    acknowledged_by = Column(String, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    justification = Column(Text, nullable=True)
    
    # Event Linking
    linked_event_type = Column(String, nullable=True) # e.g., "Failure", "Replacement"
    linked_event_id = Column(Integer, nullable=True)
    
    # Re-check Logic
    run_recheck = Column(Integer, default=1) # Boolean 1/0

class AlertConfiguration(Base):
    """Configuration for alert triggers and recipients per FPSO and Type."""
    __tablename__ = "alert_configurations"

    id = Column(Integer, primary_key=True, index=True)
    fpso_name = Column(String, index=True)
    alert_type = Column(String) # Matching the categories in 6.2
    
    # Thresholds/Parameters (placeholder JSON for now)
    rule_config = Column(Text, nullable=True)
    
    # Notification channels toggle
    notify_email = Column(Integer, default=1)
    notify_whatsapp = Column(Integer, default=0)
    notify_in_app = Column(Integer, default=1)

    recipients = relationship("AlertRecipient", back_populates="config", cascade="all, delete-orphan")

class AlertRecipient(Base):
    """Specific recipients for an AlertConfiguration."""
    __tablename__ = "alert_recipients"

    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("alert_configurations.id"))
    user_name = Column(String)
    email = Column(String, nullable=True)
    whatsapp_number = Column(String, nullable=True)
    receive_in_app = Column(Integer, default=1)

    config = relationship("AlertConfiguration", back_populates="recipients")

# M8 - Planning
class PlannedActivity(Base):
    __tablename__ = "planned_activities"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, default=ActivityType.CALIBRATION.value)
    title = Column(String)
    description = Column(Text, nullable=True)
    equipment_id = Column(Integer, ForeignKey("equipments.id"), nullable=True)
    tag_id = Column(Integer, ForeignKey("instrument_tags.id"), nullable=True)
    fpso_name = Column(String, index=True)
    
    scheduled_date = Column(DateTime)
    completed_at = Column(DateTime, nullable=True)
    duration_hours = Column(Integer, default=1)
    responsible = Column(String)
    status = Column(String, default=ActivityStatus.PLANNED.value)
    
    # Mitigation fields
    mitigation_reason = Column(Text, nullable=True)
    mitigation_attachment_url = Column(String, nullable=True)
    new_due_date = Column(DateTime, nullable=True)
    mitigated_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    equipment = relationship("Equipment")
    tag = relationship("InstrumentTag")

# M9 - Failure Notification (with ANP Compliance)
class FailureNotification(Base):
    __tablename__ = "failure_notifications"

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipments.id"))
    tag = Column(String)  # Denormalized for convenience
    fpso_name = Column(String, index=True)
    
    # Event Details
    failure_date = Column(DateTime)
    restoration_date = Column(DateTime, nullable=True) # End of event
    description = Column(Text)
    impact = Column(String) # High, Medium, Low
    estimated_volume_impact = Column(Float, default=0.0)
    volume_unit = Column(String, default="m3")
    
    # Technical Details
    cause = Column(String, nullable=True)
    corrective_action = Column(Text)
    responsible = Column(String)
    
    # ANP Compliance Fields
    anp_notification_number = Column(String, unique=True, nullable=True, index=True)
    anp_classification = Column(String, nullable=True)  # Critica, Grave, Toleravel (per Res 18/14)
    anp_deadline = Column(DateTime, nullable=True)
    anp_submitted_date = Column(DateTime, nullable=True)
    
    # Approval Workflow
    status = Column(String, default="Draft") # Draft, Awaiting Approval, Approved, Submitted
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Legacy field alignment
    anp_status = Column(String, default=ANPStatus.PENDING.value)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    equipment = relationship("Equipment")

class FPSOFailureEmailList(Base):
    __tablename__ = "fpso_failure_email_lists"
    
    id = Column(Integer, primary_key=True, index=True)
    fpso_name = Column(String, index=True)
    email = Column(String)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

# M10 - Historical Report Module
class ReportType(Base):
    __tablename__ = "report_types"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True) # e.g., Offloading Report, ANP Letter
    description = Column(String, nullable=True)
    is_active = Column(Integer, default=1)

class HistoricalReport(Base):
    __tablename__ = "historical_reports"
    id = Column(Integer, primary_key=True, index=True)
    report_type_id = Column(Integer, ForeignKey("report_types.id"))
    title = Column(String)
    file_url = Column(String)
    file_name = Column(String)
    file_size = Column(Integer) # in bytes
    report_date = Column(DateTime)
    
    # Metadata and Links (Optional)
    fpso_name = Column(String, index=True, nullable=True)
    metering_system = Column(String, nullable=True) # e.g., Gas Export
    serial_number = Column(String, nullable=True)
    
    # Tracking
    uploaded_by = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    report_type = relationship("ReportType")

# M11 - Configuration Module (System Modeling)
class HierarchyLevel(str, enum.Enum):
    FPSO = "FPSO"
    SYSTEM = "System"
    VARIABLE = "Variable"
    DEVICE = "Device"

class AttributeType(str, enum.Enum):
    TEXT = "Text"
    DATE = "Date"
    NUMERICAL = "Numerical"
    CHOICE = "Multiple Choice"

class HierarchyNode(Base):
    __tablename__ = "hierarchy_nodes"

    id = Column(Integer, primary_key=True, index=True)
    tag = Column(String, index=True)
    description = Column(String)
    level_type = Column(String)  # FPSO, System, Variable, Device
    parent_id = Column(Integer, ForeignKey("hierarchy_nodes.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AttributeDefinition(Base):
    __tablename__ = "attribute_definitions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    type = Column(String)  # Text, Date, Numerical, Choice
    unit = Column(String, nullable=True)
    validation_rules = Column(Text, nullable=True)  # JSON field for rules
    entity_type = Column(String)  # METERING_SYSTEM, DEVICE_TYPE
    created_at = Column(DateTime, default=datetime.utcnow)

class AttributeValue(Base):
    __tablename__ = "attribute_values"

    id = Column(Integer, primary_key=True, index=True)
    attribute_id = Column(Integer, ForeignKey("attribute_definitions.id"))
    entity_id = Column(Integer, index=True)  # ID of the HierarchyNode or specific record
    value = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Well(Base):
    __tablename__ = "wells"
    id = Column(Integer, primary_key=True, index=True)
    tag = Column(String, index=True)
    description = Column(String, nullable=True)
    fpso = Column(String, index=True)
    
    # --- New Fields for M11 Configurations ---
    anp_code = Column(String, index=True, nullable=True)
    sbm_code = Column(String, index=True, nullable=True)
    sample_point_gas = Column(String, nullable=True) 
    sample_point_oil = Column(String, nullable=True)
    status = Column(String, default="Active") # Active / Inactive
    
    created_at = Column(DateTime, default=datetime.utcnow)

class Holiday(Base):
    __tablename__ = "holidays"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    description = Column(String)
    fpso = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class StockLocation(Base):
    __tablename__ = "stock_locations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    fpso = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ConfigParameter(Base):
    __tablename__ = "config_parameters"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, index=True) # e.g. "pressure_transmitter_cal_freq"
    value = Column(String)
    fpso = Column(String, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
# M4 - Onshore Maintenance Kanban
class MaintenanceColumn(Base):
    __tablename__ = "maintenance_columns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    order = Column(Integer, default=0)
    
    cards = relationship("MaintenanceCard", back_populates="column")

class MaintenanceLabel(Base):
    __tablename__ = "maintenance_labels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    color = Column(String, default="#CBD5E1") # Tailwind slate-300

# Association Tables
card_label_association = Table(
    "card_label_association",
    Base.metadata,
    Column("card_id", Integer, ForeignKey("maintenance_cards.id"), primary_key=True),
    Column("label_id", Integer, ForeignKey("maintenance_labels.id"), primary_key=True)
)

card_connection_association = Table(
    "card_connection_association",
    Base.metadata,
    Column("card_id", Integer, ForeignKey("maintenance_cards.id"), primary_key=True),
    Column("connected_card_id", Integer, ForeignKey("maintenance_cards.id"), primary_key=True)
)

card_equipment_association = Table(
    "card_equipment_association",
    Base.metadata,
    Column("card_id", Integer, ForeignKey("maintenance_cards.id"), primary_key=True),
    Column("equipment_id", Integer, ForeignKey("equipments.id"), primary_key=True)
)

card_tag_association = Table(
    "card_tag_association",
    Base.metadata,
    Column("card_id", Integer, ForeignKey("maintenance_cards.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("instrument_tags.id"), primary_key=True)
)

class MaintenanceCard(Base):
    __tablename__ = "maintenance_cards"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    fpso = Column(String, index=True)
    status = Column(String, default="Not Completed") # "Completed" or "Not Completed"
    due_date = Column(DateTime, nullable=True)
    responsible = Column(String, nullable=True) # Semi-colon separated or multi-link? Simple string for now.
    
    column_id = Column(Integer, ForeignKey("maintenance_columns.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    column = relationship("MaintenanceColumn", back_populates="cards")
    labels = relationship("MaintenanceLabel", secondary=card_label_association)
    comments = relationship("MaintenanceComment", back_populates="card", cascade="all, delete-orphan")
    attachments = relationship("MaintenanceAttachment", back_populates="card", cascade="all, delete-orphan")
    
    # Self-referential connections
    connections = relationship(
        "MaintenanceCard",
        secondary=card_connection_association,
        primaryjoin=id == card_connection_association.c.card_id,
        secondaryjoin=id == card_connection_association.c.connected_card_id,
        backref="connected_to"
    )
    
    # Equipment Links
    linked_equipments = relationship("Equipment", secondary=card_equipment_association)
    linked_tags = relationship("InstrumentTag", secondary=card_tag_association)

class MaintenanceComment(Base):
    __tablename__ = "maintenance_comments"

    id = Column(Integer, primary_key=True, index=True)
    card_id = Column(Integer, ForeignKey("maintenance_cards.id"))
    text = Column(Text)
    author = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    card = relationship("MaintenanceCard", back_populates="comments")

class MaintenanceAttachment(Base):
    __tablename__ = "maintenance_attachments"

    id = Column(Integer, primary_key=True, index=True)
    card_id = Column(Integer, ForeignKey("maintenance_cards.id"))
    file_name = Column(String)
    file_path = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    card = relationship("MaintenanceCard", back_populates="attachments")
