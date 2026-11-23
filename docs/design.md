# Asisten Izin Kuliner: Phase 1 Design

Status: draft for approval · 2026-11-23

## 1. Intent

Small food and beverage businesses in Indonesia (UMKM kuliner) must pick the right
KBLI code when they register for an NIB in OSS, and then work out which permits
they need. Both steps are confusing, and a wrong KBLI code leads to the wrong
permits and a revision later.

This app lets an owner describe their business in plain Indonesian and get back:

1. one to three suggested KBLI 2025 codes, each with the official title and
   definition and a short reason it fits;
2. the risk level for that activity;
3. the permits to obtain, in order, each with its legal source.

There are two reasons to build it:

- **Learning and portfolio.** The owner of this project is a frontend engineer
  moving into AI engineering. The project is planned in five phases, each mapped
  to the skills in a target AI Engineer job description: full-stack plus vector DB,
  data pipelines, agents/MCP/evals, infrastructure, and model serving.
- **Real users.** The portfolio is meant to "sell" through real usage numbers and
  measured quality and cost, not a list of technologies. The product has to be
  genuinely useful.

This document covers **Phase 1 only**: a working app that runs locally and is
smooth enough to move to a staging environment next.

## 2. Users

Owners of micro and small food and beverage businesses who are about to register,
or who have just registered, in OSS. Most will read the result on a phone.

**In scope:**
- packaged food or drinks made at home (for example chips, frozen food, bottled
  non-alcoholic drinks)
- catering
- small warung, kedai or cafe with or without seating
- selling food online

**Out of scope:**
- large restaurants and franchises
- alcoholic drinks
- foreign investment (PMA)
- anything outside food and beverage

- medium-sized businesses (usaha menengah) and above

The app answers out-of-scope cases plainly ("belum didukung") and does not guess.

**Business size.** The app assumes micro or small, and says so in the answer
as a stated assumption. It asks about size only when the description suggests
a bigger business, for example many branches, a factory, or many employees.

**Partly in-scope businesses** (a warung that also sells sembako, a cafe that
also serves alcohol):
- The app answers the in-scope part.
- It adds a short `scope_note` naming the part it does not cover.
- It returns `out_of_scope` only when nothing in-scope remains.

## 3. Goals, non-goals, anti-goals

**Goals (Phase 1)**
- Correct KBLI suggestions for in-scope businesses, measured by an eval set.
- A permit checklist that comes only from curated, sourced data.
- Every answer shows its sources and the date of the data it used.
- `make dev` brings up the whole app locally; `make eval` produces a quality, cost
  and latency report.
- The groundwork for later phases is in place: answers logged with the data
  version, and rules data stored as files.

**Non-goals (Phase 1)**
- User accounts and login.
- An agent that chooses its own steps (Phase 3).
- Automated regulation monitoring with Airflow (Phase 2).
- Kubernetes, Terraform, CI/CD to a server (Phase 4). Staging comes right after
  Phase 1 but is not designed here.
- A self-hosted or fine-tuned model (Phase 5).
- Free-form multi-turn chat. Only one round of clarifying questions is allowed.

**Anti-goals: failure even if everything technically works**
- The app shows a permit, KBLI code or risk level that is not in the curated data.
- The app gives a confident answer without a source.
- The app answers from outdated data without saying so.
- The app collects personal data it does not need (names, NIK, phone numbers).

## 4. Constraints

- **Current law.** Data must follow **KBLI 2025** (Peraturan BPS 7/2025, used in
  OSS since about mid-June 2026) and **PP 28/2025** on risk-based licensing, which
  replaced PP 5/2021 and has been fully in force since 5 October 2025. Under it,
  permits go in order: basic permits, then business permits, then operational
  permits. There are four risk levels: rendah, menengah rendah, menengah tinggi
  and tinggi.
- **Not legal advice.** The app must say so and must point users to oss.go.id to
  confirm.
