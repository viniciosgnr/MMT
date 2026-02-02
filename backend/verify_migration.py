
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(dotenv_path="/home/marcosgnr/MMT/backend/.env")

dsn = os.getenv("DATABASE_URL")

try:
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    
    tables = [
        "equipments",
        "instrument_tags",
        "calibration_tasks",
        "samples",
        "maintenance_cards",
        "hierarchy_nodes"
    ]
    
    print("--- Migration Verification ---")
    for table in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table};")
            count = cur.fetchone()[0]
            print(f"{table}: {count} rows")
        except Exception as e:
            print(f"{table}: Error {e}")
            conn.rollback() # Reset tx
            
    conn.close()
except Exception as e:
    print(f"Connection Failed: {e}")
