import sys
import os
from datetime import datetime, timedelta

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.database import SessionLocal, engine
from backend.app import models

def seed_m9():
    db = SessionLocal()
    try:
        # 1. Add some initial failure records
        failures = [
            models.FailureNotification(
                fpso_name="FPSO ILHABELA",
                tag="62-FT-1101",
                failure_date=datetime.now() - timedelta(days=2),
                description="Turbine meter showing high deviation during daily check.",
                impact="High",
                estimated_volume_impact=450.5,
                cause="Mechanical wear on bearings",
                corrective_action="Planned replacement for next maintenance window.",
                responsible="Marcos G.",
                anp_classification="Grave",
                status="Draft"
            ),
            models.FailureNotification(
                fpso_name="FPSO PARATY",
                tag="62-PT-1103",
                failure_date=datetime.now() - timedelta(days=5),
                description="Pressure transmitter signal drift.",
                impact="Medium",
                estimated_volume_impact=12.0,
                cause="Internal electronic fault",
                corrective_action="Calibrated and monitored. Stability returned.",
                responsible="Daniel Bernoulli",
                anp_classification="Tolerável",
                status="Approved",
                approved_by="Marcos G. (ME)",
                approved_at=datetime.now() - timedelta(days=1)
            )
        ]
        
        # 2. Add some emails to the distribution list
        email_list = [
            models.FPSOFailureEmailList(fpso_name="FPSO ILHABELA", email="operation.manager@petrobras.com.br"),
            models.FPSOFailureEmailList(fpso_name="FPSO ILHABELA", email="anp.notification@petrobras.com.br"),
            models.FPSOFailureEmailList(fpso_name="FPSO PARATY", email="lead.engineer@petrobras.com.br")
        ]
        
        db.add_all(failures)
        db.add_all(email_list)
        db.commit()
        print("M9 sample failures and email lists added.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_m9()
