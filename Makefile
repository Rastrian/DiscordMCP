.PHONY: install dev test lint typecheck format up down version release-check

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

version:
	uv run python -c "from discord_mcp_platform._version import __version__; print(__version__)"

# Everything that must pass before tagging a release.
release-check: lint typecheck test

up:
	docker compose up --build

down:
	docker compose down
