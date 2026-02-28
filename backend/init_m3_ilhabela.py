import openpyxl
import json
import uuid
import sys
import os
from datetime import datetime, timedelta

# Avoid import errors if run from within 'backend'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import SamplePoint, InstrumentTag, Sample, SampleStatusHistory, SampleResult

def seed_m3_ilhabela():
    print("Starting M3 Data Seeding...")
    db = SessionLocal()
    
    try:
        # First, clear existing M3 samples to make it clean
        print("Clearing existing sample histories and results...")
        db.query(SampleStatusHistory).delete()
        db.query(SampleResult).delete()
        print("Clearing existing samples...")
        db.query(Sample).delete()
        db.commit()

        wb = openpyxl.load_workbook('cdi_data.xlsx')
        ws = wb.active
        
        # Skip header row
        rows = list(ws.iter_rows(values_only=True))[1:]
        
        print("Reading CDI Data for M3 Schedule Generation...")
        samples_created = 0
        
        for idx, row in enumerate(rows):
            meter_tag = row[0]
            classification = row[1]
            description = row[2]
            sample_tag = row[3]
            
            # Types of analysis (columns 4,5,6,7)
            raw_types = [t for t in row[4:8] if t]
            translation_map = {
                "Massa Específica": "Specific Mass",
                "Densidade": "Density",
                "BSW": "BSW",
                "Cromatografia": "Chromatography",
                "Salinidade": "Salinity",
                "Viscosidade": "Viscosity",
                "PVT": "PVT"
            }
            analysis_types = [translation_map.get(t.strip(), t.strip()) for t in raw_types]
            
            if not meter_tag and not sample_tag:
                continue
            
            # Find Meter and Sample Point
            meter = db.query(InstrumentTag).filter(InstrumentTag.tag_number.in_([meter_tag, f"{meter_tag}-CDI"])).order_by(InstrumentTag.tag_number.desc()).first()
            sp = db.query(SamplePoint).filter(
                SamplePoint.tag_number.in_([sample_tag, f"{sample_tag}-CDI"]),
                SamplePoint.fpso_name == "CDI - Cidade de Ilhabela"
            ).first()
            
            if not meter or not sp:
                print(f"Skipping row {idx}: meter={meter}, sample_point={sp}, tags={meter_tag}, {sample_tag}")
                # Fallback if somehow they don't exist (they should from M11 seed)
                continue
            
            # Now we generate a baseline 'Sample' (Analysis) record for EACH analysis_type found for this row
            if analysis_types:
                for a_type in analysis_types:
                    new_id = f"CDI-{datetime.now().strftime('%Y%m')}-{samples_created:04d}"
                    
                    sample = Sample(
                        sample_id=new_id,
                        type=a_type,
                        category="Coleta",
                        status="Planned",
                        responsible="Client Lab", # Generic
                        sample_point_id=sp.id,
                        meter_id=meter.id,
                        validation_party="Client",
                        is_active=1,
                        planned_date=datetime.now().date() + timedelta(days=5),
                        created_at=datetime.utcnow()
                    )
                    db.add(sample)
                    samples_created += 1
            else:
                # If no specific analysis type is given, just create one generic one
                new_id = f"CDI-{datetime.now().strftime('%Y%m')}-{samples_created:04d}"
                sample = Sample(
                    sample_id=new_id,
                    type="General Analysis",
                    category="Coleta",
                    status="Planned",
                    responsible="Client Lab",
                    sample_point_id=sp.id,
                    meter_id=meter.id,
                    validation_party="Client",
                    is_active=1,
                    planned_date=datetime.now().date() + timedelta(days=5),
                    created_at=datetime.utcnow()
                )
                db.add(sample)
                samples_created += 1

        db.commit()
        print(f"M3 successfully seeded with {samples_created} baseline samples from Ilhabela spreadsheet!")
        
    except Exception as e:
        print(f"Error seeding M3: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_m3_ilhabela()
