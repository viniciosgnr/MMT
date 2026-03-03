import sys
import contextlib
import random
from app.database import SessionLocal
from app.models import InstrumentTag, EquipmentTagInstallation, Equipment

MANUFACTURERS = {
    "Pressure Transmitter": ["Emerson", "Yokogawa", "Endress+Hauser", "Honeywell"],
    "Temperature Transmitter": ["Emerson", "Yokogawa", "Endress+Hauser", "WIKA"],
    "Temperature Element": ["WIKA", "Emerson", "Ashcroft", "Omega"],
    "Sample Point": ["Swagelok", "Parker", "Welker", "YZ Systems"],
    "Flow Meter (USM)": ["KROHNE", "SICK", "Daniel", "FMC"],
    "Flow Meter (Coriolis)": ["Micro Motion", "Endress+Hauser", "KROHNE", "Foxboro"]
}
MODELS = {
    "Pressure Transmitter": ["3051S", "EJA110E", "Cerabar S", "ST 800"],
    "Temperature Transmitter": ["3144P", "YTA610", "iTEMP TMT82", "T32"],
    "Temperature Element": ["TC10", "Series 65", "Thermocouple Type K", "RTD PT100"],
    "Sample Point": ["Grab Sample Panel", "V-100", "In-Line Sampler", "LGS"],
    "Flow Meter (USM)": ["ALTOSONIC V", "FLOWSIC600", "SeniorSonic", "Smith Meter"],
    "Flow Meter (Coriolis)": ["ELITE CMF", "Promass F", "OPTIMASS 6400", "CFS10"]
}

def clean_data():
    db = SessionLocal()
    try:
        mps = db.query(InstrumentTag).filter(InstrumentTag.tag_number.like('%-FT-%')).all()
        # Collect data in memory first
        mp_data = []
        for mp in mps:
            mp_data.append({
                "id": mp.id,
                "tag_number": mp.tag_number,
                "description": mp.description or "",
                "sample_points": [sp.tag_number for sp in mp.sample_points]
            })
            
        valid_tag_ids = set()
        valid_eq_ids = set()
        
        for data in mp_data:
            valid_tag_ids.add(data["id"])
            mp_tag = data["tag_number"]
            mp_desc = data["description"]
            
            # Metering point equip
            installs = db.query(EquipmentTagInstallation).filter(EquipmentTagInstallation.tag_id == data["id"]).all()
            for inst in installs:
                valid_eq_ids.add(inst.equipment_id)
                eq = db.query(Equipment).filter(Equipment.id == inst.equipment_id).first()
                if eq:
                    eq.area_service = mp_desc
            
            # Child instruments
            pfx = mp_tag.replace("-FT-", "-PT-")
            tt = mp_tag.replace("-FT-", "-TT-")
            te = mp_tag.replace("-FT-", "-TE-")
            sp_tags = data["sample_points"]
            
            child_tags = db.query(InstrumentTag).filter(InstrumentTag.tag_number.in_([pfx, tt, te] + sp_tags)).all()
            for c_tag in child_tags:
                valid_tag_ids.add(c_tag.id)
                c_installs = db.query(EquipmentTagInstallation).filter(EquipmentTagInstallation.tag_id == c_tag.id, EquipmentTagInstallation.is_active == 1).all()
                for inst in c_installs:
                    valid_eq_ids.add(inst.equipment_id)
                    eq = db.query(Equipment).filter(Equipment.id == inst.equipment_id).first()
                    if eq:
                        eq_type = eq.equipment_type
                        c_tag.description = f"{eq_type} for {mp_tag}" if eq_type != "Sample Point" else f"Sample Point for {mp_tag}"
                        eq.serial_number = f"SN-{c_tag.tag_number}"
                        eq.manufacturer = random.choice(MANUFACTURERS.get(eq_type, ["Generic"]))
                        eq.model = random.choice(MODELS.get(eq_type, ["G-100"]))
                        eq.area_service = mp_desc
        
        # Flush updates
        db.commit()
        
        # Now delete unused
        del_e = del_t = 0
        all_eqs = db.query(Equipment).all()
        for e in all_eqs:
            if e.id not in valid_eq_ids:
                active_c = db.query(EquipmentTagInstallation).filter(EquipmentTagInstallation.equipment_id == e.id, EquipmentTagInstallation.is_active == 1).count()
                if active_c == 0:
                    db.delete(e)
                    del_e += 1
        db.commit()
        
        all_tags = db.query(InstrumentTag).all()
        for t in all_tags:
            if t.id not in valid_tag_ids:
                # remove any sample point link first
                t.sample_points = []
                db.delete(t)
                del_t += 1
        db.commit()
        print(f"Success! Kept {len(valid_eq_ids)} equipments and {len(valid_tag_ids)} tags. Deleted {del_e} eq, {del_t} tags.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    clean_data()
