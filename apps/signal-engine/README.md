# Tendência Certa — Signal Engine

Serviço Python separado do backend principal, dedicado a rodar os
algoritmos geradores de sinal (ver seção 3.1 do `spec.md` na raiz do
repo). Publica sinais gerados via fila Redis e/ou chamada à API interna
do `apps/api` — não compartilha processo com o backend principal.

## Setup

```bash
cd apps/signal-engine
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Ainda sem lógica de algoritmos — apenas a fundação do projeto
(configuração de `REDIS_URL` e `API_BASE_URL`).
