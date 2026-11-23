.PHONY: dev dev-api dev-web check e2e db-reset data-load data-sample

PNPM = corepack pnpm@10.28.2

# `make dev` runs API (:8000) and web (:3000) together; Ctrl-C stops both.
dev:
	docker compose up -d --wait db
	cd api && uv run python -m app.db
	trap 'kill 0' INT TERM EXIT; \
	  (cd api && uv run uvicorn app.main:app --reload --port 8000) & \
	  $(PNPM) --dir web dev & \
	  wait

dev-api:
	docker compose up -d --wait db
	cd api && uv run python -m app.db
	cd api && uv run uvicorn app.main:app --reload --port 8000

dev-web:
	$(PNPM) --dir web dev

check:
	cd api && uv run ruff format --check .
	cd api && uv run ruff check .
	cd api && uv run mypy app
	cd api && uv run pytest
	$(PNPM) --dir web lint
	$(PNPM) --dir web typecheck
	$(PNPM) --dir web exec vitest run

# Playwright smoke test against an ALREADY RUNNING fake-mode stack:
#   EMBEDDER=fake make data-load
#   LLM_MODE=fake EMBEDDER=fake make dev      (in another terminal)
#   make e2e
# Also writes docs/screenshots/result-mobile.png.
e2e:
	$(PNPM) --dir web exec playwright test

db-reset:
	docker compose down -v
	docker compose up -d --wait db
	cd api && uv run python -m app.db

data-load:
	cd api && uv run python -m app.data.loader ../data

data-sample:
	cd api && uv run python -m app.data.sample ../data ../docs/spot-checks
