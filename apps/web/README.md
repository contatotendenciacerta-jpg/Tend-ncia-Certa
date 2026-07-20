# Tendência Certa — Web

Frontend em Next.js (App Router) para assinantes: landing page pública,
login/cadastro, dashboard de sinais e conta. Consome a API (`apps/api`) via
um client HTTP centralizado; nenhum checkout de pagamento ainda.

## Setup

```bash
cd apps/web
npm install
cp .env.example .env.local  # ajuste API_BASE_URL se a API não estiver em localhost:8000
npm run dev
```

Requer a API rodando (ver `apps/api/README.md`) e com CORS liberado para a
origem do Next (`CORS_ORIGINS` no `.env` da API).

## Variáveis de ambiente

| Variável | Uso |
|---|---|
| `API_BASE_URL` | URL base da API FastAPI. Só é lida no servidor (Route Handlers e Server Components) — nunca exposta ao navegador. |

## Arquitetura

- **Autenticação (BFF pattern)**: os formulários de login/cadastro chamam
  rotas do próprio Next (`/api/auth/login`, `/api/auth/register`,
  `/api/auth/logout`), que por sua vez chamam a API e gravam
  `access_token`/`refresh_token` em cookies **httpOnly** no domínio do
  Next — o token nunca fica acessível a JavaScript no navegador. Páginas
  protegidas (`/dashboard`, `/account`) leem o cookie no servidor
  (`src/lib/require-auth.ts`) e redirecionam para `/login` se ausente ou
  se a API responder 401.
- **Client HTTP** (`src/lib/api.ts`): único ponto que fala com a API. Lança
  `ApiError` (resposta HTTP de erro) ou `ApiNetworkError` (falha de rede),
  tratados nas páginas para mostrar estados amigáveis em vez de tela
  branca.
- **i18n** (`next-intl`): textos vêm de `packages/i18n/locales/pt-BR/*.json`
  (fora de `apps/web`, por isso o `turbopack.root` em `next.config.ts`
  aponta pra raiz do monorepo). Só `pt-BR` está ativo — adicionar `en`/`es`
  depois é só criar os arquivos e listar o locale, sem tocar em
  componentes (eles só usam `useTranslations`/`getTranslations`).
- **Estilo**: CSS Modules + tokens em `globals.css` (sem Tailwind/UI kit).
  Tema escuro fixo, pensado para um produto de sinais de trading.

## Estrutura

```
src/
  app/            # rotas (App Router): landing, login, register, dashboard, account
    api/auth/     # Route Handlers que fazem a ponte com a API e gravam cookies
  components/
    ui/           # Button, Badge, Card
    layout/       # headers público/autenticado, footer, logout
    landing/      # Hero, cards de tier, CTA final
    auth/         # formulários de login/cadastro
    dashboard/    # card de sinal, estado vazio
    feedback/     # estado de erro genérico (rede, etc.)
  lib/            # client HTTP, cookies de auth, tipos compartilhados, formatação
  i18n/           # config do next-intl + loader das mensagens
```

## Deploy

Zero-config na Vercel (Root Directory = `apps/web`). Passo a passo
completo, incluindo a sequência com o backend na Railway e o fechamento
do CORS, em [`DEPLOY.md`](../../DEPLOY.md) na raiz do repo.

## O que falta (fora do escopo desta etapa)

- Checkout de pagamento (Stripe/Mercado Pago) — as telas linkam para a
  seção de planos, mas não iniciam cobrança.
- Painel admin (CRUD de sinais/tiers) — só o consumo do assinante.
- Refresh automático de token (hoje: 401 → redireciona pro login).
