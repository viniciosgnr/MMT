"""
M1 — Tag-Level Installation History Tests
Cobre: GET /api/equipment/tags/{tag_id}/history para auditoria de quais
equipamentos estiveram instalados em uma tag ao longo do tempo.
"""
import pytest


def test_tag_history_single_install(client, equipment_factory, tag_factory, installation_factory):
    """Verifica que o histórico de uma tag mostra a instalação ativa."""
    eq = equipment_factory(serial_number="SN-TH-01")
    tag = tag_factory(tag_number="TAG-HIST-01")
    installation_factory(eq_id=eq["id"], t_id=tag["id"])

    res = client.get(f"/api/equipment/tags/{tag['id']}/history")
    assert res.status_code == 200
    history = res.json()
    assert len(history) == 1
    assert history[0]["equipment_id"] == eq["id"]
    assert history[0]["is_active"] == 1


def test_tag_history_after_equipment_swap(client, equipment_factory, tag_factory, installation_factory):
    """
    Cenário: Equip. A instalado, removido, depois Equip. B instalado.
    O histórico da tag deve mostrar ambas as instalações, a mais recente primeiro.
    """
    eq_a = equipment_factory(serial_number="SN-TH-A")
    eq_b = equipment_factory(serial_number="SN-TH-B")
    tag = tag_factory(tag_number="TAG-SWAP-HIST")

    # Install A
    inst_a = installation_factory(eq_id=eq_a["id"], t_id=tag["id"])

    # Remove A
    client.post(f"/api/equipment/remove/{inst_a['id']}")

    # Install B
    installation_factory(eq_id=eq_b["id"], t_id=tag["id"])

    res = client.get(f"/api/equipment/tags/{tag['id']}/history")
    assert res.status_code == 200
    history = res.json()
    assert len(history) == 2

    # Most recent (B) should be first and active
    assert history[0]["equipment_id"] == eq_b["id"]
    assert history[0]["is_active"] == 1

    # Older (A) should be second and inactive
    assert history[1]["equipment_id"] == eq_a["id"]
    assert history[1]["is_active"] == 0
    assert history[1]["removal_date"] is not None


def test_tag_history_multiple_equipments_chronological_order(
    client, equipment_factory, tag_factory, installation_factory
):
    """
    Verifica a ordenação cronológica (mais recente primeiro) no histórico de tags.
    """
    tag = tag_factory(tag_number="TAG-CHRONO-01")
    eq_1 = equipment_factory(serial_number="EQ-CHR-1")
    eq_2 = equipment_factory(serial_number="EQ-CHR-2")
    eq_3 = equipment_factory(serial_number="EQ-CHR-3")

    inst_1 = installation_factory(eq_id=eq_1["id"], t_id=tag["id"])
    client.post(f"/api/equipment/remove/{inst_1['id']}")

    inst_2 = installation_factory(eq_id=eq_2["id"], t_id=tag["id"])
    client.post(f"/api/equipment/remove/{inst_2['id']}")

    installation_factory(eq_id=eq_3["id"], t_id=tag["id"])

    res = client.get(f"/api/equipment/tags/{tag['id']}/history")
    history = res.json()
    assert len(history) == 3

    # Latest installed (eq_3) should be first
    assert history[0]["equipment_id"] == eq_3["id"]
    assert history[0]["is_active"] == 1


def test_tag_history_empty_for_fresh_tag(client, tag_factory):
    """Uma tag recém-criada sem instalações deve ter histórico vazio."""
    tag = tag_factory(tag_number="TAG-EMPTY-HIST")
    res = client.get(f"/api/equipment/tags/{tag['id']}/history")
    assert res.status_code == 200
    assert res.json() == []


def test_delete_tag_blocked_by_active_installation(client, equipment_factory, tag_factory, installation_factory):
    """Deletar tag com instalação ativa deve retornar 400."""
    eq = equipment_factory(serial_number="SN-DEL-BLOCK")
    tag = tag_factory(tag_number="TAG-DEL-BLOCK")
    installation_factory(eq_id=eq["id"], t_id=tag["id"])

    res = client.delete(f"/api/equipment/tags/{tag['id']}")
    assert res.status_code == 400
    assert "active equipment installation" in res.json()["detail"]


def test_delete_tag_allowed_after_removal(client, equipment_factory, tag_factory, installation_factory):
    """Deletar tag após remover o equipamento deve funcionar."""
    eq = equipment_factory(serial_number="SN-DEL-OK")
    tag = tag_factory(tag_number="TAG-DEL-OK")
    inst = installation_factory(eq_id=eq["id"], t_id=tag["id"])

    # Remove first
    client.post(f"/api/equipment/remove/{inst['id']}")

    # Now delete should succeed
    res = client.delete(f"/api/equipment/tags/{tag['id']}")
    assert res.status_code == 200
    assert res.json()["status"] == "success"
