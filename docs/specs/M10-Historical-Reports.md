# M10 — Historical Reports

> **Fonte:** PRD §12.11 — Historical Reports
> **Normas:** RTM 01/2013 (retenção de 10 anos), Resolução ANP nº 65/2014
> **Módulos Relacionados:** M1 (equipamentos), M11 (hierarquia), M12 (audit log)

---

## Descrição

Serve como repositório auditável para documentos operacionais não estruturados que não são cobertos por outros módulos (ex: cartas ANP, logs de offloading, arquivos HMI diários).

---

## Requisitos Funcionais (PRD §12.11)

### REQ-M10-01: Repositório Auditável
O sistema DEVE servir como repositório auditável para documentos não estruturados mas operacionalmente relevantes (ex: cartas ANP gerais, logs de offloading, arquivos HMI diários). **[MVP]**

### REQ-M10-02: Linkage Contextual
O sistema DEVE permitir que usuários vinculem opcionalmente arquivos uploadados a nós funcionais existentes (FPSO, Metering System, Tag) e Serial Numbers físicos para recuperação contextual.

### REQ-M10-03: Upload em Lote
O sistema DEVE suportar upload em lote de múltiplos documentos concorrentemente.

### REQ-M10-04: Non-Repudiation
O sistema DEVE automaticamente preservar timestamps de upload e usernames para garantir não repúdio.

---

## Regras MMT Aplicáveis
- **Rule 01:** Isolamento RBAC — documentos só visíveis por FPSO autorizado
- **Rule 05:** Permalinks permanentes para cada documento uploadado

## Subagents Responsáveis
- **Backend Specialist:** API de upload, storage (Supabase Buckets), linkage
- **Frontend Specialist:** UI de upload em lote, preview de documentos
- **Architecture Specialist:** Estratégia de storage para 10 anos de retenção
