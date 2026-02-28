import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))

from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT fpso_name, tag_number FROM sample_points LIMIT 10;"))
    for row in result:
        print(row)
