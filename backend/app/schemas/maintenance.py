from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

class MaintenanceRecordBase(BaseModel):
    tag: str
    description: str
    vendor: str
    vendor_contact: Optional[str] = None
    sent_date: date
    expected_return: date
    reason: str
    notes: Optional[str] = None

class MaintenanceRecordCreate(MaintenanceRecordBase):
    equipment_id: int

class MaintenanceRecordUpdate(BaseModel):
    status: Optional[str] = None
    actual_return: Optional[date] = None
    notes: Optional[str] = None

class MaintenanceRecord(MaintenanceRecordBase):
    id: int
    equipment_id: int
    actual_return: Optional[date]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
