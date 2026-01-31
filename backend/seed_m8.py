from app import models
from app.database import SessionLocal
from datetime import datetime, timedelta

def seed_m8():
    db = SessionLocal()
    try:
        # Get some equipment IDs
        eq3 = db.query(models.Equipment).filter(models.Equipment.serial_number == "KROHNE-2022-X1").first()
        eq1 = db.query(models.Equipment).filter(models.Equipment.serial_number == "SN-PT1101-2023").first()
        
        activities = [
            models.PlannedActivity(
                type=models.ActivityType.EXEC_CAL_INS.value,
                title="USM Diagnostic Check",
                description="Annual diagnostic check for fiscal USM.",
                equipment_id=eq3.id,
                fpso_name="FPSO ILHABELA",
                scheduled_date=datetime.now() + timedelta(days=2),
                responsible="Marcos G."
            ),
            models.PlannedActivity(
                type=models.ActivityType.TAKE_SAMPLE.value,
                title="Weekly Oil Sample - Main Export",
                description="Regulatory sampling for BSW and API.",
                fpso_name="FPSO PARATY",
                scheduled_date=datetime.now() + timedelta(days=-2), # Overdue
                responsible="Daniel Bernoulli"
            ),
            models.PlannedActivity(
                type=models.ActivityType.ISSUE_CERT.value,
                title="Issue Calibration Certificate - PT1101",
                description="Generate and sign cert for PT1101.",
                equipment_id=eq1.id,
                fpso_name="FPSO SAQUAREMA",
                scheduled_date=datetime.now() + timedelta(days=1),
                responsible="Marcos G."
            ),
            models.PlannedActivity(
                type=models.ActivityType.UPDATE_FLOW_COMPUTER.value,
                title="Update Flow-X Configuration",
                description="Update K-factors in FC based on latest calibration.",
                fpso_name="FPSO ILHABELA",
                scheduled_date=datetime.now() + timedelta(days=4),
                responsible="Daniel Bernoulli"
            ),
            models.PlannedActivity(
                type=models.ActivityType.EXEC_CAL_INS.value,
                title="Mitigated: Metering Skid Inspection",
                description="Visual inspection of skids.",
                fpso_name="FPSO PARATY",
                scheduled_date=datetime.now() + timedelta(days=5),
                responsible="Marcos G.",
                status="Mitigated",
                mitigation_reason="Skid currently under lockdown for painting.",
                new_due_date=datetime.now() + timedelta(days=30),
                mitigated_at=datetime.now()
            )
        ]
        
        db.add_all(activities)
        db.commit()
        print("M8 sample activities added.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_m8()
