import pytest

def test_m11_cascading_integrity(client, hierarchy_factory):
    """
    Verifica que mudanças no topo da hierarquia não quebram a integridade dos filhos.
    Cenário: FPSO Alpha -> System X -> Device 1.
    Ação: Renomear FPSO Alpha para FPSO Beta.
    Verificação: Device 1 ainda aponta para System X, que aponta para FPSO Beta.
    """
    # 1. Cria a estrutura
    fpso = hierarchy_factory(tag="FPSO Alpha", description="Original Platform", level_type="FPSO")
    sys_x = hierarchy_factory(tag="System X", description="Metering System", level_type="System", parent_id=fpso["id"])
    dev_1 = hierarchy_factory(tag="Device 1", description="Flow Computer", level_type="Device", parent_id=sys_x["id"])
    
    # 2. Renomeia o FPSO
    update_res = client.put(
        f"/api/config/hierarchy/nodes/{fpso['id']}",
        json={"tag": "FPSO Beta", "description": "Updated Platform", "level_type": "FPSO"}
    )
    assert update_res.status_code == 200
    
    # 3. Verifica a integridade via tree API
    tree_res = client.get("/api/config/hierarchy/tree")
    assert tree_res.status_code == 200
    # Nota: A tree API 'hierarchy/tree' retorna uma estrutura fixa baseada no Metering Point + Sample CDI.xlsx
    # Para verificar os nós manuais, devemos usar hierarchy/nodes ou uma tree que inclua parent_id links
    
    # Vamos verificar via hierarchy/nodes individualmente
    nodes_res = client.get("/api/config/hierarchy/nodes")
    nodes = nodes_res.json()
    
    # Encontra o novo FPSO
    fpso_beta = next(n for n in nodes if n["id"] == fpso["id"])
    assert fpso_beta["tag"] == "FPSO Beta"
    
    # Verifica System X
    system_x = next(n for n in nodes if n["id"] == sys_x["id"])
    assert system_x["parent_id"] == fpso["id"] # Link mantido por ID
    
    # Verifica Device 1
    device_1 = next(n for n in nodes if n["id"] == dev_1["id"])
    assert device_1["parent_id"] == sys_x["id"] # Link mantido por ID

def test_m11_delete_with_children_fails(client, hierarchy_factory):
    """Verifica que não é permitido deletar um nó que possui filhos."""
    parent = hierarchy_factory(tag="Parent", level_type="System")
    child = hierarchy_factory(tag="Child", level_type="Device", parent_id=parent["id"])
    
    res = client.delete(f"/api/config/hierarchy/nodes/{parent['id']}")
    assert res.status_code == 400
    assert "Cannot delete node with children" in res.json()["detail"]

def test_m11_cascading_tree_structure(client, hierarchy_factory):
    """
    Verifica se a estrutura de árvore reflete as mudanças.
    Nota: A tree API nativa é fixa no CDI.xlsx. Vamos testar a integridade
    das relações parent/child básicas que suportam a árvore futura.
    """
    # Criamos um nó órfão e depois movemos ele para um pai
    orphan = hierarchy_factory(tag="Orphan", level_type="Device")
    parent = hierarchy_factory(tag="New Parent", level_type="System")
    
    res = client.put(
        f"/api/config/hierarchy/nodes/{orphan['id']}",
        json={
            "tag": "Adopted", 
            "description": "Adopted Node", 
            "level_type": "Device", 
            "parent_id": parent["id"]
        }
    )
    assert res.status_code == 200
    assert res.json()["parent_id"] == parent["id"]
    
    # Verifica se o link persiste
    nodes = client.get("/api/config/hierarchy/nodes").json()
    adopted = next(n for n in nodes if n["id"] == orphan["id"])
    assert adopted["parent_id"] == parent["id"]
