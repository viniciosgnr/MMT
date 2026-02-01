from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from .. import database

router = APIRouter(
    prefix="/api/audit",
    tags=["Audit Simulation"],
)

class AuditResult(BaseModel):
    rule_id: str
    rule_name: str
    severity: str # Critical, Warning, Info
    status: str # Pass, Fail
    target_system: str
    details: str
    timestamp: datetime

@router.post("/simulate", response_model=List[AuditResult])
def simulate_audit_checks(db: Session = Depends(database.get_db)):
    """
    Simulates the regulatory audit checks defined in Spec 6.8.1.
    In a real system, this would query M11 (Config), M2 (Certs), and M5 (Live Data).
    Here we simulate the logic to demonstrate the workflow.
    """
    results = []
    
    # Mock Data for Simulation
    # We will pretend we checked 3 systems
    systems = [
        {"tag": "11-FE-1001", "name": "Oil Export Meter A", "type": "Turbine"},
        {"tag": "12-FE-2020", "name": "Gas Lift Meter B", "type": "Orifice"},
        {"tag": "14-FE-3050", "name": "Water Inj Meter C", "type": "Magnetic"},
    ]

    # Rule 1: check_orifice_plate_diameter (Only for Orifice)
    # Logic: Config DB says X, Certificate says Y.
    for sys in systems:
        if sys["type"] == "Orifice":
            # Simulate a FAILURE for demonstration
            results.append(AuditResult(
                rule_id="R01",
                rule_name="Orifice Plate Diameter Check",
                severity="Critical",
                status="Fail",
                target_system=sys["tag"],
                details="Configuration mismatch: Configured '12.500 mm', Certificate '12.450 mm'. Deviation > 0.1%",
                timestamp=datetime.now()
            ))
        else:
             results.append(AuditResult(
                rule_id="R01",
                rule_name="Orifice Plate Diameter Check",
                severity="Info",
                status="Pass",
                target_system=sys["tag"],
                details="N/A for this meter type",
                timestamp=datetime.now()
            ))

    # Rule 2: check_k_factor_deviation (For Turbine)
    for sys in systems:
        if sys["type"] == "Turbine":
            # Simulate a WARNING
            results.append(AuditResult(
                rule_id="R02",
                rule_name="K-Factor Deviation",
                severity="Warning",
                status="Fail",
                target_system=sys["tag"],
                details="K-Factor shift: Current '145.2', Previous '144.8'. Shift of 0.28% detected (Warning threshold 0.25%)",
                timestamp=datetime.now()
            ))

    # Rule 3: check_alarm_limits_consistency (All)
    for sys in systems:
        # Simulate Success
        results.append(AuditResult(
            rule_id="R03",
            rule_name="Alarm Limits Consistency",
            severity="Critical",
            status="Pass",
            target_system=sys["tag"],
            details="Flow Computer alarms are within Uncertainty Calculation limits.",
            timestamp=datetime.now()
        ))

    # Rule 4: check_daily_production_change (All)
    # Simulate a "Stuck Value" error
    results.append(AuditResult(
        rule_id="R08",
        rule_name="Daily Production Change",
        severity="Critical",
        status="Fail",
        target_system="14-FE-3050",
        details="Daily totalizer has not changed for 48 hours while status is 'Flowing'.",
        timestamp=datetime.now()
    ))
    
    return results

class FCVerificationResult(BaseModel):
    tag: str
    parameter: str
    mmt_value: str
    fc_value: str
    status: str # Match, Critical, Warning
    deviation: Optional[str] = None

@router.get("/fc-verification-simulate", response_model=List[FCVerificationResult])
def simulate_fc_verification(db: Session = Depends(database.get_db)):
    """
    Simulates the comparison between MMT Configuration (M11) and Flow Computer Data (M5).
    Spec 6.4.11 and 6.8 require highlighting discrepancies.
    """
    results = []
    
    # Mock Scenario: Oil Export Meter A (Turbine)
    # Parameter 1: K-Factor (Match)
    results.append(FCVerificationResult(
        tag="11-FE-1001",
        parameter="K-Factor",
        mmt_value="145.20",
        fc_value="145.20",
        status="Match"
    ))
    
    # Parameter 2: Density Alarm High (Critical Mismatch)
    results.append(FCVerificationResult(
        tag="11-FE-1001",
        parameter="Density Alarm High",
        mmt_value="850.0 kg/m3",
        fc_value="900.0 kg/m3",
        status="Critical",
        deviation="Limit looser in FC (Safety Risk)"
    ))

    # Mock Scenario: Gas Lift Meter B (Orifice)
    # Parameter 3: Plate Diameter (Warning - slight rounding diff)
    results.append(FCVerificationResult(
        tag="12-FE-2020",
        parameter="Orifice Plate Bore",
        mmt_value="12.500 mm",
        fc_value="12.499 mm",
        status="Warning",
        deviation="-0.001 mm"
    ))
    
    # Parameter 4: Differential Pressure Range (Match)
    results.append(FCVerificationResult(
        tag="12-FE-2020",
        parameter="DP Range High",
        mmt_value="2500 mbar",
        fc_value="2500 mbar",
        status="Match"
    ))

    return results
