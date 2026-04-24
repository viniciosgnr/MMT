from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from typing import List, Optional
from .. import models, database
from ..schemas import schemas
from ..dependencies import get_current_user

router = APIRouter(
    prefix="/api/equipment",
    tags=["equipment"],
)

# --- Helpers ---
def calculate_health(db_equipment: models.Equipment) -> str:
    """Calcula o status de saúde baseado nos certificados de calibração."""
    certs = [c for c in db_equipment.certificates if c.certificate_type == "Calibration"]
    if not certs:
        return "missing"
    
    today = date.today()
    warning_buffer = today + timedelta(days=30)
    
    has_expired = False
    has_warning = False
    
    for c in certs:
        if not c.expiry_date:
            continue
        if c.expiry_date < today:
            has_expired = True
        elif c.expiry_date < warning_buffer:
            has_warning = True
            
    if has_expired:
        return "expired"
    if has_warning:
        return "expiring"
    return "healthy"

# --- Physical Equipment (Serial Numbers) ---

@router.post("/", response_model=schemas.Equipment)
def create_equipment(equipment: schemas.EquipmentCreate, db: Session = Depends(database.get_db), current_user = Depends(get_current_user)):
    db_equipment = models.Equipment(**equipment.model_dump())
    db.add(db_equipment)
    db.commit()
    db.refresh(db_equipment)
    return db_equipment

@router.get("/", response_model=List[schemas.Equipment])
def read_equipments(
    skip: int = 0, 
    limit: int = 1000, 
    serial_number: Optional[str] = None,
    equipment_type: Optional[str] = None,
    db: Session = Depends(database.get_db)
):
    query = db.query(models.Equipment)
    if serial_number:
        query = query.filter(models.Equipment.serial_number.ilike(f"%{serial_number}%"))
    if equipment_type:
        query = query.filter(models.Equipment.equipment_type == equipment_type)
    
    equipments = query.offset(skip).limit(limit).all()
    for eq in equipments:
        eq.health_status = calculate_health(eq)
    return equipments

# --- Instrument Tags (Locations) ---
# IMPORTANT: These routes must come BEFORE /{equipment_id} to avoid conflicts

@router.post("/tags", response_model=schemas.InstrumentTag)
def create_tag(tag: schemas.InstrumentTagCreate, db: Session = Depends(database.get_db), current_user = Depends(get_current_user)):
    db_tag = models.InstrumentTag(**tag.model_dump())
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag

@router.get("/tags", response_model=List[schemas.InstrumentTag])
def read_tags(skip: int = 0, limit: int = 10000, tag_number: Optional[str] = None, db: Session = Depends(database.get_db)):
    query = db.query(models.InstrumentTag)
    if tag_number:
        query = query.filter(models.InstrumentTag.tag_number.ilike(f"%{tag_number}%"))
    return query.offset(skip).limit(limit).all()

@router.put("/tags/{tag_id}", response_model=schemas.InstrumentTag)
def update_tag(tag_id: int, tag_update: schemas.InstrumentTagBase, db: Session = Depends(database.get_db), current_user = Depends(get_current_user)):
    db_tag = db.query(models.InstrumentTag).filter(models.InstrumentTag.id == tag_id).first()
    if not db_tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    update_data = tag_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_tag, key, value)
    
    db.commit()
    db.refresh(db_tag)
    return db_tag

@router.delete("/tags/{tag_id}")
def delete_tag(tag_id: int, db: Session = Depends(database.get_db), current_user = Depends(get_current_user)):
    db_tag = db.query(models.InstrumentTag).filter(models.InstrumentTag.id == tag_id).first()
    if not db_tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    # --- Skill (backend-dev-guidelines): Integrity Guards ---
    # 1. Check for active installations
    active_install = db.query(models.EquipmentTagInstallation).filter(
        models.EquipmentTagInstallation.tag_id == tag_id,
        models.EquipmentTagInstallation.is_active == 1
    ).first()
    if active_install:
        raise HTTPException(status_code=400, detail="Cannot delete tag with an active equipment installation.")
    
    # 2. Check for linked sample points (METER_SAMPLE_LINK)
    # This checks if the tag is still part of the chemical analysis hierarchy
    if db_tag.sample_points:
        raise HTTPException(status_code=400, detail="Cannot delete tag linked to active Sample Points. Unlink them first.")
    
    db.delete(db_tag)
    db.commit()
    return {"status": "success", "message": "Tag deleted successfully"}

@router.get("/tags/available", response_model=List[schemas.InstrumentTag])
def read_available_tags(
    fpso_name: Optional[str] = None,
    equipment_type: Optional[str] = None,
    db: Session = Depends(database.get_db)
):
    """Get tags that have an active equipment installation matching criteria."""
    query = db.query(models.InstrumentTag).join(
        models.EquipmentTagInstallation, models.InstrumentTag.id == models.EquipmentTagInstallation.tag_id
    ).join(
        models.Equipment, models.EquipmentTagInstallation.equipment_id == models.Equipment.id
    ).filter(
        models.EquipmentTagInstallation.is_active == 1
    )
    
    if fpso_name:
        query = query.filter(models.Equipment.fpso_name == fpso_name)
    if equipment_type:
        types = [t.strip() for t in equipment_type.split(",")]
        query = query.filter(models.Equipment.equipment_type.in_(types))
        
    return query.all()

