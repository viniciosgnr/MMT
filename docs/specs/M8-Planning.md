# M8 — Planning

> **Fonte:** PRD §12.9 — Planning
> **Normas:** RTM 01/2013 (frequências de calibração), Resolução 52/2013 (amostragem)
> **Módulos Relacionados:** M2 (calibrações), M3 (amostragens), M6 (alertas), M11 (SLA matrix)

---

## Descrição

Fornece uma visão unificada de todas as atividades pendentes (calibrações, inspeções, amostragens) através da frota inteira, com sistema de cores traffic-light baseado nos thresholds do SLA.

---

## Requisitos Funcionais (PRD §12.9)

### REQ-M8-01: Calendário e Lista Agregados
O sistema DEVE fornecer views agregadas de calendário e lista de todas as calibrações planejadas, inspeções e atividades de amostragem em toda a frota. **[MVP]**

### REQ-M8-02: Traffic-Light Color Coding
O sistema DEVE usar sistema de cores traffic-light determinado pelas configurações de threshold SLA do M11:
- 🟢 **On-track** (dentro do prazo)
- 🟡 **Impending** (próximo do vencimento)
- 🔴 **Overdue** (vencido)

### REQ-M8-03: Mitigações para Atividades Overdue
O sistema DEVE permitir que usuários registrem mitigações para atividades overdue, anexando justificativas e estabelecendo nova data-alvo projetada **sem perder o registro original da violação de SLA**.

### REQ-M8-04: Filtros Multidimensionais
O sistema DEVE permitir filtragem de atividades por:
- FPSO
- Período temporal
- Tipo de atividade (calibração, execução, amostragem, emissão de laudo)

---

## Regras MMT Aplicáveis
- **Rule 04:** SLA thresholds dinâmicos via M11
- **Rule 05:** Consistência visual (traffic-light, filtros, permalinks)
- **Rule 07:** Alarming compliance (overdue = NFSM trigger)

## Subagents Responsáveis
- **Backend Specialist:** Query engine de planning, filtros multidimensionais
- **Frontend Specialist:** Calendário visual, traffic-light UI
- **Architecture Specialist:** Modelo de dados da view de planning
