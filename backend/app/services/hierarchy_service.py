"""
Hierarchy Service — Business logic for M11 Configuration hierarchy tree.

Extracted from routers/configuration.py per Clean Architecture audit finding.
Skills Applied:
- architecture-patterns → Clean Architecture, service layer separation
- backend-dev-guidelines → Layered architecture (Router → Service → Repository)
"""

from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from app import models
from app.schemas import configuration as schemas


# Exact mapping from Metering Point + Sample Point - CDI.xlsx
# TODO (Phase 3): Migrate to database table for multi-FPSO support
METER_TO_SAMPLE_POINT: Dict[str, str] = {
    'T62-FT-1103': 'T62-AP-1002', 'F65-FT-0150': 'F65-AP-1111', 'T62-FT-2221': 'T62-AP-2224',
    'T71-FT-0601': 'T71-AP-0602', 'T73-FT-0015': 'T73-AP-0001', 'T73-FT-5101': 'T73-AP-0001',
    'T73-FT-5201': 'T73-AP-0001', 'T73-FT-5301': 'T73-AP-0001', 'T73-FT-5401': 'T73-AP-0001',
    'T73-FT-5501': 'T73-AP-0001', 'T73-FT-5601': 'T73-AP-0001', 'T73-FT-5701': 'T73-AP-0001',
    'T73-FT-5801': 'T73-AP-0001', 'T73-FT-5901': 'T73-AP-0001', 'T73-FT-6001': 'T73-AP-0001',
    'T73-FT-6101': 'T73-AP-0001', 'T73-FT-6201': 'T73-AP-0001', 'T73-FT-6301': 'T73-AP-0001',
    'T73-FT-6401': 'T73-AP-0001', 'T73-FT-6501': 'T73-AP-0001', 'T74-FT-6901': 'T74-AP-6911',
    'T75-FT-0001': 'T75-AP-6000', 'T75-FT-6101': 'T75-AP-6000', 'T75-FT-6201': 'T75-AP-6000',
    'T75-FT-6301': 'T75-AP-6000', 'T75-FT-6401': 'T75-AP-6000', 'T75-FT-6501': 'T75-AP-6000',
    'T76-FT-0014': 'T76-AP-0013', 'T76-FT-0034': 'T76-AP-0033', 'T76-FT-2001': 'T76-AP-2002',
    'T77-FT-0103': 'T77-AP-1009', 'T77-FT-6951': 'T77-AP-1039', 'T71-FT-0101': 'T71-AP-0102',
    'T71-FT-0201': 'T71-AP-0202'
}


def _build_category_children(
    meter: models.InstrumentTag,
    base_cat_id: int,
    inst_lookup: Dict[str, models.InstrumentTag],
) -> List[schemas.HierarchyNodeWithChildren]:
    """Build pressure/temperature/fluid property category nodes under a metering point."""
    parts = meter.tag_number.split('-')
    pt_tag = f"{parts[0]}-PT-{parts[2]}" if len(parts) >= 3 else None
    tt_tag = f"{parts[0]}-TT-{parts[2]}" if len(parts) >= 3 else None
    te_tag = f"{parts[0]}-TE-{parts[2]}" if len(parts) >= 3 else None
    ap_tag = METER_TO_SAMPLE_POINT.get(meter.tag_number)

    categories = [
        ("Pressure", [pt_tag], "Device"),
        ("Temperature", [tt_tag, te_tag], "Device"),
        ("Fluid Properties", [ap_tag], "Sample Point"),
    ]

    result = []
    for i, (cat_name, target_tags, level_type_val) in enumerate(categories):
        cat_node = schemas.HierarchyNodeWithChildren(
            id=base_cat_id + i,
            tag=cat_name,
            description=f"{cat_name} Instruments",
            level_type="Category",
            parent_id=meter.id + 20000,
            created_at=datetime.utcnow(),
            attributes={},
            children=[],
        )
        for j, t_tag in enumerate(target_tags):
            if t_tag and t_tag in inst_lookup:
                inst = inst_lookup[t_tag]
                inst_node = schemas.HierarchyNodeWithChildren(
                    id=int(f"{base_cat_id}{i}{j}"),
                    tag=inst.tag_number,
                    description=inst.description,
                    level_type=level_type_val,
                    parent_id=cat_node.id,
                    created_at=inst.created_at,
                    attributes={},
                    children=[],
                )
                cat_node.children.append(inst_node)
        result.append(cat_node)
    return result


def get_hierarchy_tree(db: Session) -> List[schemas.HierarchyNodeWithChildren]:
    """Build the full hierarchy tree for the FPSO.

    Returns a list with a single FPSO root node containing the full tree:
    FPSO → Metering Points → Categories → Instruments/Sample Points.
    """
    fpso_param = db.query(models.ConfigParameter).filter(
        models.ConfigParameter.key == "FPSO_NAME"
    ).first()
    
    fpso_name = fpso_param.value if fpso_param else "FPSO CIDADE DE ILHABELA (CDI)"
    
    fpso = schemas.HierarchyNodeWithChildren(
        id=1,
        tag=fpso_name,
        description="Main Vessel",
        level_type="FPSO",
        parent_id=None,
        created_at=datetime.utcnow(),
        children=[],
    )

    meters = db.query(models.InstrumentTag).filter(
        models.InstrumentTag.classification.isnot(None),
        models.InstrumentTag.tag_number.like("%-FT-%"),
    ).all()

    # Batch-fetch all instrument tags to avoid N+1 queries
    valid_tags: set = set(METER_TO_SAMPLE_POINT.values())
    for m in meters:
        parts = m.tag_number.split('-')
        if len(parts) >= 3:
            valid_tags.update([
                f"{parts[0]}-PT-{parts[2]}",
                f"{parts[0]}-TT-{parts[2]}",
                f"{parts[0]}-TE-{parts[2]}",
            ])

    inst_objs = db.query(models.InstrumentTag).filter(
        models.InstrumentTag.tag_number.in_(valid_tags),
    ).all()
    inst_lookup = {inst.tag_number: inst for inst in inst_objs}

    for m in meters:
        base_cat_id = (m.id * 10) + 30000
        meter_node = schemas.HierarchyNodeWithChildren(
            id=m.id + 20000,
            tag=m.tag_number,
            description=m.description or "Metering Point",
            level_type="Metering Point",
            parent_id=fpso.id,
            created_at=m.created_at or datetime.utcnow(),
            attributes={"classification": m.classification},
            children=_build_category_children(m, base_cat_id, inst_lookup),
        )
        fpso.children.append(meter_node)

    return [fpso]
