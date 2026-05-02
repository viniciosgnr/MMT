"""Seed all 22 SLA Matrix combinations from the official specification.

Source: MMT Specifications/All Periodic Analyses.xlsx

Each unique row in the spreadsheet becomes one SLARule record.
Rows that have both Approved and Reproved variants get two records.
Rows without validation (like Enxofre, Viscosity) get status_variation='Any'.
"""
import sys
sys.path.append("/home/marcosgnr/MMT/backend")

from app.database import SessionLocal
from app.models import SLARule

# All 22 combinations from the official spreadsheet
# (classification, analysis_type, local, status_variation): {fields}
ALL_RULES = [
    # --- FISCAL CHROMATOGRAPHY ---
    # Row 0: Fiscal / Chromatography / Onshore / Approved
    {"classification": "Fiscal", "analysis_type": "Chromatography", "local": "Onshore",
     "status_variation": "Approved", "interval_days": 30, "disembark_days": 10,
     "lab_days": 20, "report_days": 25, "fc_days": 3, "fc_is_business_days": True,
     "needs_validation": True, "reproval_reschedule_days": None},
    # Row 1: Fiscal / Chromatography / Onshore / Reproved
    {"classification": "Fiscal", "analysis_type": "Chromatography", "local": "Onshore",
     "status_variation": "Reproved", "interval_days": 30, "disembark_days": 10,
     "lab_days": 20, "report_days": 25, "fc_days": None, "fc_is_business_days": False,
     "needs_validation": True, "reproval_reschedule_days": 3},
    # Row 2: Fiscal / Chromatography / Offshore / Approved
    {"classification": "Fiscal", "analysis_type": "Chromatography", "local": "Offshore",
     "status_variation": "Approved", "interval_days": 30, "disembark_days": None,
     "lab_days": None, "report_days": 25, "fc_days": 3, "fc_is_business_days": True,
     "needs_validation": True, "reproval_reschedule_days": None},
    # Row 3: Fiscal / Chromatography / Offshore / Reproved
    {"classification": "Fiscal", "analysis_type": "Chromatography", "local": "Offshore",
     "status_variation": "Reproved", "interval_days": 30, "disembark_days": None,
     "lab_days": None, "report_days": 25, "fc_days": None, "fc_is_business_days": False,
     "needs_validation": True, "reproval_reschedule_days": 3},

    # --- APROPRIATION CHROMATOGRAPHY ---
    # Row 4: Apropriation / Chromatography / Onshore / Approved
    {"classification": "Apropriation", "analysis_type": "Chromatography", "local": "Onshore",
     "status_variation": "Approved", "interval_days": 90, "disembark_days": 10,
     "lab_days": 20, "report_days": 25, "fc_days": 3, "fc_is_business_days": True,
     "needs_validation": True, "reproval_reschedule_days": None},
    # Row 5: Apropriation / Chromatography / Onshore / Reproved
    {"classification": "Apropriation", "analysis_type": "Chromatography", "local": "Onshore",
     "status_variation": "Reproved", "interval_days": 90, "disembark_days": 10,
     "lab_days": 20, "report_days": 25, "fc_days": None, "fc_is_business_days": False,
     "needs_validation": True, "reproval_reschedule_days": 3},
    # Row 6: Apropriation / Chromatography / Offshore / Approved
    {"classification": "Apropriation", "analysis_type": "Chromatography", "local": "Offshore",
     "status_variation": "Approved", "interval_days": 90, "disembark_days": None,
     "lab_days": None, "report_days": 25, "fc_days": 3, "fc_is_business_days": True,
     "needs_validation": True, "reproval_reschedule_days": None},
    # Row 7: Apropriation / Chromatography / Offshore / Reproved
    {"classification": "Apropriation", "analysis_type": "Chromatography", "local": "Offshore",
     "status_variation": "Reproved", "interval_days": 90, "disembark_days": None,
     "lab_days": None, "report_days": 25, "fc_days": None, "fc_is_business_days": False,
     "needs_validation": True, "reproval_reschedule_days": 3},

    # --- OPERATIONAL CHROMATOGRAPHY ---
    # Row 8: Operational / Chromatography / Onshore / Approved
    {"classification": "Operational", "analysis_type": "Chromatography", "local": "Onshore",
     "status_variation": "Approved", "interval_days": 180, "disembark_days": 10,
     "lab_days": 20, "report_days": 45, "fc_days": 10, "fc_is_business_days": True,
     "needs_validation": True, "reproval_reschedule_days": None},
    # Row 9: Operational / Chromatography / Onshore / Reproved
    {"classification": "Operational", "analysis_type": "Chromatography", "local": "Onshore",
     "status_variation": "Reproved", "interval_days": 180, "disembark_days": 10,
     "lab_days": 20, "report_days": 45, "fc_days": None, "fc_is_business_days": False,
     "needs_validation": True, "reproval_reschedule_days": 3},
    # Row 10: Operational / Chromatography / Offshore / Approved
    {"classification": "Operational", "analysis_type": "Chromatography", "local": "Offshore",
     "status_variation": "Approved", "interval_days": 180, "disembark_days": None,
     "lab_days": None, "report_days": 45, "fc_days": 10, "fc_is_business_days": True,
     "needs_validation": True, "reproval_reschedule_days": None},
    # Row 11: Operational / Chromatography / Offshore / Reproved
    {"classification": "Operational", "analysis_type": "Chromatography", "local": "Offshore",
     "status_variation": "Reproved", "interval_days": 180, "disembark_days": None,
     "lab_days": None, "report_days": 45, "fc_days": None, "fc_is_business_days": False,
     "needs_validation": True, "reproval_reschedule_days": 3},

    # --- APROPRIATION PVT ---
    # Row 12: Apropriation / PVT / Onshore / Approved
    {"classification": "Apropriation", "analysis_type": "PVT", "local": "Onshore",
     "status_variation": "Approved", "interval_days": 90, "disembark_days": 10,
     "lab_days": 20, "report_days": 25, "fc_days": None, "fc_is_business_days": False,
     "needs_validation": True, "reproval_reschedule_days": None},
    # Row 13: Apropriation / PVT / Offshore / Approved
    {"classification": "Apropriation", "analysis_type": "PVT", "local": "Offshore",
     "status_variation": "Approved", "interval_days": 90, "disembark_days": None,
     "lab_days": None, "report_days": 25, "fc_days": None, "fc_is_business_days": False,
     "needs_validation": True, "reproval_reschedule_days": None},
    # Row 14: Apropriation / PVT / Onshore / Reproved
    {"classification": "Apropriation", "analysis_type": "PVT", "local": "Onshore",
     "status_variation": "Reproved", "interval_days": 90, "disembark_days": 10,
     "lab_days": 20, "report_days": 25, "fc_days": None, "fc_is_business_days": False,
     "needs_validation": True, "reproval_reschedule_days": 3},
    # Row 15: Apropriation / PVT / Offshore / Reproved
    {"classification": "Apropriation", "analysis_type": "PVT", "local": "Offshore",
     "status_variation": "Reproved", "interval_days": 90, "disembark_days": None,
     "lab_days": None, "report_days": 25, "fc_days": None, "fc_is_business_days": False,
     "needs_validation": True, "reproval_reschedule_days": 3},

    # --- FISCAL ENXOFRE (no validation) ---
    # Row 16: Fiscal / Enxofre / Onshore
    {"classification": "Fiscal", "analysis_type": "Enxofre", "local": "Onshore",
     "status_variation": "Any", "interval_days": 365, "disembark_days": 10,
     "lab_days": 20, "report_days": 25, "fc_days": None, "fc_is_business_days": False,
     "needs_validation": False, "reproval_reschedule_days": None},
    # Row 17: Fiscal / Enxofre / Offshore
    {"classification": "Fiscal", "analysis_type": "Enxofre", "local": "Offshore",
     "status_variation": "Any", "interval_days": 365, "disembark_days": None,
     "lab_days": None, "report_days": 25, "fc_days": None, "fc_is_business_days": False,
     "needs_validation": False, "reproval_reschedule_days": None},

    # --- FISCAL VISCOSITY (no validation) ---
    # Row 18: Fiscal / Viscosity / Onshore
    {"classification": "Fiscal", "analysis_type": "Viscosity", "local": "Onshore",
     "status_variation": "Any", "interval_days": 365, "disembark_days": 10,
     "lab_days": 20, "report_days": 45, "fc_days": None, "fc_is_business_days": False,
     "needs_validation": False, "reproval_reschedule_days": None},
    # Row 19: Fiscal / Viscosity / Offshore
    {"classification": "Fiscal", "analysis_type": "Viscosity", "local": "Offshore",
     "status_variation": "Any", "interval_days": 365, "disembark_days": None,
     "lab_days": None, "report_days": 45, "fc_days": None, "fc_is_business_days": False,
     "needs_validation": False, "reproval_reschedule_days": None},

    # --- CUSTODY TRANSFER VISCOSITY (no validation) ---
    # Row 20: Custody Transfer / Viscosity / Onshore
    {"classification": "Custody Transfer", "analysis_type": "Viscosity", "local": "Onshore",
     "status_variation": "Any", "interval_days": 365, "disembark_days": 10,
     "lab_days": 20, "report_days": 45, "fc_days": None, "fc_is_business_days": False,
     "needs_validation": False, "reproval_reschedule_days": None},
    # Row 21: Custody Transfer / Viscosity / Offshore
    {"classification": "Custody Transfer", "analysis_type": "Viscosity", "local": "Offshore",
     "status_variation": "Any", "interval_days": 365, "disembark_days": None,
     "lab_days": None, "report_days": 45, "fc_days": None, "fc_is_business_days": False,
     "needs_validation": False, "reproval_reschedule_days": None},
]


def seed_all_slas():
    db = SessionLocal()
    count = 0
    try:
        for rule_data in ALL_RULES:
            new_rule = SLARule(**rule_data)
            db.add(new_rule)
            count += 1
        
        db.commit()
        print(f"Successfully seeded {count} SLA rules (all 22 combinations).")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_all_slas()
