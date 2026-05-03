# MMT (Metering Management Tool) - Agent Constitution

Bem-vindo ao projeto MMT. Este documento (`AGENT.md`) é a constituição principal do projeto e serve como o mapa definitivo para a IA Antigravity ou novos desenvolvedores.

## 1. Visão Geral do Sistema
O MMT é a plataforma central para gerenciar sistemas de medição fiscal e operacional em FPSOs da SBM Offshore, garantindo conformidade com normas regulatórias da ANP (ex: RTM 01/2013, Resolução 18/2014) e processos de auditoria (ISO 10012:2003).

> **📄 Documentos Primários:**
> - **PRD (Source of Truth):** `MMT Specifications/Product Requirements Document Template.pdf` — 12 módulos, 37+ requisitos, 6 referências regulatórias
> - **Specs Extraídas:** `docs/specs/M*.md` — Cada módulo do PRD em Markdown atômico
> - **Progresso Contínuo:** `PROGRESS.md` — Linha do tempo imutável das decisões do projeto

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

---

## 5. Motor de Análise Química — Regras de Negócio (M3)

Esta seção documenta as **4 regras de negócio inegociáveis** do motor de análise química. Todo agente ou desenvolvedor que tocar no módulo M3 ou M11 DEVE estar alinhado a elas.

### Regra 1 — A Matriz de SLA (M11) é a única fonte da verdade de prazos

Nenhum prazo de análise química é hardcoded. Todos são lidos dinamicamente da tabela `sla_rules` no banco de dados, gerenciável pelo administrador via Módulo 11 sem deploy.

- **Chave de lookup:** `(classification, analysis_type, local, status_variation)` — ex: `(Fiscal, Chromatography, Onshore, Approved)`
- **22 combinações cadastradas** cobrindo: Fiscal/Apropriação/Operacional × Cromatografia/PVT/Enxofre/Viscosidade × Onshore/Offshore × Approved/Reproved/Any
- **Campos-chave:** `interval_days`, `disembark_days`, `lab_days`, `report_days`, `fc_days`, `fc_is_business_days`, `reproval_reschedule_days`, `needs_validation`
- **Cascading Lookup:** Busca exata (com `status_variation`) → fallback para `Any` → fallback hardcoded
- **Approved vs Reproved:** Regras `Approved` incluem FC Update (`fc_days`). Regras `Reproved` omitem FC Update e incluem `reproval_reschedule_days`.
- **Offshore vs Onshore:** Fluxos offshore **não possuem** etapas de desembarque (`disembark_days = null`, `lab_days = null`) pois a análise é realizada a bordo do FPSO.

### Regra 2 — Gatilho de agendamento: saída do status "Sample" (etapa 2)

O sistema agenda a próxima coleta **automaticamente** sempre que um sample sai do status `Sample` (etapa 2) — independentemente para qual status ele vai em seguida.

- **Fluxo Onshore:** `Sample → Disembark preparation` → gatilha agendamento
- **Fluxo Offshore:** `Sample → Report issue` (pula desembarque) → gatilha agendamento da mesma forma
- **Data da próxima coleta:** `sampling_date (event_date) + interval_days` da regra SLA correspondente
- **Guard anti-duplicação:** A query verifica `sample_id LIKE '%-PER-{id}-%'` antes de criar. Transições subsequentes (ex: `Disembark logistics → Warehouse`) não criam novas amostras.
- **Implementação:** `backend/app/routers/chemical.py` — bloco `AUTO-SCHEDULE` antes dos `if/elif` de status

```python
# Trigger pattern — qualquer saída do status Sample
if sample.status == SampleStatus.SAMPLE.value and update.status != SampleStatus.SAMPLE:
    schedule_next_periodic_sample(sample, sla_config)
```

### Regra 3 — Reprovação: nova coleta no menor prazo entre 3 dias úteis e o próximo agendado

Quando um relatório é reprovado (`validation_status = "Reprovado"`), o sistema cria imediatamente uma amostra de emergência (prefixo `EMG`) com a data calculada como:

```
data_emergencia = report_issue_date + reproval_reschedule_days (dias úteis)
data_proxima_periodica = sampling_date + interval_days
data_final = min(data_emergencia, data_proxima_periodica)
```

- **`reproval_reschedule_days`** é configurável por regra SLA no M11 (padrão: 3 dias úteis)
- **Triggers:** `Report approve/reprove` com `validation_status = Reprovado` e `Flow computer update` com `validation_status = Reprovado`
- **O prazo periódico serve de teto:** Se o próximo agendado já estiver mais próximo que os 3 dias úteis, usa-se a data do periódico

### Regra 4 — Samples auto-agendados iniciam na etapa "Sample" (etapa 2)

Todo sample criado automaticamente pelo sistema (PER ou EMG) **começa no status `Sample`**, nunca em `Plan`. O sistema registra no histórico que a etapa `Plan` foi concluída automaticamente.

- **Motivo:** O agendamento automático **é** a conclusão do planejamento (Plan). O operador não precisa completar manualmente o Plan — ele já entra direto na fase de coleta.
- **Histórico gerado automaticamente:**
  ```
  Plan  → "Auto-scheduled periodic analysis — Plan completed by scheduler."
  Sample → "Awaiting next sample collection."
  ```
- **Aplica-se a:** PER (criado por `create_sample`), PER (criado por `update-status`), EMG (criado por reproval)
- **Invariante testada:** Nenhum sample com prefixo `PER-` ou `EMG-` deve estar no status `Plan` após a criação

### Arquivos-chave do Motor M3

| Arquivo | Responsabilidade |
|---|---|
| `backend/app/routers/chemical.py` | Endpoints: `create_sample`, `update_sample_status`, `schedule_next_periodic_sample`, `schedule_emergency_re_sampling` |
| `backend/app/services/sla_matrix.py` | `get_sla_config(db, classification, type, local, status_variation)` — lookup com cascading fallback |
| `backend/app/routers/configuration.py` | CRUD de `SLARule` via M11: `GET/POST/PUT/DELETE /config/sla-rules` |
| `backend/app/models.py` | Modelo `SLARule` com `status_variation`, `reproval_reschedule_days` |
| `backend/seed_slas.py` | Script de seed das 22 combinações oficiais |
| `backend/tests/test_m11_sla_matrix.py` | Suite TDD com 20 testes cobrindo as 4 regras de negócio |
| `backend/tests/test_m3_validate_report_pipeline.py` | Pipeline end-to-end: upload PDF → validação → agendamento |
| `frontend/.../sla-matrix.tsx` | Interface M11: tabela editável das 22 combinações com modal PUT/DELETE |
