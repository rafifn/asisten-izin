.PHONY: dev check db-reset

dev:
	docker compose up -d --wait db
	cd api && uv run python -m app.db
	cd api && uv run uvicorn app.main:app --reload --port 8000

check:
	cd api && uv run ruff format --check .
	cd api && uv run ruff check .
	cd api && uv run mypy app
	cd api && uv run pytest

db-reset:
	docker compose down -v
	docker compose up -d --wait db
	cd api && uv run python -m app.db
