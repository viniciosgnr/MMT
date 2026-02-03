# Guia de Deploy e Compartilhamento - MMT

Este guia descreve como preparar a aplicação para produção usando Docker e como disponibilizar um link externo temporário para avaliação de usuários.

## 1. Pré-requisitos
*   Docker e Docker Compose instalados.
*   Arquivo `.env` configurado na raiz (backend e frontend usarão as variáveis via docker-compose).

## 2. Preparar para Docker (Correção Aplicada)
O arquivo `frontend/next.config.mjs` deve ter a configuração `output: 'standalone'` para que o Dockerfile funcione corretamente. **Isso já foi aplicado.**

## 3. Rodar a Aplicação com Docker Compose
Para subir todo o ambiente (Frontend + Backend):

```bash
# Na raiz do projeto
docker-compose up --build -d
```
Isso iniciará:
*   Frontend em: `http://localhost:3000`
*   Backend em: `http://localhost:8000`

## 4. Compartilhar Link para Avaliação (Túnel)
Para que outros usuários acessem sua máquina local sem precisar de deploy em servidor, a maneira mais rápida é usar um **Túnel Seguro**. Recomendamos o **Cloudflare Tunnel** (gratuito e estável) ou **ngrok**.

### Opção A: Usando Cloudflare Tunnel (Recomendado)
Sem precisar instalar nada, se tiver `npm` ou `npx`:

1.  Certifique-se que o docker está rodando (`docker-compose up -d`).
2.  Rode o comando abaixo para expor o **Frontend**:
    ```bash
    npx trycloudflared --url http://localhost:3000
    ```
3.  O terminal exibirá um link temporário (ex: `https://sloth-pizza-run.trycloudflare.com`). **Envie este link para os usuários.**

**Atenção:** Como o Frontend tenta falar com o Backend, o Backend TAMBÉM precisa estar acessível.
No entanto, na configuração atual do Docker, o Frontend (Next.js) faz chamadas ao Backend.
*   Se as chamadas são **Server-Side** (dentro do `getServerSideProps` ou Server Actions), elas ocorrem dentro da rede Docker (`http://backend:8000`), então **funciona**.
*   Se as chamadas são **Client-Side** (Browser do usuário -> Backend), o navegador do usuário tentará acessar `localhost:8000`, o que **falhará**.

**Solução para Avaliação Rápida:**
A configuração atual usa `NEXT_PUBLIC_API_URL` apontando para localhost. Para avaliação externa completa sem deploy real, você precisaria expor AMBOS (Frontend e Backend) ou usar o Next.js como Proxy (que já está configurado em `next.config.mjs` via rewrites!).

**Graças aos Rewrites no Next.js:**
Se o seu `next.config.mjs` tem:
```js
rewrites() {
    return [{ source: '/api/:path*', destination: 'http://localhost:8000/api/:path*' }]
}
```
E seu frontend chama `/api/endpoints`, então **basta expor o Frontend (porta 3000)**! O Next.js repassará as requisições para o backend internamente na sua máquina.

**Resumo:**
1. Mude `NEXT_PUBLIC_API_URL` no seu `.env` local (ou do frontend) para ser vazio ou apenas `/api`.
   * Se estiver `http://localhost:8000/api`, o navegador do usuário externo tentará acessar o localhost DELE.
   * Se mudar para apenas `/api`, o navegador chamará o domínio do túnel, e o Next.js fará o proxy para o backend local.

---

## 5. Deploy Real e Gratuito (Cloud)

Para uma solução profissional onde o código roda na nuvem e não na sua máquina, usaremos a stack **Vercel (Frontend)** + **Render (Backend)** + **Supabase (Banco)**.

### Passo 1: GitHub
1.  Garanta que seu projeto está em um repositório no GitHub (Público ou Privado).

### Passo 2: Backend (Render.com + Docker)
Para evitar erros de dependência, usaremos o **Docker** (já configurado no repositório).

1.  Crie uma conta em [render.com](https://render.com).
2.  Clique em **New +** -> **Web Service**.
3.  Conecte seu repositório do GitHub.
4.  O Render deve detectar o arquivo `render.yaml` automaticamente.
    *   Se não detectar, escolha **Runtime: Docker**.
5.  **Environment Variables** (Copie do seu `.env`):
    *   `DATABASE_URL`: (Sua string de conexão COMPLETA do Supabase, incluindo a senha)
    *   `SUPABASE_URL`: (https://tpgeroygxpmbhmrewbpd.supabase.co)
    *   `SUPABASE_KEY`: (Sua Anon Key)
6.  Clique em **Create Web Service**.
7.  Aguarde o deploy (pode levar uns 5-10min na primeira vez pois baixará a imagem Docker).
8.  Copie a URL gerada (ex: `https://mmt-backend.onrender.com`).

### Passo 3: Frontend (Vercel)
A "casa" do Next.js.
1.  Crie uma conta em [vercel.com](https://vercel.com).
2.  Clique em **Add New...** -> **Project**.
3.  Importe seu repositório do GitHub.
4.  Configure:
    *   **Framework Preset:** Next.js (Automático)
    *   **Root Directory:** Clique em Edit e selecione `frontend`.
5.  **Environment Variables**:
    *   `NEXT_PUBLIC_SUPABASE_URL`: (Sua URL do Supabase)
    *   `NEXT_PUBLIC_SUPABASE_ANON_KEY`: (Sua Key do Supabase)
    *   **`NEXT_PUBLIC_API_URL`**: **Essa é crítica!** Cole aqui a URL do seu backend no Render (ex: `https://mmt-backend.onrender.com/api`).
        *   *Nota: No Render a API raiz é `/`, mas nosso client espera `/api`? Verifique se seu Router prefixa `/api` ou se você precisa adicionar `/api` na variável. No seu código atual (`api.ts`), ele espera que a variável JÁ contenha `/api` se não for localhost.*
6.  Clique em **Deploy**.

### Passo 4: Conectar
1.  No Frontend (Vercel), acesse a URL gerada (ex: `https://mmt-frontend.vercel.app`).
2.  Tente fazer login. O frontend chamará o backend no Render.
    *   *Atenção:* O Free Tier do Render entra em modo "Sleep" após 15mins inativo. A primeira requisição pode demorar ~50 segundos. Tenha paciência no primeiro acesso.

---

## 6. Deploy Docker (VPS)
(Seção anterior mantida para referência)
Para um ambiente permanente em VPS própria:
1.  Contrate uma VPS (DigitalOcean, AWS, etc.).
...

