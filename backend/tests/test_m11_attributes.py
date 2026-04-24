"""
M11 — Attribute Definition CRUD & Value Validation Tests
Cobre: criação de definições de atributo, validação de tipo (Numerical com min/max),
Text com regex, Multiple Choice, e a ligação de valores a entidades da hierarquia.
"""
import pytest


# ─── Helpers ────────────────────────────────────────────────────────────────

def _create_num_attr(client, name="Pressure Rating", min_val=0, max_val=100):
    return client.post("/api/config/attributes", json={
        "name": name,
        "description": "Numerical test attribute",
        "type": "Numerical",
        "unit": "bar",
        "entity_type": "METERING_SYSTEM",
        "validation_rules": {"min": min_val, "max": max_val},
    }).json()


def _create_text_attr(client, name="Tag Label"):
    return client.post("/api/config/attributes", json={
        "name": name,
        "description": "Text test attribute",
        "type": "Text",
        "entity_type": "METERING_SYSTEM",
        "validation_rules": {"regex": r"^[A-Z]{2,5}$"},
    }).json()


# ─── Attribute Definition CRUD ───────────────────────────────────────────────

def test_create_numerical_attribute(client):
    """Verifica criação de atributo numérico com regras min/max."""
    attr = _create_num_attr(client, name="Attr-Num-001")
    assert attr["name"] == "Attr-Num-001"
    assert attr["type"] == "Numerical"
    assert attr["id"] > 0


def test_create_text_attribute(client):
    """Verifica criação de atributo de texto com regex."""
    attr = _create_text_attr(client, name="Attr-Text-001")
    assert attr["name"] == "Attr-Text-001"
    assert attr["type"] == "Text"


def test_list_attributes_by_entity_type(client):
    """Verifica que atributos podem ser filtrados por entity_type."""
    _create_num_attr(client, name="Attr-Filter-MS")
    client.post("/api/config/attributes", json={
        "name": "Attr-Filter-DT",
        "type": "Numerical",
        "entity_type": "DEVICE_TYPE",
        "validation_rules": None,
    })

    res = client.get("/api/config/attributes?entity_type=METERING_SYSTEM")
    assert res.status_code == 200
    result = res.json()
    assert all(a["entity_type"] == "METERING_SYSTEM" for a in result)


# ─── Attribute Value CRUD & Validation ──────────────────────────────────────

def test_set_valid_numerical_attribute_value(client, hierarchy_factory):
    """Verifica que um valor numérico dentro do range é aceito."""
    node = hierarchy_factory(tag="SYS-ATTR-VAL-01", level_type="System")
    attr = _create_num_attr(client, name="Attr-Val-Num", min_val=0, max_val=100)

    res = client.post("/api/config/values", json={
        "attribute_id": attr["id"],
        "entity_id": node["id"],
        "value": "50"
    })
    assert res.status_code == 200
    assert res.json()["value"] == "50"


def test_reject_numerical_value_above_max(client, hierarchy_factory):
    """Value acima de max deve retornar 400."""
    node = hierarchy_factory(tag="SYS-ATTR-MAXFAIL", level_type="System")
    attr = _create_num_attr(client, name="Attr-MaxFail", min_val=0, max_val=100)

    res = client.post("/api/config/values", json={
        "attribute_id": attr["id"],
        "entity_id": node["id"],
        "value": "150"
    })
    assert res.status_code == 400
    assert "max" in res.json()["detail"].lower() or "validation" in res.json()["detail"].lower()


def test_reject_numerical_value_below_min(client, hierarchy_factory):
    """Value abaixo de min deve retornar 400."""
    node = hierarchy_factory(tag="SYS-ATTR-MINFAIL", level_type="System")
    attr = _create_num_attr(client, name="Attr-MinFail", min_val=10, max_val=100)

    res = client.post("/api/config/values", json={
        "attribute_id": attr["id"],
        "entity_id": node["id"],
        "value": "5"
    })
    assert res.status_code == 400


def test_set_attribute_value_updates_existing(client, hierarchy_factory):
    """
    Setar o mesmo atributo em um nó duas vezes deve atualizar o valor,
    não criar um duplicado.
    """
    node = hierarchy_factory(tag="SYS-ATTR-UPD", level_type="System")
    attr = _create_num_attr(client, name="Attr-Update-Test", min_val=0, max_val=200)

    client.post("/api/config/values", json={
        "attribute_id": attr["id"],
        "entity_id": node["id"],
        "value": "50"
    })
    client.post("/api/config/values", json={
        "attribute_id": attr["id"],
        "entity_id": node["id"],
        "value": "75"
    })

    res = client.get(f"/api/config/values/{node['id']}")
    assert res.status_code == 200
    values = [v for v in res.json() if v["attribute_id"] == attr["id"]]
    assert len(values) == 1
    assert values[0]["value"] == "75"


def test_reject_invalid_attribute_definition_id(client, hierarchy_factory):
    """Setar um atributo com attribute_id inexistente deve retornar 404."""
    node = hierarchy_factory(tag="SYS-ATTR-NOTFOUND", level_type="System")

    res = client.post("/api/config/values", json={
        "attribute_id": 999999,
        "entity_id": node["id"],
        "value": "abc"
    })
    assert res.status_code == 404


def test_get_values_for_nonexistent_entity_returns_empty(client):
    """GET /api/config/values/{entity_id} para ID inexistente retorna lista vazia."""
    res = client.get("/api/config/values/999999")
    assert res.status_code == 200
    assert res.json() == []
