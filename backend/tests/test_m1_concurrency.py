import pytest
from unittest.mock import patch, MagicMock
from app.routers.equipment import install_equipment
from app.schemas.schemas import EquipmentTagInstallationCreate
from fastapi import HTTPException

def test_m1_install_concurrency_lock_called(db_session, equipment_factory, tag_factory):
    """
    Verifica que a rota de instalação utiliza with_for_update() para garantir atomicidade.
    """
    eq = equipment_factory()
    tag = tag_factory()
    
    install_data = EquipmentTagInstallationCreate(
        equipment_id=eq["id"],
        tag_id=tag["id"],
        installed_by="Concurrency Test"
    )
    
    # Mock do db.query para verificar o uso de with_for_update
    mock_query = MagicMock()
    # Quando o query for chamado com models.InstrumentTag
    with patch.object(db_session, "query", return_value=mock_query):
        # Configuramos o mock para retornar ele mesmo em filtros e locks
        mock_query.filter.return_value = mock_query
        mock_query.with_for_update.return_value = mock_query
        mock_query.first.return_value = MagicMock(id=tag["id"])
        
        # Chamada direta (simulando a rota)
        from app.routers.equipment import install_equipment
        try:
            install_equipment(install_data, db=db_session, current_user={})
        except Exception:
            pass # Ignoramos erros posteriores de commit/relacionamento
            
        # Verifica se with_for_update foi chamado
        assert mock_query.with_for_update.called, "Installation must use with_for_update() to lock the tag."

def test_m1_prevent_duplicate_active_installation(client, equipment_factory, tag_factory):
    """
    Verifica que o sistema bloqueia tentativas de instalar em uma tag já ocupada.
    """
    eq1 = equipment_factory(serial_number="EQ-RES-001")
    eq2 = equipment_factory(serial_number="EQ-RES-002")
    tag = tag_factory(tag_number="TAG-LOCK-001")
    
    # 1. Instala o primeiro equipamento
    res1 = client.post("/api/equipment/install", json={
        "equipment_id": eq1["id"],
        "tag_id": tag["id"],
        "installed_by": "User A"
    })
    assert res1.status_code == 200
    
    # 2. Tenta instalar o segundo na mesma TAG (deve falhar)
    res2 = client.post("/api/equipment/install", json={
        "equipment_id": eq2["id"],
        "tag_id": tag["id"],
        "installed_by": "User B"
    })
    assert res2.status_code == 400
    assert "Tag is already occupied" in res2.json()["detail"]
