"""
M1 — Auto-Tag Creation on Installation Tests
Cobre: instalação com tag_id=0 e target_tag_name (criação automática de tag),
reutilização de tag existente quando o nome já existe, e instalação em tag existente (tag_id>0).
"""
import pytest


def test_auto_tag_creation_on_install(client, equipment_factory):
    """
    Verifica que instalar com tag_id=0 e target_tag_name cria automaticamente
    uma nova InstrumentTag e vincula o equipamento a ela.
    """
    eq = equipment_factory(serial_number="SN-AUTO-01")

    res = client.post(
        "/api/equipment/install",
        params={"target_tag_name": "AUTO-TAG-CREATED-001", "target_description": "Auto-gen test tag"},
        json={
            "equipment_id": eq["id"],
            "tag_id": 0,
            "installed_by": "AutoTest"
        }
    )
    assert res.status_code == 200
    install_data = res.json()
    assert install_data["is_active"] == 1
    # The tag_id should now be a valid non-zero ID
    assert install_data["tag_id"] > 0

    # Verify the tag was created in the system
    tags_res = client.get("/api/equipment/tags?tag_number=AUTO-TAG-CREATED-001")
    assert tags_res.status_code == 200
    assert len(tags_res.json()) == 1
    assert tags_res.json()[0]["tag_number"] == "AUTO-TAG-CREATED-001"


def test_auto_tag_reuses_existing_tag_name(client, equipment_factory, tag_factory):
    """
    Verifica que instalar com tag_id=0 e um target_tag_name que já existe
    reutiliza a tag existente em vez de criar um duplicado.
    """
    existing_tag = tag_factory(tag_number="EXISTING-TAG-001")
    eq = equipment_factory(serial_number="SN-AUTO-REUSE-01")

    res = client.post(
        "/api/equipment/install",
        params={"target_tag_name": "EXISTING-TAG-001"},
        json={
            "equipment_id": eq["id"],
            "tag_id": 0,
            "installed_by": "AutoTest"
        }
    )
    assert res.status_code == 200
    install_data = res.json()
    # Must link to the existing tag, not a new one
    assert install_data["tag_id"] == existing_tag["id"]

    # Confirm no duplicate tag was created
    tags_res = client.get("/api/equipment/tags?tag_number=EXISTING-TAG-001")
    assert len(tags_res.json()) == 1


def test_auto_tag_install_with_hierarchy_node(client, equipment_factory, hierarchy_factory):
    """
    Verifica que a criação automática de tag com hierarchy_node_id vincula
    corretamente o nó hierárquico à tag criada.
    """
    eq = equipment_factory(serial_number="SN-AUTO-HIER-01")
    node = hierarchy_factory(tag="SYS-AUTO-01", level_type="System")

    res = client.post(
        "/api/equipment/install",
        params={
            "target_tag_name": "AUTO-HIER-TAG-001",
            "hierarchy_node_id": node["id"]
        },
        json={
            "equipment_id": eq["id"],
            "tag_id": 0,
            "installed_by": "AutoTest"
        }
    )
    assert res.status_code == 200
    install_data = res.json()
    tag_id = install_data["tag_id"]

    # Read the tag and verify hierarchy_node_id was set
    tags_res = client.get("/api/equipment/tags?tag_number=AUTO-HIER-TAG-001")
    assert tags_res.status_code == 200
    created_tag = tags_res.json()[0]
    assert created_tag["hierarchy_node_id"] == node["id"]


def test_install_nonexistent_equipment_returns_404(client, tag_factory):
    """Instalar um equipment_id inexistente deve retornar 404."""
    tag = tag_factory(tag_number="TAG-INSTALL-404")
    res = client.post("/api/equipment/install", json={
        "equipment_id": 999999,
        "tag_id": tag["id"],
        "installed_by": "AutoTest"
    })
    assert res.status_code == 404


def test_install_nonexistent_tag_returns_404(client, equipment_factory):
    """Instalar em um tag_id inexistente deve retornar 404."""
    eq = equipment_factory(serial_number="SN-NOTAG-01")
    res = client.post("/api/equipment/install", json={
        "equipment_id": eq["id"],
        "tag_id": 999999,
        "installed_by": "AutoTest"
    })
    assert res.status_code == 404
