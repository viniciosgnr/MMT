# M6 — Monitoring & Alerts

> **Fonte:** PRD §12.7 — Monitoring & Alerts
> **Normas:** RTM 01/2013 (limites de calibração), Resolução 18/2014 (NFSM triggers)
> **Módulos Relacionados:** M2 (calibração), M3 (amostragem), M8 (planning), M11 (SLA matrix)

---

## Descrição

Fornece alertas proativos para conformidade com SLA, desvios de parâmetros de produção e violações de janelas regulatórias. É o "sistema nervoso" do MMT.

---

## Requisitos Funcionais (PRD §12.7)

### REQ-M6-01: Monitoramento de FC vs MMT
O sistema DEVE monitorar continuamente as configurações do Flow Computer contra os últimos Certificados e Laudos Laboratoriais aprovados no MMT, gerando alarme explícito se o FC operar fora de compliance. **[MVP]**

### REQ-M6-02: Alertas Escalonados de Expiração
O sistema DEVE gerar alertas automáticos para expirações próximas e vencidas de Certificados de Calibração e Amostragem Periódica, escalonando avisos funcionalmente:
- **30 dias antes**
- **15 dias antes**
- **Dia do vencimento**
- **Overdue**

### REQ-M6-03: Detecção de Anomalias em Parâmetros
O sistema DEVE identificar anomalias em parâmetros diários de produção (ex: volumes diários inalterados ou temperaturas estáticas) usando regras de desvio padrão.

### REQ-M6-04: Alertas de Breach de SLA
O sistema DEVE disparar alertas de nível sistêmico de violação de SLA em qualquer etapa dos workflows M3 (Amostragem) ou M2 (Calibração) imediatamente ao ultrapassar a data esperada de conclusão.

---

## Regras MMT Aplicáveis
- **Rule 07:** Alarming and NFSM Compliance (sensores de conformidade)
- **Rule 04:** SLA thresholds parametrizados via M11
- **Rule 05:** Traffic-light visual no dashboard

## Subagents Responsáveis
- **Backend Specialist:** Engine de alertas, cron jobs de verificação
- **Frontend Specialist:** Dashboard de alertas, traffic-light icons
- **Metrology Specialist:** Regras de compliance ANP para triggers
- **QA/TDD Specialist:** Testes de edge cases de SLA (weekends, holidays)
