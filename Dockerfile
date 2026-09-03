# syntax=docker/dockerfile:1

# ---- Builder: resolve dependencies and install the project into /app/.venv ----
FROM python:3.12-slim AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN pip install --no-cache-dir uv

# Dependency layer only: cached as long as pyproject.toml/uv.lock are unchanged.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Install the project itself as a regular (non-editable) wheel.
# The dynamic version comes from src/discord_mcp_platform/_version.py.
COPY src/ ./src/
RUN uv sync --frozen --no-dev --no-editable

# ---- Runtime: slim image with the prebuilt venv, no build tooling ----
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home appuser

COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "discord_mcp_platform.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
