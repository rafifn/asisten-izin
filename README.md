# Asisten Izin Kuliner

An assistant that helps small food and beverage businesses in Indonesia (UMKM kuliner) pick the
right **KBLI 2025** code for their OSS/NIB registration and see which **permits** follow from it.
The owner describes the business in plain Indonesian. The app answers with one to three suggested
KBLI codes, the risk level, and the permits to get, in order, each with its legal source.

Picking the wrong KBLI code leads to the wrong permits and a revision later, and both steps are
confusing for a first-time registrant. This project is also a portfolio piece: a small, honest
RAG application with a curated data set, a rules engine, an eval harness and containerised
deployment. All user-facing copy is in Indonesian.

<p align="center">
  <img src="docs/screenshots/result-mobile.png" alt="Result screen on a phone (fake-mode answer)" width="320">
</p>

*Result screen in fake mode (canned LLM answers), captured by the Playwright smoke test.*

> **Disclaimer.** The app shows "Bukan nasihat hukum. Cek ulang di oss.go.id" on every answer.
> It is a drafting aid, not legal advice. Always confirm against OSS and the cited regulations.

## How it works

```
 browser ──> web (Next.js, :3000) ──> api (FastAPI, :8000) ──> Postgres 17 + pgvector (:5433)
                                         │
                                         └──> Claude (Opus 5.5) via the anthropic SDK
```

1. **Retrieve.** The description is embedded with `BAAI/bge-m3` (local, 1024 dims) and matched
   against KBLI titles and definitions in pgvector, merged with keyword search by reciprocal rank
   fusion (at most 20 candidates per activity).
2. **Select.** Claude picks one primary code and up to two alternatives, from the candidate list
   only. It may ask at most two clarifying questions, in one round.
3. **Rules.** Risk levels and permits come from a rules engine over hand-curated data rows, never
   from the model. Every permit and rule carries its source regulation, URL and `last_verified`.
4. **Log.** Each request is stored in `query_log` with the data release behind the answer.

Design details: [docs/design.md](docs/design.md). Project rules: [CLAUDE.md](CLAUDE.md).

## Quick start (fake mode, no API key)

Fake mode uses canned LLM answers and hash-based embeddings. It is for trying the app and for
tests, and its answers are **not** representative of real quality.

Prerequisites: Docker (with Compose), [uv](https://docs.astral.sh/uv/), Node 22 with corepack,
and `make`.

```bash
cp .env.example .env          # works as-is: fake mode, local database
make db-reset                 # start Postgres on 127.0.0.1:5433 and apply migrations
make data-load                # load data/*.yaml as a new data release
corepack pnpm@10.28.2 --dir web install
make dev                      # API on :8000, web on :3000 (Ctrl-C stops both)
```

Open <http://localhost:3000>. Check the API with `curl http://localhost:8000/healthz`.

### Everything in containers

```bash
cp .env.example .env
docker compose --profile full up --build -d
docker compose --profile full run --rm api python -m app.data.loader /app/data
```

The web app is on <http://localhost:3000>, the API on <http://localhost:8000>. The `api` image
bundles the bge-m3 weights (no download at start), runs as a non-root user, applies migrations on
start, and contains `data/`. `NEXT_PUBLIC_API_URL` is inlined into the web bundle at build time:
set it in `.env` (or the shell) before `--build` if the browser must reach the API elsewhere.
Stop with `docker compose --profile full down` (add `-v` to delete the database).

### Real mode

Real answers need an Anthropic API key and the real embedder:

```bash
# in .env
LLM_MODE=real
EMBEDDER=bge
ANTHROPIC_API_KEY=sk-ant-...
```

Then reload the data so the KBLI embeddings come from bge-m3 (the first run downloads about
2 GB of weights to the Hugging Face cache):

```bash
make data-load
make dev
```

In containers, build and run with the same `.env`, then run the loader as above. Do not mix
embedders: a data release loaded with `EMBEDDER=fake` gives poor retrieval under `bge`, so reload
after switching.

## Commands

| Command | What it does |
|---|---|
| `make dev` | Start db, apply migrations, run API (:8000) and web (:3000) |
| `make dev-api` / `make dev-web` | Run one side only |
| `make check` | ruff format and lint, mypy, pytest, web lint, typecheck, vitest |
| `make e2e` | Playwright smoke test against a running fake-mode stack |
| `make db-reset` | Wipe the local database volume and re-migrate |
| `make data-load` | Validate `data/*.yaml` and insert a new data release |
| `make data-sample` | Write a random spot-check sheet to `docs/spot-checks/` |
| `make eval` | Eval dry run: case count and cost estimate, no API calls |
| `make eval EVAL_ARGS=--yes` | Real eval against the Claude API (costs money) |
| `make eval-gen` | Regenerate expected permits in `evals/cases.yaml` |
| `docker compose --profile full up --build` | The whole stack in containers |

The `make e2e` test expects a fake-mode stack: `LLM_MODE=fake EMBEDDER=fake` (the `.env.example`
defaults), data loaded, and the app running on :3000 and :8000.

## Data and sources

The KBLI 2025 list (Peraturan BPS 7/2025), the permits and the rules (PP 28/2025 and the
implementing regulations for food) are curated by hand into `data/*.yaml` and loaded as an
immutable, versioned data release. Rows are never deleted; rows that stop being valid get
`valid_to`. Answers show "Data per <date>" and a visible warning when a row was last verified
more than 183 days ago.

- [data/SOURCES.md](data/SOURCES.md) lists every source and decision.
- Its [Known limitations](data/SOURCES.md#known-limitations) section is required reading. For
  example, rare higher-risk sub-activities are not modelled, and one halal deadline still needs
  re-verification once the regulation text is published.
- Scope: food and beverage only, national-level permits with regional notes, micro and small
  businesses assumed. Medium-sized businesses and tax registration are out of scope.

## Evals

`evals/cases.yaml` holds the eval cases (single and multi-activity, out-of-scope, tricky). The
harness runs the real pipeline over them and writes a report to `evals/reports/`.

```bash
make eval                        # dry run: prints case count and cost estimate
make eval EVAL_ARGS=--yes        # real Claude API, costs money; needs `make data-load` with bge
LLM_MODE=fake EMBEDDER=fake make eval   # free plumbing check, labelled as fake
```

The Phase 1 bars are KBLI top-3 >= 0.90 and scope accuracy >= 0.95 with zero invented codes or
permits. **The baseline report against the real model is still pending**, so there are no quality
numbers yet. `evals/reports/example-fake.md` only shows the report format.

## Project status

Phase 1 of 5: a working local app (retrieval, selection, rules, UI, logging, evals) that is ready
to move to staging. Still open before Phase 1 counts as done: the real-model eval baseline and the
owner's data spot-check ([docs/spot-checks/](docs/spot-checks/)). There are no users yet, and no
accuracy claims are made. Operations: [docs/runbook.md](docs/runbook.md).
