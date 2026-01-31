"""
M2 MVP Migration: Add calibration workflow, seal tracking, and certificate management fields
"""

from sqlalchemy import text
from app.database import engine

def upgrade():
    """Add M2 MVP fields to existing tables and create seal_history table."""
    
    with engine.connect() as conn:
        # Add fields to calibration_tasks table
        print("Adding M2 fields to calibration_tasks...")
        
        # Execution details
        conn.execute(text("ALTER TABLE calibration_tasks ADD COLUMN calibration_type VARCHAR"))
        conn.execute(text("ALTER TABLE calibration_tasks ADD COLUMN temporary_completion_date DATE"))
        conn.execute(text("ALTER TABLE calibration_tasks ADD COLUMN definitive_completion_date DATE"))
        conn.execute(text("ALTER TABLE calibration_tasks ADD COLUMN is_temporary INTEGER DEFAULT 0"))
        
        # Seal information
        conn.execute(text("ALTER TABLE calibration_tasks ADD COLUMN seal_number VARCHAR"))
        conn.execute(text("ALTER TABLE calibration_tasks ADD COLUMN seal_installation_date DATE"))
        conn.execute(text("ALTER TABLE calibration_tasks ADD COLUMN seal_location VARCHAR"))
        
        # Spare management
        conn.execute(text("ALTER TABLE calibration_tasks ADD COLUMN spare_procurement_ids TEXT"))
        
        # Certificate tracking
        conn.execute(text("ALTER TABLE calibration_tasks ADD COLUMN certificate_number VARCHAR"))
        conn.execute(text("ALTER TABLE calibration_tasks ADD COLUMN certificate_issued_date DATE"))
        conn.execute(text("ALTER TABLE calibration_tasks ADD COLUMN certificate_ca_status VARCHAR"))
        conn.execute(text("ALTER TABLE calibration_tasks ADD COLUMN certificate_ca_notes TEXT"))
        
        # Add index on certificate_number
        conn.execute(text("CREATE INDEX idx_calibration_tasks_certificate_number ON calibration_tasks(certificate_number)"))
        
        print("Adding M2 fields to calibration_results...")
        
        # Add CA validation fields to calibration_results
        conn.execute(text("ALTER TABLE calibration_results ADD COLUMN ca_validated_at DATETIME"))
        conn.execute(text("ALTER TABLE calibration_results ADD COLUMN ca_validated_by VARCHAR"))
        conn.execute(text("ALTER TABLE calibration_results ADD COLUMN ca_validation_rules TEXT"))
        conn.execute(text("ALTER TABLE calibration_results ADD COLUMN ca_issues TEXT"))
        conn.execute(text("ALTER TABLE calibration_results ADD COLUMN certificate_pdf_path VARCHAR"))
        conn.execute(text("ALTER TABLE calibration_results ADD COLUMN certificate_xml_path VARCHAR"))
        
        print("Creating seal_history table...")
        
        # Create seal_history table
        conn.execute(text("""
            CREATE TABLE seal_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag_id INTEGER NOT NULL,
                seal_number VARCHAR NOT NULL,
                seal_type VARCHAR NOT NULL,
                seal_location VARCHAR NOT NULL,
                installation_date DATE NOT NULL,
                removal_date DATE,
                installed_by VARCHAR NOT NULL,
                removed_by VARCHAR,
                removal_reason VARCHAR,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (tag_id) REFERENCES instrument_tags(id)
            )
        """))
        
        # Create indexes
        conn.execute(text("CREATE INDEX idx_seal_history_tag_id ON seal_history(tag_id)"))
        conn.execute(text("CREATE INDEX idx_seal_history_seal_number ON seal_history(seal_number)"))
        conn.execute(text("CREATE INDEX idx_seal_history_is_active ON seal_history(is_active)"))
        
        conn.commit()
        print("M2 migration completed successfully!")

def downgrade():
    """Remove M2 MVP fields and seal_history table."""
    
    with engine.connect() as conn:
        print("Removing M2 fields from calibration_tasks...")
        
        # SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
        # For now, just drop the indexes
        conn.execute(text("DROP INDEX IF EXISTS idx_calibration_tasks_certificate_number"))
        
        print("Removing M2 fields from calibration_results...")
        # Same limitation for calibration_results
        
        print("Dropping seal_history table...")
        conn.execute(text("DROP TABLE IF EXISTS seal_history"))
        
        conn.commit()
        print("M2 downgrade completed!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()
