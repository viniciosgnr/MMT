import os
import psycopg2
from dotenv import load_dotenv

# Load .env from backend directory
load_dotenv(dotenv_path="/home/marcosgnr/MMT/backend/.env")

dsn = os.getenv("DATABASE_URL")
if not dsn:
    print("Error: DATABASE_URL not found in environment variables.")
    exit(1)

print(f"Attempting connection to: {dsn.split('@')[1]}") # Mask password in logs

try:
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    cur.execute("SELECT version();")
    db_version = cur.fetchone()
    print("Connection Successful!")
    print(f"Database Version: {db_version[0]}")
    conn.close()
except Exception as e:
    print(f"Connection Failed: {e}")
    exit(1)
