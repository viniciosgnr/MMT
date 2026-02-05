from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from .. import models, database
from ..schemas import schemas
from ..dependencies import get_current_user

router = APIRouter(
    prefix="/api/equipment",
    tags=["equipment"],
)

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
    limit: int = 100, 
    serial_number: Optional[str] = None,
    equipment_type: Optional[str] = None,
    db: Session = Depends(database.get_db)
):
    query = db.query(models.Equipment)
    if serial_number:
        query = query.filter(models.Equipment.serial_number.ilike(f"%{serial_number}%"))
    if equipment_type:
        query = query.filter(models.Equipment.equipment_type == equipment_type)
    
    return query.offset(skip).limit(limit).all()

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
def read_tags(skip: int = 0, limit: int = 100, tag_number: Optional[str] = None, db: Session = Depends(database.get_db)):
    query = db.query(models.InstrumentTag)
    if tag_number:
        query = query.filter(models.InstrumentTag.tag_number.ilike(f"%{tag_number}%"))
    return query.offset(skip).limit(limit).all()

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

    return db_equipment

# --- Installation & History ---

@router.post("/install", response_model=schemas.EquipmentTagInstallation)
def install_equipment(
    installation: schemas.EquipmentTagInstallationCreate, 
    db: Session = Depends(database.get_db),
    current_user = Depends(get_current_user)
):
    # Verify equipment and tag exist
    eq = db.query(models.Equipment).filter(models.Equipment.id == installation.equipment_id).first()
    tag = db.query(models.InstrumentTag).filter(models.InstrumentTag.id == installation.tag_id).first()
    
    if not eq or not tag:
        raise HTTPException(status_code=404, detail="Equipment or Tag not found")
        
    # Check if tag is already occupied
    active_install = db.query(models.EquipmentTagInstallation).filter(
        models.EquipmentTagInstallation.tag_id == installation.tag_id,
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
