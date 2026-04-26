"""
Configuration Router — M11 Asset Hierarchy & Rules.

Harness Engineering: Router layer delegates all business logic to services.
Skills Applied:
- backend-dev-guidelines → Routes only validate auth and call Services
- architecture-patterns → Clean Architecture separation
"""

import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import models, database
from ..schemas import configuration as schemas
from ..dependencies import get_current_user, get_current_user_fpso
from ..services.hierarchy_service import get_hierarchy_tree
from ..services.validation_service import ValidationService

router = APIRouter(
    prefix="/api/config",
    tags=["configuration"],
)

# --- Hierarchy Management ---

@router.get("/hierarchy/tree", response_model=List[schemas.HierarchyNodeWithChildren])
def get_tree(
    db: Session = Depends(database.get_db),
    auth_context: dict = Depends(get_current_user_fpso)
):
    """Get the full FPSO hierarchy tree. Delegated to HierarchyService."""
    # Currently passed to service if we had fpso scoping there.
    # Service will tackle dynamic FPSO loading in Phase 3.
    return get_hierarchy_tree(db)

@router.get("/hierarchy/nodes", response_model=List[schemas.HierarchyNode])
def get_hierarchy_nodes(db: Session = Depends(database.get_db)):
    return db.query(models.HierarchyNode).all()

@router.post("/hierarchy/nodes", response_model=schemas.HierarchyNode)
def create_hierarchy_node(
    node: schemas.HierarchyNodeCreate,
    db: Session = Depends(database.get_db),
    current_user=Depends(get_current_user),
):
    if node.level_type == "Metering Point":
        classification = node.attributes.get("classification") if node.attributes else None
        m = models.InstrumentTag(
            tag_number=node.tag,
            description=node.description,
            classification=classification,
        )
        db.add(m)
        db.commit()
        db.refresh(m)
        return {
            "id": m.id + 20000,
            "tag": m.tag_number,
            "description": m.description,
            "level_type": "Metering Point",
            "created_at": m.created_at,
            "parent_id": node.parent_id,
            "attributes": {"classification": m.classification},
        }

    elif node.level_type == "Sample Point":
        # Legacy logic — import via seed scripts
        pass

    else:
        data = node.model_dump()
        if "attributes" in data:
            del data["attributes"]
        db_node = models.HierarchyNode(**data)
        db.add(db_node)
        db.commit()
        db.refresh(db_node)
        return db_node

@router.put("/hierarchy/nodes/{node_id}", response_model=schemas.HierarchyNode)
def update_hierarchy_node(
    node_id: int,
    node_update: schemas.HierarchyNodeBase,
    db: Session = Depends(database.get_db),
    current_user=Depends(get_current_user),
):
    db_node = db.query(models.HierarchyNode).filter(models.HierarchyNode.id == node_id).first()
    if not db_node:
        raise HTTPException(status_code=404, detail="Node not found")

    update_data = node_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_node, key, value)

    db.commit()
    db.refresh(db_node)
    return db_node

@router.delete("/hierarchy/nodes/{node_id}")
def delete_hierarchy_node(
    node_id: int,
    db: Session = Depends(database.get_db),
    current_user=Depends(get_current_user),
):
    db_node = db.query(models.HierarchyNode).filter(models.HierarchyNode.id == node_id).first()
    if not db_node:
        raise HTTPException(status_code=404, detail="Node not found")

    has_children = db.query(models.HierarchyNode).filter(
        models.HierarchyNode.parent_id == node_id
    ).first()
    if has_children:
        raise HTTPException(status_code=400, detail="Cannot delete node with children")

    db.delete(db_node)
    db.commit()
    return {"status": "success", "message": "Node deleted successfully"}

# --- Dynamic Attributes ---

@router.get("/attributes", response_model=List[schemas.AttributeDefinition])
def get_attributes(
    entity_type: Optional[str] = None, 
    db: Session = Depends(database.get_db),
    auth_context: dict = Depends(get_current_user_fpso)
):
    query = db.query(models.AttributeDefinition)
    if entity_type:
        query = query.filter(models.AttributeDefinition.entity_type == entity_type)
    return query.all()

@router.post("/attributes", response_model=schemas.AttributeDefinition)
def create_attribute_definition(
    attr: schemas.AttributeDefinitionCreate,
    db: Session = Depends(database.get_db),
    current_user=Depends(get_current_user),
):
    data = attr.model_dump()

    if attr.validation_rules:
        if hasattr(attr.validation_rules, "model_dump"):
            data["validation_rules"] = json.dumps(attr.validation_rules.model_dump())
        else:
            data["validation_rules"] = json.dumps(attr.validation_rules)

    db_attr = models.AttributeDefinition(**data)
    db.add(db_attr)
    db.commit()
    db.refresh(db_attr)
    return db_attr

@router.get("/values/{entity_id}", response_model=List[schemas.AttributeValue])
def get_attribute_values(entity_id: int, db: Session = Depends(database.get_db)):
    return db.query(models.AttributeValue).filter(
        models.AttributeValue.entity_id == entity_id
    ).all()

