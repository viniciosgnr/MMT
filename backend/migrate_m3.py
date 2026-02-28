import sqlite3

def migrate():
    print("Connecting to DB...")
    conn = sqlite3.connect("mmt_mvp.db")
    cursor = conn.cursor()

    columns_to_add = [
        ("meter_id", "INTEGER NULL"),
        ("validation_party", "VARCHAR DEFAULT 'Client'"),
        ("is_active", "INTEGER DEFAULT 1")
    ]

    for col_name, col_type in columns_to_add:
        try:
            print(f"Adding column {col_name} to samples...")
            cursor.execute(f"ALTER TABLE samples ADD COLUMN {col_name} {col_type};")
            print(f"Success: {col_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"Column {col_name} already exists.")
            else:
                print(f"Error adding {col_name}: {e}")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
