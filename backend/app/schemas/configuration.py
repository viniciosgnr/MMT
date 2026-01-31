from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class HierarchyNodeBase(BaseModel):
    tag: str
    description: str
    level_type: str
    parent_id: Optional[int] = None

class HierarchyNodeCreate(HierarchyNodeBase):
    pass

class HierarchyNode(HierarchyNodeBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class AttributeDefinitionBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: str # Text, Date, Numerical, Choice
    unit: Optional[str] = None
    validation_rules: Optional[str] = None
    entity_type: str # METERING_SYSTEM, DEVICE_TYPE

class AttributeDefinitionCreate(AttributeDefinitionBase):
    pass

class AttributeDefinition(AttributeDefinitionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class AttributeValueBase(BaseModel):
    attribute_id: int
    entity_id: int
    value: str

class AttributeValueCreate(AttributeValueBase):
    pass

class AttributeValue(AttributeValueBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class HierarchyNodeWithChildren(HierarchyNode):
    children: List["HierarchyNodeWithChildren"] = []

HierarchyNodeWithChildren.model_rebuild()

class WellBase(BaseModel):
    tag: str
    description: Optional[str] = None
    fpso: str

class WellCreate(WellBase):
    pass

class Well(WellBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class HolidayBase(BaseModel):
    date: datetime
    description: str
    fpso: str

class HolidayCreate(HolidayBase):
    pass

class Holiday(HolidayBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class StockLocationBase(BaseModel):
    name: str
    description: Optional[str] = None
    fpso: str

class StockLocationCreate(StockLocationBase):
    pass

class StockLocation(StockLocationBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class ConfigParameterBase(BaseModel):
    key: str
    value: str
    fpso: str
    description: Optional[str] = None

class ConfigParameterCreate(ConfigParameterBase):
    pass

class ConfigParameter(ConfigParameterBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True
