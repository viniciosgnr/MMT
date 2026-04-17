# M9 — Failure Notification (NFSM)

> **Fonte:** PRD §12.10 — Failure Notification — NFSM
> **Normas:** Resolução ANP nº 18/2014, Ofício Circular ANP/NFP nº 02/2021
> **Módulos Relacionados:** M2 (calibração), M3 (amostragem), M6 (alertas), M7 (export XML)

---

## Descrição

Gerencia o ciclo completo de Notificações de Falha de Medição (NFSM) conforme Resolução ANP nº 18/2014. A NFSM é o documento regulatório mais crítico — envio atrasado resulta em multa de $30.000+ por evento.

---

## Requisitos Funcionais (PRD §12.10)

### REQ-M9-01: Ciclo de Vida Completo
O sistema DEVE gerenciar o ciclo completo da NFSM:
**Abertura → Edição → Aprovação → Fechamento**

### REQ-M9-02: Notificação Inicial vs Final
O sistema DEVE diferenciar entre:
- **Notificação Inicial**: DEVE ser submetida em ≤ 240 horas após detecção
- **Notificação Final**: Contém dados consolidados de resolução

### REQ-M9-03: Aprovação Mandatória do ME
O sistema DEVE exigir aprovação explícita do Metering Engineer (ME) para o fechamento de qualquer NFSM.

### REQ-M9-04: Formato XML ANP-Compliant
O sistema DEVE estruturar dados de NFSM capturados em formato **completamente conforme** com o schema XML da ANP, facilitando exportação imediata para o portal.

### REQ-M9-05: Email Automático por FPSO
O sistema DEVE suportar listas de distribuição de email configuráveis por FPSO para despachar automaticamente relatórios PDF de NFSMs aprovadas para stakeholders.

---

## Regras MMT Aplicáveis
- **Rule 07:** NFSM Compliance (core rule — este módulo é a implementação direta)
- **Rule 01:** Isolamento RBAC por FPSO nas listas de distribuição
- **Rule 03:** Envio de email assíncrono (background task)

## Subagents Responsáveis
- **Backend Specialist:** CRUD de NFSM, geração XML, email dispatch
- **Metrology Specialist:** Schema XML ANP, regras de timing (240h)
- **Security Specialist:** Validação de aprovação ME, audit trail
- **QA/TDD Specialist:** Edge cases de timing (240h boundary)
