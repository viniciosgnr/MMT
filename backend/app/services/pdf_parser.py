"""
PDF Parser Service — Extracts lab report data from GT Química PDFs.

Supports two report types:
  - PVT: Density (Massa específica), RS (RGO), FE
  - CRO (Chromatography): O₂, Densidade Relativa do Gás Real

Security hardening (Phase 2):
  - Magic bytes validation
  - File size limits (10MB max)
  - Safe filename handling
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Optional
import fitz  # pymupdf

logger = logging.getLogger("mmt.pdf_parser")

# Security limits
MAX_PDF_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
PDF_MAGIC_BYTES = b"%PDF"


@dataclass
class PVTResult:
    """Extracted values from a PVT lab report."""
    report_type: str = "PVT"
    boletim: Optional[str] = None
    tag_point: Optional[str] = None
    sampling_date: Optional[str] = None
    density: Optional[float] = None         # Massa específica (kg/m³)
    density_unit: str = "kg/m³"
    rs: Optional[float] = None              # RGO ou RS
    rs_unit: str = "m³ STD gás/STD óleo morto"
    fe: Optional[float] = None              # Fator de Encolhimento
    fe_unit: str = "-"
    bsw: Optional[float] = None             # Teor de água e sedimentos (%)
    bsw_unit: str = "%"
    raw_text: str = ""


@dataclass
class CROResult:
    """Extracted values from a Chromatography lab report."""
    report_type: str = "CRO"
    boletim: Optional[str] = None
    tag_point: Optional[str] = None
    sampling_date: Optional[str] = None
    o2: Optional[float] = None                              # Oxigênio (%)
    o2_unit: str = "%"
    relative_density_real: Optional[float] = None            # Densidade Relativa do Gás Real (dimensionless)
    relative_density_real_unit: str = "-"
    h2s: Optional[float] = None                             # Sulfeto de Hidrogênio (ppm)
    h2s_unit: str = "ppm"
    raw_text: str = ""


def _validate_pdf_bytes(pdf_bytes: bytes, filename: str = "") -> None:
    """Validate PDF bytes before processing.

    Security checks:
    1. Magic bytes validation (%PDF header)
    2. File size limit (10MB)

    Raises:
        ValueError: If validation fails.
    """
    if len(pdf_bytes) > MAX_PDF_SIZE_BYTES:
        logger.warning("PDF rejected: size %d bytes exceeds limit (%d). File: %s",
                        len(pdf_bytes), MAX_PDF_SIZE_BYTES, filename)
        raise ValueError(
            f"PDF exceeds maximum allowed size of {MAX_PDF_SIZE_BYTES // (1024*1024)}MB"
        )

    if not pdf_bytes[:4].startswith(PDF_MAGIC_BYTES):
        logger.warning("PDF rejected: invalid magic bytes. File: %s", filename)
        raise ValueError("File does not appear to be a valid PDF")


def _parse_br_float(value_str: str) -> Optional[float]:
    """Parse a Brazilian-format float (comma as decimal separator)."""
    if not value_str:
        return None
    try:
        # Handling thousands separator (dot) and decimal separator (comma)
        clean_str = value_str.replace(".", "").replace(",", ".")
        return float(clean_str)
    except ValueError:
        return None


def _extract_tag_point(text: str) -> Optional[str]:
    """Extract the sampling tag/point (e.g. '662-AP-2233 / P-02')."""
    m = re.search(r"(\d{3}-AP-\d{4}\s*/\s*P-\d+(?:\s*\([^)]+\))?)", text)
    return m.group(1).strip() if m else None


def _extract_boletim(text: str) -> Optional[str]:
    """Extract the Boletim number (e.g. 'PVT Sepetiba/26-16901')."""
    m = re.search(r"Boletim de Resultado de Análise N°\n(.+)", text)
    if m:
        value = m.group(1).strip()
        if re.match(r"(PVT|CRO)\s", value):
            return value
    m2 = re.search(r"((PVT|CRO)\s+\S+/\d{2}-\d+)", text)
    return m2.group(1).strip() if m2 else None


def _extract_sampling_date(text: str) -> Optional[str]:
    """Extract the collection date (Data da Coleta)."""
    m = re.search(r"FPSO\s+.*?\n(\d{2}/\d{2}/\d{4})", text)
    if m:
        return m.group(1)
    m = re.search(r"Data de Receb.*?\n.*?(\d{2}/\d{2}/\d{4})", text)
    return m.group(1) if m else None


def detect_report_type(text: str) -> str:
    """Detect whether the report is PVT or CRO based on content."""
    if re.search(r"RGO ou RS|Fator de Encolhimento|FE\n|Massa específica", text):
        return "PVT"
    if re.search(r"Cromatografia|cromatografia|Composição.*Gás|Concentração\s+Molar", text, re.IGNORECASE):
        return "CRO"
    if re.search(r"PVT\s", text):
        return "PVT"
    if re.search(r"CRO\s", text):
        return "CRO"
    return "UNKNOWN"


def extract_pvt(text: str) -> PVTResult:
    """Extract PVT values from PDF text."""
    result = PVTResult(raw_text=text)
    result.boletim = _extract_boletim(text)
    result.tag_point = _extract_tag_point(text)
    result.sampling_date = _extract_sampling_date(text)

    m = re.search(r"Massa específica absoluta.*?\n([\d,]+)", text)
    if m:
        result.density = _parse_br_float(m.group(1))

    m = re.search(r"RGO ou RS\n([\d,]+)", text)
    if m:
        result.rs = _parse_br_float(m.group(1))

    m = re.search(r"\bFE\n([\d,]+)", text)
    if m:
        result.fe = _parse_br_float(m.group(1))

    return result


def extract_cro(text: str) -> CROResult:
    """Extract Chromatography values from PDF text."""
    result = CROResult(raw_text=text)
    result.boletim = _extract_boletim(text)
    result.tag_point = _extract_tag_point(text)
    result.sampling_date = _extract_sampling_date(text)

    m = re.search(r"O2\nOxigênio\n\w+\n([\d,]+)", text)
    if m:
        result.o2 = _parse_br_float(m.group(1))

    m = re.search(r"Densidade Relativa do G[aá]s Real\n\w+\n([\d,]+)", text)
    if m:
        result.relative_density_real = _parse_br_float(m.group(1))

    return result


def parse_pdf(pdf_path: str) -> PVTResult | CROResult:
    """Parse a lab report PDF and return extracted values.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        PVTResult or CROResult with extracted values.

    Raises:
        ValueError: If the report type cannot be determined or file is invalid.
    """
    # Read and validate before parsing
    with open(pdf_path, "rb") as f:
        raw = f.read()
    _validate_pdf_bytes(raw, pdf_path)

    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()

    report_type = detect_report_type(text)

    if report_type == "PVT":
        return extract_pvt(text)
    elif report_type == "CRO":
        return extract_cro(text)
    else:
        raise ValueError("Unknown report type. Could not detect PVT or CRO from PDF content.")


def parse_pdf_bytes(pdf_bytes: bytes, filename: str = "") -> PVTResult | CROResult:
    """Parse a lab report from in-memory bytes (for file upload handling).

    Args:
        pdf_bytes: Raw PDF bytes.
        filename: Original filename (used as fallback for type detection).

    Returns:
        PVTResult or CROResult with extracted values.

    Raises:
        ValueError: If validation fails or report type is unknown.
    """
    _validate_pdf_bytes(pdf_bytes, filename)

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()

    report_type = detect_report_type(text)

    # Fallback: detect from filename
    if report_type == "UNKNOWN" and filename:
        if "PVT" in filename.upper():
            report_type = "PVT"
        elif "CRO" in filename.upper():
            report_type = "CRO"

    if report_type == "PVT":
        return extract_pvt(text)
    elif report_type == "CRO":
        return extract_cro(text)
    else:
        raise ValueError("Unknown report type. Could not detect PVT or CRO.")