@router.get("/{equipment_id}", response_model=schemas.Equipment)
def read_equipment(equipment_id: int, db: Session = Depends(database.get_db)):
    db_equipment = db.query(models.Equipment).filter(models.Equipment.id == equipment_id).first()
    if not db_equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    # Mock Sync Status (Logic: ID % 3 to show variety)
    # Real logic implementation pending in M5 Integration Service
    states = ["synced", "warning", "error"]
    db_equipment.sync_status = states[equipment_id % 3]
    db_equipment.last_synced_at = datetime.now() if db_equipment.sync_status == "synced" else None

    db_equipment.health_status = calculate_health(db_equipment)
    return db_equipment

# --- Installation & History ---

@router.post("/install", response_model=schemas.EquipmentTagInstallation)
def install_equipment(
    installation: schemas.EquipmentTagInstallationCreate, 
    target_tag_name: Optional[str] = Query(None),
    target_description: Optional[str] = Query(None),
    hierarchy_node_id: Optional[int] = Query(None),
    db: Session = Depends(database.get_db),
    current_user = Depends(get_current_user)
):
    # Verify equipment exists
    eq = db.query(models.Equipment).filter(models.Equipment.id == installation.equipment_id).first()
    if not eq:
        raise HTTPException(status_code=404, detail="Equipment not found")
        
    tag_id = installation.tag_id

    # If tag_id is 0 but target_tag_name is provided, we create a new tag
    if tag_id == 0 and target_tag_name:
        # Check if tag already exists
        existing_tag = db.query(models.InstrumentTag).filter(models.InstrumentTag.tag_number == target_tag_name).first()
        if existing_tag:
            tag_id = existing_tag.id
            installation.tag_id = tag_id  # Sync back so model_dump() is correct
        else:
            new_tag = models.InstrumentTag(
                tag_number=target_tag_name,
                description=target_description or f"Auto-generated for {eq.serial_number}",
                hierarchy_node_id=hierarchy_node_id
            )
            db.add(new_tag)
            db.commit()
            db.refresh(new_tag)
            tag_id = new_tag.id
            installation.tag_id = tag_id

    # Use with_for_update() to lock the tag record and prevented concurrent installations
    tag = db.query(models.InstrumentTag).filter(models.InstrumentTag.id == tag_id).with_for_update().first()
    if not tag:
         raise HTTPException(status_code=404, detail="Target Tag not found")
        
    # Check if tag is already occupied
    active_install = db.query(models.EquipmentTagInstallation).filter(
        models.EquipmentTagInstallation.tag_id == tag_id,
        models.EquipmentTagInstallation.is_active == 1
    ).first()
    
    if active_install:
        raise HTTPException(status_code=400, detail="Tag is already occupied. Remove current equipment first.")

    db_install = models.EquipmentTagInstallation(**installation.model_dump())
    db.add(db_install)
    db.commit()
    db.refresh(db_install)
    return db_install

@router.post("/remove/{installation_id}")
def remove_equipment(installation_id: int, db: Session = Depends(database.get_db), current_user = Depends(get_current_user)):
    db_install = db.query(models.EquipmentTagInstallation).filter(models.EquipmentTagInstallation.id == installation_id).first()
    if not db_install:
        raise HTTPException(status_code=404, detail="Installation record not found")
    
    db_install.removal_date = datetime.utcnow()
    db_install.is_active = 0
    db.commit()
    return {"status": "success", "message": "Equipment removed from tag"}

@router.get("/{equipment_id}/history", response_model=List[schemas.EquipmentTagInstallation])
def get_equipment_history(equipment_id: int, db: Session = Depends(database.get_db)):
    return db.query(models.EquipmentTagInstallation).filter(
        models.EquipmentTagInstallation.equipment_id == equipment_id
    ).order_by(models.EquipmentTagInstallation.installation_date.desc()).all()

@router.get("/tags/{tag_id}/history", response_model=List[schemas.EquipmentTagInstallation])
def get_tag_history(tag_id: int, db: Session = Depends(database.get_db)):
    return db.query(models.EquipmentTagInstallation).filter(
        models.EquipmentTagInstallation.tag_id == tag_id
    ).order_by(models.EquipmentTagInstallation.installation_date.desc()).all()

# --- Certificates ---

@router.post("/certificates", response_model=schemas.EquipmentCertificate)
def add_certificate(cert: schemas.EquipmentCertificateCreate, db: Session = Depends(database.get_db), current_user = Depends(get_current_user)):
    db_cert = models.EquipmentCertificate(**cert.model_dump())
    db.add(db_cert)
    db.commit()
    db.refresh(db_cert)
    return db_cert

@router.get("/{equipment_id}/certificates", response_model=List[schemas.EquipmentCertificate])
def read_equipment_certificates(equipment_id: int, db: Session = Depends(database.get_db)):
    return db.query(models.EquipmentCertificate).filter(models.EquipmentCertificate.equipment_id == equipment_id).all()

# --- Hierarchy (M11 for Export Module) ---

@router.get("/hierarchy/nodes")
def get_hierarchy_nodes(db: Session = Depends(database.get_db)):
    # Returns the tree-ready nodes
    return db.query(models.HierarchyNode).all()
