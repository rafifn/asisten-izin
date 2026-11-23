# Runbook

Operational notes for Asisten Izin Kuliner. Commands assume the repo root. In containers, prefix
with `docker compose --profile full run --rm api` and use `/app/data` for the data directory.

## Loading new data

Data lives in `data/*.yaml` (`kbli_scope`, `kbli_2020_map`, `permits`, `rules`). Loading is
**additive**: each load validates every file and then inserts a new `data_release`, atomically.
If any row is invalid (for example a missing `source_regulation`, `source_url` or
`last_verified`) the loader prints `data error: <file>: row <n>: <problem>` and changes nothing.

```bash
make data-load                                                 # native
docker compose --profile full run --rm api python -m app.data.loader /app/data   # containers
```

The API always answers from the highest release id, so a new release is live as soon as the
load finishes (no restart). The embedder in use is recorded in the release notes
(`embedder=bge` or `embedder=fake`). Real deployments must load with `EMBEDDER=bge`.

Changing data files inside a running container image needs a rebuild (`data/` is copied into the
`api` image), or mount the directory over `/app/data`.

## Updating a rule when a regulation changes

1. Edit the YAML: change the row in `data/rules.yaml` or `data/permits.yaml`. Keep the sources
   current: update `source_regulation`, `source_url` and `last_verified`. To retire a row, set
   `valid_to` rather than deleting it. Note the reasoning in `data/SOURCES.md`.
2. `make data-load` creates a new release.
3. `make eval` (dry run) and then `make eval EVAL_ARGS=--yes` to compare against the bars. If the
   expected permits in `evals/cases.yaml` change legitimately, run `make eval-gen` and review the
   diff (`make eval-gen EVAL_GEN_ARGS=--review` writes `evals/REVIEW.md`).
4. Get the change reviewed and merged, then redeploy and load the data.

Each answer is logged with its `data_release_id`, so answers produced before a correction can be
found with the query below.

## Reading `query_log`

Every analyze request writes one row. Columns: `created_at`, `input` (PII redacted by regex),
`attributes`, `clarifications`, `output` (JSON), `data_release_id`, `model`, `tokens_in`,
`tokens_out`, `cost_usd`, `latency_ms`, `helpful`, `comment`, `request_uuid`.

```bash
docker compose exec db psql -U asisten -d asisten_izin
```

```sql
-- latest requests
select created_at, left(input, 60) as input, helpful, cost_usd, latency_ms
from query_log order by id desc limit 20;

-- spend and latency per day
select created_at::date as day, count(*) as n, sum(cost_usd) as usd,
       percentile_cont(0.5) within group (order by latency_ms) as p50_ms
from query_log group by 1 order by 1 desc;

-- unhelpful answers with comments
select created_at, input, comment from query_log where helpful = false order by id desc;

-- answers affected by a corrected release (e.g. release 3 fixed a rule)
select id, created_at, input from query_log where data_release_id < 3 order by id;

-- which releases exist
select id, created_at, notes from data_release order by id;
```

With the containerised stack, the database is the same `db` service (port 5433 on the host).
Raw input text is proposed to be kept 90 days on staging; there is no automatic purge yet.

## When Claude is down

The API converts Claude failures into `503` with `{"error": {"code": "llm_unavailable", ...}}`
and the UI shows a "busy, try again" message. The anthropic client has server-side refusal
fallbacks enabled. Nothing is served from a cache and the model never writes permits, so there is
no degraded mode that gives answers. What to do:

1. Check `curl http://localhost:8000/healthz` (API up) and the Anthropic status page.
2. Check the API logs for the error: `docker compose --profile full logs api --tail 100`.
   An authentication error means `ANTHROPIC_API_KEY` is missing or revoked; fix `.env` and
   restart the API container.
3. If it is an outage, wait; users can retry.
4. Do **not** switch a real deployment to `LLM_MODE=fake`: it returns canned answers that look
   real. Use fake mode only for demos and tests.

## Owner spot-check

Before Phase 1 counts as done, the owner checks a random sample of data rows against their
sources.

```bash
make data-sample                 # writes docs/spot-checks/<today>.md
SEED=20261123 make data-sample   # reproducible sample for a given seed
```

The sheet lists 10 random rows from `permits.yaml` and `rules.yaml` (at least 3 permits). For each
row, open `source_url`, check the fields and fill in the last line
(`verified by owner: yes/no, note:`). Fix wrong rows in the YAML and reload. Commit the filled-in
sheet.

## Running the eval safely

- `make eval` is a **dry run**: it prints the case count and a rough cost estimate and exits.
  No API calls are made.
- `make eval EVAL_ARGS=--yes` (or `EVAL_CONFIRM=1`) calls the real Claude API for every case and
  **costs money**. Run it only against a database loaded with `EMBEDDER=bge`
  (`make data-load` with `.env` set to real mode); the runner checks the release notes.
- `LLM_MODE=fake EMBEDDER=fake make eval` is free, but the report is labelled as not a quality
  measurement.
- Reports are written to `evals/reports/<timestamp>.md`. Fake-mode reports are git-ignored.

The eval runs natively (it needs `evals/` and `uv`), not inside the `api` image.

## Rolling back to a previous data release

Data releases are never deleted, and the tables are keyed by release id, so an older release is
still fully intact in the database. There is **no rollback command** today: the API always reads
the highest `data_release.id`. What is possible now:

- **Forward fix (recommended).** Revert the bad change in `data/*.yaml` (for example `git revert`)
  and run `make data-load`. This creates a new release with the old content and becomes current.
- **Inspect an old release.** All data tables carry `data_release_id`, so you can query any older
  release in `psql` and compare it with the current one.
- **Find affected answers.** Use the `query_log.data_release_id` query above.

Do not delete rows from `data_release` or the data tables by hand. A selectable "active release"
setting is not implemented.

## Containers: quick reference

```bash
docker compose --profile full up --build -d     # db, api, web
docker compose --profile full ps
docker compose --profile full logs -f api
docker compose --profile full down              # keep the database
docker compose --profile full down -v           # also delete the database volume
```

The api container runs `python -m app.db` (idempotent migrations) before starting uvicorn.
`NEXT_PUBLIC_API_URL` is baked into the web image at build time; rebuild `web` when it changes.
The API's CORS allow-list comes from `CORS_ORIGINS` (comma-separated, default
`http://localhost:3000`); set it to the staging web origin. `make dev` and the `full` profile share
ports 8000/3000, so stop one before starting the other. `make db-reset CONFIRM=1` deletes the local
database (all data releases and `query_log`) and stops api/web.
