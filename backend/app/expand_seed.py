from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
from . import models
from .database import SessionLocal, engine

def create_scenario_a_perfect(db: Session, campaign_id, sp_id):
    """Scenario A: The Perfect Equipment (High Volume History)"""
    print("Creating Scenario A (Perfect)...")
    
    # 1. Equipment
    eq = models.Equipment(
        serial_number="SN-PERFECT-001",
        model="Krohne Optisonic 3400",
        manufacturer="Krohne",
        equipment_type="Ultrasonic Flow Meter",
        status="Active",
        calibration_frequency_months=12
    )
    db.add(eq)
    db.commit()
    db.refresh(eq)

    # 2. Tag & Install
    tag = models.InstrumentTag(
        tag_number="TOTAL-EXP-01", 
        description="Total Export Fiscal Meter", 
        area="Metering Skid", 
        service="Export",
        sample_point_id=sp_id
    )
    db.add(tag)
    db.commit()
    db.refresh(tag)

    install = models.EquipmentTagInstallation(equipment_id=eq.id, tag_id=tag.id, is_active=1)
    db.add(install)

    # 3. Rich Calibration History (3 years)
    for i in range(3):
        task = models.CalibrationTask(
            campaign_id=campaign_id,
            equipment_id=eq.id,
            tag=tag.tag_number,
            description=f"Annual Calibration 202{2+i}",
            due_date=datetime.now() - timedelta(days=365*(2-i)),
            status="Executed",
            exec_date=datetime.now() - timedelta(days=365*(2-i))
        )
        db.add(task)
        db.commit() # Get ID
        
        # Add Success Result
        res = models.CalibrationResult(
            task_id=task.id,
            standard_reading=10.0,
            equipment_reading=10.0,
            uncertainty=0.01,
            notes="Perfect linearity found.",
            approved_by="Metrology Manager",
            approved_at=task.exec_date
        )
        db.add(res)
    
    # 4. Maintenance (Routine only)
    card = models.MaintenanceCard(
        title="Routine Greasing - SN-PERFECT-001",
        description="Annual greasing of bearings.",
        fpso="FPSO PARATY",
        status="Completed",
        responsible="Maintenance Team",
        column_id=1 # Backlog or similar
    )
    card.linked_equipments = [eq]
    db.add(card)

    db.commit()
    return eq

