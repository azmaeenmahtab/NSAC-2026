.PHONY: setup dev-api dev-web lint lint-py lint-web test test-py test-web pipeline

setup:
	uv sync --all-packages --all-extras
	cd apps/web && pnpm install

dev-api:
	uv run uvicorn app.main:app --app-dir services/api --reload --port 8000

dev-web:
	cd apps/web && pnpm dev

lint: lint-py lint-web

lint-py:
	uv run ruff check .
	uv run mypy pipeline services/api

lint-web:
	cd apps/web && pnpm typecheck && pnpm lint

test: test-py test-web

test-py:
	uv run pytest

test-web:
	cd apps/web && pnpm test

pipeline:
	uv run python -m pyroscope_pipeline all
