# M11 - Configuration Module (Asset Hierarchy & Rules)

### Visão Geral (Overview)
Elimina hard-code (códigos engessados). O módulo M11 é o "Sistema Nervoso Central" que parametriza de forma autônoma a infraestrutura da SBM e da ANP em linguagem que o MMT possa ler de forma algorítmica.

### Requisitos Funcionais Extraídos (PRD & FS)

#### 1. Digital Twin e Componentização Arbórea
- Modela integralmente cada Navio.
- Camadas obrigatórias hierárquicas para ancorar módulos (M1, M2):
  1. `FPSO` (Vessel Head)
  2. `Metering System` / System Description
  3. `Process Variable` associada
  4. `Device tag` final.
- Instrumentos/sistemas ganham explicitamente Tags baseadas em gravidade (Custody Transfer, Allocation, Operational).

#### 2. Property Engine Restritivo (Validation Bounds)
- Admins criam schemas de validação de valores de Data sem encostar na UI ou servidor. 
- Capacidade de rodar comparativos intrínsecos como: `<, >, between X & Y, Mandatórios condicionais`, salvando o back-end de re-deploy em qualquer nova resolução do INMETRO.

#### 3. Matriz SLA Absoluta (Multi-Dimensional)
- Toda e qualquer checagem temporal em workflow cruza o eixo `Classification` x `Analysis Type` x `Location`.
- Agrega no backend bases de cálculo lógicas acoplando "Holiday Calendars" segregados por estado ou matriz operacional (`FPSO`), blindando a veracidade de cálculos baseados em *Business Days* exigidos de multas ativas.
