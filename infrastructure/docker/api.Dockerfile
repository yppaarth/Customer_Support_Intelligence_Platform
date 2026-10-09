FROM python:3.12-slim

WORKDIR /app
COPY apps/api/pyproject.toml /app/pyproject.toml
COPY apps/api/app /app/app
COPY apps/api/alembic /app/alembic
COPY apps/api/alembic.ini /app/alembic.ini
RUN pip install --no-cache-dir -e ".[dev]"
CMD ["sh", "-c", "alembic -c alembic.ini upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
