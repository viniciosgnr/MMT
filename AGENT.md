# MMT (Metering Management Tool) - Agent Constitution

Bem-vindo ao projeto MMT. Este documento (`AGENT.md`) é a constituição principal do projeto e serve como o mapa definitivo para a IA Antigravity ou novos desenvolvedores.

## 1. Visão Geral do Sistema
O MMT é a plataforma central para gerenciar sistemas de medição fiscal e operacional em FPSOs da SBM Offshore, garantindo conformidade com normas regulatórias da ANP (ex: RTM 01/2013, Resolução 18/2014) e processos de auditoria (ISO 10012:2003).

A arquitetura moderna foi concebida sob três pilares:
- **Frontend:** Next.js 15 (App Router), Tailwind CSS v4, componentes Radix UI via Shadcn. Focado em Server Components e alta responsividade.
- **Backend:** API REST robusta construída em Python (FastAPI, Uvicorn, SQLAlchemy V2, Pydantic V2). Faz uso extensivo de processamento assíncrono e extração de dados via `PyMuPDF`.
- **Database / Auth:** Gerenciado primariamente via Supabase (PostgreSQL) com RLS, usando a Service Role estritamente no backend.

> **ALERTA CRÍTICO: REGRAS DO PROJETO**
> NUNCA inicie uma implementação complexa sem consultar as leis na pasta `.agent/rules/`. Elas definem os limites do que pode e não pode ser feito (ex: Isolamento Multi-FPSO, RBAC, e Imutabilidade de Dados).

---

## 2. Módulos Críticos de Foco
O ecossistema é formado por 12 grandes módulos (definidos na *Functional Specification*). Contudo, nosso ciclo imediato de testes e expansão técnica recai profundamente sobre os três módulos abaixo:

### Módulo 11 (M11) - Configuration Module (A Base Lógica)
- **Responsabilidade:** Ser a única fonte da verdade paramétrica. NENHUMA regra métrica, como `se fluido_fiscal e limite > 45 dias`, deve ser "hard-coded" no sistema.
- **Property Engine & Hierarchy:** Permite aos admins configurarem a árvore hierárquica (FPSO -> Metering System -> Run -> Instruments) e anexarem meta-dados dinâmicos aos equipamentos (ex: ranges obrigatórios, classificações).
- **SLA Matrix:** Define cruzamentos condicionais baseados em classificações de sistema, criando as janelas de prazo para workflows e ditando feriados. O motor de cálculo de atraso extrai dados exatos daqui.

### Módulo 1 (M1) - Equipment Registration & Installation
- **Responsabilidade:** Rastrear a jornada física e imutável dos equipamentos a bordo dos navios.
- **Abstração Fundamental:** Uma **TAG** (ex: T62-FT-1103) é um "endereço lógico/vazio" em um desenho de engenharia (P&ID). Um **Serial Number** (SN) é o bloco de metal instrumentado real.
- **Mecânica Central:** A funcionalidade de *Installation* encaixa um Serial Number vivo em uma TAG viva, e OBRIGATORIAMENTE valida se os pre-requisitos configurados no M11 são satisfeitos (validação semântica). O *Uninstallation* guarda histórico.

### Módulo 3 (M3) - Chemical Analysis
- **Responsabilidade:** Orquestração completa de amostragens (Óleo Diário, PVT, Cromatografia de Gás), logística laboratorial e processamento de resultados.
- **OCR e Parse de Relatórios:** Utiliza inteligência no backend (provavelmente `PyMuPDF` ou ferramentas OCR da stack de IA) para varrer PDFs imensos de laboratório e extrair partições molares (Methane, H2S, O2, Density, BSW).
- **Critical Analysis (CA):** É a barreira matemática. Compara os valores recém extraídos contra históricos (desvios de 2-Sigma) e ranges legais (PAM).
- **Emergency Sample Trigger:** O workflow avalia a CA; se um laudo laboratorial falhar, ele cria imediatamente um bloqueio e dispara um fluxo de emergência paralelo limitando a resolução a 3 dias úteis.

---

## 3. Comandos Básicos (Local Dev)
- **Backend Docker:**
```bash
docker-compose up backend
```
*(Expõe o FastAPI na porta 8000, consumindo `SUPABASE_URL` via env).*

- **Frontend Node:**
```bash
cd frontend && npm run dev
```
*(Expõe o App Router na porta 3000).*

## 4. Padrão Arquitetural Agêntico: Harness Engineering
Este projeto adota OBRIGATORIAMENTE a arquitetura de **Harness Engineering** como padrão fundamental. A infraestrutura do MMT engloba o "Motor de IA" (Model) blindando-o nos seguintes eixos:

- **Guides (Feedforward Constriction):**
  - O documento `AGENT.md` (Visão Macro) e `SYSTEM_ARCHITECTURE.md`.
  - As Tarefas / Specs (Arquivos gerados dinamicamente nos processos de artefatos temporários).
  - Nossas Convenções Estritas hospedadas dentro de `.agent/rules/` (As The MMT Rules).
  - Delimitação estrita de Personas carregadas em `.agent/subagents/`.

- **Sensors (Feedback & Validation):**
  - **Linters & Type Checkers:** A validade estrutural imposta pelo `eslint` no Frontend e Pydantic no Backend. Tolerância zero para tipagem ambígua.
  - **Testes / E2E:** O fluxo inegociável de TDD (Red-Green-Refactor) onde os testes de matemática para M3 e M2 são elaborados *antes* da codificação lógica. Uso de QA / E2E para blindar regressões do frontend.
  - **Review Agents:** Ciclos autônomos de revisão orquestrados pelos subagentes na fase de checagem.

- **Memória & Bootstrap:**
  - Disciplina inalienável no Github Versioning (Git Discipline) controlada via regras de Commit convencionais.
  - Orquestração técnica ágil mapeada através da automatização contínua com `docker-compose` e `.agent/workflows/`.
