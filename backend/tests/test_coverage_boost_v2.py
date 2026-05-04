import pytest
import anyio
import os
import tempfile
from unittest.mock import MagicMock, patch
from app import models
from app.services.validation_service import ValidationService
from app.services.planning_service import PlanningService
from app.services.sync_service import SyncService
from app.services.maintenance_service import MaintenanceService
from app.services.hierarchy_service import get_hierarchy_tree
from app.services.history_service import HistoryService
from app.services.alerts_service import AlertsService
from app.services.equipment_service import calculate_health
from app.services.calibration_service import CalibrationService
from app.services.pdf_parser import (
    detect_report_type, 
    _parse_br_float, 
    _validate_pdf_bytes, 
    _extract_boletim, 
    extract_pvt,
    extract_cro,
    parse_pdf_bytes,
    parse_pdf
)
from app.schemas import calibration as cal_schemas
from app.schemas.phase3 import (
    PlannedActivityCreate, 
    PlannedActivityUpdate, 
    PlannedActivityMitigate, 
    SyncSourceCreate, 
    DataIngestionPayload, 
    OperationalDataIngest,
    ReportTypeCreate,
    AlertAcknowledge
)
from app.schemas.schemas import MaintenanceCardCreate
from datetime import datetime, date
import json
from fastapi import HTTPException

def test_validation_service_all_branches(db_session):
    """Cover all branches of ValidationService."""
    def_num = models.AttributeDefinition(
        name="Num", type="Numerical", validation_rules=json.dumps({"min": 10, "max": 20})
    )
    assert ValidationService.validate_attribute_value(def_num, "15") is True
    with pytest.raises(ValueError, match="below minimum"):
        ValidationService.validate_attribute_value(def_num, "5")
    with pytest.raises(ValueError, match="above maximum"):
        ValidationService.validate_attribute_value(def_num, "25")

def test_service_layer_mega_boost(db_session):
    """Cover multiple small services to push total coverage."""
    # 1. Hierarchy
    get_hierarchy_tree(db_session)
    
    # 2. History
    rt = ReportTypeCreate(name="RT", description="D", category="C")
    HistoryService.create_report_type(db_session, rt)
    
    # 3. Alerts
    alert = models.Alert(fpso_name="FPSO B", type="Warning", severity="Critical", message="M")
    db_session.add(alert)
    db_session.commit()
    ack = AlertAcknowledge(acknowledged_by="U", justification="J")
    AlertsService.acknowledge_alert(db_session, alert.id, ack)
    
    # 4. Equipment Health
    eq = models.Equipment(serial_number="SN-BOOST-ULTIMATE")
    db_session.add(eq)
    db_session.commit()
    assert calculate_health(eq) == "missing"
    cert = models.EquipmentCertificate(equipment_id=eq.id, certificate_type="Calibration", expiry_date=date.today())
    db_session.add(cert)
    db_session.commit()
    assert calculate_health(eq) == "expiring"
    
    # 5. Calibration
    task = models.CalibrationTask(
        equipment_id=eq.id,
        tag="T-BOOST",
        description="D",
        status="Pending",
        due_date=date.today()
    )
    db_session.add(task)
    db_session.commit()
    
    plan_data = cal_schemas.CalibrationPlanData(procurement_ids=[1, 2], notes="N")
    CalibrationService.plan_calibration(db_session, task.id, plan_data)
    
    exec_data = cal_schemas.CalibrationExecutionData(
        execution_date=date.today(),
        calibration_type="PRV",
        completion_date=date.today(),
        seal_number="S1",
        seal_date=date.today(),
        seal_location="L",
        seal_type="Wire"
    )
    CalibrationService.execute_calibration(db_session, task.id, exec_data, "U1")

def test_maintenance_service_board_boost(db_session):
    """Cover update_card branches."""
    col1 = models.MaintenanceColumn(name="C1", order=1)
    db_session.add(col1)
    db_session.commit()
    
    card_req = MaintenanceCardCreate(title="X", fpso="FPSO B", column_id=col1.id)
    card = MaintenanceService.create_card(db_session, card_req)
    
    # Target branches in update_card
    MaintenanceService.update_card(db_session, card.id, {"title": "New Title"})
    with pytest.raises(HTTPException) as exc:
        MaintenanceService.update_card(db_session, card.id, {"title": "X"}, user_fpso="FPSO A")
    assert exc.value.status_code == 403

def test_planning_service_lifecycle(db_session):
    """Cover PlanningService lifecycle."""
    act = PlannedActivityCreate(
        type="Calibration", title="T", description="D",
        scheduled_date=datetime(2026, 1, 1), responsible="H", fpso_name="FPSO B"
    )
    db_act = PlanningService.create_activity(db_session, act)
    PlanningService.update_activity(db_session, db_act.id, PlannedActivityUpdate(description="U"))
    PlanningService.mitigate_activity(db_session, db_act.id, PlannedActivityMitigate(reason="R", new_due_date=datetime(2026, 2, 1)))
    PlanningService.cancel_activity(db_session, db_act.id)

@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ["asyncio"])
async def test_sync_service_lifecycle(db_session, anyio_backend):
    """Cover SyncService branches."""
    source = SyncSourceCreate(name="S", type="API", fpso="FPSO B")
    db_source = SyncService.create_sync_source(db_session, source)
    
    payload = DataIngestionPayload(
        source_id=db_source.id,
        data=[OperationalDataIngest(tag_number="T", value=1.0, timestamp=datetime.utcnow())]
    )
    SyncService.ingest_data(db_session, payload)
    
    # Cover file upload branch
    csv_content = b"tag,value,timestamp\nT1,10.5,2026-01-01T12:00:00"
    await SyncService.upload_sync_file(db_session, db_source.id, csv_content, "test.csv")

def test_pdf_parser_file_handling():
    """Cover parse_pdf."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
        # Use ASCII-only for bytes write
        tf.write(b"%PDF-1.4\nMassa especifica\n850,5\n" * 10)
        tf_path = tf.name
    try:
        with patch("app.services.pdf_parser.fitz.open") as mock_open:
            mock_doc = MagicMock()
            mock_page = MagicMock()
            # String can contain non-ASCII
            mock_page.get_text.return_value = "Boletim PVT Sepetiba/26-1\nMassa específica absoluta (kg/m\xb3)\n850,5"
            mock_doc.__iter__.return_value = [mock_page]
            mock_open.return_value = mock_doc
            res = parse_pdf(tf_path)
            assert res.density == 850.5
            
            # Additional parser branches
            assert detect_report_type("Massa específica") == "PVT"
            assert detect_report_type("Cromatografia") == "CRO"
            assert detect_report_type("PVT ") == "PVT"
            assert _parse_br_float("1.234,56") == 1234.56
    finally:
        if os.path.exists(tf_path):
            os.remove(tf_path)
