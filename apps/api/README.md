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
