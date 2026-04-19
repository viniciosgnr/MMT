from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
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
    # 1. Root Node (FPSO)
    fpso = schemas.HierarchyNodeWithChildren(
        id=1,
        tag="FPSO CIDADE DE ILHABELA (CDI)",
        description="Main Vessel",
        level_type="FPSO",
        parent_id=None,
        created_at=datetime.utcnow(),
        children=[]
    )
    
    # Exact mapping from Metering Point + Sample Point - CDI.xlsx
    METER_TO_SAMPLE_POINT = {
        'T62-FT-1103': 'T62-AP-1002', 'F65-FT-0150': 'F65-AP-1111', 'T62-FT-2221': 'T62-AP-2224', 
        'T71-FT-0601': 'T71-AP-0602', 'T73-FT-0015': 'T73-AP-0001', 'T73-FT-5101': 'T73-AP-0001', 
        'T73-FT-5201': 'T73-AP-0001', 'T73-FT-5301': 'T73-AP-0001', 'T73-FT-5401': 'T73-AP-0001', 
        'T73-FT-5501': 'T73-AP-0001', 'T73-FT-5601': 'T73-AP-0001', 'T73-FT-5701': 'T73-AP-0001', 
        'T73-FT-5801': 'T73-AP-0001', 'T73-FT-5901': 'T73-AP-0001', 'T73-FT-6001': 'T73-AP-0001', 
        'T73-FT-6101': 'T73-AP-0001', 'T73-FT-6201': 'T73-AP-0001', 'T73-FT-6301': 'T73-AP-0001', 
        'T73-FT-6401': 'T73-AP-0001', 'T73-FT-6501': 'T73-AP-0001', 'T74-FT-6901': 'T74-AP-6911', 
        'T75-FT-0001': 'T75-AP-6000', 'T75-FT-6101': 'T75-AP-6000', 'T75-FT-6201': 'T75-AP-6000', 
        'T75-FT-6301': 'T75-AP-6000', 'T75-FT-6401': 'T75-AP-6000', 'T75-FT-6501': 'T75-AP-6000', 
        'T76-FT-0014': 'T76-AP-0013', 'T76-FT-0034': 'T76-AP-0033', 'T76-FT-2001': 'T76-AP-2002', 
        'T77-FT-0103': 'T77-AP-1009', 'T77-FT-6951': 'T77-AP-1039', 'T71-FT-0101': 'T71-AP-0102', 
        'T71-FT-0201': 'T71-AP-0202'
    }

    # 2. Metering Points (InstrumentTags with classification and tag containing '-FT-')
    meters = db.query(models.InstrumentTag).filter(
        models.InstrumentTag.classification.isnot(None),
        models.InstrumentTag.tag_number.like("%-FT-%")
    ).all()
    
    # Extract just the valid tags from the mapping to prevent N+1 queries
    valid_tags_to_fetch = set(METER_TO_SAMPLE_POINT.values())
    for m in meters:
        parts = m.tag_number.split('-')
        if len(parts) >= 3:
            valid_tags_to_fetch.update([
                f"{parts[0]}-PT-{parts[2]}",
                f"{parts[0]}-TT-{parts[2]}",
                f"{parts[0]}-TE-{parts[2]}"
            ])
            
    # Fetch all relevant instrument tags at once
    inst_objs = db.query(models.InstrumentTag).filter(
        models.InstrumentTag.tag_number.in_(valid_tags_to_fetch)
    ).all()
    
    # Map them by tag number
    inst_lookup = {inst.tag_number: inst for inst in inst_objs}
            
    for m in meters:
        meter_node = schemas.HierarchyNodeWithChildren(
            id=m.id + 20000, 
            tag=m.tag_number,
            description=m.description or "Metering Point",
            level_type="Metering Point",
            parent_id=fpso.id,
            created_at=m.created_at or datetime.utcnow(),
            attributes={"classification": m.classification},
            children=[]
        )
        fpso.children.append(meter_node)
        
        # 3. Auto-generated Categories under Metering Point
        cats = [
            ("Pressure", ["PT"]),
            ("Temperature", ["TT", "TE"]),
            ("Fluid Properties", ["AP"]) # Sample Points
        ]
        
        base_cat_id = (m.id * 10) + 30000
        
        # Get specific AP tag per the exact mapping
        ap_tag = METER_TO_SAMPLE_POINT.get(m.tag_number, None)

        parts = m.tag_number.split('-')
        pt_tag = f"{parts[0]}-PT-{parts[2]}" if len(parts) >= 3 else None
        tt_tag = f"{parts[0]}-TT-{parts[2]}" if len(parts) >= 3 else None
        te_tag = f"{parts[0]}-TE-{parts[2]}" if len(parts) >= 3 else None
        
        # We need composite IDs for AP combinations since multiple FTs can use the same AP
        # Offset to prevent collision with other nodes
        for i, (cat_name, target_tags, level_type_val) in enumerate([
            ("Pressure", [pt_tag], "Device"),
            ("Temperature", [tt_tag, te_tag], "Device"),
            ("Fluid Properties", [ap_tag], "Sample Point")
        ]):
            cat_node = schemas.HierarchyNodeWithChildren(
                id=base_cat_id + i,
                tag=cat_name,
                description=f"{cat_name} Instruments",
                level_type="Category",
                parent_id=meter_node.id,
                created_at=datetime.utcnow(),
                attributes={},
                children=[]
            )
            meter_node.children.append(cat_node)
            
            # Find instruments for this category mapping
            for j, t_tag in enumerate(target_tags):
                if t_tag and t_tag in inst_lookup:
                    inst = inst_lookup[t_tag]
                    
                    inst_node = schemas.HierarchyNodeWithChildren(
                        id=int(f"{base_cat_id}{i}{j}"), # Unique composite ID
                        tag=inst.tag_number,
                        description=inst.description,
                        level_type=level_type_val,
                        parent_id=cat_node.id,
                        created_at=inst.created_at,
                        attributes={},
                        children=[]
                    )
                    cat_node.children.append(inst_node)
            
    return [fpso]
    
