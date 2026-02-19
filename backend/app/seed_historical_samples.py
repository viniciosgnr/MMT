"""
Import ~10% of historical collections from the Sampling Plan spreadsheet.
Selects records with the most complete data across all 4 collection types.

Usage: python -m app.seed_historical_samples
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import openpyxl

DATABASE_URL = os.environ.get("DATABASE_URL", "")
EXCEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                          "MMT Specifications", "06 - Sampling Plan (2).xlsm")

# FPSO abbreviation -> full name
FPSO_MAP = {
    "CDS": "CDS - Cidade de Saquarema",
    "CDM": "CDM - Cidade de Maricá",
    "CDI": "CDI - Cidade de Ilhabela",
    "CDP": "CDP - Cidade de Paraty",
    "ESS": "ESS - Espírito Santo",
    "CPX": "CPX - Capixaba",
    "CDA": "CDA - Cidade de Anchieta",
    "ADG": "ADG - Alexandre de Gusmão",
    "ATD": "ATD - Almirante Tamandaré",
    "SEP": "SEP - Sepetiba",
}

# Reverse lookup
FPSO_ABBR = {v: k for k, v in FPSO_MAP.items()}

# Status mapping from Portuguese to our English statuses
STATUS_MAP = {
    "Aprovado": "Report approved/reproved",
    "Reprovado": "Report approved/reproved",
    "Pendente": "Delivered at vendor",
    None: "Planned",
}

VALIDATION_MAP = {
    "Aprovado": "Approved",
    "Reprovado": "Reproved",
    "Pendente": None,
    None: None,
}


def main():
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)
    if not os.path.exists(EXCEL_PATH):
        print(f"ERROR: Excel file not found at {EXCEL_PATH}")
        sys.exit(1)

    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Load sample points for matching
    sp_rows = session.execute(text("SELECT id, tag_number, fpso_name FROM sample_points")).fetchall()
    sp_lookup = {}
    for sp_id, tag, fpso in sp_rows:
        sp_lookup[(tag, fpso)] = sp_id

    # Read Excel
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True, read_only=True)
    ws = wb["Coletas"]

    all_rows = []
    for row in ws.iter_rows(min_row=2):
        vals = [cell.value for cell in row]
        if not vals[1]:  # Skip empty rows
            continue
        fpso = vals[1]
        tag = vals[2]
        tipo = vals[3]
        coleta_real = vals[6]
        desemb_prev = vals[7]
        desemb_real = vals[8]
        osm_id = vals[9]
        lab_prev = vals[10]
        lab_real = vals[11]
        laudo_prev = vals[12]
        laudo_real = vals[13]
        cv_prev = vals[14]
        cv_real = vals[15]
        status = vals[16]
        laudo_num = vals[17]
        notes = vals[18]
        mitigated = vals[20]

        # Build completeness score (prefer rows with more data filled)
        score = 0
        if isinstance(coleta_real, datetime): score += 2
        if isinstance(desemb_real, datetime): score += 2
        if isinstance(lab_real, datetime): score += 2
        if isinstance(laudo_real, datetime): score += 2
        if osm_id and str(osm_id).strip(): score += 1
        if status: score += 1
        if laudo_num: score += 1

        all_rows.append({
            "fpso": fpso,
            "tag": tag,
            "tipo": tipo,
            "coleta_real": coleta_real if isinstance(coleta_real, datetime) else None,
            "desemb_prev": desemb_prev if isinstance(desemb_prev, datetime) else None,
            "desemb_real": desemb_real if isinstance(desemb_real, datetime) else None,
            "osm_id": str(osm_id).strip() if osm_id and str(osm_id).strip() not in ["-", "None"] else None,
            "lab_prev": lab_prev if isinstance(lab_prev, datetime) else None,
            "lab_real": lab_real if isinstance(lab_real, datetime) else None,
            "laudo_prev": laudo_prev if isinstance(laudo_prev, datetime) else None,
            "laudo_real": laudo_real if isinstance(laudo_real, datetime) else None,
            "cv_prev": cv_prev if isinstance(cv_prev, datetime) else None,
            "cv_real": cv_real if isinstance(cv_real, datetime) else None,
            "status": status,
            "laudo_num": str(laudo_num).strip() if laudo_num and str(laudo_num).strip() not in ["-", "None"] else None,
            "notes": str(notes).strip() if notes and str(notes).strip() not in ["-", "None"] else None,
            "mitigated": 1 if mitigated and str(mitigated).strip().lower() in ["sim", "yes", "1"] else 0,
            "score": score,
        })

    # Sort by completeness score descending, then pick ~107 records
    all_rows.sort(key=lambda x: -x["score"])
    target = max(107, len(all_rows) // 10)
    selected = all_rows[:target]

    print(f"Total rows in spreadsheet: {len(all_rows)}")
    print(f"Selected {len(selected)} rows (top {target} by completeness)")

    # Count existing samples to avoid duplicate sample_id
    max_id_row = session.execute(text("SELECT MAX(id) FROM samples")).fetchone()
    next_id = (max_id_row[0] or 0) + 1

    inserted = 0
    skipped = 0
    for i, r in enumerate(selected):
        # Find matching sample point
        fpso_full = r["fpso"]
        # Try to match the FPSO name
        matched_fpso = None
        for full_name in FPSO_MAP.values():
            if fpso_full in full_name or full_name.startswith(fpso_full):
                matched_fpso = full_name
                break
        if not matched_fpso:
            matched_fpso = fpso_full

        # Find sample point by tag
        sp_id = None
        for (sp_tag, sp_fpso), sid in sp_lookup.items():
            if r["tag"] and (r["tag"] in sp_tag or sp_tag in r["tag"]) and matched_fpso == sp_fpso:
                sp_id = sid
                break

        # Determine status
        mapped_status = STATUS_MAP.get(r["status"], "Planned")
        validation = VALIDATION_MAP.get(r["status"])

        # If has all 4 actual dates and approved, mark as Flow computer updated
        if r["coleta_real"] and r["desemb_real"] and r["lab_real"] and r["laudo_real"] and r["status"] == "Aprovado":
            if r["cv_real"]:
                mapped_status = "Flow computer updated"
            else:
                mapped_status = "Report approved/reproved"

        # Generate a unique sample_id
        fpso_abbr = FPSO_ABBR.get(matched_fpso, fpso_full[:3].upper())
        date_str = r["coleta_real"].strftime("%y%m") if r["coleta_real"] else "2025"
        sample_id = f"HIST-{fpso_abbr}-{date_str}-{next_id + i:04d}"

        # Calculate expected dates from Coleta Realizado (10-10-5-5)
        disembark_expected = None
        lab_expected = None
        report_expected = None
        fc_expected = None
        if r["coleta_real"]:
            disembark_expected = (r["coleta_real"] + timedelta(days=10)).date()
            lab_expected = (r["coleta_real"] + timedelta(days=20)).date()
            report_expected = (r["coleta_real"] + timedelta(days=25)).date()
            fc_expected = (r["coleta_real"] + timedelta(days=30)).date()

        try:
            session.execute(text("""
                INSERT INTO samples (
                    sample_id, type, status, responsible, sample_point_id,
                    osm_id, laudo_number, mitigated,
                    planned_date, sampling_date,
                    disembark_expected_date, disembark_date,
                    lab_expected_date, delivery_date,
                    report_expected_date, report_issue_date,
                    fc_expected_date, fc_update_date,
                    validation_status, notes, created_at
                ) VALUES (
                    :sample_id, :type, :status, :responsible, :sp_id,
                    :osm_id, :laudo_number, :mitigated,
                    :planned_date, :sampling_date,
                    :disembark_expected, :disembark_date,
                    :lab_expected, :delivery_date,
                    :report_expected, :report_issue_date,
                    :fc_expected, :fc_update_date,
                    :validation_status, :notes, :created_at
                )
            """), {
                "sample_id": sample_id,
                "type": r["tipo"],
                "status": mapped_status,
                "responsible": "Historical Import",
                "sp_id": sp_id,
                "osm_id": r["osm_id"],
                "laudo_number": r["laudo_num"],
                "mitigated": r["mitigated"],
                "planned_date": (r["coleta_real"] - timedelta(days=7)).date() if r["coleta_real"] else None,
                "sampling_date": r["coleta_real"].date() if r["coleta_real"] else None,
                "disembark_expected": disembark_expected,
                "disembark_date": r["desemb_real"].date() if r["desemb_real"] else None,
                "lab_expected": lab_expected,
                "delivery_date": r["lab_real"].date() if r["lab_real"] else None,
                "report_expected": report_expected,
                "report_issue_date": r["laudo_real"].date() if r["laudo_real"] else None,
                "fc_expected": fc_expected,
                "fc_update_date": r["cv_real"] if r["cv_real"] else None,
                "validation_status": validation,
                "notes": r["notes"],
                "created_at": r["coleta_real"] if r["coleta_real"] else datetime.utcnow(),
            })
            inserted += 1
        except Exception as e:
            skipped += 1
            print(f"  ✗ Skipped {sample_id}: {e}")
            session.rollback()
            continue

    session.commit()

    # Summary
    from collections import Counter
    types = Counter(r["tipo"] for r in selected)
    statuses = Counter(r["status"] for r in selected)
    print(f"\n══ Done! Inserted {inserted} historical samples (skipped {skipped}) ══")
    print(f"By type: {dict(types)}")
    print(f"By status: {dict(statuses)}")
    session.close()


if __name__ == "__main__":
    main()
