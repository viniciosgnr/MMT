"""
Harness Engineering — conftest.py for M3 Integration Tests
Skills Applied:
- fastapi-pro → TestClient, dependency overrides, factory pattern, session management
- backend-dev-guidelines → Layered architecture, testing discipline

Banco de dados SQLite em memória para isolamento total do Supabase.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.database import Base, get_db
import app.models as db_models
from app.dependencies import get_current_user

# --- Skill (fastapi-pro): SQLite in-memory for ultra-fast durable tests ---
from sqlalchemy.pool import StaticPool
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Skill (fastapi-pro): Dependency override for database session."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


def override_get_current_user():
    """Skill (fastapi-pro): Bypass auth during integration tests."""
    return {
        "id": "harness-bot-01",
        "email": "harness@sbmoffshore.com",
        "username": "harness-bot",
        "role": "HarnessAdmin",
        "fpso_name": None
    }


# --- Apply dependency overrides ---
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


# --- Skill (fastapi-pro): Factory pattern for test data generation ---
class SamplePointFactory:
    """Factory para gerar SamplePoints de teste rapidamente."""
    _counter = 0

    @classmethod
    def create(cls, client, **overrides):
        cls._counter += 1
        defaults = {
            "tag_number": f"SP-FACTORY-{cls._counter:04d}",
            "description": f"Auto-generated SP {cls._counter}",
            "fpso_name": "FPSO Harness",
        }
        defaults.update(overrides)
        res = client.post("/api/chemical/sample-points", json=defaults)
        assert res.status_code == 200, f"Factory SamplePoint failed: {res.text}"
        return res.json()


class SampleFactory:
    """Factory para gerar Samples de teste rapidamente."""
    _counter = 0

    @classmethod
    def create(cls, client, sample_point_id, **overrides):
        cls._counter += 1
        defaults = {
            "sample_id": f"SAMPLE-FACTORY-{cls._counter:04d}",
            "type": "Chromatography",
            "sample_point_id": sample_point_id,
            "local": "Onshore",
            "planned_date": "2026-06-01",
        }
        defaults.update(overrides)
        res = client.post("/api/chemical/samples", json=defaults)
        assert res.status_code == 200, f"Factory Sample failed: {res.text}"
        return res.json()


class EquipmentFactory:
    """Factory para gerar Equipamentos físicos de teste."""
    _counter = 0

    @classmethod
    def create(cls, client, **overrides):
        cls._counter += 1
        defaults = {
            "serial_number": f"SN-FAC-{cls._counter:04d}",
            "model": f"Model-{cls._counter}",
            "manufacturer": "Harness Corp",
            "equipment_type": "Flow Computer",
            "fpso_name": "FPSO Harness",
            "status": "Active"
        }
        defaults.update(overrides)
        res = client.post("/api/equipment/", json=defaults)
        assert res.status_code == 200, f"Factory Equipment failed: {res.text}"
        return res.json()


class InstrumentTagFactory:
    """Factory para gerar Tags de instrumentação (Locais)."""
    _counter = 0

    @classmethod
    def create(cls, client, **overrides):
        cls._counter += 1
        defaults = {
            "tag_number": f"TAG-FAC-{cls._counter:04d}",
            "description": f"Harness Test Tag {cls._counter}",
            "area": "Process",
            "service": "Metering"
        }
        defaults.update(overrides)
        res = client.post("/api/equipment/tags", json=defaults)
        assert res.status_code == 200, f"Factory InstrumentTag failed: {res.text}"
        return res.json()


class EquipmentTagInstallationFactory:
    """Factory para gerar instalações de equipamentos em tags."""

    @classmethod
    def create(cls, client, equipment_id, tag_id, **overrides):
        defaults = {
            "equipment_id": equipment_id,
            "tag_id": tag_id,
            "installed_by": "Harness Engineer",
            "installation_date": datetime.utcnow().isoformat()
        }
        defaults.update(overrides)
        res = client.post("/api/equipment/install", json=defaults)
        assert res.status_code == 200, f"Factory Installation failed: {res.text}"
        return res.json()
    
class EquipmentCertificateFactory:
    """Factory para gerar certificados de calibração."""
    _counter = 0

    @classmethod
    def create(cls, client, equipment_id, **overrides):
        cls._counter += 1
        defaults = {
            "equipment_id": equipment_id,
            "certificate_number": f"CERT-FAC-{cls._counter:04d}",
            "issue_date": (datetime.utcnow() - timedelta(days=30)).date().isoformat(),
            "expiry_date": (datetime.utcnow() + timedelta(days=335)).date().isoformat(),
            "certificate_type": "Calibration"
        }
        defaults.update(overrides)
        res = client.post("/api/equipment/certificates", json=defaults)
        assert res.status_code == 200, f"Factory Certificate failed: {res.text}"
        return res.json()


class HierarchyNodeFactory:
    """Factory para gerar nós da hierarquia (M11)."""
    _counter = 0

    @classmethod
    def create(cls, client, **overrides):
        cls._counter += 1
        defaults = {
            "tag": f"NODE-FAC-{cls._counter:04d}",
            "description": f"Hierarchy Node {cls._counter}",
            "level_type": "System"
        }
        defaults.update(overrides)
        res = client.post("/api/config/hierarchy/nodes", json=defaults)
        assert res.status_code == 200, f"Factory HierarchyNode failed: {res.text}"
        return res.json()


# --- Fixtures ---
@pytest.fixture(scope="module")
def client():
    """Skill (fastapi-pro): TestClient with full DB lifecycle."""
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def db_session() -> Session:
    """Direct DB session for tests that need manual data injection."""
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture
def sp_factory(client):
    """Fixture that yields a SamplePoint factory bound to the test client."""
    return lambda **kw: SamplePointFactory.create(client, **kw)


@pytest.fixture
def sample_factory(client):
    """Fixture that yields a Sample factory bound to the test client."""
    def _create(sample_point_id, **kw):
        return SampleFactory.create(client, sample_point_id, **kw)
    return _create


@pytest.fixture
def equipment_factory(client):
    """Fixture para factory de Equipment."""
    return lambda **kw: EquipmentFactory.create(client, **kw)


@pytest.fixture
def tag_factory(client):
    """Fixture para factory de InstrumentTag."""
    return lambda **kw: InstrumentTagFactory.create(client, **kw)


@pytest.fixture
def installation_factory(client):
    """Fixture para factory de Installation."""
    return lambda eq_id, t_id, **kw: EquipmentTagInstallationFactory.create(client, eq_id, t_id, **kw)


@pytest.fixture
def hierarchy_factory(client):
    """Fixture para factory de HierarchyNode."""
    return lambda **kw: HierarchyNodeFactory.create(client, **kw)


@pytest.fixture
def certificate_factory(client):
    """Fixture para factory de EquipmentCertificate."""
    return lambda eq_id, **kw: EquipmentCertificateFactory.create(client, eq_id, **kw)
