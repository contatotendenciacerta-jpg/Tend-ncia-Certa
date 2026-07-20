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
