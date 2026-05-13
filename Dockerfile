FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock* ./

RUN uv sync || true

COPY . .

RUN uv sync

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "discord_mcp_platform.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
