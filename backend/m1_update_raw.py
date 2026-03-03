import sys
import random
from sqlalchemy import text
from app.database import engine

MANUFACTURERS = {
    "Pressure Transmitter": ["Emerson", "Yokogawa", "Endress+Hauser", "Honeywell"],
    "Temperature Transmitter": ["Emerson", "Yokogawa", "Endress+Hauser", "WIKA"],
    "Temperature Element": ["WIKA", "Emerson", "Ashcroft", "Omega"],
    "Sample Point": ["Swagelok", "Parker", "Welker", "YZ Systems"],
}

MODELS = {
    "Pressure Transmitter": ["3051S", "EJA110E", "Cerabar S", "ST 800"],
    "Temperature Transmitter": ["3144P", "YTA610", "iTEMP TMT82", "T32"],
    "Temperature Element": ["TC10", "Series 65", "Thermocouple Type K", "RTD PT100"],
    "Sample Point": ["Grab Sample Panel", "V-100", "In-Line Sampler", "LGS"],
}

def run():
    with engine.connect() as conn:
        print("Fetching MPs...")
        mps = conn.execute(text("SELECT id, tag_number, description FROM instrument_tags WHERE tag_number LIKE '%-FT-%'")).fetchall()
        
        valid_tags = set()
        valid_eqs = set()
        
        for mp in mps:
            valid_tags.add(mp.id)
            mp_tag = mp.tag_number
            mp_desc = mp.description or ""
            
            # update eq linked to mp
            installs = conn.execute(text("SELECT equipment_id FROM equipment_tag_installations WHERE tag_id = :tid"), {"tid": mp.id}).fetchall()
            for i in installs:
                valid_eqs.add(i.equipment_id)
                # Metering points also need their tag area updated
                conn.execute(text("UPDATE instrument_tags SET area = :desc WHERE id = :tid"), {"desc": mp_desc, "tid": mp.id})

            # Find sample points linked to this MP
            sps = conn.execute(text("SELECT sample_point_id FROM meter_sample_link WHERE meter_id = :mid"), {"mid": mp.id}).fetchall()
            sp_ids = [s.sample_point_id for s in sps]
            
            # also PT, TT, TE
            pfx = mp_tag.replace("-FT-", "-PT-")
            tt = mp_tag.replace("-FT-", "-TT-")
            te = mp_tag.replace("-FT-", "-TE-")
            child_names = tuple([pfx, tt, te])
            
            sp_ids_tuple = tuple(sp_ids) if sp_ids else (-1,)
            
            child_tags = conn.execute(text("SELECT id, tag_number FROM instrument_tags WHERE tag_number IN :tags OR id IN :sp_ids"), 
                                      {"tags": child_names, "sp_ids": sp_ids_tuple}).fetchall()
                                      
            for c in child_tags:
                valid_tags.add(c.id)
                
                c_installs = conn.execute(text("SELECT equipment_id FROM equipment_tag_installations WHERE tag_id = :tid AND is_active = 1"), {"tid": c.id}).fetchall()
                for i in c_installs:
                    valid_eqs.add(i.equipment_id)
                    
                    eq_type = conn.execute(text("SELECT equipment_type FROM equipments WHERE id = :eid"), {"eid": i.equipment_id}).scalar()
                    
                    if eq_type:
                        t_desc = f"{eq_type} for {mp_tag}" if "Sample Point" not in eq_type else f"Sample Point for {mp_tag}"
                        
                        # Update tag desc and area
                        conn.execute(text("UPDATE instrument_tags SET description = :desc, area = :area, service = :area WHERE id = :tid"), 
                                     {"desc": t_desc, "area": mp_desc, "tid": c.id})
                        
                        # Update eq fields
                        sn = f"SN-{c.tag_number}"
                        mfg = random.choice(MANUFACTURERS.get(eq_type, ["Generic"]))
                        mod = random.choice(MODELS.get(eq_type, ["G-100"]))
                        
                        conn.execute(text("UPDATE equipments SET serial_number = :sn, manufacturer = :mfg, model = :mod WHERE id = :eid"),
                                     {"sn": sn, "mfg": mfg, "mod": mod, "eid": i.equipment_id})

        print("Deleting unused...")
        if valid_eqs:
            conn.execute(text("DELETE FROM equipment_tag_installations WHERE equipment_id NOT IN :eqs OR tag_id NOT IN :tgs"), {"eqs": tuple(valid_eqs), "tgs": tuple(valid_tags)})
            conn.execute(text("DELETE FROM equipments WHERE id NOT IN :eqs"), {"eqs": tuple(valid_eqs)})
        if valid_tags:
            conn.execute(text("DELETE FROM meter_sample_link WHERE meter_id NOT IN :tgs AND sample_point_id NOT IN :tgs"), {"tgs": tuple(valid_tags)})
            conn.execute(text("DELETE FROM instrument_tags WHERE id NOT IN :tgs"), {"tgs": tuple(valid_tags)})
            
        conn.commit()
        print(f"Done! Kept {len(valid_eqs)} equipments and {len(valid_tags)} tags.")

if __name__ == "__main__":
    run()
