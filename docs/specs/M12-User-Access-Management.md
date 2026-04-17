# M12 — User & Access Management

> **Fonte:** PRD §12.12 — User & Access Management
> **Normas:** RTM 01/2013 (audit trail), ISO 10012 (rastreabilidade)
> **Módulos Relacionados:** Todos (transversal)

---

## Descrição

Controla autenticação, autorização e administração de usuários. Módulo transversal que define o RBAC para todo o sistema, isolamento por FPSO e audit log imutável.

---

## Requisitos Funcionais (PRD §12.12)

### REQ-M12-01: RBAC Hierárquico
O sistema DEVE suportar Role-Based Access Control (RBAC) com perfis de acesso hierárquicos predefinidos:
- **System Admin** — acesso total
- **Metering Engineer (ME)** — gestão de calibrações e laudos
- **Metering Technician (MT)** — execução operacional offshore

### REQ-M12-02: Isolamento por FPSO
O sistema DEVE aplicar isolamento rigoroso do tipo tenant no nível de FPSO: usuários DEVEM acessar e visualizar **apenas** dados dos navios explicitamente atribuídos a eles.

### REQ-M12-03: Audit Log Imutável
O sistema DEVE registrar toda ação mutante do usuário (Create/Update/Delete) em **todos os módulos** em um Audit Log imutável.

### REQ-M12-04: RBAC nas APIs
O sistema DEVE estender todas as regras de RBAC às APIs REST subjacentes, garantindo que as **mesmas permissões** sejam avaliadas programaticamente (sem bypass via API).

---

## Regras MMT Aplicáveis
- **Rule 01:** REGRA FUNDACIONAL — este módulo é a implementação direta do isolamento Multi-FPSO

## Implementação Técnica
- **Supabase Auth:** Autenticação via JWT (login/password)
- **PostgreSQL RLS:** Row-Level Security policies para isolamento de FPSO
- **Middleware FastAPI:** `get_current_user()` dependency para validação em todas as rotas
- **Next.js Middleware:** Proteção de rotas no App Router

## Subagents Responsáveis
- **Auth Specialist:** Líder — toda a estratégia de autenticação e autorização
- **Backend Specialist:** Dependencies FastAPI, RLS policies
- **Security Specialist:** Auditoria de segurança, pentest de bypass
- **Frontend Specialist:** Protected routes, session management
