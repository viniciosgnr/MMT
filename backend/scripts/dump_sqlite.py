
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import models
import datetime
import os

def dump_data():
    # Explicitly connect to SQLite regardless of .env or app/database.py
    # This prevents using the Postgres engine for dumping the legacy data
    sqlite_url = "sqlite:///./mmt_mvp.db"
    if not os.path.exists("./mmt_mvp.db"):
        print("Error: mmt_mvp.db not found in current directory.")
        return

    print(f"Connecting to {sqlite_url}...")
    engine_sqlite = create_engine(sqlite_url, connect_args={"check_same_thread": False})
    SessionSqlite = sessionmaker(bind=engine_sqlite)
    db = SessionSqlite()
    
    data = {}
    
    # List of models to dump
    models_to_dump = [
        ("equipments", models.Equipment),
        ("instrument_tags", models.InstrumentTag),
        ("equipment_tag_installations", models.EquipmentTagInstallation),
        ("equipment_certificates", models.EquipmentCertificate),
        ("calibration_campaigns", models.CalibrationCampaign),
        ("calibration_tasks", models.CalibrationTask),
        ("calibration_results", models.CalibrationResult),
        ("sample_points", models.SamplePoint),
        ("sampling_campaigns", models.SamplingCampaign),
        ("samples", models.Sample),
        ("sample_status_histories", models.SampleStatusHistory),
        ("sample_results", models.SampleResult),
        ("maintenance_records", models.MaintenanceRecord),
        ("installation_history", models.InstallationHistory),
        ("sync_sources", models.SyncSource),
        ("sync_jobs", models.SyncJob),
        ("operational_data", models.OperationalData),
        ("sync_status", models.SyncStatus),
        ("alerts", models.Alert),
        ("alert_configurations", models.AlertConfiguration),
        ("alert_recipients", models.AlertRecipient),
        ("planned_activities", models.PlannedActivity),
        ("failure_notifications", models.FailureNotification),
        ("fpso_failure_email_lists", models.FPSOFailureEmailList),
        ("report_types", models.ReportType),
        ("historical_reports", models.HistoricalReport),
        ("hierarchy_nodes", models.HierarchyNode),
        ("attribute_definitions", models.AttributeDefinition),
        ("attribute_values", models.AttributeValue),
        ("wells", models.Well),
        ("holidays", models.Holiday),
        ("stock_locations", models.StockLocation),
        ("config_parameters", models.ConfigParameter),
        ("maintenance_columns", models.MaintenanceColumn),
        ("maintenance_labels", models.MaintenanceLabel),
        ("maintenance_cards", models.MaintenanceCard),
        ("maintenance_comments", models.MaintenanceComment),
        ("maintenance_attachments", models.MaintenanceAttachment),
    ]

    for table_name, model_class in models_to_dump:
        print(f"Dumping {table_name}...")
        try:
            records = db.query(model_class).all()
            table_data = []
            for record in records:
                # Convert record to dict, handling dates
                record_dict = record.__dict__.copy()
                record_dict.pop('_sa_instance_state', None)
                
                # Serialize dates
                for key, value in record_dict.items():
                    if isinstance(value, (datetime.date, datetime.datetime)):
                        record_dict[key] = value.isoformat()
                
                table_data.append(record_dict)
            data[table_name] = table_data
        except Exception as e:
            print(f"Warning: Could not dump {table_name}: {e}")

    # Handle Association Tables manually since they are not Models
    with engine_sqlite.connect() as conn:
        associations = [
            "card_label_association",
            "card_connection_association",
            "card_equipment_association",
            "card_tag_association"
        ]
        for assoc in associations:
            print(f"Dumping {assoc}...")
            try:
                # Use SQL text or Table object
                # models.Base.metadata.tables might be empty if not bound? 
                # No, tables are defined in models.py regardless of bind.
                if assoc in models.Base.metadata.tables:
                    result = conn.execute(models.Base.metadata.tables[assoc].select())
                    rows = [dict(row._mapping) for row in result]
                    data[assoc] = rows
            except Exception as e:
                print(f"Warning: Could not dump {assoc}: {e}")

    with open("data_dump.json", "w") as f:
        json.dump(data, f, indent=4)
    
    print("Dump complete: data_dump.json")
    db.close()

if __name__ == "__main__":
    dump_data()
