import sys
import os
from datetime import datetime, timedelta

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.database import SessionLocal
from backend.app import models

def seed_m10():
    db = SessionLocal()
    try:
        # 1. Create Report Types
        types = [
            models.ReportType(name="Offloading Report", description="Reports generated after each offloading operation."),
            models.ReportType(name="ANP Letter", description="Official communications with ANP."),
            models.ReportType(name="Daily HMI File", description="Daily collect from HMI systems."),
            models.ReportType(name="Audit Log", description="Internal and external audit records."),
            models.ReportType(name="Maintenance Photo", description="Visual records of maintenance activities.")
        ]
        db.add_all(types)
        db.commit() # Commit to get IDs
        
        # 2. Add some sample reports
        reports = [
            models.HistoricalReport(
                report_type_id=types[0].id,
                title="Offloading Cert #2025-01",
                file_url="/uploads/historical/offload_2025_01.pdf",
                file_name="offload_2025_01.pdf",
                file_size=1024567,
                report_date=datetime.now() - timedelta(days=10),
                fpso_name="FPSO ILHABELA",
                uploaded_by="Marcos G."
            ),
            models.HistoricalReport(
                report_type_id=types[1].id,
                title="ANP Notification - Resolution 18 Compliance",
                file_url="/uploads/historical/anp_res18_letter.pdf",
                file_name="anp_res18_letter.pdf",
                file_size=542000,
                report_date=datetime.now() - timedelta(days=5),
                fpso_name="Generic",
                uploaded_by="Marcos G."
            ),
             models.HistoricalReport(
                report_type_id=types[2].id,
                title="HMI Daily Dump - Jan 20th",
                file_url="/uploads/historical/hmi_dump_jan20.zip",
                file_name="hmi_dump_jan20.zip",
                file_size=15420000,
                report_date=datetime.now() - timedelta(days=11),
                fpso_name="FPSO PARATY",
                uploaded_by="System Sync"
            )
        ]
        
        db.add_all(reports)
        db.commit()
        print("M10 sample report types and reports added.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_m10()
