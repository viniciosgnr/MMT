from app.database import SessionLocal
from app.routers.configuration import get_hierarchy_tree
import json

db = SessionLocal()
tree = get_hierarchy_tree(db)
dumped = tree[0].model_dump()
for child in dumped["children"]:
    if child["tag"] == "T73-FT-5801":
        print(f"Meter: {child['tag']}")
        print(f"Children in dict: {[c['tag'] for c in child.get('children', [])]}")
