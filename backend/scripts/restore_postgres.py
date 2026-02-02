
import json
import os
import datetime
import decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from app import models, database

# Explicitly load .env
from dotenv import load_dotenv
load_dotenv(dotenv_path="../.env")

# Must use the new Postgres URL for this script
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("Error: DATABASE_URL not found.")
    exit(1)

# Setup independent engine/session for restore
engine_pg = create_engine(DATABASE_URL)
SessionPG = sessionmaker(bind=engine_pg)

def restore_data():
    print("Starting Restore Process...")
    
    # 1. Create Tables in Target DB (Idempotent)
    print("Creating tables in Postgres...")
    models.Base.metadata.create_all(bind=engine_pg)
    
    db = SessionPG()
    
    # Load JSON
    try:
        with open("data_dump.json", "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: data_dump.json not found.")
        return

    # Helper to parse dates
    def parse_value(key, value):
        if value is None:
            return None
        # Naive check for date strings (ISO format)
        if isinstance(value, str):
            # Try datetime
            try:
                if "T" in value:
                     return datetime.datetime.fromisoformat(value)
                elif "-" in value and len(value) == 10:
                     return datetime.date.fromisoformat(value)
            except ValueError:
                pass
        return value

    # Order is Critical for FKs
    restore_order = [
         # Base Config
        ("report_types", models.ReportType),
        ("sync_sources", models.SyncSource),
        ("stock_locations", models.StockLocation),
        ("maintenance_columns", models.MaintenanceColumn),
        ("maintenance_labels", models.MaintenanceLabel),
        ("attribute_definitions", models.AttributeDefinition),
        ("hierarchy_nodes", models.HierarchyNode), # Self-referential, might need 2 passes or careful sort?
                                                   # Assuming nodes are dumped in order of creation (parents first)
        
        # Core Assets
        ("equipments", models.Equipment),
        ("sample_points", models.SamplePoint),
        ("instrument_tags", models.InstrumentTag), # Links to hierarchy, sample_point
        ("wells", models.Well),
        ("holidays", models.Holiday),
        ("config_parameters", models.ConfigParameter),

        # Relationships L1
        ("equipment_tag_installations", models.EquipmentTagInstallation),
        ("equipment_certificates", models.EquipmentCertificate),
        ("alert_configurations", models.AlertConfiguration),
        
        # Campaigns
        ("calibration_campaigns", models.CalibrationCampaign),
        ("sampling_campaigns", models.SamplingCampaign),
        
        # Tasks & Samples
        ("calibration_tasks", models.CalibrationTask),
        ("samples", models.Sample),
        ("maintenance_cards", models.MaintenanceCard), # Self-ref
        ("planned_activities", models.PlannedActivity),
        
        # Results & Records
        ("calibration_results", models.CalibrationResult),
        ("sample_status_histories", models.SampleStatusHistory),
        ("sample_results", models.SampleResult),
        ("maintenance_records", models.MaintenanceRecord),
        
        # Others
        ("installation_history", models.InstallationHistory),
        ("sync_jobs", models.SyncJob),
        ("operational_data", models.OperationalData),
        ("sync_status", models.SyncStatus),
        ("alerts", models.Alert),
        ("failure_notifications", models.FailureNotification),
        ("fpso_failure_email_lists", models.FPSOFailureEmailList),
        ("historical_reports", models.HistoricalReport),
        ("attribute_values", models.AttributeValue),
        ("alert_recipients", models.AlertRecipient),
        ("maintenance_comments", models.MaintenanceComment),
        ("maintenance_attachments", models.MaintenanceAttachment),
    ]

    # Map table name to keys in JSON
    for table_name, model_class in restore_order:
        if table_name not in data:
            continue
            
        print(f"Restoring {table_name} ({len(data[table_name])} records)...")
        records = data[table_name]
        
        for record_data in records:
            # Clean data
            clean_data = {}
            for k, v in record_data.items():
                clean_data[k] = parse_value(k, v)
            
            # Check if exists (Idempotency - simplistic check by ID)
            # Given we are likely starting fresh, we can skip check or allow failure
            # But let's check
            existing = db.query(model_class).filter_by(id=clean_data['id']).first()
            if not existing:
                obj = model_class(**clean_data)
                db.add(obj)
        
        try:
            db.commit()
        except Exception as e:
            print(f"Error committing {table_name}: {e}")
            db.rollback()

    # Restore Associations (Raw SQL)
    associations = [
        "card_label_association",
        "card_connection_association",
        "card_equipment_association",
        "card_tag_association"
    ]
    
    with engine_pg.connect() as conn:
        for assoc in associations:
            if assoc in data and data[assoc]:
                print(f"Restoring {assoc}...")
                rows = data[assoc]
                # Insert statement
                try:
                    conn.execute(
                        models.Base.metadata.tables[assoc].insert(),
                        rows
                    )
                    conn.commit()
                except Exception as e:
                    print(f"Error inserting {assoc} (likely duplicates): {e}")

    print("Restore complete.")
    db.close()

if __name__ == "__main__":
    restore_data()
