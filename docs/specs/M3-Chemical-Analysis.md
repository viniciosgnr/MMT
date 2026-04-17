# M3 - Chemical Analysis Specification

### Visão Geral (Overview)
Comanda a esteira vitalícia de auditorias físico-químicas de gás, óleo e água amostradas on-shore ou off-shore até terminarem averbadas em um Flow Computer, respondendo ativamente às multas reguladas pelo RTM 01/2013 do ANP.

### Requisitos Funcionais Extraídos (PRD & FS)

#### 1. Tipos de Sampling Operacionais e Fiscais
- **Daily / Op Fiscal:** Monitoramento severo do limite normatizado de `BSW` de escoamento. Acima de 1% deve cruzar com M9 (Failure Notification).
- **Relacionados a Ofloading:** Operações eventuais custodiadas por navios aliviadores.
- **Periódicas:** Estudos completos CRO (Cromatografia PVT de Gás) guiados por periodicidade dinâmica que disparam recálculos nas UCs do sistema após upload.

#### 2. Workflow Dimensional Complexo
- O M3 varre um State-Machine massivo de 11 pontes atômicas: `Plan -> Sample -> Disembark logistics -> Warehouse -> Lab -> Report Issued -> Validation -> FC Update`.
- Responde com resiliência: Corta passos logísticos `(Logistics to vendor / Delivered at vendor)` automaticamente se a flag "Onshore" e "Offboard" for local.

#### 3. Parse Sensível Documental Integrado (OCR)
- Backend processa PDF e Excel nativo dos Laboratórios 3rd party para drag-and-drop. Emite as partições sensíveis (Methane, O2, Density).

#### 4. Critical Analysis Barrier e Falhas (2-Sigma)
- Valores extraídos nunca assumem a verdade suprema. Param pela **CA (Critical Analysis)** na barreira do Servidor, calculando o limite 2-Sigma sob o histórico da Tag amparado pelos requerimentos do INMETRO.
- **Emergency Reproval:** Caso reprovada na C.A., dispara de prontidão uma `Emergency Sample Requirement` compulsória amarrada em no máximo 3 dias úteis subsequentes. 

#### 5. SLAs Enforcement & All Periodic Analyses Matrix
A base motriz de `Due Dates` estabelece os tetos temporais (SLA) para amostragem Periódica ditando o comportamento arquitetural do M3:

- **Intervalos de Coleta Base (T0):**
  - Fiscal: 30 dias
  - Apropriation: 90 dias
  - Operational: 180 dias
  - Enxofre/Viscosidade (Sulfur/Viscosity): 365 dias

- **Prazos Logísticos Cravados (Onshore):**
  - Disembark: Até 10 dias após a coleta.
  - Laboratory: Até 20 dias após a coleta.
  - Report Issued: Até 25 dias após a coleta (45 dias para Operational).
  - *Nota Arquitetural:* Para amostras *Offshore*, a plataforma suprime sumariamente as janelas de transporte (Disembark/Lab = `NA`).

- **Geração de FC Updates (Time-to-Live):**
  - Fiscal/Apropriation: Limite de 3 dias úteis após a emissão do laudo aprovado.
  - Operational: Limite de 10 dias úteis após a emissão.
  - PVT, Enxofre e Viscosidade: Não geram Flow Computer Update (`NA`).

- **Emergency Sample Trigger (Regra de Reprovação):**
  - Se a C.A. cruzar limites (Reprovação), a etapa FC Update morre.
  - A Engine DEVE recalcular o *Planned Date* da próxima amostragem para: `min(Próxima Coleta Regular, +3 Dias Úteis após emissão da reprovação)`.
