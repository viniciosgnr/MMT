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

        # 4. Sampling Campaigns (M3)
        sampling_campaign = models.SamplingCampaign(
            name="Quarterly Gas Analysis - Q1 2024",
            fpso_name="FPSO PARATY",
            start_date=datetime.now().date() - timedelta(days=10),
            status=models.CampaignStatus.ACTIVE.value,
            responsible="Daniel Bernoulli"
        )
        db.add(sampling_campaign)
        db.commit()
        db.refresh(sampling_campaign)

        # Legacy section 5 removed as it is handled by the new M3 seeding in section 16.
        pass

        # 5.1 Calibration Results (M2) - Needed for M7 Export
        res1 = models.CalibrationResult(
            task_id=tasks[0].id,
            standard_reading=10.0,
            equipment_reading=10.1,
            uncertainty=0.015,
            uncertainty_report_url="/docs/uncertainty/UNC-62PT1101-2401.pdf",
            fc_evidence_url="/docs/evidence/FC-62PT1101-2401.png",
            certificate_url="/docs/certs/CERT-62PT1101-2401.pdf",
            approved_by="Metrology Manager",
            approved_at=datetime.utcnow(),
            notes="As-found within tolerance."
        )
        db.add(res1)
        db.commit()

        # 5.2 Equipment Certificates (M1)
        cert1 = models.EquipmentCertificate(
            equipment_id=eq1.id,
            certificate_number="CERT-PT-2023-001",
            issue_date=datetime.now().date() - timedelta(days=100),
            expiry_date=datetime.now().date() + timedelta(days=265),
            file_path="/docs/certs/ Rosemount_3051S_SN123.pdf"
        )
        db.add(cert1)
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

        # 7. Installation History
        hist1 = models.InstallationHistory(
            equipment_id=eq1.id,
            location=tag1.tag_number,
            installation_date=datetime.now() - timedelta(days=365),
            installed_by="Daniel Bernoulli",
            reason="Initial Commissioning",
            notes="System startup."
        )
        hist2 = models.InstallationHistory(
            equipment_id=eq2.id,
            location=tag2.tag_number,
            installation_date=datetime.now() - timedelta(days=200),
            installed_by="Daniel Bernoulli",
            reason="Replacement",
            notes="Previous unit failed drift test."
        )
        db.add_all([hist1, hist2])
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

        # 10. Alerts (M6)
        alerts = [
            models.Alert(
                type="System Configuration",
                severity=models.AlertSeverity.CRITICAL.value,
                title="K-Factor Mismatch",
                message="Flowmeter T62-FT-1103 configured K-Factor (150.5) differs from last certificate (152.1).",
                fpso_name="FPSO MARICÁ",
                tag_number="T62-FT-1103",
                equipment_id=eq3.id
            ),
            models.Alert(
                type="Metrological Confirmation",
                severity=models.AlertSeverity.WARNING.value,
                title="Pending Calibration Certificate",
                message="Calibration executed for T62-PT-1101 on 2024-01-28 but certificate is not yet uploaded.",
                fpso_name="FPSO MARICÁ",
                tag_number="T62-PT-1101",
                equipment_id=eq1.id
            ),
            models.Alert(
                type="Sampling",
                severity=models.AlertSeverity.INFO.value,
                title="Sampling Due Soon",
                message="Oil sampling for 'FPSO SAQUAREMA' scheduled for tomorrow.",
                fpso_name="FPSO SAQUAREMA",
                tag_number=None
            ),
            models.Alert(
                type="Failure Notification",
                severity=models.AlertSeverity.CRITICAL.value,
                title="Failure Notification Overdue",
                message="Failure #1024 has been open for > 240h without a final report.",
                fpso_name="FPSO SEPETIBA",
                tag_number="65-PT-2201"
            )
        ]
        db.add_all(alerts)
        db.commit()

        # 10.1 Alert Configuration (M6.2)
        configs = [
            models.AlertConfiguration(
                fpso_name="FPSO MARICÁ",
                alert_type="System Configuration",
                notify_email=1,
                notify_whatsapp=1,
                notify_in_app=1
            ),
            models.AlertConfiguration(
                fpso_name="FPSO SAQUAREMA",
                alert_type="Metrological Confirmation",
                notify_email=1,
                notify_whatsapp=0,
                notify_in_app=1
            )
        ]
        db.add_all(configs)
        db.commit()
        db.refresh(configs[0])
        db.refresh(configs[1])

        recipients = [
            models.AlertRecipient(config_id=configs[0].id, user_name="Daniel Bernoulli", email="daniel.bernoulli@sbm.com", whatsapp_number="+552199999999", receive_in_app=1),
            models.AlertRecipient(config_id=configs[0].id, user_name="Maintenance Lead", email="maint.lead@sbm.com", receive_in_app=1),
            models.AlertRecipient(config_id=configs[1].id, user_name="Metrology Specialist", email="metro.spec@sbm.com", receive_in_app=1)
        ]
        db.add_all(recipients)
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

        # 16. M3 - Chemical Analysis (Sample Points & Lifecycle)
        print("Seeding Chemical Analysis (M3)...")
        # Sample Points
        sp1 = models.SamplePoint(
            tag_number="62-SP-1101", 
            description="Gas Export Sample Point", 
            fpso_name="FPSO PARATY", 
            fluid_type="Gas",
            is_operational=1,
            sampling_interval_days=30,
            validation_method_implemented=1
        )
        sp2 = models.SamplePoint(
            tag_number="65-SP-2101", 
            description="Oil Export Sample Point", 
            fpso_name="FPSO SEPETIBA", 
            fluid_type="Oil",
            is_operational=1,
            sampling_interval_days=15,
            validation_method_implemented=0
        )
        db.add_all([sp1, sp2])
        db.commit()
        db.refresh(sp1)
        
        # Link meter to sample point
        tag1.sample_point_id = sp1.id
        db.commit()

        # Create a Sample with History
        s1 = models.Sample(
            sample_id="SAM-2024-001",
            sample_point_id=sp1.id,
            type="Gas",
            status=models.SampleStatus.REPORT_UNDER_VALIDATION,
            responsible="Daniel Bernoulli",
            planned_date=datetime.now().date() - timedelta(days=20),
            sampling_date=datetime.now().date() - timedelta(days=15),
            disembark_date=datetime.now().date() - timedelta(days=14),
            delivery_date=datetime.now().date() - timedelta(days=12),
            report_issue_date=datetime.now().date() - timedelta(days=2),
            lab_report_url="/reports/lab_gas_001.pdf"
        )
        db.add(s1)
        db.commit()
        db.refresh(s1)

        # History for s1
        history_steps = [
            (models.SampleStatus.PLANNED, "Initial planning", datetime.now() - timedelta(days=20)),
            (models.SampleStatus.SAMPLED, "Sample taken on board", datetime.now() - timedelta(days=15)),
            (models.SampleStatus.DISEMBARK_PREP, "Preparing cylinder for disembark", datetime.now() - timedelta(days=14.5)),
            (models.SampleStatus.DISEMBARK_LOGISTICS, "Cylinder on the boat to shore", datetime.now() - timedelta(days=14)),
            (models.SampleStatus.WAREHOUSE, "Arrived at onshore warehouse", datetime.now() - timedelta(days=13)),
            (models.SampleStatus.LOGISTICS_TO_VENDOR, "Sent to Lab-Tech Onshore", datetime.now() - timedelta(days=12.5)),
            (models.SampleStatus.DELIVERED_AT_VENDOR, "Laboratory confirmed receipt", datetime.now() - timedelta(days=12)),
            (models.SampleStatus.REPORT_ISSUED, "Report issued by lab", datetime.now() - timedelta(days=2)),
            (models.SampleStatus.REPORT_UNDER_VALIDATION, "SBM/ME analyzing results", datetime.now() - timedelta(days=1))
        ]
        
        for ost, ocm, oda in history_steps:
            db.add(models.SampleStatusHistory(sample_id=s1.id, status=ost, comments=ocm, entered_at=oda))
        
        # Add a Result to s1 for validation testing
        res1 = models.SampleResult(sample_id=s1.id, parameter="Methane Content", value=89.5, unit="%")
        res2 = models.SampleResult(sample_id=s1.id, parameter="H2S Content", value=2.1, unit="ppm")
        db.add_all([res1, res2])
        db.commit()

        print("Seeding completed successfully.")
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
