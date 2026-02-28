import sys
import os
from sqlalchemy import text
from dotenv import load_dotenv

sys.path.append(os.path.abspath('backend'))
load_dotenv('backend/.env')

from app.database import engine

sql_statements = [
    # 1. Remap meter_id in samples table
    """
    UPDATE samples s
    SET meter_id = good_mp.id
    FROM instrument_tags bad_mp, instrument_tags good_mp
    WHERE s.meter_id = bad_mp.id
      AND bad_mp.tag_number LIKE '%-CDI'
      AND good_mp.tag_number = REPLACE(bad_mp.tag_number, '-CDI', '')
    """,
    # 2. Remap sample_point_id in samples table
    """
    UPDATE samples s
    SET sample_point_id = good_sp.id
    FROM sample_points bad_sp, sample_points good_sp
    WHERE s.sample_point_id = bad_sp.id
      AND bad_sp.tag_number LIKE '%-CDI'
      AND good_sp.tag_number = REPLACE(bad_sp.tag_number, '-CDI', '')
    """,
    # 3. Clear meter_sample_link for bad tags
    """
    DELETE FROM meter_sample_link
    WHERE meter_id IN (SELECT id FROM instrument_tags WHERE tag_number LIKE '%-CDI')
       OR sample_point_id IN (SELECT id FROM sample_points WHERE tag_number LIKE '%-CDI')
    """,
    # 4. Safe to delete all "-CDI" nodes now
    """
    DELETE FROM instrument_tags WHERE tag_number LIKE '%-CDI'
    """,
    """
    DELETE FROM sample_points WHERE tag_number LIKE '%-CDI'
    """
]

with engine.begin() as conn:
    for sql in sql_statements:
        try:
            res = conn.execute(text(sql))
            print(f"Executed OK. Rows affected: {res.rowcount}")
        except Exception as e:
            print(f"Error executing: {e}")

print("SQL cleanup done. Now you can run the hierarchy parsing again.")
