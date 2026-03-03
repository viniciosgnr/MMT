from app.database import SessionLocal
from app import models
from datetime import datetime
import uuid

db = SessionLocal()

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

equip_specs = {
    "PT": {"type": "Pressure Transmitter", "mf": "Rosemount", "model": "3051S Coplanar"},
    "TT": {"type": "Temperature Transmitter", "mf": "Emerson", "model": "3144P"},
    "TE": {"type": "Temperature Element", "mf": "WIKA", "model": "TR10"},
    "AP": {"type": "Sample Point", "mf": "Swagelok", "model": "V10"}
}

fpso_name = "FPSO CIDADE DE ILHABELA (CDI)"

# 1. Build Whitelist of Valid Tags
valid_tags = set(METER_TO_SAMPLE_POINT.keys())
for meter_tag, sample_tag in METER_TO_SAMPLE_POINT.items():
    valid_tags.add(sample_tag)
    # Generate PT, TT, TE based on prefix
    parts = meter_tag.split('-')
    if len(parts) >= 3:
        valid_tags.add(f"{parts[0]}-PT-{parts[2]}")
        valid_tags.add(f"{parts[0]}-TT-{parts[2]}")
        valid_tags.add(f"{parts[0]}-TE-{parts[2]}")

print("=== DEEP CLEANING ORPHAN TAGS ===", flush=True)

# 2. Cleanup orphaned data
all_db_tags = db.query(models.InstrumentTag).all()
deleted_count = 0
for tag in all_db_tags:
    if tag.tag_number not in valid_tags:
        # Delete installations
        db.query(models.EquipmentTagInstallation).filter(models.EquipmentTagInstallation.tag_id == tag.id).delete()
        # Delete seal history
        db.query(models.SealHistory).filter(models.SealHistory.tag_id == tag.id).delete()
        # Delete certificates
        db.query(models.EquipmentCertificate).filter(models.EquipmentCertificate.tag_id == tag.id).delete()
        # Delete planned activities
        db.query(models.PlannedActivity).filter(models.PlannedActivity.tag_id == tag.id).delete()
        # Delete tag
        db.delete(tag)
        deleted_count += 1
db.commit()
print(f"Deleted {deleted_count} orphaned tags and their installations.")

print("\n=== POPULATING VIRTUAL TAGS & EQUIPMENT ===", flush=True)

count_tag, count_eq, count_inst = 0, 0, 0

for m_tag, ap_tag in METER_TO_SAMPLE_POINT.items():
    # Fetch meter to inherit its area and service
    meter_obj = db.query(models.InstrumentTag).filter(models.InstrumentTag.tag_number == m_tag).first()
    
    # Strictly inherit the meter's properties if they exist
    area_or_service = meter_obj.area if (meter_obj and meter_obj.area) else (meter_obj.description if meter_obj else f"Process {m_tag}")
    actual_service = meter_obj.service if (meter_obj and meter_obj.service) else area_or_service
    
    parts = m_tag.split('-')
    if len(parts) < 3:
        continue
        
    children_to_create = {
        f"{parts[0]}-PT-{parts[2]}": "PT",
        f"{parts[0]}-TT-{parts[2]}": "TT",
        f"{parts[0]}-TE-{parts[2]}": "TE",
        ap_tag: "AP"
    }
    
    for auto_tag, eq_prefix in children_to_create.items():
        specs = equip_specs[eq_prefix]
        
        # Determine specific description (e.g., "Sample Point for T73-FT-5801" or "Offloading")
        desc = f"{specs['type']} for {m_tag}"
        
        # Override metadata logic for Sample Points
        if eq_prefix == "AP":
             if auto_tag == 'T73-AP-0001':
                 desc = 'Sample Point T73-AP-0001'
                 area_or_service = 'Gas Lift'
                 actual_service = 'Gas Lift'
             elif auto_tag == 'T75-AP-6000':
                 desc = 'Sample Point T75-AP-6000'
                 area_or_service = 'Injection Gas'
                 actual_service = 'Injection Gas'
             elif meter_obj and meter_obj.description:
                 desc = meter_obj.description # Default to meter's desc based on spreadsheet
        
        # 1. Ensure Tag Exists & Update Missing Metadata
        tag_obj = db.query(models.InstrumentTag).filter(models.InstrumentTag.tag_number == auto_tag).first()
        if not tag_obj:
            tag_obj = models.InstrumentTag(
                tag_number=auto_tag,
                description=desc,
                area=area_or_service,
                service=actual_service,
            )
            db.add(tag_obj)
            db.commit()
            db.refresh(tag_obj)
            count_tag += 1
        else:
            # Force update area/service for existing AP tags that might be missing them
            tag_obj.description = desc
            tag_obj.area = area_or_service
            tag_obj.service = actual_service
            db.commit()
        
        # 2. Check installation
        inst_obj = db.query(models.EquipmentTagInstallation).filter(
            models.EquipmentTagInstallation.tag_id == tag_obj.id,
            models.EquipmentTagInstallation.is_active == 1
        ).first()
        
        if not inst_obj:
            # Create the unique equipment
            sn = f"SN-{auto_tag}-{str(uuid.uuid4())[:4].upper()}"
            eq_obj = models.Equipment(
                equipment_type=specs["type"],
                serial_number=sn,
                manufacturer=specs["mf"],
                model=specs["model"],
                fpso_name=fpso_name,
                status="Active"
            )
            db.add(eq_obj)
            db.commit()
            db.refresh(eq_obj)
            count_eq += 1
            
            # Install it
            new_inst = models.EquipmentTagInstallation(
                equipment_id=eq_obj.id,
                tag_id=tag_obj.id,
                installation_date=datetime.utcnow(),
                is_active=1
            )
            db.add(new_inst)
            db.commit()
            count_inst += 1

print(f"\nSUCCESS: Created {count_tag} tags, {count_eq} physical equipments, and completed {count_inst} active installations in Module 1.")
