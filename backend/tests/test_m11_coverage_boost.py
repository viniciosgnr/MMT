import pytest
from app import models
from app.services.validation_service import ValidationService
from unittest.mock import MagicMock

def test_validation_service_error_branches():
    # 1. Malformed JSON rules
    bad_attr = MagicMock(spec=models.AttributeDefinition)
    bad_attr.validation_rules = "invalid-json{"
    bad_attr.id = 999
    with pytest.raises(ValueError, match="Validation rules are corrupted"):
        ValidationService.validate_attribute_value(bad_attr, "test")

    # 2. Text validation (min_length)
    text_attr = MagicMock(spec=models.AttributeDefinition)
    text_attr.type = "Text"
    text_attr.validation_rules = {"min_length": 10}
    with pytest.raises(ValueError, match="length 4 is below minimum 10"):
        ValidationService.validate_attribute_value(text_attr, "fail")

    # 3. Text validation (regex)
    regex_attr = MagicMock(spec=models.AttributeDefinition)
    regex_attr.type = "Text"
    regex_attr.validation_rules = {"regex": "^Harness.*"}
    with pytest.raises(ValueError, match="match required format"):
        ValidationService.validate_attribute_value(regex_attr, "Wrong")
    assert ValidationService.validate_attribute_value(regex_attr, "Harness-Bot") is True

    # 4. Choice validation (missing options)
    choice_attr = MagicMock(spec=models.AttributeDefinition)
    choice_attr.type = "Multiple Choice"
    choice_attr.validation_rules = {} # missing options key
    with pytest.raises(ValueError, match="missing valid 'options' list"):
        ValidationService.validate_attribute_value(choice_attr, "val")

def test_configuration_pagination_and_filters(client):
    # Wells pagination
    client.post("/api/config/wells", json={"tag": "PAG-1", "fpso": "CDI", "status": "Active"})
    client.post("/api/config/wells", json={"tag": "PAG-2", "fpso": "CDI", "status": "Active"})
    res = client.get("/api/config/wells?skip=1&limit=1")
    assert len(res.json()) == 1
    
    # Stock Locations pagination
    client.post("/api/config/stock-locations", json={"name": "ST-1", "fpso": "CDI"})
    client.post("/api/config/stock-locations", json={"name": "ST-2", "fpso": "CDI"})
    res_st = client.get("/api/config/stock-locations?limit=1")
    assert len(res_st.json()) == 1

    # Holidays pagination
    client.post("/api/config/holidays", json={"date": "2026-12-01T00:00:00", "description": "H1", "fpso": "CDI"})
    res_h = client.get("/api/config/holidays?limit=1")
    assert len(res_h.json()) >= 1

def test_validation_service_numerical_branches():
    # 1. Type error
    num_attr = MagicMock(spec=models.AttributeDefinition)
    num_attr.type = "Numerical"
    num_attr.validation_rules = {}
    with pytest.raises(ValueError, match="must be a number"):
        ValidationService.validate_attribute_value(num_attr, "not-a-number")
    
    # 2. Min/Max branches
    num_attr.validation_rules = {"min": 10, "max": 20}
    with pytest.raises(ValueError, match="below minimum 10"):
        ValidationService.validate_attribute_value(num_attr, "5")
    with pytest.raises(ValueError, match="above maximum 20"):
        ValidationService.validate_attribute_value(num_attr, "25")
    assert ValidationService.validate_attribute_value(num_attr, "15") is True

def test_config_router_filtering_and_errors(client):
    # Read Wells (no filter)
    res_w = client.get("/api/config/wells")
    assert res_w.status_code == 200
    
    # Read Stock Locations (no filter)
    res_sl = client.get("/api/config/stock-locations")
    assert res_sl.status_code == 200

    # Read Holidays (no filter)
    res_h = client.get("/api/config/holidays")
    assert res_h.status_code == 200

def test_config_router_remaining_getters(client):
    # Cover the read_attributes logic and other miscellaneous gets
    res = client.get("/api/config/attributes")
    assert res.status_code == 200
    res = client.get("/api/config/hierarchy/nodes")
    assert res.status_code == 200
    res = client.get("/api/config/wells?skip=0&limit=10")
    assert res.status_code == 200

