# M1 - Equipment Registration & Installation Specification

### Visão Geral (Overview)
O Módulo 1 centraliza os números de série (entidades físicas), Tags (posições lógicas no plant) e todo o ciclo de vida de instalações/remoções a bordo dos FPSOs da SBM.

### Requisitos Funcionais Extraídos (PRD & FS)

#### 1. Entidades Principais e Abstração
- **Tag (Functional Location):** Endereço único de montagem atrelado a um P&ID (ex: T62-FT-1103). Tags são ancoradas perfeitamente; elas *nunca* mudam quando um hardware é trocado.
- **Serial Number (Dispositivo Físico):** O transmissor ou medidor real. Certificados de calibração são anexados a Serial Numbers, não às tags provisórias.

#### 2. Instalação, Remoção e Autenticidade
- Toda ação de instalação vincula temporariamente um *Serial Number* a uma *Tag* garantindo a imutabilidade do `Audit Trail` sobre a data em que aquela peça operou num medidor fiscal.
- O sistema aplica a inteligência do `Property Engine` (M11) para filtrar e provar metadados limitantes (Fluid Type, Compatibility) evitando que engenheiros instalem hardwares incompatíveis. O MMT Rule 01 (RBAC/FPSO) define quem visualiza.

#### 3. Documentação Automática
- Durante a troca física ou instalação, um Check-list compulsório bloqueia as etapas e força o backend a processar um PDF formal do SBM: o **Equipment Change Report** (Apêndice D do DRP).

#### 4. Conflito Calibratório (Intervalos)
- Metrology Frequencies: O Engineer (ME) decide a frequência quando insere o Serial, mas se acoplar numa Tag classificada como `Custody Transfer`, o MMT prioriza compulsoriamente a resolução/intervalo de menor limite configurado para aquela base.
