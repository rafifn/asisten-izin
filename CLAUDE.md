# Asisten Izin Kuliner

Suggests KBLI 2025 codes and permits for Indonesian food businesses.

## Stack

FastAPI (Python 3.12, uv) in `api/`, Next.js in `web/`, Postgres 17 + pgvector
(Docker, `127.0.0.1:5433`). psycopg 3 with raw SQL; migrations are plain SQL in
`db/migrations/`, applied by `app.db.migrate()`.

## Commands

- `make dev`: start db, apply migrations, run API (8000) and web (3000); `make e2e` runs Playwright against a running fake-mode stack
- `make check`: ruff format --check, ruff check, mypy app, pytest
- `make setup`: start db, migrate, load data (non-destructive); `make db-reset CONFIRM=1`: wipe the local db volume and re-migrate (refuses without CONFIRM=1)
- `make eval`: dry run (case count + cost estimate); `make eval EVAL_ARGS=--yes` calls the real API (costs money). `make eval-gen` regenerates expected permits in `evals/cases.yaml`

## Rules

- KBLI version is `2025` (Peraturan BPS 7/2025). Permits follow PP 28/2025.
  Never use KBLI 2020 or PP 5/2021 as a data source, except the 2020→2025
  conversion table.
- The LLM never produces permits, risk levels, or KBLI codes outside the
  candidate list. Permit text comes only from data rows.
- Every `permit` and every `permit_rule` must have `source_regulation`,
  `source_url` and `last_verified`, or the loader refuses the data.
- Rows are never deleted. Rows that are no longer valid get `valid_to`.
- Model: `claude-opus-5-5`, called only through the official `anthropic` Python
  SDK.
  - Use structured outputs for every call.
  - Set effort explicitly on every call.
  - Turn on server-side refusal fallbacks: beta `server-side-fallback-2026-07-01`
    with `fallbacks="default"`.
  - Pricing for cost logging: $4.00 per 1M input tokens, $20.00 per 1M output
    tokens.
- Embeddings: `BAAI/bge-m3`, dimension 1024, computed when data is loaded.
- At most 2 clarifying questions, in at most 1 round. A request that carries
  `answers` never gets questions back.
- Retrieval returns at most 20 candidates per activity, merged with reciprocal
  rank fusion with k = 60.
- Selection picks 1 primary code and at most 2 alternatives per activity.
- The stale warning shows when any `last_verified` used in the answer is older
  than 183 days.
- Input `description` is 3 to 2000 characters after trimming.
- All error responses use `{"error": {"code": "...", "message": "..."}}`. Codes:
  `invalid_input` (400), `not_found` (404), `llm_unavailable` (503),
  `internal` (500).
- All user-facing copy is in Indonesian. The disclaimer text is exactly:
  `Bukan nasihat hukum. Cek ulang di oss.go.id`.
- Local ports: Postgres `127.0.0.1:5433` (5432 is used by the owner's shoplink
  project), API `8000`, web `3000`.
- Secrets: read `ANTHROPIC_API_KEY` from `.env`, or use an `ant auth login`
  profile. Never commit `.env`.
