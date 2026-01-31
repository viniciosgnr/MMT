from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from enum import Enum

class EquipmentStatus(str, Enum):
    ACTIVE = "Active"
    MAINTENANCE = "Maintenance"
    INACTIVE = "Inactive"

class CalibrationStatus(str, Enum):
    PENDING = "Pending"
    SCHEDULED = "Scheduled"
    EXECUTED = "Executed"
    OVERDUE = "Overdue"

class EquipmentBase(BaseModel):
    serial_number: str
    model: str
    manufacturer: Optional[str] = None
    equipment_type: str
    specifications: Optional[str] = None
    status: str = "Active"
    calibration_frequency_months: Optional[int] = None
    calculation_base: str = "Calibration Date"

class EquipmentCreate(EquipmentBase):
    pass

class Equipment(EquipmentBase):
    id: int
    created_at: datetime
    certificates: List["EquipmentCertificate"] = []

    class Config:
        from_attributes = True

class InstrumentTagBase(BaseModel):
    tag_number: str
    description: str
    area: Optional[str] = None
    service: Optional[str] = None
    hierarchy_node_id: Optional[int] = None

class InstrumentTagCreate(InstrumentTagBase):
    pass

class InstrumentTag(InstrumentTagBase):
    id: int
    created_at: datetime
    installations: List["EquipmentTagInstallation"] = []

    class Config:
        from_attributes = True

class EquipmentTagInstallationBase(BaseModel):
    equipment_id: int
    tag_id: int
    installed_by: str
    installation_report_path: Optional[str] = None
    checklist_data: Optional[str] = None

class EquipmentTagInstallationCreate(EquipmentTagInstallationBase):
    installation_date: Optional[datetime] = None

class EquipmentTagInstallation(EquipmentTagInstallationBase):
    id: int
    installation_date: datetime
    removal_date: Optional[datetime] = None
    is_active: int
    equipment: Optional["Equipment"] = None

    class Config:
        from_attributes = True

class EquipmentCertificateBase(BaseModel):
    equipment_id: int
    certificate_number: str
    issue_date: date
    expiry_date: Optional[date] = None
    certificate_type: Optional[str] = None
    file_path: Optional[str] = None
    tag_id: Optional[int] = None

class EquipmentCertificateCreate(EquipmentCertificateBase):
    pass

class EquipmentCertificate(EquipmentCertificateBase):
    id: int

    class Config:
        from_attributes = True

class CalibrationBase(BaseModel):
    equipment_id: int
    due_date: date
    planned_date: Optional[date] = None
    status: CalibrationStatus = CalibrationStatus.PENDING

class CalibrationCreate(CalibrationBase):
    pass

class Calibration(CalibrationBase):
    id: int
    certificate_url: Optional[str] = None

    class Config:
        from_attributes = True
# Maintenance Kanban
class MaintenanceColumnBase(BaseModel):
    name: str
    order: int = 0

class MaintenanceColumnCreate(MaintenanceColumnBase):
    pass

class MaintenanceColumn(MaintenanceColumnBase):
    id: int
    class Config:
        from_attributes = True

class MaintenanceLabelBase(BaseModel):
    name: str
    color: str = "#CBD5E1"

class MaintenanceLabelCreate(MaintenanceLabelBase):
    pass

class MaintenanceLabel(MaintenanceLabelBase):
    id: int
    class Config:
        from_attributes = True

class MaintenanceCommentBase(BaseModel):
    text: str
    author: str

class MaintenanceCommentCreate(MaintenanceCommentBase):
    pass

class MaintenanceComment(MaintenanceCommentBase):
    id: int
    card_id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class MaintenanceAttachmentBase(BaseModel):
    file_name: str
    file_path: str

class MaintenanceAttachmentCreate(MaintenanceAttachmentBase):
    pass

class MaintenanceAttachment(MaintenanceAttachmentBase):
    id: int
    card_id: int
    uploaded_at: datetime
    class Config:
        from_attributes = True

class MaintenanceCardBase(BaseModel):
    title: str
    description: Optional[str] = None
    fpso: str
    status: str = "Not Completed"
    due_date: Optional[datetime] = None
    responsible: Optional[str] = None
    column_id: int

class MaintenanceCardCreate(MaintenanceCardBase):
    label_ids: List[int] = []
    connected_card_ids: List[int] = []
    equipment_ids: List[int] = []
    tag_ids: List[int] = []

class MaintenanceCard(MaintenanceCardBase):
    id: int
    created_at: datetime
    labels: List[MaintenanceLabel] = []
    comments: List[MaintenanceComment] = []
    attachments: List[MaintenanceAttachment] = []
    connections: List["MaintenanceCard"] = []
    linked_equipments: List[Equipment] = []
    linked_tags: List[InstrumentTag] = []

    class Config:
        from_attributes = True
