.PHONY: install dev test lint typecheck format up down

install:
	uv sync

dev:
	uv run uvicorn discord_mcp_platform.app.main:app --reload

test:
	PYTHONPATH=src uv run pytest -v

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy src

up:
	docker compose up --build

down:
	docker compose down
