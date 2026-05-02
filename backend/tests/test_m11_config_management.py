"""
M11 — Well & Configuration Management Tests
Cobre: CRUD de poços (wells), parâmetros de configuração (ConfigParameter),
stock-locations, holidays, e updates de hierarquia em nós estáticos.
"""
import pytest


# ─── Wells ──────────────────────────────────────────────────────────────────

def test_create_attribute_with_date_rule(client):
    payload = {
        "entity_type": "InstrumentTag",
        "name": "InstallationDate",
        "type": "Date",
        "validation_rules": {"format": "YYYY-MM-DD"} # Used to test our DATE robust validation
    }
    response = client.post("/api/config/attributes", json=payload)
    assert response.status_code == 200
    return response.json()

def test_create_attribute_with_choice_rule(client):
    payload = {
        "entity_type": "InstrumentTag",
        "name": "VendorName",
        "type": "Multiple Choice",
        "validation_rules": {"options": ["CompanyA", "CompanyB"]}
    }
    response = client.post("/api/config/attributes", json=payload)
    assert response.status_code == 200
    return response.json()

def test_invalid_date_attribute_value_format(client):
    # Relies on order or we just create it:
    attr = test_create_attribute_with_date_rule(client)
    payload = {
        "attribute_id": attr["id"],
        "entity_id": 99,
        "value": "2024/10/01" # Invalid format
    }
    response = client.post("/api/config/values", json=payload)
    assert response.status_code == 400
    assert "YYYY-MM-DD" in response.json()["detail"]

def test_valid_date_attribute_value(client):
    attr = test_create_attribute_with_date_rule(client)
    payload = {
        "attribute_id": attr["id"],
        "entity_id": 99,
        "value": "2024-10-01"
    }
    response = client.post("/api/config/values", json=payload)
    assert response.status_code == 200

def test_invalid_choice_attribute_value(client):
    attr = test_create_attribute_with_choice_rule(client)
    payload = {
        "attribute_id": attr["id"],
        "entity_id": 99,
        "value": "CompanyC" # Not in options
    }
    response = client.post("/api/config/values", json=payload)
    assert response.status_code == 400
    assert "not a valid option" in response.json()["detail"]

