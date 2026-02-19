"""
Seed real sample points from the Sampling Plan Excel spreadsheet.
Reads the 'Pontos de Coleta' tab and inserts all points per FPSO.

Usage: python -m app.seed_sample_points
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "")

# FPSO abbreviation -> full FPSO name mapping
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

# ──── DATA extracted from the Excel "Pontos de Coleta" tab ────
# Each entry: (tag_number, description_or_tag_suffix)
# Format in Excel: TAG (Description)  e.g. T77-FT-0103 (Fuel Gas)
POINTS_RAW = {
    "CDS": [
        "T77-FT-0103 (Fuel Gas)",
        "T76-FT-0014 (HP Flare)",
        "T76-FT-0034 (LP Flare)",
        "T74-AX-6911 (Export Gas)",
        "T74-AX-6951 (Import Gas)",
        "T73-AP-0001 (Gas Lift)",
        "T71-AX-0102 (HP Separator)",
        "T71-AX-0202 (IP Flash Vessel)",
        "T71-AX-0402 (LP Degasser)",
        "T75-AX-1139 (Injection Gas)",
        "Poço LL-46 (P-01)",
        "Poço LL-91 (P-02)",
        "Poço LL-07 (P-03)",
        "Poço LL-85 (P-05)",
        "Poço LL-80 (P-08)",
        "Poço LL-81 (P-09)",
        "Poço LL-59 (P-10)",
        "Poço LL-106 (P-16)",
        "Oil Fiscal",
        "T62-AP-0124 (Operational Oil)",
        "Poço RJS-677 (P-04)",
    ],
    "CDM": [
        "T76-FT-0014 (HP Flare)",
        "T76-FT-0034 (LP Flare)",
        "T77-FT-0103 (Fuel Gas)",
        "T74-FT-6901 (Export Gas)",
        "T77-FT-6951 (Import Gas)",
        "T73-AP-0001 (Gas Lift)",
        "T71-AX-0102 (HP Separator)",
        "T71-AX-0202 (IP Flash Vessel)",
        "T71-AX-0204 (LP Degasser)",
        "T75-AX-1139 (Injection Gas)",
        "Poço LL-48 (P-01)",
        "Poço LL-63 (P-02)",
        "Poço LL-58 (P-03)",
        "Poço LL-12 (P-05)",
        "Poço LL-84 (P-06)",
        "Poço LL-66 (P-09)",
        "Poço LL-87 (P-14)",
        "Poço LL-61 (P-16)",
        "Poço TUP-128 (P-06)",
        "Oil Fiscal",
        "T62-AP-0124 (Operational Oil)",
        "Poço TUP-132 (P-08)",
    ],
    "CDI": [
        "T76-FT-0014 (HP Flare)",
        "T76-FT-0034 (LP Flare)",
        "T77-FT-6911 (Export Gas)",
        "T77-FT-6951 (Import Gas)",
        "T77-FT-0103 (Fuel Gas)",
        "T73-AP-0001 (Gas Lift)",
        "T71-AX-0102 (HP Separator)",
        "T71-AX-0202 (IP Flash Vessel)",
        "T71-AX-0402 (LP Degasser)",
        "T75-AP-1139 (Injection Gas)",
        "Poço SPH-15 (P-1)",
        "Poço SPS-69 (P-2)",
        "Poço SPH-7 (P-3)",
        "Poço SPH-8 (P-4)",
        "Poço SPH-20 (P-5)",
        "Poço SPH-14 (P-6)",
        "Poço SPH-16 (P-7)",
        "Poço SPH-17 (P-9)",
        "Poço SPH-6 (P-10)",
        "Oil Fiscal",
        "T62-AP-0124 (Operational Oil)",
    ],
    "CDP": [
        "T76-FT-0014 (HP Flare)",
        "T76-FT-0034 (LP Flare)",
        "T77-FT-0103 (Fuel Gas)",
        "T74-FT-6701 (Export Gas)",
        "T74-FT-6751 (Import Gas)",
        "T73-AP-0016 (Gas Lift)",
        "T71-AP-0176 (HP Separator)",
        "T71-AP-0163 (IP Flash Vessel)",
        "T71-AP-0173 (LP Degasser)",
        "T75-AP-1109 (Injection Gas)",
        "T75-AP-3109 (CO2 to Flare)",
        "Poço LL-28 (P-1)",
        "Poço LL-19 (P-02)",
        "Poço LL-119 (P-02)",
        "Poço LL-15 (P-3)",
        "Poço LL-17 (P-04)",
        "Poço LL-11 (P-5)",
        "Poço RJS-674 (P-6)",
        "Poço LL-22 (P-8)",
        "Poço TUP-120 (P-7)",
        "T62-AP-1111 (Oil Fiscal)",
        "T62-AP-0124 (Operational Oil)",
        "Poço TUP-127 (P-05)",
    ],
    "ESS": [
        "T74-FX-061 (Export Gas)",
        "T77-FX-041 (Fuel Gas)",
        "T76-FX-010 (HP Flare)",
        "T76-FX-020 (LP Flare)",
        "T74-FX-072 (Import Gas)",
    ],
    "CPX": [
        "T77-FT-001 (Fuel Gas)",
        "T76-FT-001 (HP Flare)",
        "T76-FT-011 (LP Flare)",
        "M74-FT-100 (Export Gas)",
        "T71-SP-067 (LP Separator)",
        "T71-SP-232 (HP Separator)",
        "Poço CHT-05",
        "Poço CHT-07",
        "Poço CHT-9H",
        "Poço BFR-01",
        "Poço BFR-03",
        "Poço JUB-45",
        "Poço BAZ-10",
    ],
    "CDA": [
        "T77-FT-001 (Fuel Gas)",
        "T76-FT-002 (HP Flare)",
        "T76-FT-012 (LP Flare)",
        "M74-FT-005 (Export Gas)",
        "T71-SP-372 HP-A (CG)",
        "T62-SP-159 HP-A (PVT)",
        "T71-SP-376 HP-B (CG)",
        "T62-SP-149 HP-B (PVT)",
        "PST-223 2º SEP",
        "F64-AT-002A - Offloading",
        "Poço 6-BAZ-01",
        "Poço 7-BAZ-03",
        "Poço 7-BAZ-04",
        "Poço BAZ-06",
        "Poço BAZ-09",
        "Poço BAZ-10",
        "Poço 7-JUB-34",
        "Poço 7-PRB-01",
        "Poço JUB-63",
        "Cargo Tank",
    ],
    "ADG": [
        "776-AP-0006 (HP Flare)",
        "776-AP-0026 (LP Flare)",
        "777-AP-1212 (Fuel Gas)",
        "771-AP-0225 (Flare Assist)",
        "773-AP-0014 (Gas Lift)",
        "771-AP-0123 (FWKO Drum)",
        "771-AP-0202 (IP Flash Vessel)",
        "771-AP-0213 (LP Degasser)",
        "771-AP-0102 (HP Separator)",
        "772-AP-1710-1 (Gas Dehydration)",
        "777-AP-1211 (Flare Pilot)",
        "775-AP-6014 (Gas Injection)",
        "667-AP-2297 (FWKO Drum)",
        "Poço MRO-24 (P-06)",
        "Poço MRO-37 (P-10)",
    ],
    "ATD": [
        "776-AP-0018-2 (HP Flare)",
        "776-AP-0036-2 (LP Flare)",
        "777-AP-1506 (Fuel Gas)",
        "776-AP-7001 (Flare Assist)",
        "773-AP-0014 (Gas Lift)",
        "771-AP-0712A (FWKO Drum A)",
        "771-AP-0712B (FWKO Drum B)",
        "771-AP-0202A (IP Degasser A)",
        "771-AP-0202B (IP Degasser B)",
        "771-AP-0253A (LP Degasser A)",
        "771-AP-0253B (LP Degasser B)",
        "772-AP-1710 (Gas Dehydration)",
        "777-AP-1211 (Flare Pilot)",
        "775-AP-6008 (Gas Injection)",
        "777-AP-1403 (Fuel Gas to Flare Stack)",
        "Oil Fiscal",
        "662-AP-0106 (FWKO Drum)",
        "Poço 7-BUZ-70D-RJS (P-1)",
        "Poço 7-BUZ-87D-RJS (P-4)",
        "Poço 7-BUZ-74D-RJS (P-5)",
        "Poço 7-BUZ-85D-RJS (P-7)",
        "Poço 9-RJS-716 (P-6)",
        "Poço 7-BUZ-41D-RJS (PWAG1)",
    ],
    "SEP": [
        "776-AP-0006 (HP Flare)",
        "776-AP-0030 (LP Flare)",
        "777-AP-1104 (Fuel Gas)",
        "771-AP-0221 (Flare Assist)",
        "773-AP-0011 (Gas Lift Total)",
        "771-AP-0102 (HP Separator)",
        "771-AP-0123 (FWKO Drum)",
        "771-AP-0202 (IP Flash Vessel)",
        "771-AP-0213 (LP Degasser)",
        "772-AP-1710 (Gas Dehydration)",
        "777-AP-1211 (Flare Pilot)",
        "775-AP-6008 (Gas de Injeção)",
        "Poço MRO-27 (P-8)",
        "Poço MRO-16 (P-2)",
        "Poço MRO-17 (P-3)",
        "Poço MRO-18D (P-5)",
        "Poço 3-RJS-739A (P-6)",
        "Poço P-10",
        "662-AP-1005 (Oil Fiscal)",
        "662-AP-0162 (FWKO Drum)",
    ],
}




def parse_tag_description(raw: str):
    """Parse 'TAG (Description)' format into (tag, description)."""
    raw = raw.strip()
    # Handle formats like: T77-FT-0103 (Fuel Gas)
    if "(" in raw and raw.endswith(")"):
        idx = raw.index("(")
        tag = raw[:idx].strip()
        desc = raw[idx+1:-1].strip()
        return tag, desc
    # Handle "TAG Description" without parens, e.g. "T71-SP-067 LP-Separator"
    if " " in raw and not raw.startswith("Poço") and not raw.startswith("Oil") and not raw.startswith("Cargo") and not raw.startswith("PST") and not raw.startswith("F64"):
        parts = raw.split(" ", 1)
        # Check if first part looks like a tag (contains a dash)
        if "-" in parts[0] and len(parts) > 1:
            return parts[0].strip(), parts[1].strip()
    # Simple entries like "Oil Fiscal", "Poço CHT-05", "Cargo Tank"
    return raw, raw


def get_interval(desc: str) -> int:
    """Assign sampling interval based on type."""
    d = desc.lower()
    if "fiscal" in d or "export" in d:
        return 15
    if "flare" in d:
        return 30
    if "poço" in d.lower() or "well" in d:
        return 30
    return 30


def main():
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)

    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Clear existing sample points (detach from samples and instrument_tags first)
    print("Clearing existing sample points...")
    session.execute(text("UPDATE samples SET sample_point_id = NULL WHERE sample_point_id IS NOT NULL"))
    session.execute(text("UPDATE instrument_tags SET sample_point_id = NULL WHERE sample_point_id IS NOT NULL"))
    session.execute(text("DELETE FROM sample_points"))
    session.commit()

    total = 0
    for fpso_abbr, points_list in POINTS_RAW.items():
        fpso_name = FPSO_MAP[fpso_abbr]
        print(f"\n── {fpso_name} ({len(points_list)} points) ──")

        for raw in points_list:
            tag, desc = parse_tag_description(raw)
            # Make tag unique per FPSO by prefixing with abbreviation if it's a generic tag
            # that appears in multiple FPSOs (like "Oil Fiscal")
            unique_tag = tag
            if tag in ("Oil Fiscal", "Cargo Tank"):
                unique_tag = f"{fpso_abbr}-{tag.replace(' ', '-')}"

            # Check for duplicate tags (same tag on different FPSOs)
            existing = session.execute(
                text("SELECT id FROM sample_points WHERE tag_number = :tag"),
                {"tag": unique_tag}
            ).fetchone()

            if existing:
                # Append FPSO abbreviation to make unique
                unique_tag = f"{unique_tag}-{fpso_abbr}"

            interval = get_interval(desc)

            session.execute(text("""
                INSERT INTO sample_points (tag_number, description, fpso_name,
                                          is_operational, sampling_interval_days, validation_method_implemented)
                VALUES (:tag, :desc, :fpso, 1, :interval, 0)
            """), {
                "tag": unique_tag,
                "desc": desc,
                "fpso": fpso_name,
                "interval": interval,
            })
            total += 1
            print(f"  ✓ {unique_tag} — {desc}")

    session.commit()
    print(f"\n══ Done! Inserted {total} sample points across {len(POINTS_RAW)} FPSOs ══")
    session.close()


if __name__ == "__main__":
    main()
