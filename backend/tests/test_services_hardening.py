from datetime import date
from app.services.pdf_parser import detect_report_type, _parse_br_float, _validate_pdf_bytes
from app.services.sync_service import SyncService
from app.schemas.phase3 import SyncSourceCreate
from app import models
import pytest
import uuid

def test_pdf_parser_detect():
    """Test PDF detection logic with various strings."""
    # Based on regex: r"RGO ou RS|Fator de Encolhimento|FE\n|Massa específica"
    assert detect_report_type("Massa específica") == "PVT"
    assert detect_report_type("RGO ou RS") == "PVT"
    # Based on regex: r"Cromatografia|cromatografia|Composição.*Gás|Concentração\s+Molar"
    assert detect_report_type("Cromatografia") == "CRO"
    assert detect_report_type("Composição do Gás") == "CRO"

def test_pdf_float_parsing():
    """Test Brazilian float parsing logic."""
    assert _parse_br_float("850,5") == 850.5
    assert _parse_br_float("1.234,56") == 1234.56
    assert _parse_br_float(None) is None

def test_pdf_validation_errors():
    """Test PDF validation logic (security hardening)."""
    with pytest.raises(ValueError, match="maximum allowed size"):
        _validate_pdf_bytes(b"x" * (11 * 1024 * 1024))
    
    with pytest.raises(ValueError, match="valid PDF"):
        _validate_pdf_bytes(b"NOTAPDF")

def test_sync_service_creation(db_session):
    """Test creating sync source."""
    src = SyncSourceCreate(name=f"SRC-{uuid.uuid4().hex[:4]}", type="API", description="Desc", fpso="FPSO Harness")
    res = SyncService.create_sync_source(db_session, src)
    assert res.name.startswith("SRC-")

def test_calibration_task_persistence(db_session):
    """Test calibration task persistence."""
    task = models.CalibrationTask(
        tag=f"T-{uuid.uuid4().hex[:4]}",
        due_date=date(2026, 1, 1),
        status="Pending"
    )
    db_session.add(task)
    db_session.commit()
    assert task.id is not None
