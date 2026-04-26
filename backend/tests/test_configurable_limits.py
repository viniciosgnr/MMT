"""
Harness Engineering Configuration Parametrization Tests — Phase 3.

Verifies that CA Limits (O2, H2S, BSW) and FPSO Names are dynamically loaded 
from the M11 ConfigParameter database instead of hardcoded values.
"""
import pytest
from app.models import ConfigParameter
from app.services.validation_engine import _check_o2_limit
from app.services.hierarchy_service import get_hierarchy_tree

def test_ca_hard_limits_read_from_database(client, db_session):
    """Test that validation engine uses M11 configured limits when available."""
    
    # 1. Start with no config (should use defaults: 0.5 for O2)
    check_no_config = _check_o2_limit(0.6, db_session)
    assert check_no_config.status == "fail"
    assert "exceeds limit" in check_no_config.detail
    
    # 2. Add custom strict config parameter (0.2 limit)
    param = ConfigParameter(
        key="VALIDATION_LIMIT_O2",
        value="0.2",
        fpso="GLOBAL",
        description="Strict O2 limit for tests"
    )
    db_session.add(param)
    db_session.commit()
    
    # 3. Test value that passes default (0.4 < 0.5) but fails strict (0.4 > 0.2)
    check_strict = _check_o2_limit(0.4, db_session)
    assert check_strict.status == "fail"
    
    # 4. Cleanup
    db_session.delete(param)
    db_session.commit()

def test_hierarchy_service_reads_fpso_from_database(client, db_session):
    """Test that hierarchy tree uses the FPSO name configured in M11 parameters."""
    
    # 1. Setup a custom FPSO name in the config table
    param = ConfigParameter(
        key="FPSO_NAME",
        value="FPSO HARNESS TEST",
        fpso="GLOBAL",
    )
    db_session.add(param)
    db_session.commit()
    
    # 2. Get tree and verify
    tree = get_hierarchy_tree(db_session)
    assert tree is not None
    assert len(tree) >= 1
    assert tree[0].tag == "FPSO HARNESS TEST"
    
    # 3. Cleanup
    db_session.delete(param)
    db_session.commit()