def create_scenario_b_problematic(db: Session, campaign_id, sp_id):
    """Scenario B: The Problem Child (Failures, Rejections, Maintenance)"""
    print("Creating Scenario B (Problematic)...")

    # 1. Equipment
    eq = models.Equipment(
        serial_number="SN-PROBLEM-X99",
        model="Rosemount 8750",
        manufacturer="Rosemount",
        equipment_type="Magnetic Flow Meter",
        status="Maintenance", # In Maintenance
        calibration_frequency_months=6
    )
    db.add(eq)
    db.commit()
    db.refresh(eq)

    # 2. Tag
    tag = models.InstrumentTag(
        tag_number="BAD-ACTOR-01", 
        description="Water Injection Meter", 
        area="Injection Skid", 
        service="Injection",
        sample_point_id=sp_id
    )
    db.add(tag)
    db.commit()
    db.refresh(tag)

    install = models.EquipmentTagInstallation(equipment_id=eq.id, tag_id=tag.id, is_active=1)
    db.add(install)

    # 3. Failed Calibration
    task = models.CalibrationTask(
        campaign_id=campaign_id,
        equipment_id=eq.id,
        tag=tag.tag_number,
        description="Urgent Verification",
        due_date=datetime.now() - timedelta(days=5),
        status="Executed - Rejected", # Failed
        exec_date=datetime.now() - timedelta(days=5)
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # Add Failed Result
    dict_fail = models.CalibrationResult(
        task_id=task.id,
        standard_reading=10.0,
        equipment_reading=10.8, # Failed
        notes="Error > 5%. Failed.",
        approved_by="Metrology Manager"
    )
    db.add(dict_fail)

    # 4. Auto-Failure Notification (Simulated M2->M9)
    fail = models.FailureNotification(
        equipment_id=eq.id,
        tag=tag.tag_number,
        fpso_name="FPSO PARATY",
        failure_date=datetime.now() - timedelta(days=5),
        description="Calibration Failed (Error > 5%). Sensor drift detected.",
        impact="High",
        status="Open",
        cause="Sensor Drift",
        responsible="Daniel Bernoulli"
    )
    db.add(fail)

    # 5. Open Maintenance Card (M4)
    card = models.MaintenanceCard(
        title="Replace Sensor SN-PROBLEM-X99",
        description="Calibration failed. Replace sensor module immediately.",
        fpso="FPSO PARATY",
        status="In Progress",
        due_date=datetime.now() + timedelta(days=2),
        responsible="Maintenance Lead",
        column_id=2 # In Prep
    )
    card.linked_equipments = [eq]
    db.add(card)

    db.commit()
    return eq

def create_scenario_c_synced(db: Session, campaign_id, sp_id):
    """Scenario C: Synced Data Impact"""
    print("Creating Scenario C (Synced)...")
    
    eq = models.Equipment(
        serial_number="SN-SYNC-ALERT-01",
        model="Coriolis Elite",
        manufacturer="Micro Motion",
        equipment_type="Mass Flow Meter",
        status="Active",
        calibration_frequency_months=12
    )
    db.add(eq)
    db.commit()
    db.refresh(eq)

    tag = models.InstrumentTag(
        tag_number="SYNC-TEST-01", 
        description="Oil Offload Meter", 
        area="Offload", 
        service="Oil",
        sample_point_id=sp_id
    )

    db.add(tag)
    db.commit()
    db.refresh(tag)

    install = models.EquipmentTagInstallation(equipment_id=eq.id, tag_id=tag.id, is_active=1)
    db.add(install)

    # Task with Sync Alert
    task = models.CalibrationTask(
        campaign_id=campaign_id,
        equipment_id=eq.id,
        tag=tag.tag_number,
        description="Planned Calibration - [System] Sync Alert: Bad data quality received on 2024-02-01. Value: 0.0 kg/h",
        due_date=datetime.now() + timedelta(days=30),
        status="Planned"
    )
    db.add(task)
    db.commit()

def expand_samples(db: Session, sp_id):
    """Generate 15 samples for a sample point to show trends."""
    print(f"Generating 15 samples for Sample Point {sp_id}...")
    
    statuses = ["Approved", "Approved", "Approved", "Rejected", "Approved"]
    
    for i in range(15):
        date_offset = 15 - i
        s = models.Sample(
            sample_id=f"SAM-HIST-{i:03d}",
            sample_point_id=sp_id,
            type="Oil",
            status="Report Issued",
            responsible="System (Seed)",
            validation_status=statuses[i % len(statuses)], # Rotate statuses
            sampling_date=datetime.now().date() - timedelta(days=date_offset*7) # Weekly samples
        )
        db.add(s)
        
        # Add result
        res_val = 80 + (i * 0.5) + (random.random() * 2) # Trending value
        db.add(models.SampleResult(sample_id=s.id, parameter="BS&W", value=round(res_val, 2), unit="%"))
    
    db.commit()

def run_expansion():
    print("Starting Data Expansion...")
    db = SessionLocal()
    try:
        # FIX: Reset sequences to avoid UniqueViolation
        print("Resetting sequences...")
        from sqlalchemy import text # Import here or at top
        tables = [
            "equipments", 
            "instrument_tags", 
            "sample_points", 
            "calibration_tasks", 
            "maintenance_cards", 
            "failure_notifications", 
            "samples",
            "equipment_tag_installations",
            "calibration_results"
        ]
        for t in tables:
            try:
                db.execute(text(f"SELECT setval('{t}_id_seq', (SELECT MAX(id) FROM {t}) + 1);"))
            except Exception as e:
                print(f"Warning: Could not reset sequence for {t}: {e}")
        db.commit()

        # Prerequisites
        campaign = db.query(models.CalibrationCampaign).first()
        if not campaign:
            print("No campaign found. Please seed basic data first.")
            return

        # Shared Sample Point - Get or Create
        sp = db.query(models.SamplePoint).filter(models.SamplePoint.tag_number == "SP-EXPAND-01").first()
        if not sp:
            sp = models.SamplePoint(
                tag_number="SP-EXPAND-01",
                description="Expansion Test Point",
                fpso_name="FPSO PARATY",
                fluid_type="Oil",
                is_operational=1
            )
            db.add(sp)
            db.commit()
            db.refresh(sp)
            print("Created Shared Sample Point.")
        else:
            print("Shared Sample Point already exists.")

        # Create scenarios (Idempotent checks inside)
        if not db.query(models.Equipment).filter(models.Equipment.serial_number == "SN-PERFECT-001").first():
            create_scenario_a_perfect(db, campaign.id, sp.id)
        else:
            print("Scenario A already exists.")

        if not db.query(models.Equipment).filter(models.Equipment.serial_number == "SN-PROBLEM-X99").first():
            create_scenario_b_problematic(db, campaign.id, sp.id)
        else:
            print("Scenario B already exists.")
            
        if not db.query(models.Equipment).filter(models.Equipment.serial_number == "SN-SYNC-ALERT-01").first():
            create_scenario_c_synced(db, campaign.id, sp.id)
        else:
            print("Scenario C already exists.")
        
        # Expand samples for the shared point
        expand_samples(db, sp.id)

        print("Data Expansion Completed Successfully!")

    except Exception as e:
        print(f"Error expanding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_expansion()
