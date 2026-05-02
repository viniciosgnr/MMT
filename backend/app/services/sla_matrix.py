from typing import Dict, Tuple, Optional

# Key: (Classification, Type of Analysis, Local)
# Values:
# interval_days: int (Days until next collection if approved)
# disembark_days: int or None (Days after sampling)
# lab_days: int or None (Days after sampling)
# report_days: int or None (Days after sampling)
# fc_days: int or None (Days after REPORT EMISSION)
# fc_is_business_days: bool (Calculate business days for FC)
# Needs validation: bool (whether the certificate involves approval/reproval)

SLA_MATRIX: Dict[Tuple[str, str, str], dict] = {
    # FISCAL - CHROMATOGRAPHY
    ("Fiscal", "Chromatography", "Onshore"): {
        "interval_days": 30,
        "disembark_days": 10,
        "lab_days": 20,
        "report_days": 25,
        "fc_days": 3,
        "fc_is_business_days": True,
        "needs_validation": True
    },
    ("Fiscal", "Chromatography", "Offshore"): {
        "interval_days": 30,
        "disembark_days": None,
        "lab_days": None,
        "report_days": 25,
        "fc_days": 3,
        "fc_is_business_days": True,
        "needs_validation": True
    },
    # APROPRIATION - CHROMATOGRAPHY
    ("Apropriation", "Chromatography", "Onshore"): {
        "interval_days": 90,
        "disembark_days": 10,
        "lab_days": 20,
        "report_days": 25,
        "fc_days": 3,
        "fc_is_business_days": True,
        "needs_validation": True
    },
    ("Apropriation", "Chromatography", "Offshore"): {
        "interval_days": 90,
        "disembark_days": None,
        "lab_days": None,
        "report_days": 25,
        "fc_days": 3,
        "fc_is_business_days": True,
        "needs_validation": True
    },
    # OPERATIONAL - CHROMATOGRAPHY
    ("Operational", "Chromatography", "Onshore"): {
        "interval_days": 180,
        "disembark_days": 10,
        "lab_days": 20,
        "report_days": 45,
        "fc_days": 10,
        "fc_is_business_days": True,
        "needs_validation": True
    },
    ("Operational", "Chromatography", "Offshore"): {
        "interval_days": 180,
        "disembark_days": None,
        "lab_days": None,
        "report_days": 45,
        "fc_days": 10,
        "fc_is_business_days": True,
        "needs_validation": True
    },
    # APROPRIATION - PVT
    ("Apropriation", "PVT", "Onshore"): {
        "interval_days": 90,
        "disembark_days": 10,
        "lab_days": 20,
        "report_days": 25,
        "fc_days": None,
        "fc_is_business_days": False,
        "needs_validation": True
    },
    ("Apropriation", "PVT", "Offshore"): {
        "interval_days": 90,
        "disembark_days": None,
        "lab_days": None,
        "report_days": 25,
        "fc_days": None,
        "fc_is_business_days": False,
        "needs_validation": True
    },
    # FISCAL - ENXOFRE
    ("Fiscal", "Enxofre", "Onshore"): {
        "interval_days": 365,
        "disembark_days": 10,
        "lab_days": 20,
        "report_days": 25,
        "fc_days": None,
        "fc_is_business_days": False,
        "needs_validation": False
    },
    ("Fiscal", "Enxofre", "Offshore"): {
        "interval_days": 365,
        "disembark_days": None,
        "lab_days": None,
        "report_days": 25,
        "fc_days": None,
        "fc_is_business_days": False,
        "needs_validation": False
    },
    # FISCAL - VISCOSITY
    ("Fiscal", "Viscosity", "Onshore"): {
        "interval_days": 365,
        "disembark_days": 10,
        "lab_days": 20,
        "report_days": 45,
        "fc_days": None,
        "fc_is_business_days": False,
        "needs_validation": False
    },
    ("Fiscal", "Viscosity", "Offshore"): {
        "interval_days": 365,
        "disembark_days": None,
        "lab_days": None,
        "report_days": 45,
        "fc_days": None,
        "fc_is_business_days": False,
        "needs_validation": False
    },
    # CUSTODY TRANSFER - VISCOSITY
    ("Custody Transfer", "Viscosity", "Onshore"): {
        "interval_days": 365,
        "disembark_days": 10,
        "lab_days": 20,
        "report_days": 45,
        "fc_days": None,
        "fc_is_business_days": False,
        "needs_validation": False
    },
    ("Custody Transfer", "Viscosity", "Offshore"): {
        "interval_days": 365,
        "disembark_days": None,
        "lab_days": None,
        "report_days": 45,
        "fc_days": None,
        "fc_is_business_days": False,
        "needs_validation": False
    },
    # MISC / TEST DEFAULTS
    ("Fiscal", "PVT", "Onshore"): {
        "interval_days": 90,
        "disembark_days": 10,
        "lab_days": 20,
        "report_days": 25,
        "fc_days": None,
        "fc_is_business_days": False,
        "needs_validation": True
    },
    ("Fiscal", "PVT", "Offshore"): {
        "interval_days": 90,
        "disembark_days": None,
        "lab_days": None,
        "report_days": 25,
        "fc_days": None,
        "fc_is_business_days": False,
        "needs_validation": True
    }
}

from sqlalchemy.orm import Session
from app import models

def get_sla_config(db: Session, classification: str, analysis_type: str, local: str) -> Optional[dict]:
    """Returns the SLA configuration from DB (SLARule) or fallback matrix if not found."""
    # Standardize inputs
    c = classification.strip().title() if classification else "Fiscal"
    t = analysis_type.strip().title() if analysis_type else "Chromatography"
    l = local.strip().title() if local else "Onshore"
    
    # Aliases
    if t == "Cro":
        t = "Chromatography"
    elif t == "Pvt":
        t = "PVT"

    # 1. Check Database
    rule = db.query(models.SLARule).filter(
        models.SLARule.classification == c,
        models.SLARule.analysis_type == t,
        models.SLARule.local == l
    ).first()

    if rule:
        return {
            "interval_days": rule.interval_days,
            "disembark_days": rule.disembark_days,
            "lab_days": rule.lab_days,
            "report_days": rule.report_days,
            "fc_days": rule.fc_days,
            "fc_is_business_days": bool(rule.fc_is_business_days),
            "needs_validation": bool(rule.needs_validation)
        }

    # 2. Fallback to Hardcoded Matrix
    key = (c, t, l)
    if key in SLA_MATRIX:
        return SLA_MATRIX[key]
        
    # Provide None for unknown combinations, as expected by system safety tests
    return None
