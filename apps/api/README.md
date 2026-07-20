# Tendência Certa — API

Backend principal (FastAPI + PostgreSQL). Ver `spec.md` na raiz do repo
para o modelo de dados completo.

## Setup

```bash
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # ajuste DATABASE_URL/REDIS_URL se necessário
```

## Migrations

```bash
alembic upgrade head       # aplica as migrations no banco configurado em .env
alembic revision --autogenerate -m "descrição"  # gera nova migration a partir dos models
```

## Rodando a API

```bash
uvicorn app.main:app --reload
```

## Endpoints

- **Autenticação**: `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me`
- **Admin** (role `admin`): CRUD completo em `/admin/markets`, `/admin/assets`,
  `/admin/subscription-tiers` e `/admin/signals` (este último aceita `targets`
  aninhados para TP1/TP2/TP3 no create/update)
- **Público** (role `subscriber` autenticado): `GET /signals` — aplica o
  gating de `visibility_tier`, `markets_allowed` e `signal_delay_minutes`
  conforme o tier ativo do usuário (ver `app/services/signal_visibility.py`)
- **Billing**:
  - `POST /billing/stripe/checkout-session` e `POST /billing/mercadopago/preference`
    (autenticado) — criam a sessão/preferência de checkout para um
    `SubscriptionTier`, ou agendam um downgrade sem cobrar nada (ver regra
    abaixo)
  - `POST /billing/stripe/webhook` e `POST /billing/mercadopago/webhook`
    (públicos, chamados pelos provedores) — nunca confiam no payload sem
    validar a assinatura (`Stripe-Signature` / `X-Signature` + `X-Request-Id`)
  - `STRIPE_*`/`MERCADOPAGO_*` são opcionais (`None` por padrão) — sem
    elas configuradas, esses 4 endpoints respondem `503` ("pagamento
    ainda não configurado") em vez de quebrar; o resto da API funciona
    normalmente
- **Admin — teste sem pagamento**: `POST /admin/users/{id}/grant-subscription`
  (`tier_id`, `duration_days`) ativa uma assinatura na hora, sem Stripe/MP,
  registrada com `payment_provider = manual`. Só para testar o produto —
  não é uma funcionalidade do produto em si.

### Regra de upgrade/downgrade

Ao chamar `checkout-session`/`preference` para um tier diferente do ativo:
- **Upgrade** (tier mais caro) → segue para o checkout normalmente; o
  webhook de confirmação cancela a assinatura antiga e ativa a nova.
- **Downgrade** (tier mais barato) → não cria checkout nenhum, só agenda
  a troca (`Subscription.pending_tier_id`) para `current_period_end`.
  `apply_due_downgrades()` em `subscription_service.py` efetiva a troca
  quando o período expira — ainda não há um scheduler (Celery/cron) neste
  repo para chamá-la automaticamente, é o próximo passo natural.

O acesso (`Subscription.status = active`) só é liberado quando o webhook
confirma o pagamento — nunca no momento em que o checkout é criado.

### Nota sobre a escolha Stripe vs Mercado Pago

- **Stripe**: usa `mode=subscription` do Checkout — a cobrança recorrente
  é gerenciada pelo próprio Stripe (fatura automaticamente, dispara
  `invoice.payment_failed`/`customer.subscription.deleted`).
- **Mercado Pago**: usa Checkout Pro (`/checkout/preferences`), pensado
  para suportar PIX/boleto/cartão. PIX e boleto não têm captura automática
  recorrente no MP, então aqui cada `Payment` aprovado cobre um período
  (`billing_interval` do tier) e a renovação exige um novo checkout —
  ainda não há lembrete automático de renovação (fica para depois, junto
  com o scheduler).

Pagar.me (mencionado no spec.md) não foi implementado nesta etapa — só
Stripe e Mercado Pago foram pedidos aqui.

## Testes

```bash
pip install -r requirements-dev.txt
createdb tendencia_certa_test  # banco Postgres separado, usado só pelos testes
pytest
```

Os testes usam Postgres de verdade (não SQLite) porque os models usam tipos
específicos do dialeto (UUID, ARRAY, Enum nativo). Configure a variável
`DATABASE_URL` (env var, não `.env`) se o banco de teste tiver credenciais
diferentes do padrão em `tests/conftest.py`.

## Deploy

Dockerfile + `railway.json` prontos para deploy na Railway. Passo a passo
completo (incluindo o seed de dados de teste em produção) em
[`DEPLOY.md`](../../DEPLOY.md) na raiz do repo.
