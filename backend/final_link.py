from app.database import engine
from sqlalchemy import text
import pandas as pd
import json

df = pd.read_excel('/home/marcosgnr/MMT/MMT Specifications/Metering Point + Sample Point - CDI.xlsx')
data = df.to_dict(orient='records')
fpso_name = "FPSO CIDADE DE ILHABELA (CDI)"

statements = []
for row in data:
    mp_tag = str(row.get('Metering Point')).strip()
    sp_tag = str(row.get('Sample Point')).strip()
    classification = str(row.get('Classification')).strip()
    description = str(row.get('Description')).strip()
    
    if pd.isna(row.get('Sample Point')):
        sp_tag = None

    # Upsert MP
    statements.append(text(f"""
        INSERT INTO instrument_tags (tag_number, description, classification)
        VALUES ('{mp_tag}', '{description}', '{classification}')
        ON CONFLICT (tag_number) 
        DO UPDATE SET classification = EXCLUDED.classification, description = EXCLUDED.description;
    """))

    # Upsert SP
    if sp_tag and sp_tag != 'nan':
        analysis_types = []
        for col in ['Type of Analysis 1', 'Type of analysis 2', 'Type of Analysis 3', 'Type 4']:
            val = row.get(col)
            if pd.notna(val) and str(val).strip():
                analysis_types.append(str(val).strip())
        
        at_json = json.dumps(analysis_types) if analysis_types else '[]'
        
        statements.append(text(f"""
            INSERT INTO sample_points (tag_number, description, fpso_name, analysis_types)
            VALUES ('{sp_tag}', 'Sample point for {mp_tag}', '{fpso_name}', '{at_json}')
            ON CONFLICT (tag_number) 
            DO UPDATE SET analysis_types = EXCLUDED.analysis_types, fpso_name = EXCLUDED.fpso_name;
        """))
        
        # Link MP and SP
        statements.append(text(f"""
            INSERT INTO meter_sample_link (meter_id, sample_point_id)
            SELECT m.id, s.id
            FROM instrument_tags m, sample_points s
            WHERE m.tag_number = '{mp_tag}' AND s.tag_number = '{sp_tag}'
            ON CONFLICT DO NOTHING;
        """))

with engine.begin() as conn:
    for stmt in statements:
        conn.execute(stmt)
print("Insertion and linkage successful via SQL.")
