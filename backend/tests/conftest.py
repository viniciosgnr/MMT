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
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.database import Base, get_db
from app.dependencies import get_current_user

# --- Skill (fastapi-pro): SQLite in-memory for ultra-fast isolated tests ---
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
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
        "role": "HarnessAdmin"
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
            "fase": "Prod",
            "number": f"SP-FACTORY-{cls._counter:04d}",
            "description": f"Auto-generated SP {cls._counter}",
            "fpso_name": "FPSO Harness",
            "system": "Gas",
            "fluid": "Gas",
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


# --- Fixtures ---
@pytest.fixture(scope="module")
def client():
    """Skill (fastapi-pro): TestClient with full DB lifecycle."""
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


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
