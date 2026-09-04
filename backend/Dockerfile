# --- base: dependencias comunes ---
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN useradd --create-home --shell /bin/bash appuser

COPY requirements.txt requirements-dev.txt ./

# --- dev: incluye dependencias de desarrollo (tests, lint, tipos) ---
FROM base AS dev

RUN pip install --no-cache-dir -r requirements-dev.txt

COPY . .
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
