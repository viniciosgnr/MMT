from app.database import SessionLocal
from app.models import InstrumentTag, EquipmentTagInstallation, Equipment

db = SessionLocal()
query = db.query(InstrumentTag).join(
    EquipmentTagInstallation, InstrumentTag.id == EquipmentTagInstallation.tag_id
).join(
    Equipment, EquipmentTagInstallation.equipment_id == Equipment.id
).filter(
    EquipmentTagInstallation.is_active == 1
)

fpso = "FPSO CIDADE DE ILHABELA (CDI)"
q1 = query.filter(Equipment.fpso_name == fpso).filter(Equipment.equipment_type.in_(["Pressure Transmitter"]))
print(f"Counts for PT: {q1.count()}")
for tag in q1.limit(5).all():
    print(tag.tag_number)

eqs = db.query(Equipment).filter(Equipment.fpso_name == fpso).count()
print(f"Total equipment for {fpso}: {eqs}")

