from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from . import models
from .database import SessionLocal, engine

def seed_data():
    # Create tables if they don't exist
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(models.Equipment).first():
            print("Database already contains data, skipping seed.")
            return

        print("Seeding database with sample MMT data...")

        # 1. Physical Equipment (Serial Numbers)
        equipments = [
            models.Equipment(
                serial_number="SN-PT1101-2023",
                model="Rosemount 3051S",
                manufacturer="Emerson",
                equipment_type="Pressure Transmitter",
                status=models.EquipmentStatus.ACTIVE.value,
                calibration_frequency_months=12
            ),
            models.Equipment(
                serial_number="SN-TT1102-B",
                model="Rosemount 644",
                manufacturer="Emerson",
                equipment_type="Temperature Transmitter",
                status=models.EquipmentStatus.ACTIVE.value,
                calibration_frequency_months=24
            ),
            models.Equipment(
                serial_number="KROHNE-2022-X1",
                model="Krohne Altosonic V12",
                manufacturer="Krohne",
                equipment_type="Ultrasonic Flow Meter",
                status=models.EquipmentStatus.ACTIVE.value,
                calibration_frequency_months=12
            ),
            models.Equipment(
                serial_number="SN-PT2201-W",
                model="ABB 266MST",
                manufacturer="ABB",
                equipment_type="Pressure Transmitter",
                status=models.EquipmentStatus.MAINTENANCE.value,
                calibration_frequency_months=12
            )
        ]
        db.add_all(equipments)
        db.commit()

        # Refresh to get IDs
        eq1 = db.query(models.Equipment).filter(models.Equipment.serial_number == "SN-PT1101-2023").first()
        eq2 = db.query(models.Equipment).filter(models.Equipment.serial_number == "SN-TT1102-B").first()
        eq3 = db.query(models.Equipment).filter(models.Equipment.serial_number == "KROHNE-2022-X1").first()
        eq4 = db.query(models.Equipment).filter(models.Equipment.serial_number == "SN-PT2201-W").first()

        # 1.1 Instrument Tags (Logical Locations)
        tags = [
            models.InstrumentTag(tag_number="62-PT-1101", description="Export Gas Pressure", area="Main Deck", service="Gas Export"),
            models.InstrumentTag(tag_number="62-TT-1102", description="Oil Rundown Temp", area="Separator Skid", service="Oil Rundown"),
            models.InstrumentTag(tag_number="62-FT-1103", description="Fiscal Gas Flow", area="Metering Skid", service="Gas Export"),
            models.InstrumentTag(tag_number="65-PT-2201", description="Injection Pressure", area="Water Injection Skid", service="Water Injection")
        ]
        db.add_all(tags)
        db.commit()
        
        tag1 = db.query(models.InstrumentTag).filter(models.InstrumentTag.tag_number == "62-PT-1101").first()
        tag2 = db.query(models.InstrumentTag).filter(models.InstrumentTag.tag_number == "62-TT-1102").first()
        tag3 = db.query(models.InstrumentTag).filter(models.InstrumentTag.tag_number == "62-FT-1103").first()
        tag4 = db.query(models.InstrumentTag).filter(models.InstrumentTag.tag_number == "65-PT-2201").first()

        # 1.2 Installations (Linking S/N to Tags)
        installations = [
            models.EquipmentTagInstallation(equipment_id=eq1.id, tag_id=tag1.id, installed_by="Daniel Bernoulli", is_active=1),
            models.EquipmentTagInstallation(equipment_id=eq2.id, tag_id=tag2.id, installed_by="Daniel Bernoulli", is_active=1),
            models.EquipmentTagInstallation(equipment_id=eq3.id, tag_id=tag3.id, installed_by="Daniel Bernoulli", is_active=1)
        ]
        db.add_all(installations)
        db.commit()

        # 2. Calibration Campaigns
        campaign = models.CalibrationCampaign(
            name="Q1 2024 Campaign - PARATY",
            fpso_name="FPSO PARATY",
            start_date=datetime.now().date() - timedelta(days=10),
            status=models.CampaignStatus.ACTIVE.value,
            responsible="Daniel Bernoulli",
            description="Routine quarterly calibration campaign."
        )
        db.add(campaign)
        db.commit()
        db.refresh(campaign)

        # 3. Calibration Tasks
        tasks = [
            models.CalibrationTask(
                campaign_id=campaign.id,
                equipment_id=eq1.id,
                tag=tag1.tag_number,
                description="Quarterly Calibration",
                due_date=datetime.now().date() - timedelta(days=2),
                status=models.CalibrationTaskStatus.EXECUTED.value,
                exec_date=datetime.now().date() - timedelta(days=1)
            ),
            models.CalibrationTask(
                campaign_id=campaign.id,
                equipment_id=eq3.id,
                tag=tag3.tag_number,
                description="Annual Verification",
                due_date=datetime.now().date() + timedelta(days=5),
                status=models.CalibrationTaskStatus.SCHEDULED.value,
                plan_date=datetime.now().date() + timedelta(days=5)
            )
        ]
        db.add_all(tasks)
        db.commit()

        # 4. Sampling Campaigns
        sampling_campaign = models.SamplingCampaign(
            name="Monthly Oil Analysis Jan/24",
            fpso_name="FPSO PARATY",
            start_date=datetime.now().date() - timedelta(days=5),
            status=models.CampaignStatus.COMPLETED.value,
            responsible="Daniel Bernoulli"
        )
        db.add(sampling_campaign)
        db.commit()
        db.refresh(sampling_campaign)

        # 5. Samples
        sample = models.Sample(
            campaign_id=sampling_campaign.id,
            sample_id="OIL-2401-001",
            type="Oil",
            collection_date=datetime.now().date() - timedelta(days=4),
            location="Oil Export Header",
            status=models.SampleStatus.ANALYZED.value,
            responsible="Daniel Bernoulli",
            compliance_status="Compliant"
        )
        db.add(sample)
        db.commit()

        # 6. Maintenance Records
        maint = models.MaintenanceRecord(
            equipment_id=eq4.id,
            tag=tag4.tag_number,
            description="Pressure Transmitter Repair",
            vendor="Emerson Service Center",
            sent_date=datetime.now().date() - timedelta(days=15),
            expected_return=datetime.now().date() + timedelta(days=15),
            status=models.MaintenanceStatus.AT_VENDOR.value,
            reason="Electronics Failure"
        )
        db.add(maint)
        db.commit()

        # 7. Installation History (Legacy record type replaced by tag-based history)
        # We'll just create a historical installation for eq1/tag1
        hist = models.EquipmentTagInstallation(
            equipment_id=eq1.id,
            tag_id=tag1.id,
            installation_date=datetime.now() - timedelta(days=365),
            removal_date=datetime.now() - timedelta(days=364),
            installed_by="Daniel Bernoulli",
            is_active=0
        )
        db.add(hist)
        db.commit()

        # 8. Planned Activities
        activities = [
            models.PlannedActivity(
                type=models.ActivityType.CALIBRATION.value,
                title="Gas Export USM Verification",
                description="Full verification of the USM metering system.",
                equipment_id=eq3.id,
                fpso_name="FPSO PARATY",
                scheduled_date=datetime.now() + timedelta(days=5),
                responsible="Daniel Bernoulli"
            ),
            models.PlannedActivity(
                type=models.ActivityType.SAMPLING.value,
                title="Bimonthly Gas Sampling",
                description="Gas analysis for fiscal reporting.",
                fpso_name="FPSO PARATY",
                scheduled_date=datetime.now() + timedelta(days=10),
                responsible="Daniel Bernoulli"
            )
        ]
        db.add_all(activities)
        db.commit()

        # 9. Sync Status
        syncs = [
            models.SyncStatus(
                module_name="M1 - Equipment",
                last_sync=datetime.now() - timedelta(hours=2),
                status=models.SyncStatusEnum.SYNCED.value,
                records_synced=150
            ),
            models.SyncStatus(
                module_name="M2 - Calibration",
                last_sync=datetime.now() - timedelta(hours=1),
                status=models.SyncStatusEnum.SYNCED.value,
                records_synced=45
            )
        ]
        db.add_all(syncs)
        db.commit()

        # 10. Alerts
        alerts = [
            models.Alert(
                type=models.AlertType.CALIBRATION.value,
                severity=models.AlertSeverity.WARNING.value,
                title="Upcoming Calibration",
                message="Equipment 62-FT-1103 is due in 5 days.",
                equipment_id=eq3.id
            ),
            models.Alert(
                type=models.AlertType.MAINTENANCE.value,
                severity=models.AlertSeverity.CRITICAL.value,
                title="Critical Maintenance Delayed",
                message="Equipment 65-PT-2201 is overdue from vendor Emerson.",
                equipment_id=eq4.id
            )
        ]
        db.add_all(alerts)
        db.commit()
        
        # 11. Failure Notifications
        failures = [
             models.FailureNotification(
                equipment_id=eq2.id,
                tag=tag2.tag_number,
                fpso_name="FPSO PARATY",
                failure_date=datetime.now() - timedelta(days=30),
                description="Temperature sensor drift outside tolerance.",
                impact="Low",
                corrective_action="Sensor replaced and calibrated.",
                responsible="Daniel Bernoulli",
                anp_notification_number="ANP-2024-001",
                anp_classification="Tolerável",
                anp_status="Submitted"
            )
        ]
        db.add_all(failures)
        db.commit()

        # 12. M11 - Hierarchy Nodes
        fpso_node = models.HierarchyNode(tag="FPSO PARATY", description="Fiscal Metering Vessel", level_type="FPSO")
        db.add(fpso_node)
        db.commit()
        db.refresh(fpso_node)

        gas_sys = models.HierarchyNode(tag="Gas Export", description="Gas Fiscal Export System", level_type="System", parent_id=fpso_node.id)
        oil_sys = models.HierarchyNode(tag="Oil Export", description="Oil Fiscal Export System", level_type="System", parent_id=fpso_node.id)
        db.add_all([gas_sys, oil_sys])
        db.commit()
        db.refresh(gas_sys)

        press_var = models.HierarchyNode(tag="Export Pressure", description="Process Pressure Loop", level_type="Variable", parent_id=gas_sys.id)
        db.add(press_var)
        db.commit()
        db.refresh(press_var)

        pt_device = models.HierarchyNode(tag="62-PT-1101", description="Rosemount 3051S", level_type="Device", parent_id=press_var.id)
        db.add(pt_device)
        db.commit()
        db.refresh(pt_device)

        # Link Tag to Hierarchy
        tag1.hierarchy_node_id = pt_device.id
        db.commit()

        # 14. M4 - Onshore Maintenance Kanban
        print("Seeding Kanban board...")
        
        # Columns
        cols = [
            models.MaintenanceColumn(name="Backlog", order=0),
            models.MaintenanceColumn(name="In Preparation", order=1),
            models.MaintenanceColumn(name="At Vendor", order=2),
            models.MaintenanceColumn(name="Calibrating", order=3),
            models.MaintenanceColumn(name="Returned / Final QC", order=4),
            models.MaintenanceColumn(name="Completed", order=5)
        ]
        db.add_all(cols)
        db.commit()
        
        # Get column references
        col_backlog = db.query(models.MaintenanceColumn).filter(models.MaintenanceColumn.name == "Backlog").first()
        col_vendor = db.query(models.MaintenanceColumn).filter(models.MaintenanceColumn.name == "At Vendor").first()
        
        # Labels
        labels = [
            models.MaintenanceLabel(name="Critical", color="#EF4444"), # Red
            models.MaintenanceLabel(name="Routine", color="#3B82F6"),  # Blue
            models.MaintenanceLabel(name="Calibration", color="#10B981"), # Green
            models.MaintenanceLabel(name="Repair", color="#F59E0B"),    # Amber
            models.MaintenanceLabel(name="Urgent", color="#7C3AED")     # Purple
        ]
        db.add_all(labels)
        db.commit()
        
        label_critical = db.query(models.MaintenanceLabel).filter(models.MaintenanceLabel.name == "Critical").first()
        label_calib = db.query(models.MaintenanceLabel).filter(models.MaintenanceLabel.name == "Calibration").first()
        
        # Sample Cards
        card1 = models.MaintenanceCard(
            title="Recalibrate USM 62-FT-1103",
            description="Annual calibration required for fiscal USM. Must be sent to Krohne Brazil.",
            fpso="FPSO PARATY",
            status="Not Completed",
            due_date=datetime.utcnow() + timedelta(days=15),
            responsible="Daniel Bernoulli",
            column_id=col_vendor.id
        )
        card1.labels = [label_critical, label_calib]
        card1.linked_equipments = [eq3]
        card1.linked_tags = [tag3]
        
        card2 = models.MaintenanceCard(
            title="Repair PT 65-PT-2201",
            description="Intermittent signal issues. Check electronics and diaphragm.",
            fpso="FPSO SEPETIBA",
            status="Not Completed",
            due_date=datetime.utcnow() + timedelta(days=5),
            responsible="Daniel Bernoulli",
            column_id=col_backlog.id
        )
        card2.linked_equipments = [eq4]
        
        db.add_all([card1, card2])
        db.commit()
        
        # Add a comment
        comment = models.MaintenanceComment(
            card_id=card1.id,
            text="Waiting for customs clearance for Krohne Brazilian facility.",
            author="Daniel Bernoulli"
        )
        db.add(comment)
        db.commit()

        print("Seeding completed successfully.")
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
