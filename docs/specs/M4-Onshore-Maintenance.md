# M4 — Onshore Maintenance

> **Fonte:** PRD §12.5 — Onshore Maintenance
> **Normas:** Integração com IFS (CMMS)
> **Módulos Relacionados:** M1 (equipamentos), M11 (configuração), M2 (calibração)

---

## Descrição

Rastreia atividades de manutenção de equipamentos retornados às instalações onshore, com linkage ao sistema de gestão de manutenção (IFS/CMMS).

---

## Requisitos Funcionais (PRD §12.5)

### REQ-M4-01: Logs de Atividades de Manutenção
O sistema DEVE gerenciar logs de atividades de manutenção para equipamentos retornados ao armazém onshore designado.

### REQ-M4-02: Integração com IFS Work Orders
O sistema DEVE fornecer linkage de integração estruturado com IFS (CMMS) Work Orders para rastreamento de status de reparo.

### REQ-M4-03: Bloqueio de Reinstalação
O sistema DEVE **bloquear explicitamente** a reinstalação de qualquer equipamento em uma tag Custody Transfer (CT) se o equipamento estiver marcado como "under maintenance".

---

## Regras MMT Aplicáveis
- **Rule 01:** Isolamento RBAC por FPSO (manutenção restrita ao FPSO correto)
- **Rule 03:** Sync assíncrono com IFS
- **Rule 04:** Status de manutenção parametrizados via M11

## Subagents Responsáveis
- **Backend Specialist:** API de CRUD de manutenção, integração IFS
- **Metrology Specialist:** Regras de bloqueio de reinstalação