def test_create_well(client):
    """Verifica criação de poço de produção no M11."""
    res = client.post("/api/config/wells", json={
        "tag": "WELL-P-RJS-001A",
        "fpso": "CDI",
        "status": "Active"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["tag"] == "WELL-P-RJS-001A"
    assert data["id"] > 0


def test_list_wells_by_fpso(client):
    """Verifica filtragem de poços por FPSO."""
    client.post("/api/config/wells", json={"tag": "WELL-CDI-01", "fpso": "CDI", "status": "Active"})
    client.post("/api/config/wells", json={"tag": "WELL-BUZ-01", "fpso": "BUZ", "status": "Active"})

    res = client.get("/api/config/wells?fpso=CDI")
    assert res.status_code == 200
    assert all("CDI" in w["fpso"] for w in res.json())


def test_update_well(client):
    """Verifica atualização de status de um poço."""
    res = client.post("/api/config/wells", json={
        "tag": "WELL-UPD-01", "fpso": "CDI", "status": "Active"
    })
    well_id = res.json()["id"]

    upd = client.put(f"/api/config/wells/{well_id}", json={"status": "Inactive"})
    assert upd.status_code == 200
    assert upd.json()["status"] == "Inactive"


def test_delete_well(client):
    """Verifica deleção de um poço."""
    res = client.post("/api/config/wells", json={
        "tag": "WELL-DEL-01", "fpso": "CDI", "status": "Active"
    })
    well_id = res.json()["id"]

    del_res = client.delete(f"/api/config/wells/{well_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"


def test_update_nonexistent_well_returns_404(client):
    """PUT em poço inexistente deve retornar 404."""
    res = client.put("/api/config/wells/999999", json={
        "name": "GHOST", "fpso": "X", "type": "Y", "status": "Active"
    })
    assert res.status_code == 404


# ─── ConfigParameters ────────────────────────────────────────────────────────

def test_set_and_retrieve_config_parameter(client):
    """Verifica criação e leitura de parâmetro de configuração por FPSO."""
    res = client.post("/api/config/parameters", json={
        "key": "max_bsw_alert",
        "value": "0.8",
        "fpso": "CDI",
        "description": "Max BSW before alert"
    })
    assert res.status_code == 200
    assert res.json()["key"] == "max_bsw_alert"

    read = client.get("/api/config/parameters?fpso=CDI")
    assert read.status_code == 200
    keys = [p["key"] for p in read.json()]
    assert "max_bsw_alert" in keys


def test_set_config_parameter_updates_existing(client):
    """Definir o mesmo parâmetro duas vezes deve atualizar, não duplicar."""
    client.post("/api/config/parameters", json={
        "key": "sla_days", "value": "30", "fpso": "CDI", "description": "SLA days"
    })
    client.post("/api/config/parameters", json={
        "key": "sla_days", "value": "45", "fpso": "CDI", "description": "SLA days updated"
    })
    read = client.get("/api/config/parameters?fpso=CDI")
    sla = [p for p in read.json() if p["key"] == "sla_days"]
    assert len(sla) == 1
    assert sla[0]["value"] == "45"


# ─── Stock Locations ─────────────────────────────────────────────────────────

def test_create_stock_location(client):
    """Verifica criação de localização de estoque."""
    res = client.post("/api/config/stock-locations", json={
        "name": "Almoxarifado Principal",
        "fpso": "CDI",
        "description": "Main warehouse"
    })
    assert res.status_code == 200
    assert res.json()["name"] == "Almoxarifado Principal"


def test_list_stock_locations_by_fpso(client):
    """Verifica listagem de localizações por FPSO."""
    client.post("/api/config/stock-locations", json={"name": "SL-CDI", "fpso": "CDI"})
    client.post("/api/config/stock-locations", json={"name": "SL-BUZ", "fpso": "BUZ"})

    res = client.get("/api/config/stock-locations?fpso=CDI")
    assert res.status_code == 200
    assert all("CDI" in sl["fpso"] for sl in res.json())


# ─── Holidays ────────────────────────────────────────────────────────────────

def test_create_holiday(client):
    """Verifica criação de feriado para cálculo de SLA."""
    res = client.post("/api/config/holidays", json={
        "date": "2026-01-01T00:00:00",
        "description": "Ano Novo",
        "fpso": "CDI"
    })
    assert res.status_code == 200
    assert res.json()["description"] == "Ano Novo"


def test_list_holidays_by_fpso(client):
    """Verifica listagem de feriados por FPSO."""
    client.post("/api/config/holidays", json={"date": "2026-04-21T00:00:00", "description": "Tiradentes", "fpso": "CDI"})
    client.post("/api/config/holidays", json={"date": "2026-04-21T00:00:00", "description": "Tiradentes", "fpso": "BUZ"})

    res = client.get("/api/config/holidays?fpso=CDI")
    assert res.status_code == 200
    assert all(h["fpso"] == "CDI" for h in res.json())


# ─── Hierarchy Node Updates ───────────────────────────────────────────────────

def test_update_hierarchy_node_description(client, hierarchy_factory):
    """Verifica que a descrição de um nó hierárquico pode ser atualizada."""
    node = hierarchy_factory(tag="SYS-UPD-01", description="Original Description", level_type="System")

    res = client.put(f"/api/config/hierarchy/nodes/{node['id']}", json={
        "tag": "SYS-UPD-01",
        "description": "Updated Description",
        "level_type": "System"
    })
    assert res.status_code == 200
    assert res.json()["description"] == "Updated Description"


def test_update_nonexistent_hierarchy_node_returns_404(client):
    """PUT em nó hierárquico inexistente deve retornar 404."""
    res = client.put("/api/config/hierarchy/nodes/999999", json={
        "tag": "GHOST", "description": "Ghost node", "level_type": "System"
    })
    assert res.status_code == 404

# ─── SLARule ─────────────────────────────────────────────────────────────────

def test_create_sla_rule(client):
    """Verifica criação de regra SLA no M11."""
    res = client.post("/api/config/sla-rules", json={
        "classification": "Fiscal",
        "analysis_type": "Chromatography",
        "local": "Onshore",
        "interval_days": 30,
        "disembark_days": 10,
        "lab_days": 20,
        "report_days": 25,
        "fc_days": 3,
        "fc_is_business_days": True,
        "needs_validation": True
    })
    assert res.status_code == 200
    assert res.json()["classification"] == "Fiscal"
    assert res.json()["interval_days"] == 30

def test_list_sla_rules(client):
    """Verifica listagem de regras SLA."""
    client.post("/api/config/sla-rules", json={
        "classification": "Apropriation",
        "analysis_type": "Chromatography",
        "local": "Offshore",
        "interval_days": 90,
        "report_days": 25,
        "needs_validation": True
    })
    res = client.get("/api/config/sla-rules")
    assert res.status_code == 200
    assert len(res.json()) >= 1
