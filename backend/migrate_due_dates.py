"""
Migration script: Recalculate due_date for all existing samples
based on the corrected PHASE_DUE mapping.

Logic: due_date = expected date of the NEXT milestone
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app import models

PHASE_DUE = {
    "Planned": "planned_date",
    "Sampled": "disembark_expected_date",
    "Disembark preparation": "disembark_expected_date",
    "Disembark logistics": "disembark_expected_date",
    "Warehouse": "lab_expected_date",
    "Logistics to vendor": "lab_expected_date",
    "Delivered at vendor": "report_expected_date",
    "Report issued": "report_expected_date",
    "Report under validation": "report_expected_date",
    "Report approved/reproved": "fc_expected_date",
    "Flow computer updated": "fc_expected_date",
}


def migrate():
    db = SessionLocal()
    try:
        samples = db.query(models.Sample).all()
        updated = 0
        skipped = 0

        for sample in samples:
            field = PHASE_DUE.get(sample.status)
            if not field:
                skipped += 1
                continue

            new_due = getattr(sample, field, None)
            old_due = sample.due_date

            if old_due != new_due:
                print(f"  [{sample.sample_id}] status={sample.status} | "
                      f"due_date: {old_due} → {new_due} (field={field})")
                sample.due_date = new_due
                updated += 1
            else:
                skipped += 1

        db.commit()
        print(f"\n✅ Migration complete: {updated} updated, {skipped} unchanged")
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Migrating due_dates for existing samples...")
    print("=" * 60)
    migrate()
