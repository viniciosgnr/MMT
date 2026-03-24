from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os
import sys

# Append the parent directory to sys.path so we can import app modules directly if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import models
from app.database import SessionLocal, engine

def seed_m2():
    db = SessionLocal()
    try:
        print("Injecting M2 specific mock tasks and results...")

        # Get existing references dynamically
        campaign = db.query(models.CalibrationCampaign).first()
        equipments = db.query(models.Equipment).limit(4).all()
        if len(equipments) < 4:
            print("Not enough equipments found.")
            return
        eq1, eq2, eq3, eq4 = equipments

        tags = db.query(models.InstrumentTag).limit(4).all()
        if len(tags) < 4:
            print("Not enough tags found.")
            return
        tag1, tag2, tag3, tag4 = tags

        if not campaign:
            print("No campaign found.")
            return

        # 3. Calibration Tasks
        tasks = [
            models.CalibrationTask(
                campaign_id=campaign.id,
                equipment_id=eq1.id,
                tag=tag1.tag_number,
                description="Routine Pressure Calib",
                type="Calibration",
                due_date=datetime.now().date() - timedelta(days=2),
                status=models.CalibrationTaskStatus.PENDING.value,
            ),
            models.CalibrationTask(
                campaign_id=campaign.id,
                equipment_id=eq3.id,
                tag=tag3.tag_number,
                description="Annual Verification",
                type="Verification",
                due_date=datetime.now().date() + timedelta(days=5),
                status=models.CalibrationTaskStatus.SCHEDULED.value,
                plan_date=datetime.now().date() + timedelta(days=5)
            ),
            models.CalibrationTask(
                campaign_id=campaign.id,
                equipment_id=eq2.id,
                tag=tag2.tag_number,
                description="Temp Sensor CA Validation",
                type="Calibration",
                calibration_type="ex-situ",
                due_date=datetime.now().date() - timedelta(days=1),
                status=models.CalibrationTaskStatus.EXECUTED.value,
                exec_date=datetime.now().date() - timedelta(days=5),
                is_temporary=1,
                seal_number="SBM-SEAL-001",
                seal_installation_date=datetime.now().date() - timedelta(days=5),
                seal_location="Terminal Block",
                certificate_number="CERT-2024-TMP01",
                certificate_issued_date=datetime.now().date() - timedelta(days=4),
                certificate_ca_status="pending"
            ),
            models.CalibrationTask(
                campaign_id=campaign.id,
                equipment_id=eq4.id,
                tag=tag4.tag_number,
                description="Water Inj PT Validation",
                type="Calibration",
                calibration_type="in-situ",
                due_date=datetime.now().date() - timedelta(days=1),
                status=models.CalibrationTaskStatus.EXECUTED.value,
                exec_date=datetime.now().date() - timedelta(days=10),
                is_temporary=0,
                seal_number="SBM-SEAL-002",
                seal_installation_date=datetime.now().date() - timedelta(days=10),
                seal_location="Manifold",
                certificate_number="CERT-2024-OK02",
                certificate_issued_date=datetime.now().date() - timedelta(days=9),
                certificate_ca_status="approved"
            ),
            models.CalibrationTask(
                campaign_id=campaign.id,
                equipment_id=eq1.id,
                tag=tag1.tag_number,
                description="Historical Audited Task",
                type="Calibration",
                calibration_type="in-situ",
                due_date=datetime.now().date() - timedelta(days=100),
                status="Completed",
                exec_date=datetime.now().date() - timedelta(days=105),
                is_temporary=0,
                seal_number="SBM-SEAL-OLD",
                seal_installation_date=datetime.now().date() - timedelta(days=105),
                seal_location="Terminal Block",
                certificate_number="CERT-2023-OLD01",
                certificate_issued_date=datetime.now().date() - timedelta(days=100),
                certificate_ca_status="approved"
            )
        ]
        db.add_all(tasks)
        db.commit()

        # Get their assigned IDs
        db.refresh(tasks[2])
        db.refresh(tasks[3])
        db.refresh(tasks[4])

        # 5.1 Calibration Results
        res_list = [
             models.CalibrationResult(
                 task_id=tasks[2].id, # Temporary CA Pending
                 standard_reading=100.0,
                 equipment_reading=100.5,
                 uncertainty=0.15,
                 certificate_url="/docs/certs/CERT-TMP.pdf",
             ),
             models.CalibrationResult(
                 task_id=tasks[3].id, # CA Approved, waiting on FC
                 standard_reading=50.0,
                 equipment_reading=50.0,
                 uncertainty=0.01,
                 certificate_url="/docs/certs/CERT-OK02.pdf",
             ),
             models.CalibrationResult(
                 task_id=tasks[4].id, # Completed
                 standard_reading=10.0,
                 equipment_reading=10.1,
                 uncertainty=0.015,
                 fc_evidence_url="/docs/evidence/FC-62PT1101-2301.xml",
                 certificate_url="/docs/certs/CERT-2023-OLD01.pdf",
                 notes="As-found within tolerance. Flow Computer audited successfully."
             )
        ]
        db.add_all(res_list)
        db.commit()

        # 5.1.5 Seal History
        seals = [
            models.SealHistory(
                 tag_id=tag1.id,
                 seal_number="SBM-SEAL-OLD",
                 seal_type="Lead",
                 seal_location="Terminal Block",
                 installation_date=datetime.now().date() - timedelta(days=105),
                 installed_by="Daniel Bernoulli",
                 is_active=0,
                 removal_date=datetime.now().date() - timedelta(days=5),
                 removed_by="Carlos Silva",
                 removal_reason="Routine Sensor Replacement"
            ),
            models.SealHistory(
                 tag_id=tag1.id,
                 seal_number="SBM-SEAL-NEW",
                 seal_type="Wire",
                 seal_location="Terminal Block",
                 installation_date=datetime.now().date() - timedelta(days=5),
                 installed_by="Carlos Silva",
                 is_active=1
            )
        ]
        db.add_all(seals)
        db.commit()
        print("M2 Mock Data Injected Successfully!")

    except Exception as e:
        print(f"Error seeding M2 data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_m2()
