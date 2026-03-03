import os
import sys
import openpyxl
from datetime import datetime
from sqlalchemy.orm import Session

# Add the backend directory to python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app import models
from app.database import SessionLocal, engine

# Create tables if they don't exist
models.Base.metadata.create_all(bind=engine)

def seed_cdi_data():
    db = SessionLocal()
    try:
        # Load the spreadsheet
        file_path = "/app/cdi_data.xlsx"
        print(f"Loading data from {file_path}...")
        
        wb = openpyxl.load_workbook(file_path, data_only=True)
        sheet = wb['Sheet1']
        
        fpso_name = "FPSO CIDADE DE ILHABELA (CDI)"
        
        # Keep track of created items
        created_equipment = 0
        created_tags = 0
        created_installations = 0
        created_sample_points = 0
        
        print("Parsing Sheet1 for Meters and Sample Points...")
        
        # Get headers from row 1
        headers = [cell.value for cell in sheet[1]]
        
        for row in sheet.iter_rows(min_row=2, values_only=True):
            row_dict = dict(zip(headers, row))
            
            meter_tag = str(row_dict.get('Metering Point', '') or '').strip()
            sp_tag = str(row_dict.get('Sample Point', '') or '').strip()
            
            # Process Metering Point -----------------------------------------
            if meter_tag and meter_tag != 'nan' and meter_tag != 'None':
                service = str(row_dict.get('Description', '') or '').strip()
                
                # Step 1: Ensure Metering Point exists
                mp = db.query(models.InstrumentTag).filter(models.InstrumentTag.tag_number == meter_tag).first()
                if not mp:
                    classification = str(row_dict.get('Classification', '') or '').strip()
                    if classification == 'nan' or classification == 'None': classification = None
                    mp = models.InstrumentTag(
                        tag_number=meter_tag,
                        description=service,
                        classification=classification
                    )
                    db.add(mp)
                    db.commit()
                    db.refresh(mp)
                
                # Step 2: Create associated instruments (PT, TT, TE)
                mp_prefix = meter_tag.split("-FT-")[0] if "-FT-" in meter_tag else meter_tag[:3]
                suffix = meter_tag.split("-FT-")[1] if "-FT-" in meter_tag else meter_tag[3:].strip("-")
                
                instr_types = [
                    ("PT", "Pressure Transmitter"),
                    ("TT", "Temperature Transmitter"),
                    ("TE", "Temperature Element")
                ]
                
                for code, type_name in instr_types:
                    inst_tag_str = f"{mp_prefix}-{code}-{suffix}"
                    
                    # Check if tag exists
                    inst_tag = db.query(models.InstrumentTag).filter(models.InstrumentTag.tag_number == inst_tag_str).first()
                    if not inst_tag:
                        inst_tag = models.InstrumentTag(
                            tag_number=inst_tag_str,
                            description=f"{type_name} for {meter_tag}"
                        )
                        db.add(inst_tag)
                        db.commit()
                        db.refresh(inst_tag)
                        created_tags += 1
                    
                    # Check if Equipment exists
                    serial_num = f"SN-{inst_tag_str}"
                    eq = db.query(models.Equipment).filter(models.Equipment.serial_number == serial_num).first()
                    if not eq:
                        eq = models.Equipment(
                            serial_number=serial_num,
                            model="Generic CDI Model",
                            manufacturer="CDI Default",
                            equipment_type=type_name,
                            fpso_name=fpso_name,
                            status="Active",
                            calibration_frequency_months=12
                        )
                        db.add(eq)
                        db.commit()
                        db.refresh(eq)
                        created_equipment += 1
                    
                    # Check Installation
                    active_install = db.query(models.EquipmentTagInstallation).filter(
                        models.EquipmentTagInstallation.tag_id == inst_tag.id,
                        models.EquipmentTagInstallation.equipment_id == eq.id,
                        models.EquipmentTagInstallation.is_active == 1
                    ).first()
                    
                    if not active_install:
                        install = models.EquipmentTagInstallation(
                            equipment_id=eq.id,
                            tag_id=inst_tag.id,
                            installed_by="CDI Seed Script",
                            installation_date=datetime.utcnow()
                        )
                        db.add(install)
                        db.commit()
                        created_installations += 1

            # Process Sample Point ------------------------------------------
            if sp_tag and sp_tag != 'nan' and sp_tag != 'None':
                service = str(row_dict.get('Description', '') or '').strip()
                
                # Step 1: Ensure Sample Tag exists
                inst_tag = db.query(models.InstrumentTag).filter(models.InstrumentTag.tag_number == sp_tag).first()
                if not inst_tag:
                    inst_tag = models.InstrumentTag(
                        tag_number=sp_tag,
                        description=service or f"Sample Point for {meter_tag}"
                    )
                    db.add(inst_tag)
                    db.commit()
                    db.refresh(inst_tag)
                    created_tags += 1
                
                # Step 2: Ensure Sample Point Equipment exists
                serial_num = f"SN-{sp_tag}"
                eq = db.query(models.Equipment).filter(models.Equipment.serial_number == serial_num).first()
                if not eq:
                    eq = models.Equipment(
                        serial_number=serial_num,
                        model="Valve/Probe",
                        manufacturer="CDI Default",
                        equipment_type="Sample Point",
                        fpso_name=fpso_name,
                        status="Active"
                    )
                    db.add(eq)
                    db.commit()
                    db.refresh(eq)
                    created_equipment += 1
                
                # Step 3: Check Installation
                active_install = db.query(models.EquipmentTagInstallation).filter(
                    models.EquipmentTagInstallation.tag_id == inst_tag.id,
                    models.EquipmentTagInstallation.equipment_id == eq.id,
                    models.EquipmentTagInstallation.is_active == 1
                ).first()
                
                if not active_install:
                    install = models.EquipmentTagInstallation(
                        equipment_id=eq.id,
                        tag_id=inst_tag.id,
                        installed_by="CDI Seed Script",
                        installation_date=datetime.utcnow()
                    )
                    db.add(install)
                    db.commit()
                    created_installations += 1

                # Also ensure the SamplePoint entity exists to link to Metering Point dynamically
                sp = db.query(models.SamplePoint).filter(models.SamplePoint.tag_number == sp_tag).first()
                if not sp:
                    sp = models.SamplePoint(
                        tag_number=sp_tag,
                        description=service,
                        fpso_name=fpso_name
                    )
                    db.add(sp)
                    db.commit()
                    db.refresh(sp)
                    created_sample_points += 1
                
                # Link to meter if necessary
                if meter_tag and meter_tag != 'nan' and meter_tag != 'None':
                    mp = db.query(models.InstrumentTag).filter(models.InstrumentTag.tag_number == meter_tag).first()
                    if mp and sp not in mp.sample_points:
                        mp.sample_points.append(sp)
                        db.commit()
        
        print(f"Finished Seeding.")
        print(f"Created Equipment: {created_equipment}")
        print(f"Created Tags: {created_tags}")
        print(f"Created Installations: {created_installations}")
        print(f"Created Sample Points (Entities): {created_sample_points}")
        
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        print(f"Error seeding data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_cdi_data()