@router.get("/hierarchy/nodes", response_model=List[schemas.HierarchyNode])
def get_hierarchy_nodes(db: Session = Depends(database.get_db)):
    return db.query(models.HierarchyNode).all()

@router.post("/hierarchy/nodes", response_model=schemas.HierarchyNode)
def create_hierarchy_node(node: schemas.HierarchyNodeCreate, db: Session = Depends(database.get_db), current_user = Depends(get_current_user)):
    from datetime import datetime
    
    if node.level_type == "Metering Point":
        classification = node.attributes.get("classification") if node.attributes else None
        m = models.InstrumentTag(tag_number=node.tag, description=node.description, classification=classification)
        db.add(m)
        db.commit()
        db.refresh(m)
        return {"id": m.id + 20000, "tag": m.tag_number, "description": m.description, "level_type": "Metering Point", "created_at": m.created_at, "parent_id": node.parent_id, "attributes": {"classification": m.classification}}
    
    elif node.level_type == "Sample Point":
        # The parent_id sent from frontend is the offset Category ID
        # Since this is legacy logic, we skip for new hierarchy as we import them
        pass
        
    else:
        # Fallback for generic nodes
        data = node.model_dump()
        if "attributes" in data:
            del data["attributes"]
        db_node = models.HierarchyNode(**data)
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
    # Prepare data for DB
    data = attr.model_dump()
    
    # Serialize validation_rules to JSON string if present
    if attr.validation_rules:
        import json
        # Check if it's a Pydantic model
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
    return db.query(models.AttributeValue).filter(models.AttributeValue.entity_id == entity_id).all()

@router.post("/values", response_model=schemas.AttributeValue)
def set_attribute_value(val: schemas.AttributeValueCreate, db: Session = Depends(database.get_db), current_user = Depends(get_current_user)):
    # 1. Fetch Definition
    definition = db.query(models.AttributeDefinition).filter(models.AttributeDefinition.id == val.attribute_id).first()
    if not definition:
        raise HTTPException(status_code=404, detail="Attribute definition not found")

    # 2. Dynamic Validation via Service
    from ..services.validation_service import ValidationService
    try:
        ValidationService.validate_attribute_value(definition, val.value)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

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
        # Extract FPSO short code (e.g., "CDI" from "CDI - Cidade de Ilhabela")
        # to handle multiple naming conventions in the database
        code = fpso.split(" - ")[0].strip() if " - " in fpso else fpso
        query = query.filter(models.Well.fpso.ilike(f"%{code}%"))
    return query.all()

@router.post("/wells", response_model=schemas.Well)
def create_well(well: schemas.WellCreate, db: Session = Depends(database.get_db), current_user = Depends(get_current_user)):
    db_well = models.Well(**well.model_dump())
    db.add(db_well)
    db.commit()
    db.refresh(db_well)
    return db_well

@router.put("/wells/{well_id}", response_model=schemas.Well)
def update_well(well_id: int, well: schemas.WellUpdate, db: Session = Depends(database.get_db), current_user = Depends(get_current_user)):
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
def delete_well(well_id: int, db: Session = Depends(database.get_db), current_user = Depends(get_current_user)):
    db_well = db.query(models.Well).filter(models.Well.id == well_id).first()
    if not db_well:
        raise HTTPException(status_code=404, detail="Well not found")
    db.delete(db_well)
    db.commit()
    return {"status": "success"}

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