- **Runs on a MacBook.** Docker, `uv` and Node 22 are already installed. Python is
  3.12, installed through `uv`; the system Python is 3.9 and is not used.
- **Only one external call.** The Claude API is the only external dependency at
  runtime. Embeddings run locally.
- **Follows the owner's existing conventions** from their `shoplink` project:
  `docs/design.md`, a `Makefile` with `dev`/`check` targets, a local-only Docker
  Compose file, `CLAUDE.md` for coding agents, and work split into issues with
  acceptance criteria.

## 5. Approaches considered

| # | Approach | Trade-off |
|---|---|---|
| **1** | **Next.js frontend + FastAPI (Python) backend + Postgres/pgvector** | Matches the job description's stack (React/Next.js, Python/FastAPI, vector DB). Later phases (Airflow, fine-tuning, vLLM) are Python. The frontend uses the owner's existing strength. The cost is two languages and two servers to set up. |
| 2 | Next.js only, TypeScript full-stack | Fastest for the owner, but proves no Python skill, and phases 2 and 5 would need Python anyway. |
| 3 | Python only, FastAPI + HTMX | Fewest moving parts, but the UI feels like a demo on phones, and the owner's frontend skill goes unused. |

**Chosen: 1**, by the owner.

## 6. Design

### 6.1 What the user sees

1. A single page with one text box: "Ceritakan usahamu", plus two or three example
   prompts.
2. If the description is too vague, the app asks **at most two** short questions in
   one round, as tappable options where possible. Examples: dikemas atau langsung
   disantap? ada tempat makan? bahan hewani?
3. The result:

