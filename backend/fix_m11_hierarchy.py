import sys
import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

sys.path.append(os.path.abspath('backend'))
load_dotenv('backend/.env')

from app.database import SessionLocal, engine
from app.models import InstrumentTag, SamplePoint, meter_sample_link, HierarchyNode, Sample

def fix_hierarchy():
    db = SessionLocal()
    try:
        fpso_name = "FPSO CIDADE DE ILHABELA (CDI)"
        excel_path = '/home/marcosgnr/MMT/MMT Specifications/Metering Point + Sample Point - CDI.xlsx'
        df = pd.read_excel(excel_path)
        data = df.to_dict(orient='records')

        # 1. Create or ensure correct nodes exist first
        print("Ensuring correct base nodes exist...")
        correct_mps = {}
        correct_sps = {}
        
        for row in data:
            mp_tag = str(row.get('Metering Point')).strip()
            classification = str(row.get('Classification')).strip()
            description = str(row.get('Description')).strip()
            sp_tag = str(row.get('Sample Point')).strip()
            if pd.isna(row.get('Sample Point')):
                sp_tag = None
            
            # Find or Create MP
            mp = db.query(InstrumentTag).filter(InstrumentTag.tag_number == mp_tag).first()
            if not mp:
                mp = InstrumentTag(tag_number=mp_tag, description=description, classification=classification)
                db.add(mp)
                db.flush()
            correct_mps[mp_tag] = mp

            # Find or Create SP
            if sp_tag and sp_tag != 'nan':
                sp = db.query(SamplePoint).filter(SamplePoint.tag_number == sp_tag).first()
                if not sp:
                    sp = SamplePoint(tag_number=sp_tag, description="Sample point for " + mp_tag, fpso_name=fpso_name)
                    db.add(sp)
                    db.flush()
                correct_sps[sp_tag] = sp

        db.commit()

        # 2. Re-point Samples from bad nodes to good nodes
        print("Re-pointing existing samples to correct nodes...")
        # Since the bad nodes have "-CDI", their correct counterpart is just the tag without "-CDI"
        samples = db.query(Sample).all()
        for sample in samples:
            # Fix meter_id
            if sample.meter_id:
                bad_mp = db.query(InstrumentTag).get(sample.meter_id)
                if bad_mp and bad_mp.tag_number.endswith("-CDI"):
                    correct_tag = bad_mp.tag_number.replace("-CDI", "")
                    if correct_tag in correct_mps:
                        sample.meter_id = correct_mps[correct_tag].id
            
            # Fix sample_point_id
            if sample.sample_point_id:
                bad_sp = db.query(SamplePoint).get(sample.sample_point_id)
                if bad_sp and bad_sp.tag_number.endswith("-CDI"):
                    correct_tag = bad_sp.tag_number.replace("-CDI", "")
                    if correct_tag in correct_sps:
                        sample.sample_point_id = correct_sps[correct_tag].id

        db.commit()
        print("Samples repointed successfully.")

        # 3. Clean up bad '-CDI' data
        print("Cleaning up malformed '-CDI' nodes...")
        bad_tags = db.query(InstrumentTag).filter(InstrumentTag.tag_number.endswith("-CDI")).all()
        bad_sps = db.query(SamplePoint).filter(SamplePoint.tag_number.endswith("-CDI")).all()
        
        for tag in bad_tags:
            tag.sample_points = []
        db.commit()
        
        for tag in bad_tags:
            db.delete(tag)
        for sp in bad_sps:
            db.delete(sp)
        db.commit()
        print(f"Deleted {len(bad_tags)} malformed Metering Points and {len(bad_sps)} Sample Points.")
        
        # 4. Clear existing links for CDI tags to start fresh
        all_cdi_tags = db.query(InstrumentTag).filter(InstrumentTag.classification.isnot(None)).all()
        for t in all_cdi_tags:
            t.sample_points = []
        db.commit()
        print("Cleared previous CDI tag links.")

        # 5. Build relations based on Excel
        print("Building relations...")
        processed_count = 0
        for row in data:
            mp_tag = str(row.get('Metering Point')).strip()
            classification = str(row.get('Classification')).strip()
            description = str(row.get('Description')).strip()
            sp_tag = str(row.get('Sample Point')).strip()
            if pd.isna(row.get('Sample Point')):
                sp_tag = None
            
            mp = correct_mps[mp_tag]
            mp.classification = classification
            if description and str(description) != 'nan':
                mp.description = description
                
            if sp_tag and sp_tag != 'nan':
                sp = correct_sps[sp_tag]
                sp.fpso_name = fpso_name
                
                analysis_types = []
                for col in ['Type of Analysis 1', 'Type of analysis 2', 'Type of Analysis 3', 'Type 4']:
                    val = row.get(col)
                    if pd.notna(val) and str(val).strip():
                        analysis_types.append(str(val).strip())
                
                if analysis_types:
                    import json
                    sp.analysis_types = json.dumps(analysis_types)
                
                if sp not in mp.sample_points:
                    mp.sample_points.append(sp)
            
            processed_count += 1
            
        db.commit()
        print(f"Successfully processed {processed_count} rows and synchronized hierarchies.")

    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        print(f"Error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_hierarchy()
