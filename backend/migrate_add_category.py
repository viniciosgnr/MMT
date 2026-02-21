"""Migration: Add 'category' column to samples table."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from sqlalchemy import text

def migrate():
    db = SessionLocal()
    try:
        # Add column if not exists
        db.execute(text("""
            ALTER TABLE samples ADD COLUMN IF NOT EXISTS category VARCHAR DEFAULT 'Coleta'
        """))
        # Set all existing samples to 'Coleta'
        result = db.execute(text("UPDATE samples SET category = 'Coleta' WHERE category IS NULL"))
        db.commit()
        print(f"✅ Migration complete. Updated {result.rowcount} rows to 'Coleta'.")
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