```
Usaha: keripik pisang dikemas, dijual online & titip warung
Data per 15 Nov 2026 · Dianggap usaha mikro/kecil

KBLI 2025 yang perlu didaftarkan
  Kegiatan 1: produksi keripik
    ★ 10xxx  <official title>   kenapa cocok: ...   [definisi resmi ▾]
             risiko: <from data>
      10xxx  <official title>   pilih ini jika ...
  Kegiatan 2: jualan online            (only if it truly needs its own code)
    ★ 47xxx  <official title>   kenapa cocok: ...
             risiko: <from data>

Izin yang perlu diurus (berurutan)
  1. NIB, di OSS                    untuk: semua       [sumber ▾]
  2. SPP-IRT, ...                   untuk: 10xxx       [sumber ▾]
  3. Sertifikat halal, ...          untuk: 10xxx       [sumber ▾]
  ⓘ Prosedur bisa berbeda per daerah. Cek ke dinas setempat.

⚠ Bukan nasihat hukum. Cek ulang di oss.go.id
Apakah ini membantu?  👍  👎
```

   **Multiple activities.** A business can have one or more **activities**.
   - Each activity gets one primary KBLI plus optional alternatives ("pilih ini
     jika").
   - Separate activities appear only when they truly need separate codes. The
     builder confirms this from KBLI definitions; for example, a producer selling
     its own product online may not need a retail code.
   - The permit list is merged and de-duplicated across the primary codes. Each
     permit is labeled with the code(s) that require it.
   - Choosing an alternative re-runs only the deterministic permit lookup through
     the API (`POST /v1/permits`), so the UI still holds no business logic.

   **Old KBLI 2020 codes.** If the user mentions one, the result shows a small
   note: "kode lama X → kode baru Y".

4. Out-of-scope input gets a short, plain message and nothing else.
5. If any data row behind the answer has not been verified for more than 6 months,
   a visible warning appears.

### 6.2 Architecture

```
Browser (Next.js, Indonesian UI)
   │  JSON over HTTP
   ▼
FastAPI  ──►  Claude API (claude-opus-5-5)
   │
   ├─►  embedding model (local, in-process)
   ▼
Postgres 17 + pgvector  (KBLI, permits, rules, logs)
```

- **`web/`**: Next.js (App Router), Tailwind, shadcn/ui, pnpm. This is the same
  stack as the owner's other projects. The UI has no business logic.
- **`api/`**: FastAPI on Python 3.12, managed with `uv`. Owns the whole request
  pipeline.
- **`db`**: Postgres 17 with pgvector, running in Docker Compose.
- **Embeddings**: a local multilingual model that handles Indonesian well. Starting
  choice: `BAAI/bge-m3`. The builder may swap it if the eval shows a better
  option. KBLI embeddings are computed when data is loaded, not per request.
- **LLM**: Claude Opus 5.5 (`claude-opus-5-5`) through the official `anthropic`
  Python SDK.
  - Use structured outputs for every call.
  - Set effort explicitly (its default is `medium`) and tune it with the eval.
  - Enable server-side refusal fallbacks (`fallbacks: "default"`).
  - Switching to a cheaper model is a later, eval-driven decision, not a Phase 1
    one.

### 6.3 Request pipeline

The code controls the flow. This is a fixed workflow, not an agent.

0. **Redact.** A regex pass masks obvious personal data before anything reaches
   Claude or the log: NIK-like 16-digit numbers, phone numbers, emails. This
   cannot catch everything, which is why the UI asks users not to type personal
   details.
1. **Understand.** One Claude call turns the description into structured data:
   - the list of activities, each with its attributes: packaged or served, has
     seating, sells online, uses animal products
   - business size (assumed micro/small unless signals say otherwise)
   - scope status: in, partial with a note, or out
   - any KBLI 2020 code mentioned
   - missing information, as up to 2 clarifying questions

   If questions come back and this is the first round, return them to the UI.
   After the user answers, continue with whatever is known.
2. **Retrieve.** For each activity, run a hybrid search over **in-scope KBLI codes
   only**: Postgres keyword search plus vector search, merged with reciprocal
   rank fusion, top ~20 candidates. Any KBLI 2025 code mapped from a mentioned
   2020 code is added to the candidates.
3. **Select.** A second Claude call picks, per activity, one primary code and up
   to two alternatives, **from the candidate list only**, each with a reason or a
   "pilih ini jika" note. It may merge activities that one code already covers.
   The API rejects any code that is not among the candidates and retries once. If
   the retry also fails, it returns a safe "tidak yakin" result.
4. **Look up permits.** This step is deterministic and makes no LLM call.
   - Rules in the database map (KBLI code + attributes) to a risk level and an
     ordered list of permits.
   - Lookups for the primary codes are merged and de-duplicated, and each permit
     is labeled with the code(s) that require it.
   - Permit names, descriptions and sources come straight from the data.
5. **Respond.** The response is assembled as structured JSON (see 6.4). The only
   LLM-written text is the KBLI reasons and the scope note.
6. **Log.** Each request is stored, after redaction, with:
   - input and clarifications
   - output JSON
   - data release ID and model ID
   - input and output tokens, cost, latency
   - feedback, filled in later

**Rule for Claude calls:** the model never produces permits or risk levels. It
only interprets the description and chooses among real KBLI candidates.

### 6.4 API surface

- `POST /v1/analyze` takes `{ description, answers? }` and returns one of:
  - `{ status: "needs_clarification", questions[] }`
  - `{ status: "out_of_scope", message }`
  - `{ status: "ok", result }`

  The `result` holds:
  - `activities[]`, each with a label, `primary` (code, title, definition,
    reason, risk_level) and `alternatives[]` (code, title, definition,
    when_to_choose, risk_level)
  - `permits[]`: order, name, issuer, description, `for_kbli[]`,
    `regional_note?`, source {regulation, article, url}, last_verified
  - `assumptions[]`, `scope_note?`, and `kbli_2020_mapping?` (from, to[])
  - `data_as_of`, `stale_warning`, `request_id`
- `POST /v1/permits` takes `{ request_id, primary_codes[] }` and returns the
  merged `permits[]`. The UI calls it when the user picks an alternative. It uses
  the attributes stored for that request and makes no LLM call.
- `POST /v1/feedback` takes `{ request_id, helpful: bool, comment? }`. The
  comment is redacted the same way as the input.
- `GET /healthz`.

Errors follow the owner's existing shape:
`{"error": {"code": "...", "message": "..."}}`.

### 6.5 Data model

| Table | Columns |
|---|---|
| `data_release` | id, created_at, notes. One row per data load. |
| `kbli` | code, version (`2025`), title, definition, in_scope, embedding |
| `permit` | id, name, issuer, description, how_to, source_regulation, source_article, source_url, valid_from, valid_to (null = still valid), last_verified |
| `permit_rule` | id, kbli_code, conditions (JSON over the attributes from step 1), risk_level, permit_id, step_order, valid_from, valid_to |
| `query_log` | id, created_at, input, clarifications, output, data_release_id, model, tokens_in, tokens_out, cost_usd, latency_ms, helpful, comment |

Rows that are no longer valid are **never deleted**. They get a `valid_to` date
instead.

`query_log` stores only redacted text. Locally there is no retention limit.
For staging, the proposed limit is 90 days of raw text, after which only metrics
and feedback are kept. That limit is decided when staging is designed.

### 6.6 Data sourcing and curation

- **Source of truth.** Rules data lives in the repo as files under `data/`, for
  example `data/kbli_scope.yaml`, `data/permits.yaml` and `data/rules.yaml`. The
  database is loaded from these files by `make data-load`, which validates the
  schema and refuses to load any permit or rule without a source. Git history is
  the audit trail.
- **KBLI 2025.** Comes from BPS's official publication. The scope list covers
  food and non-alcoholic drink manufacturing, food and beverage service, and the
  relevant food retail and online selling codes. The builder confirms the exact
  codes against the real KBLI 2025 text. The BPS 2020→2025 conversion table is
  loaded as well, so users who mention an old code can be helped.
- **Permit boundary (owner's decision): national plus sector.** The list
  includes everything OSS requires for the KBLI code under PP 28/2025, such as
  NIB and the basic requirements for micro/small low-risk activities. It also
  includes sector permits for food: SPP-IRT or BPOM MD for packaged products,
  halal certification, and SLHS for catering and food service.
  - All permits are described at the national level.
  - Where the procedure or issuer differs by region (for example SLHS from the
    local Dinas Kesehatan), the permit carries a `regional_note` saying "cek ke
    dinas setempat".
  - The app does not ask for location and has no per-region data.
  - Tax registration is out of scope.
- **Permits and risk levels: sourcing.** Curated by hand from PP 28/2025 (and its
  attachments) and the relevant implementing regulations: BPOM on SPP-IRT, the
  halal product rules, and similar. Curation happens during the build. The owner
  then **spot-checks a random sample** against the sources before Phase 1 counts
  as done.

### 6.7 Handling regulation changes

- Every permit and rule row carries `valid_from`, `valid_to`, `last_verified` and
  its source.
- Changing a rule means editing a data file. That edit goes through review and is
  checked by re-running the eval.
- Answers show "Data per <date>". Rows not verified for more than 6 months trigger
  a visible warning.
- Logs record the data release behind each answer, so answers affected by a later
  correction can be found.
- **Phase 2** adds automated monitoring of official sources (JDIH, BPK). AI drafts
  a summary and a proposed data edit, and a human approves it. Changes are never
  applied automatically.

### 6.8 Evaluation

- **Cases.** `evals/cases.yaml` holds about 50 cases. Each case has a description
  and optional clarification answers, plus the expected values:
  - primary KBLI and other acceptable KBLI codes
  - risk level and the permit set
  - out-of-scope flag

  Each case has one or more activities, and each activity has a primary code
  plus other acceptable codes. Include about 10 out-of-scope or tricky cases
  (partly in scope, medium-sized, old KBLI 2020 code) and about 5 multi-activity
  cases.
- **Who writes them.** The builder drafts the cases from realistic business
  descriptions, and the owner reviews them.
- **`make eval`** runs the real pipeline against the real Claude API and writes a
  report to `evals/reports/<timestamp>.md`. The report covers:
  - KBLI top-1 and top-3 hit rate, scored per expected activity
  - permit set exact match, over the merged set for the primary codes
  - scope accuracy (in / partial / out)
  - clarification rate
  - average cost per question
  - p50 and p95 latency
- **Phase 1 bars** (proposed, can be adjusted after the first baseline run):
  - KBLI top-3 ≥ 90%
  - out-of-scope accuracy ≥ 95%
  - zero permits or codes outside the data (guaranteed by design, and asserted by
    the eval)

### 6.9 Local development

```
asisten-izin/
  api/         FastAPI app, tests (pytest)
  web/         Next.js app
  data/        curated YAML rules data
  evals/       cases.yaml, runner, reports/
  db/          migrations (SQL), init
  docs/        design.md, runbook.md
  docker-compose.yml   local only: Postgres + pgvector
  Makefile
  CLAUDE.md
  .env.example
```

`Makefile` targets:

| Target | What it does |
|---|---|
| `make dev` | Postgres in Docker; API and web run natively with hot reload |
| `make data-load` | Validate the YAML and load it into the DB as a new data release |
| `make db-reset` | Rebuild the local DB: migrations, then data-load |
| `make check` | Format, lint and type-check both apps, plus unit and integration tests |
| `make eval` | Run the eval against the real API (costs money) |

- **Secrets.** Read `ANTHROPIC_API_KEY` from `.env`, or use an `ant auth login`
  profile. Never commit secrets.
- **Tests.** Unit tests cover the rules engine, validators and the candidate-only
  check. Integration tests run against the local DB. Claude calls are faked in
  tests; the eval is the real-model check. Add one Playwright smoke test for the
  main flow.

### 6.10 Ready for staging when

- `make check` passes.
- `make eval` meets the Phase 1 bars.
- The owner's data spot-check is done.
- A fresh clone gets running with `make dev` by following the README.
- Every service runs in a container, so staging can reuse the same images.

## 7. Who decided what

**Owner's decisions**
- Scope B: KBLI plus permits, food and beverage only.
- Architecture 1: Next.js + FastAPI.
- Multiple activities produce a primary code plus additional codes.
- Permit boundary: national plus sector, with regional notes.
- Run locally first, then staging.

**Claude's calls (correct any of these)**
- Medium-sized businesses are out of scope.
- Size is assumed micro/small and shown as an assumption.
- Partly in-scope businesses get the in-scope answer plus a `scope_note`.
- PII is redacted with a regex before the LLM and the log.
- Proposed 90-day raw-text retention for staging.
- KBLI 2020 codes map into the candidate list, with a small conversion note.
- Model: Claude Opus 5.5. Local embeddings: bge-m3.
- Phase 1 eval bars.
- Directory layout and `Makefile` targets.

## 8. Left to the builder

- Prompt wording and the exact attribute schema in step 1.
- Postgres keyword-search configuration (there is no built-in Indonesian stemmer;
  `simple` plus trigram is fine) and the RRF parameters.
- Effort level per Claude call, chosen with the eval.
- UI details beyond the sketch in 6.1.
- Library choices inside each app (ORM or raw SQL, migration tool).
- Swapping the embedding model if the eval shows a better one.

## 9. Risks and open items

- **KBLI 2025 machine-readable source.** A clean CSV or Excel file may not exist.
  If only a PDF is available, extraction plus a manual check is part of the work.
- **Curating permits from PP 28/2025 attachments is the slowest part.** Limiting
  scope to kuliner micro/small is what keeps it doable.
- **Legal accuracy.** Mitigated by the sourced-data-only rule, the disclaimer, the
  staleness warning and the owner's spot-check.
