# M5 — Synchronize Data

> **Fonte:** PRD §12.6 — Synchronize Data
> **Normas:** Resolução ANP nº 65/2014 (Data Exchange)
> **Módulos Relacionados:** M4 (IFS), M7 (Export), M11 (configuração)

---

## Descrição

Gerencia a troca de dados com sistemas externos por meio de APIs REST estruturadas. Abrange a exposição de dados aprovados para consumo externo e a importação incremental de dados do CMMS (IFS).

---

## Requisitos Funcionais (PRD §12.6)

### REQ-M5-01: APIs REST Documentadas
O sistema DEVE expor APIs REST seguras e documentadas para sistemas externos consultarem parâmetros de calibração aprovados e laudos laboratoriais avaliados. **[MVP]**

### REQ-M5-02: Sync Incremental com IFS
O sistema DEVE buscar inventário de peças sobressalentes e status de equipamentos do CMMS (IFS) de forma incremental ou via sync agendado em background. **[MVP]**

### REQ-M5-03: Monitoramento de Saúde de Sync
O sistema DEVE monitorar continuamente a saúde das sincronizações e marcar permanentemente payloads API com falha em um dashboard administrativo para revisão.

---

## Regras MMT Aplicáveis
- **Rule 03:** Integrações e exports devem ser assíncronos (background tasks)
- **Rule 01:** APIs devem respeitar isolamento RBAC por FPSO

## Subagents Responsáveis
- **Backend Specialist:** Endpoints REST, background sync, health monitoring
- **CICD Specialist:** Scheduling de jobs, retry policies
- **Architecture Specialist:** Design de contratos de API
