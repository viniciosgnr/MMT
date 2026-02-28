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
    }
}

def get_sla_config(classification: str, analysis_type: str, local: str) -> Optional[dict]:
    """Returns the SLA configuration for a given combination, or a default if not found."""
    # Standardize inputs to match matrix keys exactly if needed, but assuming exact match for now
    key = (classification, analysis_type, local)
    
    # Check if exact match exists
    if key in SLA_MATRIX:
        return SLA_MATRIX[key]
        
    # Provide a safe default fallback if the combination isn't strictly defined
    return {
        "interval_days": 30, # Default safest interval
        "disembark_days": 10 if local == "Onshore" else None,
        "lab_days": 20 if local == "Onshore" else None,
        "report_days": 25,
        "fc_days": 5,
        "fc_is_business_days": False,
        "needs_validation": True
    }
