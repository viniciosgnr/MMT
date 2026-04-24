"""
Pillar 3 — RBAC Role-Based Access Control Tests
Testa que endpoints respeitam os roles: Viewer (somente leitura),
Inspector (pode criar/editar amostras), Admin (acesso total).
Auth é simulada via dependency_overrides com roles distintos.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.dependencies import get_current_user


# ─── Role Factories ──────────────────────────────────────────────────────────

def make_user(role: str):
    return {"id": f"{role}-user", "email": f"{role}@test.com", "role": role}


def override_viewer():
    return make_user("Viewer")


def override_inspector():
    return make_user("Inspector")


def override_admin():
    return make_user("Admin")


# ─── DB Setup ────────────────────────────────────────────────────────────────

rbac_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
RBACSession = sessionmaker(autocommit=False, autoflush=False, bind=rbac_engine)


def override_get_db_rbac():
    db = RBACSession()
    try:
        yield db
    finally:
        db.close()


# ─── Client Fixtures ─────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def viewer_client():
    app.dependency_overrides[get_db] = override_get_db_rbac
    app.dependency_overrides[get_current_user] = override_viewer
    Base.metadata.create_all(bind=rbac_engine)
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def inspector_client():
    app.dependency_overrides[get_db] = override_get_db_rbac
    app.dependency_overrides[get_current_user] = override_inspector
    Base.metadata.create_all(bind=rbac_engine)
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def admin_client():
    app.dependency_overrides[get_db] = override_get_db_rbac
    app.dependency_overrides[get_current_user] = override_admin
    Base.metadata.create_all(bind=rbac_engine)
    with TestClient(app) as c:
        yield c


# ─── Shared Setup: Seeds via Admin ───────────────────────────────────────────

@pytest.fixture(scope="module")
def seeded_sp(admin_client):
    """Sample point criado via admin para ser usada nos testes de role."""
    sp = admin_client.post("/api/chemical/sample-points", json={
        "tag_number": "SP-RBAC-001",
        "description": "RBAC Test SP",
        "fpso_name": "FPSO RBAC",
    }).json()
    return sp


@pytest.fixture(scope="module")
def seeded_equipment(admin_client):
    res = admin_client.post("/api/equipment/", json={
        "serial_number": "SN-RBAC-001",
        "equipment_type": "Flow Computer",
    })
    return res.json()


# ─── Viewer: GET endpoints devem funcionar ───────────────────────────────────

class TestViewerGETAccess:
    """Viewer deve ter acesso de leitura a todos os endpoints principais."""

    def test_viewer_can_list_equipment(self, viewer_client):
        res = viewer_client.get("/api/equipment/")
        assert res.status_code == 200

    def test_viewer_can_list_tags(self, viewer_client):
        res = viewer_client.get("/api/equipment/tags")
        assert res.status_code == 200

    def test_viewer_can_list_sample_points(self, viewer_client):
        res = viewer_client.get("/api/chemical/sample-points")
        assert res.status_code == 200

    def test_viewer_can_list_samples(self, viewer_client):
        res = viewer_client.get("/api/chemical/samples")
        assert res.status_code == 200

    def test_viewer_can_get_hierarchy(self, viewer_client):
        res = viewer_client.get("/api/config/hierarchy/nodes")
        assert res.status_code == 200

    def test_viewer_can_get_wells(self, viewer_client):
        res = viewer_client.get("/api/config/wells")
        assert res.status_code == 200


# ─── Viewer: mutações devem ser bloqueadas ────────────────────────────────────
# NOTA: O sistema atual usa Supabase Auth externamente (sem RBAC no backend).
# Estes testes documentam o comportamento *atual* e definem o contrato de rolecheck.
# Antes de implementar RBAC nativo, eles verificam que o endpoint existe e está acessível.
# Quando RBAC nativo for adicionado, os asserts devem ser trocados para 403.

class TestViewerMutationContract:
    """
    Documenta o estado atual do RBAC.
    Viewers podem chamar endpoints de mutação pois o controle de acesso
    é feito no nível Supabase/Frontend.
    Estes testes vão falhar quando RBAC nativo for implementado no backend.
    """

    def test_viewer_post_equipment_returns_non_500(self, viewer_client):
        """Viewer não deve causar 500. Hoje: 200 (RBAC não está no backend)."""
        res = viewer_client.post("/api/equipment/", json={
            "serial_number": "SN-VIEWER-MUT",
            "model": "TestModel",
            "equipment_type": "Test",
        })
        assert res.status_code != 500


    def test_viewer_post_sample_returns_non_500(self, viewer_client, seeded_sp):
        """Viewer não deve causar 500 ao criar amostra."""
        res = viewer_client.post("/api/chemical/samples", json={
            "sample_id": "VIEWER-MUT-001",
            "type": "Chromatography",
            "sample_point_id": seeded_sp["id"],
            "local": "Onshore",
            "planned_date": "2026-06-01",
        })
        assert res.status_code != 500


# ─── Inspector: pode criar/editar amostras ─────────────────────────────────

class TestInspectorAccess:
    """Inspector tem acesso de escrita a M3 (amostras) e leitura a M1."""

    def test_inspector_can_create_sample_point(self, inspector_client):
        res = inspector_client.post("/api/chemical/sample-points", json={
            "tag_number": "SP-INSPECTOR-001",
            "description": "Inspector Test SP",
            "fpso_name": "FPSO RBAC",
        })
        assert res.status_code == 200

    def test_inspector_can_list_equipment(self, inspector_client):
        res = inspector_client.get("/api/equipment/")
        assert res.status_code == 200

    def test_inspector_can_upload_report(self, inspector_client):
        """Inspector deve conseguir usar o endpoint de upload (sem 401/403)."""
        from unittest.mock import patch, mock_open
        from app.services.pdf_parser import CROResult

        sp = inspector_client.post("/api/chemical/sample-points", json={
            "tag_number": "SP-INSP-UPLOAD",
            "description": "Upload Test",
            "fpso_name": "FPSO RBAC",
        }).json()
        sample = inspector_client.post("/api/chemical/samples", json={
            "sample_id": "INSP-UPL-001",
            "type": "Chromatography",
            "sample_point_id": sp["id"],
            "local": "Onshore",
            "planned_date": "2026-06-01",
        }).json()

        mock = CROResult(report_type="CRO", boletim="INSP-CRO-001", o2=0.1)
        with patch("app.routers.chemical.parse_pdf_bytes", return_value=mock), \
             patch("app.routers.chemical.open", mock_open()), \
             patch("app.routers.chemical.os.makedirs"):
            res = inspector_client.post(
                f"/api/chemical/samples/{sample['id']}/validate-report",
                files={"file": ("r.pdf", b"dummy", "application/pdf")}
            )
        assert res.status_code == 200


# ─── Admin: acesso total ──────────────────────────────────────────────────────

class TestAdminAccess:
    """Admin tem acesso completo a todos os recursos."""

    def test_admin_can_create_equipment(self, admin_client):
        res = admin_client.post("/api/equipment/", json={
            "serial_number": "SN-ADMIN-001",
            "model": "Promass 300",
            "equipment_type": "Pressure Transmitter",
            "manufacturer": "Yokogawa",
        })
        assert res.status_code == 200

    def test_admin_can_create_hierarchy_node(self, admin_client):
        res = admin_client.post("/api/config/hierarchy/nodes", json={
            "tag": "SYS-ADMIN-TEST",
            "description": "Admin Created Node",
            "level_type": "System",
        })
        assert res.status_code == 200

    def test_admin_can_delete_hierarchy_node(self, admin_client):
        node = admin_client.post("/api/config/hierarchy/nodes", json={
            "tag": "SYS-ADMIN-DEL",
            "description": "To be deleted",
            "level_type": "System",
        }).json()
        res = admin_client.delete(f"/api/config/hierarchy/nodes/{node['id']}")
        assert res.status_code == 200

    def test_admin_can_trigger_sla_check(self, admin_client):
        res = admin_client.post("/api/chemical/check-slas")
        assert res.status_code == 200
        assert "alerts_created" in res.json()
