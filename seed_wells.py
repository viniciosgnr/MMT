import os
import sys

# Ensure backend directory is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))

from app.database import SessionLocal
from app.models import Well

def seed_wells():
    db = SessionLocal()
    try:
        fpso = "FPSO CIDADE DE ILHABELA (CDI)"
        default_gas = "T71-AP-0602"
        default_oil = "T62-AP-2224"
        
        wells_data = [
            {"tag": "Poço SPH-15 (P-1)", "anp_code": "SPH-15", "sbm_code": "P-1"},
            {"tag": "Poço SPS-69 (P-2)", "anp_code": "SPS-69", "sbm_code": "P-2"},
            {"tag": "Poço SPH-7 (P-3)", "anp_code": "SPH-7", "sbm_code": "P-3"},
            {"tag": "Poço SPH-8 (P-4)", "anp_code": "SPH-8", "sbm_code": "P-4"},
            {"tag": "Poço SPH-20 (P-5)", "anp_code": "SPH-20", "sbm_code": "P-5"},
            {"tag": "Poço SPH-14 (P-6)", "anp_code": "SPH-14", "sbm_code": "P-6"},
            {"tag": "Poço SPH-16 (P-7)", "anp_code": "SPH-16", "sbm_code": "P-7"},
            {"tag": "Poço SPH-17 (P-9)", "anp_code": "SPH-17", "sbm_code": "P-9"},
            {"tag": "Poço SPH-6 (P-10)", "anp_code": "SPH-6", "sbm_code": "P-10"},
        ]
        
        # Clear existing wells for this FPSO
        db.query(Well).delete()
        
        for data in wells_data:
            w = Well(
                tag=data["tag"],
                anp_code=data["anp_code"],
                sbm_code=data["sbm_code"],
                sample_point_gas=default_gas,
                sample_point_oil=default_oil,
                status="Active",
                fpso=fpso
            )
            db.add(w)
            
        db.commit()
        print(f"Successfully seeded {len(wells_data)} wells for {fpso}.")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding wells: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_wells()
