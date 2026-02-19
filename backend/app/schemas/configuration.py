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

from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import List, Optional, Union, Dict, Any

class AttributeTypeEnum(str, Enum):
    TEXT = "Text"
    DATE = "Date"
    NUMERICAL = "Numerical"
    CHOICE = "Multiple Choice"

class NumericalRules(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None

class TextRules(BaseModel):
    min_length: Optional[int] = None
    regex: Optional[str] = None

class AttributeDefinitionBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: AttributeTypeEnum
    unit: Optional[str] = None
    validation_rules: Optional[Union[NumericalRules, TextRules, Dict[str, Any]]] = None # Can be specific model or generic dict
    entity_type: str # METERING_SYSTEM, DEVICE_TYPE

class AttributeDefinitionCreate(AttributeDefinitionBase):
    pass

class AttributeDefinition(AttributeDefinitionBase):
    id: int
    created_at: datetime
    
    # Validator to parse JSON string from DB
    @field_validator('validation_rules', mode='before')
    @classmethod
    def parse_validation_rules(cls, v):
        if isinstance(v, str) and v.strip():
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {} # Fallback
        return v
    
    # Validator to handle Legacy DB values for Enum
    @field_validator('type', mode='before')
    @classmethod
    def parse_legacy_type(cls, v):
        if v == "Choice":
            return "Multiple Choice"
        return v
    
    model_config = ConfigDict(from_attributes=True)


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