@router.post("/values", response_model=schemas.AttributeValue)
def set_attribute_value(
    val: schemas.AttributeValueCreate,
    db: Session = Depends(database.get_db),
    current_user=Depends(get_current_user),
):
    definition = db.query(models.AttributeDefinition).filter(
        models.AttributeDefinition.id == val.attribute_id
    ).first()
    if not definition:
        raise HTTPException(status_code=404, detail="Attribute definition not found")

    try:
        ValidationService.validate_attribute_value(definition, val.value)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    db_val = db.query(models.AttributeValue).filter(
        models.AttributeValue.attribute_id == val.attribute_id,
        models.AttributeValue.entity_id == val.entity_id,
    ).first()

    if db_val:
        db_val.value = val.value
    else:
        db_val = models.AttributeValue(**val.model_dump())
        db.add(db_val)

    db.commit()
    db.refresh(db_val)
    return db_val

# --- Specialized Configurations ---

@router.get("/wells", response_model=List[schemas.Well])
def get_wells(
    fpso: Optional[str] = None,
    skip: int = 0,
    limit: int = 1000,
    db: Session = Depends(database.get_db),
):
    query = db.query(models.Well)
    if fpso:
        code = fpso.split(" - ")[0].strip() if " - " in fpso else fpso
        query = query.filter(models.Well.fpso.ilike(f"%{code}%"))
    return query.offset(skip).limit(limit).all()

@router.post("/wells", response_model=schemas.Well)
def create_well(
    well: schemas.WellCreate,
    db: Session = Depends(database.get_db),
    current_user=Depends(get_current_user),
):
    db_well = models.Well(**well.model_dump())
    db.add(db_well)
    db.commit()
    db.refresh(db_well)
    return db_well

@router.put("/wells/{well_id}", response_model=schemas.Well)
def update_well(
    well_id: int,
    well: schemas.WellUpdate,
    db: Session = Depends(database.get_db),
    current_user=Depends(get_current_user),
):
    db_well = db.query(models.Well).filter(models.Well.id == well_id).first()
    if not db_well:
        raise HTTPException(status_code=404, detail="Well not found")

    update_data = well.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_well, key, value)

    db.commit()
    db.refresh(db_well)
    return db_well

@router.delete("/wells/{well_id}")
def delete_well(
    well_id: int,
    db: Session = Depends(database.get_db),
    current_user=Depends(get_current_user),
):
    db_well = db.query(models.Well).filter(models.Well.id == well_id).first()
    if not db_well:
        raise HTTPException(status_code=404, detail="Well not found")
    db.delete(db_well)
    db.commit()
    return {"status": "success", "message": "Well deleted successfully"}

@router.get("/holidays", response_model=List[schemas.Holiday])
def get_holidays(
    fpso: Optional[str] = None,
    skip: int = 0,
    limit: int = 1000,
    db: Session = Depends(database.get_db),
):
    query = db.query(models.Holiday)
    if fpso:
        query = query.filter(models.Holiday.fpso == fpso)
    return query.offset(skip).limit(limit).all()

@router.post("/holidays", response_model=schemas.Holiday)
def create_holiday(
    holiday: schemas.HolidayCreate,
    db: Session = Depends(database.get_db),
    current_user=Depends(get_current_user),
):
    db_holiday = models.Holiday(**holiday.model_dump())
    db.add(db_holiday)
    db.commit()
    db.refresh(db_holiday)
    return db_holiday

@router.get("/stock-locations", response_model=List[schemas.StockLocation])
def get_stock_locations(
    fpso: Optional[str] = None,
    skip: int = 0,
    limit: int = 1000,
    db: Session = Depends(database.get_db),
):
    query = db.query(models.StockLocation)
    if fpso:
        query = query.filter(models.StockLocation.fpso == fpso)
    return query.offset(skip).limit(limit).all()

@router.post("/stock-locations", response_model=schemas.StockLocation)
def create_stock_location(
    loc: schemas.StockLocationCreate,
    db: Session = Depends(database.get_db),
    current_user=Depends(get_current_user),
):
    db_loc = models.StockLocation(**loc.model_dump())
    db.add(db_loc)
    db.commit()
    db.refresh(db_loc)
    return db_loc

@router.get("/parameters", response_model=List[schemas.ConfigParameter])
def get_parameters(
    fpso: Optional[str] = None,
    skip: int = 0,
    limit: int = 1000,
    db: Session = Depends(database.get_db),
):
    query = db.query(models.ConfigParameter)
    if fpso:
        query = query.filter(models.ConfigParameter.fpso == fpso)
    return query.offset(skip).limit(limit).all()

@router.post("/parameters", response_model=schemas.ConfigParameter)
def set_parameter(
    param: schemas.ConfigParameterCreate,
    db: Session = Depends(database.get_db),
    current_user=Depends(get_current_user),
):
    db_param = db.query(models.ConfigParameter).filter(
        models.ConfigParameter.key == param.key,
        models.ConfigParameter.fpso == param.fpso,
    ).first()

    if db_param:
        db_param.value = param.value
        db_param.description = param.description
    else:
        db_param = models.ConfigParameter(**param.model_dump())
        db.add(db_param)

    db.commit()
    db.refresh(db_param)
    return db_param
