"""
Equipment Service — Business logic for M1 Equipment lifecycle.

Extracted from routers/equipment.py per Clean Architecture audit finding.
Skills Applied:
- architecture-patterns → Clean Architecture, service layer separation
- backend-dev-guidelines → Layered architecture (Router → Service → Repository)
"""

from datetime import date, timedelta
from app import models


def calculate_health(db_equipment: models.Equipment) -> str:
    """Calculate equipment health status based on calibration certificates.

    Returns:
        "healthy"  - All calibration certificates valid (>30 days remaining)
        "expiring" - At least one certificate expires within 30 days
        "expired"  - At least one certificate has expired
        "missing"  - No calibration certificates attached
    """
    certs = [c for c in db_equipment.certificates if c.certificate_type == "Calibration"]
    if not certs:
        return "missing"

    today = date.today()
    warning_buffer = today + timedelta(days=30)

    has_expired = False
    has_warning = False

    for c in certs:
        if not c.expiry_date:
            continue
        if c.expiry_date < today:
            has_expired = True
        elif c.expiry_date < warning_buffer:
            has_warning = True

    if has_expired:
        return "expired"
    if has_warning:
        return "expiring"
    return "healthy"
