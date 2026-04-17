# M2 — Metrological Confirmation

> **Fonte:** PRD §12.3 — Metrological Confirmation
> **Normas:** ISO 10012:2003, Resolução ANP nº 18/2014, RTM 01/2013
> **Módulos Relacionados:** M1 (equipamentos), M11 (SLA matrix, propriedades), M6 (alertas), M9 (NFSM)

---

## Descrição

Gerencia o ciclo completo de calibração metrológica conforme ISO 10012:2003 e regulamentações ANP. Abrange desde o planejamento até a atualização do Flow Computer, incluindo controle de lacres, emissão de certificados, análise crítica automatizada e cálculo de incerteza.

---

## Requisitos Funcionais (PRD §12.3)

### REQ-M2-01: Workflow de Calibração Auditável
O sistema DEVE rastrear calibrações através de um workflow rígido e auditável:
**Planning → Execution → Seal Control → Certificate Issuance → Critical Analysis (CA) → Uncertainty Calculation (UC) → Flow Computer (FC) Update → Closure.**

### REQ-M2-02: Override Temporário de FC
O sistema DEVE calcular valores temporários de override para o Flow Computer conforme regulações ANP quando um medidor é removido de uma linha para calibração ex-situ.

### REQ-M2-03: Rastreamento de Lacres
O sistema DEVE gerenciar rastreamento de lacres físicos (instalação, remoção, status atual por tag), permitindo geração de relatórios de lacres direcionados para auditorias regulatórias.

### REQ-M2-04: Extração Automatizada de Certificados
O sistema DEVE suportar extração automatizada de parâmetros de certificados de calibração importados (formatos XML/PDF) emitidos por laboratórios terceiros (ex: Inmetro/RBC).

### REQ-M2-05: Análise Crítica Automatizada (CA)
O sistema DEVE executar Critical Analysis automatizada usando verificações de desvio histórico 2-sigma e regras de limite rígido para marcar certificados como **Approved** ou **Reproved**.

### REQ-M2-06: Cálculo de Incerteza (UC)
O sistema DEVE executar Cálculos de Incerteza (UC) sob demanda e agendados, utilizando os últimos parâmetros aprovados.

### REQ-M2-07: Watermark "FOR REFERENCE ONLY"
O sistema DEVE marcar visualmente ou aplicar watermark em qualquer documentação gerada como **"FOR REFERENCE ONLY"** até que a etapa final de FC Update seja formalmente fechada e aprovada.

---

## Regras MMT Aplicáveis
- **Rule 02:** Imutabilidade Matemática para UCs e CAs
- **Rule 04:** Parâmetros dinâmicos via M11 (frequências de calibração)
- **Rule 07:** NFSM compliance para falhas de medição

## Subagents Responsáveis
- **Backend Specialist:** Endpoints de workflow, cálculos UC, parsing de certificados
- **Metrology Specialist:** Regras de CA, formatos ANP, validação de certificados
- **QA/TDD Specialist:** Testes de 2-sigma, edge cases de UC, cobertura de workflow
- **Frontend Specialist:** Stepper visual de compliance, upload de certificados
