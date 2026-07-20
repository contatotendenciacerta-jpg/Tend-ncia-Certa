FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Railway sets $PORT at runtime; shell form so the variable expands.
# Migrations run on every boot - safe because Alembic upgrades are
# idempotent (no-op if the DB is already at head).
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
