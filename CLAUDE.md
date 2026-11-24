# Asisten Izin Kuliner

Suggests KBLI 2025 codes and permits for Indonesian food businesses.

## Stack

FastAPI (Python 3.12, uv) in `api/`, Next.js in `web/`, Postgres 17 + pgvector
(Docker, `127.0.0.1:5433`). psycopg 3 with raw SQL; migrations are plain SQL in
`db/migrations/`, applied by `app.db.migrate()`.

## Commands

- `make dev`: start db, apply migrations, run API (8000) and web (3000); `make e2e` runs Playwright against a running fake-mode stack
- `make check`: ruff format --check, ruff check, mypy app, pytest
- `make setup`: start db, migrate, load data (non-destructive); `make db-reset CONFIRM=1`: wipe the local db volume (`docker compose --profile full down -v`), start db, migrate and load data with the configured `EMBEDDER` (refuses without CONFIRM=1)
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
- LLM provider is chosen by `LLM_PROVIDER` (default `deepseek`; or `claude`). Both
  implement `parse(system, user, schema, effort) -> LlmResult` and every reply is a
  validated Pydantic model. Set effort explicitly on every call.
  - DeepSeek (`app/llm/deepseek.py`): model `deepseek-flash` (override
    `DEEPSEEK_MODEL`), official OpenAI-compatible API at `https://api.deepseek.com`
    via the `openai` SDK, JSON mode (`response_format={"type": "json_object"}`) with
    the JSON Schema in the system prompt, Pydantic validation, one retry on a
    blank/truncated/invalid reply, then `refused=True`. Effort maps to
    `reasoning_effort` (low→none, medium→low, high→high). Cost logging at peak
    rates: $0.30 per 1M input, $1.20 per 1M output.
  - Claude (`app/llm/client.py`): `claude-opus-5-5` through the official
    `anthropic` SDK only, structured outputs, server-side refusal fallbacks
    (beta `server-side-fallback-2026-07-01`, `fallbacks="default"`). Cost logging:
    $4.00 per 1M input, $20.00 per 1M output.
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
- Secrets: read `DEEPSEEK_API_KEY` (DeepSeek) or `ANTHROPIC_API_KEY` / an
  `ant auth login` profile (Claude) from `.env`. Never commit `.env`.
