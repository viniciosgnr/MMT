import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))

from app.database import engine
from sqlalchemy import text

alter_statements = [
    "ALTER TABLE wells ADD COLUMN anp_code VARCHAR;",
    "ALTER TABLE wells ADD COLUMN sbm_code VARCHAR;",
    "ALTER TABLE wells ADD COLUMN sample_point_gas VARCHAR;",
    "ALTER TABLE wells ADD COLUMN sample_point_oil VARCHAR;",
    "ALTER TABLE wells ADD COLUMN status VARCHAR DEFAULT 'Active';"
]

with engine.begin() as conn:
    for stmt in alter_statements:
        try:
            conn.execute(text(stmt))
            print(f"Executed: {stmt}")
        except Exception as e:
            print(f"Error on {stmt}: {e}")

print("Migration completed.")
