import pytest
from sqlalchemy.orm import Session
from app import models, schemas
from app.services.validation_engine import validate_report, CheckResult
from app.services.pdf_parser import PVTResult, CROResult
from datetime import datetime, timedelta

def setup_m11_limits(db: Session):
    """Setup some custom limits in ConfigParameter."""
    params = [
        models.ConfigParameter(key="VALIDATION_LIMIT_O2", value="0.8"), # Override 0.5
        models.ConfigParameter(key="SIGMA_MULTIPLIER", value="3.0"),   # Relaxed sigma
        models.ConfigParameter(key="HISTORY_SIZE", value="5"),         # Smaller window
    ]
    for p in params:
        db.merge(p)
    db.commit()

def create_mock_history(db: Session, sample_point_id: int, parameter: str, values: list):
    """Create historical sample results for a parameter."""
    for i, val in enumerate(values):
        # Create a sample
        s = models.Sample(
            sample_id=f"HIST-{parameter}-{i}",
            sample_point_id=sample_point_id,
            type="Chromatography" if parameter == "relative_density_real" else "PVT",
            status="Approved",
            sampling_date=datetime.now() - timedelta(days=i+1)
        )
        db.add(s)
        db.flush()
        
        # Create a result
        res = models.SampleResult(
            sample_id=s.id,
            parameter=parameter,
            value=val,
            unit="unit",
            created_at=datetime.now() - timedelta(days=i+1)
        )
        db.add(res)
    db.commit()

def test_validation_o2_limit(db_session: Session):
    """Test O2 hard limit validation."""
    setup_m11_limits(db_session) # Limit is 0.8
    
    sample = models.Sample(sample_id="T1", sample_point_id=1, type="Chromatography")
    db_session.add(sample)
    db_session.commit()

    # Pass: 0.7 < 0.8
    cro_pass = CROResult(boletim="B1", tag_point="P1", o2=0.7)
    res_pass = validate_report(cro_pass, sample, db_session)
    assert res_pass.overall_status == "Approved"
    assert res_pass.checks[0].status == "pass"

    # Fail: 0.9 > 0.8
    cro_fail = CROResult(boletim="B2", tag_point="P1", o2=0.9)
    res_fail = validate_report(cro_fail, sample, db_session)
    assert res_fail.overall_status == "Reproved"
    assert res_fail.checks[0].status == "fail"

def test_validation_2sigma_bootstrap(db_session: Session):
    """Test 2-sigma bootstrapping (first sample always passes)."""
    db_session.query(models.SampleResult).delete()
    db_session.commit()
    
    sample = models.Sample(sample_id="FIRST", sample_point_id=1, type="PVT")
    db_session.add(sample)
    db_session.commit()

    # First sample: no history. Should pass regardless of value (within reason)
    pvt = PVTResult(boletim="B1", tag_point="P1", density=850.0, density_unit="kg/m3")
    res = validate_report(pvt, sample, db_session)
    
    assert res.overall_status == "Approved"
    check = [c for c in res.checks if c.parameter == "density"][0]
    assert check.status == "pass"
    assert "bootstrapped" in check.detail

def test_validation_2sigma_violation(db_session: Session):
    """Test 2-sigma violation with real history."""
    db_session.query(models.SampleResult).delete()
    db_session.commit()
    
    sp_id = 1
    # Create history: 100, 102, 98, 101, 99 (Mean=100, Std ~1.5)
    create_mock_history(db_session, sp_id, "density", [100.0, 102.0, 98.0, 101.0, 99.0])
    
    sample = models.Sample(sample_id="NEW", sample_point_id=sp_id, type="PVT")
    db_session.add(sample)
    db_session.commit()

    # Sigma is 3.0 (from setup_m11_limits)
    # Range should be approx [100 - 3*1.5, 100 + 3*1.5] -> [95.5, 104.5]
    
    # Pass: 103
    pvt_pass = PVTResult(boletim="B1", tag_point="P1", density=103.0, density_unit="kg/m3")
    res_pass = validate_report(pvt_pass, sample, db_session)
    assert res_pass.overall_status == "Approved"
    
    # Fail: 110 (Way out of 3-sigma)
    pvt_fail = PVTResult(boletim="B2", tag_point="P1", density=110.0, density_unit="kg/m3")
    res_fail = validate_report(pvt_fail, sample, db_session)
    assert res_fail.overall_status == "Reproved"
    check = [c for c in res_fail.checks if c.parameter == "density"][0]
    assert check.status == "fail"

def test_informative_limits_warnings(db_session: Session):
    """Test that H2S and BSW only trigger warnings, not reprovals."""
    sample = models.Sample(sample_id="WARN", sample_point_id=1, type="PVT")
    db_session.add(sample)
    db_session.commit()

    # BSW limit is 1.0. 1.5 should be a warning
    pvt = PVTResult(boletim="B1", tag_point="P1", bsw=1.5)
    res = validate_report(pvt, sample, db_session)
    
    assert res.overall_status == "Approved" # Still approved!
    bsw_check = [c for c in res.checks if c.parameter == "bsw"][0]
    assert bsw_check.status == "warning"
    assert "Informative" in bsw_check.detail
