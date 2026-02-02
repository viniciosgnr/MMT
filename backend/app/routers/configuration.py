from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, database
from ..schemas import configuration as schemas
from ..dependencies import get_current_user

router = APIRouter(
    prefix="/api/config",
    tags=["configuration"],
)

# --- Hierarchy Management ---

@router.get("/hierarchy/tree", response_model=List[schemas.HierarchyNodeWithChildren])
def get_hierarchy_tree(db: Session = Depends(database.get_db)):
    # Fetch all nodes
    all_nodes = db.query(models.HierarchyNode).all()
    
    # Build tree structure
    node_map = {node.id: schemas.HierarchyNodeWithChildren.from_orm(node) for node in all_nodes}
    tree = []
    
    for node_id, node_obj in node_map.items():
        if node_obj.parent_id is None:
            tree.append(node_obj)
        else:
            parent = node_map.get(node_obj.parent_id)
            if parent:
                if not hasattr(parent, 'children'):
                    parent.children = []
                parent.children.append(node_obj)
                
    return tree

@router.post("/hierarchy/nodes", response_model=schemas.HierarchyNode)
def create_hierarchy_node(node: schemas.HierarchyNodeCreate, db: Session = Depends(database.get_db), current_user = Depends(get_current_user)):
    db_node = models.HierarchyNode(**node.model_dump())
    db.add(db_node)
    db.commit()
    db.refresh(db_node)
    return db_node

@router.delete("/hierarchy/nodes/{node_id}")
def delete_hierarchy_node(node_id: int, db: Session = Depends(database.get_db), current_user = Depends(get_current_user)):
    db_node = db.query(models.HierarchyNode).filter(models.HierarchyNode.id == node_id).first()
    if not db_node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    # Check for children
    has_children = db.query(models.HierarchyNode).filter(models.HierarchyNode.parent_id == node_id).first()
    if has_children:
        raise HTTPException(status_code=400, detail="Cannot delete node with children")
        
    db.delete(db_node)
    db.commit()
    return {"status": "success"}

# --- Dynamic Attributes ---

@router.get("/attributes", response_model=List[schemas.AttributeDefinition])
def get_attributes(entity_type: Optional[str] = None, db: Session = Depends(database.get_db)):
    query = db.query(models.AttributeDefinition)
    if entity_type:
        query = query.filter(models.AttributeDefinition.entity_type == entity_type)
    return query.all()

@router.post("/attributes", response_model=schemas.AttributeDefinition)
def create_attribute_definition(attr: schemas.AttributeDefinitionCreate, db: Session = Depends(database.get_db), current_user = Depends(get_current_user)):
    db_attr = models.AttributeDefinition(**attr.model_dump())
    db.add(db_attr)
    db.commit()
    db.refresh(db_attr)
    return db_attr

@router.get("/values/{entity_id}", response_model=List[schemas.AttributeValue])
def get_attribute_values(entity_id: int, db: Session = Depends(database.get_db)):
    return db.query(models.AttributeValue).filter(models.AttributeValue.entity_id == entity_id).all()

@router.post("/values", response_model=schemas.AttributeValue)
def set_attribute_value(val: schemas.AttributeValueCreate, db: Session = Depends(database.get_db), current_user = Depends(get_current_user)):
    # 1. Fetch Definition
    definition = db.query(models.AttributeDefinition).filter(models.AttributeDefinition.id == val.attribute_id).first()
    if not definition:
        raise HTTPException(status_code=404, detail="Attribute definition not found")

    # 2. Dynamic Validation
    import json
    if definition.validation_rules:
        try:
            rules = json.loads(definition.validation_rules)
            
            # Numerical Validation
            if definition.type == "Numerical":
                try:
                    num_val = float(val.value)
                    if "min" in rules and num_val < rules["min"]:
                        raise HTTPException(status_code=400, detail=f"Value {num_val} is below minimum {rules['min']}")
                    if "max" in rules and num_val > rules["max"]:
                        raise HTTPException(status_code=400, detail=f"Value {num_val} is above maximum {rules['max']}")
                except ValueError:
                    raise HTTPException(status_code=400, detail="Value must be numerical")
            
            # Text Validation (Regex/Length)
            if definition.type == "Text":
                if "min_length" in rules and len(val.value) < rules["min_length"]:
                    raise HTTPException(status_code=400, detail=f"Text too short (min {rules['min_length']})")
                if "regex" in rules:
                    import re
                    if not re.match(rules["regex"], val.value):
                        raise HTTPException(status_code=400, detail="Value does not match required format")

        except json.JSONDecodeError:
            pass # Ignore malformed rules for now or log them

    # 3. Save Value
    db_val = db.query(models.AttributeValue).filter(
        models.AttributeValue.attribute_id == val.attribute_id,
        models.AttributeValue.entity_id == val.entity_id
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
def get_wells(fpso: Optional[str] = None, db: Session = Depends(database.get_db)):
    query = db.query(models.Well)
    if fpso:
        query = query.filter(models.Well.fpso == fpso)
    return query.all()

@router.post("/wells", response_model=schemas.Well)
def create_well(well: schemas.WellCreate, db: Session = Depends(database.get_db), current_user = Depends(get_current_user)):
    db_well = models.Well(**well.model_dump())
    db.add(db_well)
    db.commit()
    db.refresh(db_well)
    return db_well

@router.get("/holidays", response_model=List[schemas.Holiday])
def get_holidays(fpso: Optional[str] = None, db: Session = Depends(database.get_db)):
    query = db.query(models.Holiday)
    if fpso:
        query = query.filter(models.Holiday.fpso == fpso)
    return query.all()

@router.post("/holidays", response_model=schemas.Holiday)
def create_holiday(holiday: schemas.HolidayCreate, db: Session = Depends(database.get_db), current_user = Depends(get_current_user)):
    db_holiday = models.Holiday(**holiday.model_dump())
    db.add(db_holiday)
    db.commit()
    db.refresh(db_holiday)
    return db_holiday

@router.get("/stock-locations", response_model=List[schemas.StockLocation])
def get_stock_locations(fpso: Optional[str] = None, db: Session = Depends(database.get_db)):
    query = db.query(models.StockLocation)
    if fpso:
        query = query.filter(models.StockLocation.fpso == fpso)
    return query.all()

@router.post("/stock-locations", response_model=schemas.StockLocation)
def create_stock_location(loc: schemas.StockLocationCreate, db: Session = Depends(database.get_db), current_user = Depends(get_current_user)):
    db_loc = models.StockLocation(**loc.model_dump())
    db.add(db_loc)
    db.commit()
    db.refresh(db_loc)
    return db_loc

@router.get("/parameters", response_model=List[schemas.ConfigParameter])
def get_parameters(fpso: Optional[str] = None, db: Session = Depends(database.get_db)):
    query = db.query(models.ConfigParameter)
    if fpso:
        query = query.filter(models.ConfigParameter.fpso == fpso)
    return query.all()

@router.post("/parameters", response_model=schemas.ConfigParameter)
def set_parameter(param: schemas.ConfigParameterCreate, db: Session = Depends(database.get_db), current_user = Depends(get_current_user)):
    db_param = db.query(models.ConfigParameter).filter(
        models.ConfigParameter.key == param.key,
        models.ConfigParameter.fpso == param.fpso
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
