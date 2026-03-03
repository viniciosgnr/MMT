from app.database import SessionLocal
from app.routers.configuration import get_hierarchy_tree

db = SessionLocal()
tree = get_hierarchy_tree(db)
# Find T73-FT-5801
for child in tree[0].children:
    if child.tag == "T73-FT-5801":
        print(f"Found {child.tag}")
        print(f"Children of {child.tag}: {[c.tag for c in child.children]}")
        for c in child.children:
            print(f"  {c.tag} children: {[gc.tag for gc in c.children]}")
