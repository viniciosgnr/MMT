"""
Pillar 2 — API Contract & OpenAPI Schema Validation Tests
Schemathesis v4 API + custom GET-endpoint smoke tests.
Verifica que: (1) o schema OpenAPI é válido, (2) todos os GETs retornam < 500,
(3) campos críticos estão presentes nos schemas de resposta.
"""
import pytest
import schemathesis
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.dependencies import get_current_user

# ─── Isolated DB ─────────────────────────────────────────────────────────────

contract_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
ContractSession = sessionmaker(autocommit=False, autoflush=False, bind=contract_engine)


def override_get_db_contract():
    db = ContractSession()
    try:
        yield db
    finally:
        db.close()


def override_get_current_user_contract():
    return {"id": "schema-bot", "email": "schema@test.com", "role": "Admin"}


@pytest.fixture(scope="module")
def contract_client():
    app.dependency_overrides[get_db] = override_get_db_contract
    app.dependency_overrides[get_current_user] = override_get_current_user_contract
    Base.metadata.create_all(bind=contract_engine)
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture(scope="module")
def openapi_schema(contract_client):
    res = contract_client.get("/openapi.json")
    assert res.status_code == 200
    return res.json()


# ─── Core schema validation ──────────────────────────────────────────────────

def test_openapi_schema_is_accessible(contract_client):
    """GET /openapi.json deve retornar 200 com schema válido."""
    res = contract_client.get("/openapi.json")
    assert res.status_code == 200
    data = res.json()
    assert data.get("openapi", "").startswith("3.")
    assert "paths" in data
    assert len(data["paths"]) > 0


def test_openapi_has_api_routes(openapi_schema):
    """O schema deve conter rotas para os 3 módulos: equipment, chemical, config."""
    paths = openapi_schema["paths"]
    has_equipment = any("/equipment" in p for p in paths)
    has_chemical = any("/chemical" in p for p in paths)
    has_config = any("/config" in p for p in paths)
    assert has_equipment, "Schema missing /equipment endpoints"
    assert has_chemical, "Schema missing /chemical endpoints"
    assert has_config, "Schema missing /config endpoints"


def test_equipment_response_schema_has_critical_fields(openapi_schema):
    """Equipment schema deve ter id, serial_number, equipment_type."""
    schemas = openapi_schema.get("components", {}).get("schemas", {})
    equipment = schemas.get("Equipment", {})
    assert "properties" in equipment, "Equipment schema missing 'properties'"
    props = set(equipment["properties"].keys())
    for field in ["id", "serial_number", "equipment_type"]:
        assert field in props, f"Equipment schema missing field: {field}"


def test_sample_response_schema_has_critical_fields(openapi_schema):
    """Sample schema deve ter id, sample_id, status, sample_point_id."""
    schemas = openapi_schema.get("components", {}).get("schemas", {})
    sample = schemas.get("Sample", {})
    assert "properties" in sample, "Sample schema missing 'properties'"
    props = set(sample["properties"].keys())
    for field in ["id", "sample_id", "status", "sample_point_id"]:
        assert field in props, f"Sample schema missing field: {field}"


def test_hierarchy_node_schema_has_critical_fields(openapi_schema):
    """HierarchyNode schema deve ter id, tag, level_type."""
    schemas = openapi_schema.get("components", {}).get("schemas", {})
    node = schemas.get("HierarchyNode", {})
    if not node:
        pytest.skip("HierarchyNode not in schemas (may be inline)")
    props = set(node.get("properties", {}).keys())
    for field in ["id", "tag", "level_type"]:
        assert field in props, f"HierarchyNode schema missing field: {field}"


# ─── GET smoke test: all simple endpoints must return < 500 ──────────────────

def test_all_get_endpoints_without_path_params_return_non_500(contract_client, openapi_schema):
    """
    Todos os GETs sem path params obrigatórios devem retornar 2xx ou 4xx — nunca 5xx.
    Cada 5xx indica um bug de servidor que o fuzzer detectou.
    """
    paths = openapi_schema.get("paths", {})
    violations = []

    for path, methods in paths.items():
        if "get" not in methods or "{" in path:
            continue
        res = contract_client.get(path)
        if res.status_code >= 500:
            violations.append(f"GET {path} → {res.status_code}: {res.text[:150]}")

    assert not violations, "Endpoints retornando 5xx:\n" + "\n".join(violations)


# ─── Schemathesis v4: register schema and smoke-test via schemathesis.pytest ─

def test_schemathesis_can_load_openapi_schema(openapi_schema):
    """
    Schemathesis v4 pode carregar o schema OpenAPI sem errors.
    Confirma que a spec é parseável pelo engine de fuzzing.
    """
    schema = schemathesis.openapi.from_dict(openapi_schema)
    assert schema is not None
    total_ops = sum(len(methods) for methods in openapi_schema["paths"].values())
    assert total_ops > 10, f"Expected > 10 API operations, got {total_ops}"

