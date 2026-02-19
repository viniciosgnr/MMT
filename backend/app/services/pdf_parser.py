"""
PDF Parser Service — Extracts lab report data from GT Química PDFs.

Supports two report types:
  - PVT: Density (Massa específica), RS (RGO), FE
  - CRO (Chromatography): O₂, Density Absolute (Std + Operating conditions)
"""

import re
from dataclasses import dataclass, field
from typing import Optional
import fitz  # pymupdf


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
    raw_text: str = ""


@dataclass
class CROResult:
    """Extracted values from a Chromatography lab report."""
    report_type: str = "CRO"
    boletim: Optional[str] = None
    tag_point: Optional[str] = None
    sampling_date: Optional[str] = None
    o2: Optional[float] = None                      # Oxigênio (%)
    o2_unit: str = "%"
    density_abs_std: Optional[float] = None          # Densidade Absoluta - Condição Padrão (kg/m³)
    density_abs_std_unit: str = "kg/m³"
    density_abs_op: Optional[float] = None           # Densidade Absoluta - Condição Operação (kg/m³)
    density_abs_op_unit: str = "kg/m³"
    raw_text: str = ""


def _parse_br_float(value_str: str) -> Optional[float]:
    """Parse a Brazilian-format float (comma as decimal separator)."""
    if not value_str:
        return None
    try:
        return float(value_str.replace(",", "."))
    except ValueError:
        return None


def _extract_tag_point(text: str) -> Optional[str]:
    """Extract the sampling tag/point (e.g. '662-AP-2233 / P-02')."""
    m = re.search(r"(\d{3}-AP-\d{4}\s*/\s*P-\d+(?:\s*\([^)]+\))?)", text)
    return m.group(1).strip() if m else None


def _extract_boletim(text: str) -> Optional[str]:
    """Extract the Boletim number (e.g. 'PVT Sepetiba/26-16901')."""
    # The boletim appears after "Boletim de Resultado de Análise N°"
    m = re.search(r"Boletim de Resultado de Análise N°\n(.+)", text)
    if m:
        value = m.group(1).strip()
        # Sometimes the next line leaks in — take only lines starting with PVT/CRO
        if re.match(r"(PVT|CRO)\s", value):
            return value
    # Fallback: search for PVT/CRO pattern anywhere
    m2 = re.search(r"((PVT|CRO)\s+\S+/\d{2}-\d+)", text)
    return m2.group(1).strip() if m2 else None


def _extract_sampling_date(text: str) -> Optional[str]:
    """Extract the collection date (Data da Coleta).
    
    The date appears near the FPSO name in the report layout,
    e.g. 'FPSO Cidade de Sepetiba\n17/01/2026\n'
    """
    # Look for date right after FPSO mention
    m = re.search(r"FPSO\s+.*?\n(\d{2}/\d{2}/\d{4})", text)
    if m:
        return m.group(1)
    # Fallback: look for date near "Data da Coleta" or "Data de Receb"
    m = re.search(r"Data de Receb.*?\n.*?(\d{2}/\d{2}/\d{4})", text)
    return m.group(1) if m else None


def detect_report_type(text: str) -> str:
    """Detect whether the report is PVT or CRO based on content."""
    if re.search(r"RGO ou RS|Fator de Encolhimento|FE\n|Massa específica", text):
        return "PVT"
    if re.search(r"Cromatografia|cromatografia|Composição.*Gás|Concentração\s+Molar", text, re.IGNORECASE):
        return "CRO"
    # Fallback: check boletim prefix
    if re.search(r"PVT\s", text):
        return "PVT"
    if re.search(r"CRO\s", text):
        return "CRO"
    return "UNKNOWN"


def extract_pvt(text: str) -> PVTResult:
    """Extract PVT values from PDF text.
    
    Expected text patterns:
        Massa específica absoluta do óleo morto - 20 °C\n875,39\n...
        RGO ou RS\n88,0571\n...
        FE\n0,8241\n...
    """
    result = PVTResult(raw_text=text)
    result.boletim = _extract_boletim(text)
    result.tag_point = _extract_tag_point(text)
    result.sampling_date = _extract_sampling_date(text)

    # Massa específica absoluta do óleo morto - value is on the next line
    m = re.search(r"Massa específica absoluta.*?\n([\d,]+)", text)
    if m:
        result.density = _parse_br_float(m.group(1))

    # RGO ou RS
    m = re.search(r"RGO ou RS\n([\d,]+)", text)
    if m:
        result.rs = _parse_br_float(m.group(1))

    # FE (Fator de Encolhimento)
    m = re.search(r"\bFE\n([\d,]+)", text)
    if m:
        result.fe = _parse_br_float(m.group(1))

    return result


def extract_cro(text: str) -> CROResult:
    """Extract Chromatography values from PDF text.
    
    Extracts:
        - O₂ from the Contaminantes section
        - Densidade Absoluta from Condição Padrão section
        - Densidade Absoluta from Condição Operação section
    """
    result = CROResult(raw_text=text)
    result.boletim = _extract_boletim(text)
    result.tag_point = _extract_tag_point(text)
    result.sampling_date = _extract_sampling_date(text)

    # O₂ — in Contaminantes section: O2\nOxigênio\n1A\n0,032
    m = re.search(r"O2\nOxigênio\n\w+\n([\d,]+)", text)
    if m:
        result.o2 = _parse_br_float(m.group(1))

    # Split text into standard and operating condition sections
    # "Propriedades do Gás (Condição Padrão)" ... "Propriedades do Gás (Condição Operação"
    std_section = ""
    op_section = ""
    
    std_match = re.search(r"Propriedades do Gás \(Condição Padrão\)", text)
    op_match = re.search(r"Propriedades do Gás \(Condição Operação", text)
    
    if std_match and op_match:
        std_section = text[std_match.start():op_match.start()]
        # Operating section goes until Contaminantes or end
        contam_match = re.search(r"Contaminantes", text[op_match.start():])
        if contam_match:
            op_section = text[op_match.start():op_match.start() + contam_match.start()]
        else:
            op_section = text[op_match.start():]
    elif std_match:
        std_section = text[std_match.start():]

    # Densidade Absoluta — Condição Padrão
    m = re.search(r"Densidade Absoluta\n\w+\n([\d,]+)\nkg/m", std_section)
    if m:
        result.density_abs_std = _parse_br_float(m.group(1))

    # Densidade Absoluta — Condição Operação
    m = re.search(r"Densidade Absoluta\n\w+\n([\d,]+)\nkg/m", op_section)
    if m:
        result.density_abs_op = _parse_br_float(m.group(1))

    return result


def parse_pdf(pdf_path: str) -> PVTResult | CROResult:
    """Parse a lab report PDF and return extracted values.
    
    Args:
        pdf_path: Path to the PDF file.
    
    Returns:
        PVTResult or CROResult with extracted values.
    
    Raises:
        ValueError: If the report type cannot be determined.
    """
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
        raise ValueError(f"Unknown report type. Could not detect PVT or CRO from PDF content.")


def parse_pdf_bytes(pdf_bytes: bytes, filename: str = "") -> PVTResult | CROResult:
    """Parse a lab report from in-memory bytes (for file upload handling).
    
    Args:
        pdf_bytes: Raw PDF bytes.
        filename: Original filename (used as fallback for type detection).
    
    Returns:
        PVTResult or CROResult with extracted values.
    """
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
        raise ValueError(f"Unknown report type. Could not detect PVT or CRO.")
