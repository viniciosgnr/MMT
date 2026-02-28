import sqlite3

def migrate():
    print("Starting M11 Many-to-Many Migration...")
    conn = sqlite3.connect('mmt_mvp.db')
    cursor = conn.cursor()

    try:
        # Create association table
        print("Creating meter_sample_link table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS meter_sample_link (
            meter_id INTEGER NOT NULL,
            sample_point_id INTEGER NOT NULL,
            PRIMARY KEY (meter_id, sample_point_id),
            FOREIGN KEY(meter_id) REFERENCES instrument_tags (id),
            FOREIGN KEY(sample_point_id) REFERENCES sample_points (id)
        );
        ''')

        # Add new columns to instrument_tags and sample_points
        # SQLite doesn't support IF NOT EXISTS for columns in ALTER TABLE, so we intercept the error
        print("Adding classification to instrument_tags...")
        try:
            cursor.execute("ALTER TABLE instrument_tags ADD COLUMN classification VARCHAR NULL;")
            print("Successfully added classification column.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("Column 'classification' already exists, continuing.")
            else:
                raise e

        print("Adding analysis_types to sample_points...")
        try:
            cursor.execute("ALTER TABLE sample_points ADD COLUMN analysis_types TEXT NULL;")
            print("Successfully added analysis_types column.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("Column 'analysis_types' already exists, continuing.")
            else:
                raise e
        
        # Optionally, migrate existing 1-to-many relationships (from instrument_tags.sample_point_id) to the new table
        print("Migrating existing 1-to-Many relationships to meter_sample_link...")
        cursor.execute('''
            INSERT OR IGNORE INTO meter_sample_link (meter_id, sample_point_id)
            SELECT id, sample_point_id FROM instrument_tags WHERE sample_point_id IS NOT NULL
        ''')

        conn.commit()
        print("Migration completed successfully.")

    except Exception as ex:
        print(f"Migration failed: {ex}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
