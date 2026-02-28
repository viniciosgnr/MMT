import openpyxl
import json
from app.database import SessionLocal
from app.models import SamplePoint, InstrumentTag

def seed_cdi():
    print("Starting CDI Hierarchy Seeding...")
    db = SessionLocal()
    
    try:
        wb = openpyxl.load_workbook('cdi_data.xlsx')
        ws = wb.active
        
        # Skip header row
        rows = list(ws.iter_rows(values_only=True))[1:]
        
        for row in rows:
            meter_tag = row[0]
            classification = row[1]
            description = row[2]
            sample_tag = row[3]
            
            # Types of analysis (columns 4,5,6,7)
            raw_types = [t for t in row[4:8] if t]
            translation_map = {
                "Massa Específica": "Specific mass",
                "Densidade": "Density",
                "BSW": "BSW",
                "Cromatografia": "Chromatography",
                "Salinidade": "Salinity",
                "Viscosidade": "Viscosity",
                "PVT": "PVT"
            }
            analysis_types = [translation_map.get(t.strip(), t.strip()) for t in raw_types]
            
            # Skip empty rows completely
            if not meter_tag and not sample_tag:
                continue
                
            sp = None
            if sample_tag:
                # See if a CDI specific one exists first
                sp = db.query(SamplePoint).filter(SamplePoint.tag_number.like(f"%{sample_tag}%"), SamplePoint.fpso_name == "CDI - Cidade de Ilhabela").first()
                if not sp:
                    # Check if base tag is taken
                    existing = db.query(SamplePoint).filter(SamplePoint.tag_number == sample_tag).first()
                    new_tag = f"{sample_tag}-CDI" if existing else sample_tag
                    sp = SamplePoint(
                        tag_number=new_tag,
                        description=f"Sample Point for {sample_tag}",
                        fpso_name="CDI - Cidade de Ilhabela",
                    )
                    db.add(sp)
                    db.flush()
                
                # Update analysis types
                sp.analysis_types = json.dumps(analysis_types) if analysis_types else None
                
            if meter_tag:
                # Find CDI meter (by assuming it either has -CDI or is uniquely CDI's)
                meter = db.query(InstrumentTag).filter(InstrumentTag.tag_number.like(f"%{meter_tag}%")).first()
                # If meter exists but we want to make sure it's not a different fpso's... actually we can just check if exactly meter_tag exists.
                # If we need to create one because it's missing or we want a dedicated one:
                existing_meter = db.query(InstrumentTag).filter(InstrumentTag.tag_number == meter_tag).first()
                if not meter or (existing_meter and not existing_meter.tag_number.endswith("-CDI") and "-CDI" not in meter.tag_number):
                     # If the existing meter is NOT a CDI meter, we should create a new suffixed one unless we already found a suffixed one.
                     # Let's find exactly meter_tag or meter_tag + "-CDI"
                     meter = db.query(InstrumentTag).filter(InstrumentTag.tag_number.in_([meter_tag, f"{meter_tag}-CDI"])).order_by(InstrumentTag.tag_number.desc()).first()
                     if not meter or (meter.tag_number == meter_tag and meter_tag != f"{meter_tag}-CDI"): # It might be saquarema's
                         if existing_meter:
                             meter = InstrumentTag(
                                 tag_number=f"{meter_tag}-CDI",
                                 description=description or "",
                             )
                         else:
                             meter = InstrumentTag(
                                 tag_number=meter_tag,
                                 description=description or "",
                             )
                         db.add(meter)
                         db.flush()
                
                # Update classification and description
                meter.classification = classification
                if description:
                    meter.description = description
                    
                # Link them M2M
                if sp:
                    if meter not in sp.meters:
                        sp.meters.append(meter)
                        
        db.commit()
        print("CDI Hierarchy successfully seeded!")
        
    except Exception as e:
        print(f"Error seeding CDI: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_cdi()
