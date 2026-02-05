# Arquitetura do Sistema MMT

Este documento detalha como os componentes do Metering Management Tool (MMT) se comunicam, como a segurança é gerenciada e como o deploy é orquestrado.

## 1. Visão Geral (Big Picture)

O MMT é uma aplicação web moderna composta por três pilares principais:

```mermaid
graph TD
    User[Usuário / Navegador] -->|Acessa URL| CDN[Vercel CDN]
    User -->|API Calls (HTTPS)| Backend[Backend Python (Render/Docker)]
    User -->|Auth & Realtime| Supabase[Supabase (Auth/DB/Storage)]
    
    CDN -->|Entrega Estático| User
    Backend -->|Query SQL| Supabase
    Backend -->|Valida Token| Supabase
```

*   **Frontend (Next.js):** Responsável pela interface visual, interações e lógica de apresentação.
*   **Backend (FastAPI):** Responsável pela lógica de negócios complexa, cálculos de engenharia, validação de regras e orquestração de dados.
*   **Banco de Dados (Supabase):** Responsável pelo armazenamento (PostgreSQL), autenticação de usuários e armazenamento de arquivos (Buckets).

---

## 2. Fluxo de Comunicação & Dados

### A. O Ciclo de uma Requisição (Request Flow)

Quando um usuário clica em "Salvar Calibração", o seguinte acontece:

1.  **Frontend (Cliente):**
    *   O navegador prepara um JSON com os dados.
    *   O utilitário `apiFetch` (em `frontend/lib/api.ts`) captura o **Token de Sessão** (JWT) do usuário logado no Supabase.
    *   A requisição é enviada para `https://mmt-backend.onrender.com/api/calibration...`.

2.  **Backend (Servidor):**
    *   O FastAPI recebe a requisição.
    *   **Middleware de Segurança:** Antes de executar qualquer código, ele valida se o Token JWT é válido e se o usuário tem permissão.
    *   **Pydantic:** Valida se os dados do JSON estão no formato correto (tipagem forte).
    *   **Controller:** Executa a regra de negócio (ex: cálculo de incerteza).
    *   **ORM (SQLAlchemy):** Converte a operação para SQL e envia ao banco.

3.  **Database (Supabase):**
    *   Executa o SQL e retorna os dados.

### B. Integração Frontend <-> Supabase
O Frontend fala **diretamente** com o Supabase apenas para:
*   **Login/Logout:** O cliente Supabase (`utils/supabase/client.ts`) gerencia a sessão no navegador.
*   **Realtime:** Para ouvir mudanças no banco em tempo real (ex: Dashboard de Amostras), o frontend abre um WebSocket direto com o Supabase.

---

## 3. Variáveis de Ambiente e Segurança

O sistema usa dois conjuntos de chaves. É crucial entender a diferença:

### Chaves Públicas (`NEXT_PUBLIC_...`)
Visíveis para qualquer pessoa que inspecionar o código no navegador.
*   `NEXT_PUBLIC_SUPABASE_URL`: O endereço do seu projeto Supabase.
*   `NEXT_PUBLIC_SUPABASE_ANON_KEY`: Uma chave "segura" que permite apenas ações públicas (login) ou ações protegidas pelas regras de segurança do banco (RLS).
*   **Uso:** O Frontend usa para desenhar a tela de login e iniciar a sessão.

### Chaves Privadas (Backend)
Nunca saem do servidor. Armazenamento seguro de segredos.
*   `DATABASE_URL`: Contém a SENHA mestre do banco de dados (`postgresql://postgres:...`). Permite acesso total e irrestrito.
*   `SUPABASE_KEY` (Service Role): Permite ignorar regras de segurança.
*   **Uso:** O Backend (Render) usa para ler/gravar qualquer dado, tabelas de auditoria e configurações sensíveis.

> **Regra de Ouro:** NUNCA coloque a `DATABASE_URL` no Frontend (`.env.local`). Se fizer isso, qualquer usuário pode roubar seu banco de dados.

---

## 4. Estratégia de Deploy (Deployment)

A aplicação cresceu e adotou uma estratégia **Container-Native** para robustez:

### Frontend (Vercel) | "Serverless Native"
A Vercel é a "casa" do Next.js.
*   **Build:** A Vercel pega seu código, compila e otimiza assets (imagens, fontes) automaticamente.
*   **Execução:** Roda em uma infraestrutura global (Edge Network), garantindo altíssima velocidade de carregamento.
*   **Por que não Docker aqui?** Usar Docker no frontend perderia as otimizações nativas da Vercel (Image Optimization, ISR, Edge Caching).

### Backend (Render) | "Docker Container"
O Render hospeda o "cérebro" da aplicação.
*   **Build:** O Render lê o `Dockerfile` do backend, cria uma imagem Linux isolada, instala as dependências exatas definidas e inicia o servidor.
*   **Por que Docker aqui?** Python é sensível a versões de bibliotecas. O Docker garante que o código rode no Render *exatamente* como roda na sua máquina, eliminando o clássico problema "funciona na minha máquina".

### Banco de Dados (Supabase) | "Managed Database"
O Supabase oferece um PostgreSQL gerenciado.
*   Você não precisa instalar Docker/Postgres. Ele já está na nuvem, com backups e segurança configurados.
