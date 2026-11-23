"""Eval runner: calls `analyze()` in-process over evals/cases.yaml and writes a report.

Never calls the real Claude API unless given `--yes` (or EVAL_CONFIRM=1). Without it, prints
the case count and a rough cost estimate and exits 0. `LLM_MODE=fake EMBEDDER=fake` exercises
the plumbing for free (the report is then labelled as not a quality measurement).
"""

import argparse
import math
import os
import sys
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

from app.config import Settings
from app.data.loader import current_release_id
from app.db import Conn, connect
from app.deps import AnyLlm, build_embedder, build_llm
from app.errors import ApiError
from app.evals.cases import CASES_PATH, REPO_ROOT, Case, load_cases
from app.evals.score import DataCodes, invented, score_kbli, score_permits
from app.pipeline.analyze import UNSURE_NOTE, NeedsClarification, Ok, OutOfScope, analyze
from app.retrieval.embedder import Embedder

REPORTS_DIR = REPO_ROOT / "evals" / "reports"
BAR_TOP3 = 0.90
BAR_SCOPE = 0.95
# Rough cost model for the pre-run estimate: ~2 LLM calls per case, ~6k in + ~1k out each.
CALLS_PER_CASE = 2
IN_TOK, OUT_TOK = 6_000, 1_000
IN_USD, OUT_USD = 4.00, 20.00


def estimate_cost(n_cases: int) -> float:
    per_call = (IN_TOK * IN_USD + OUT_TOK * OUT_USD) / 1_000_000
    return n_cases * CALLS_PER_CASE * per_call


@dataclass
class CaseResult:
    case: Case
    status: str  # ok | out_of_scope | needs_clarification | error
    clarified: bool
    got_scope: str  # in | partial | out | clarify | error
    ok: Ok | None
    cost_usd: float
    latency_s: float
    error: str | None = None
    kbli: dict[str, float] | None = None
    permits_ok: bool | None = None
    risk_ok: bool | None = None
    invented: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)


def got_scope(resp: NeedsClarification | OutOfScope | Ok) -> str:
    if isinstance(resp, OutOfScope):
        return "out"
    if isinstance(resp, NeedsClarification):
        return "clarify"
    note = resp.result.scope_note
    return "partial" if note is not None and note != UNSURE_NOTE else "in"


def _request_cost(conn: Conn, request_id: Any) -> float:
    row = conn.execute(
        "select cost_usd from query_log where request_uuid = %s", [request_id]
    ).fetchone()
    return float(row[0]) if row and row[0] is not None else 0.0


def first_option_answers(q: NeedsClarification) -> dict[str, str]:
    return {x.id: (x.options[0] if x.options else "tidak tahu") for x in q.questions}


def run_case(
    conn: Conn, llm: AnyLlm, embedder: Embedder, case: Case, today: date, commit: bool = True
) -> tuple[NeedsClarification | OutOfScope | Ok | None, bool, float, float, str | None]:
    """Returns (final response, clarified, cost, latency seconds, error).

    Commits after every request (like the API does) unless `commit` is False (tests).
    """

    def done() -> None:
        if commit:
            conn.commit()

    started = time.perf_counter()
    cost = 0.0
    clarified = False
    answers = case.answers
    try:
        resp = analyze(conn, llm, embedder, case.description, answers, today)
        done()
        cost += _request_cost(conn, resp.request_id)
        if isinstance(resp, NeedsClarification):
            clarified = True
            resp = analyze(conn, llm, embedder, case.description, first_option_answers(resp), today)
            done()
            cost += _request_cost(conn, resp.request_id)
    except ApiError as e:
        done()
        return None, clarified, cost, time.perf_counter() - started, f"{e.code}: {e.message}"
    return resp, clarified, cost, time.perf_counter() - started, None


def score_case(
    case: Case,
    resp: NeedsClarification | OutOfScope | Ok | None,
    clarified: bool,
    cost: float,
    latency: float,
    error: str | None,
    name_to_id: Mapping[str, str],
    data: DataCodes,
) -> CaseResult:
    exp = case.expect
    ok = resp if isinstance(resp, Ok) else None
    scope = "error" if resp is None else got_scope(resp)
    status = "error" if resp is None else resp.status
    r = CaseResult(case, status, clarified, scope, ok, cost, latency, error)
    if scope != exp.scope:
        r.failures.append(f"scope: expected {exp.scope}, got {scope}")
    if exp.clarify and not clarified:
        r.failures.append("expected a clarification question on the first pass")
    if error:
        r.failures.append(f"error: {error}")
    if ok is not None:
        r.invented = invented(ok.result, data)
        if r.invented:
            r.failures.append("invented: " + ", ".join(r.invented))
    if exp.activities:
        got = ok.result.activities if ok else []
        r.kbli = score_kbli([a.model_dump() for a in exp.activities], got)
        if r.kbli["top3"] < 1.0:
            want = ", ".join(a.primary for a in exp.activities)
            have = ", ".join(f"{a.primary.code}+{[x.code for x in a.alternatives]}" for a in got)
            r.failures.append(f"kbli: expected {want}; got {have or 'none'}")
        elif r.kbli["top1"] < 1.0:
            r.failures.append("kbli: top-3 hit but not top-1")
    if exp.permits is not None:
        r.permits_ok = bool(ok) and score_permits(exp.permits, ok.result.permits, name_to_id)  # type: ignore[union-attr]
        if not r.permits_ok:
            have_ids = (
                sorted(name_to_id.get(p.name, p.name) for p in ok.result.permits) if ok else []
            )
            r.failures.append(f"permits: expected {sorted(exp.permits)}; got {have_ids}")
    if exp.risk and ok is not None:
        by_code = {a.primary.code: a.primary.risk_level for a in ok.result.activities}
        checked = {c: lvl for c, lvl in exp.risk.items() if c in by_code}
        if checked:
            r.risk_ok = all(by_code[c] == lvl for c, lvl in checked.items())
    return r


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[max(0, math.ceil(q * len(ordered)) - 1)]


def summarize(results: list[CaseResult]) -> dict[str, Any]:
    pooled = {"top1": 0.0, "top3": 0.0}
    n_act = 0
    for r in results:
        if r.kbli is not None:
            n = len(r.case.expect.activities)
            n_act += n
            pooled["top1"] += r.kbli["top1"] * n
            pooled["top3"] += r.kbli["top3"] * n
    permit_cases = [r for r in results if r.permits_ok is not None]
    risk_cases = [r for r in results if r.risk_ok is not None]
    n = len(results) or 1
    return {
        "cases": len(results),
        "activities": n_act,
        "top1": pooled["top1"] / n_act if n_act else 0.0,
        "top3": pooled["top3"] / n_act if n_act else 0.0,
        "permit_exact": sum(bool(r.permits_ok) for r in permit_cases) / len(permit_cases)
        if permit_cases
        else 0.0,
        "permit_cases": len(permit_cases),
        "risk_match": sum(bool(r.risk_ok) for r in risk_cases) / len(risk_cases)
        if risk_cases
        else 0.0,
        "risk_cases": len(risk_cases),
        "scope": sum(r.got_scope == r.case.expect.scope for r in results) / n,
        "clarification_rate": sum(r.clarified for r in results) / n,
        "invented": sum(len(r.invented) for r in results),
        "avg_cost": sum(r.cost_usd for r in results) / n,
        "total_cost": sum(r.cost_usd for r in results),
        "p50": percentile([r.latency_s for r in results], 0.50),
        "p95": percentile([r.latency_s for r in results], 0.95),
    }


def _mark(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def render_report(
    results: list[CaseResult], settings: Settings, release_id: int, started: datetime
) -> str:
    s = summarize(results)
    fake = settings.llm_mode == "fake" or settings.embedder == "fake"
    out: list[str] = []
    if fake:
        out += [
            "> **FAKE MODE REPORT: NOT A QUALITY MEASUREMENT.** "
            f"(LLM_MODE={settings.llm_mode}, EMBEDDER={settings.embedder}.) "
            "It only exercises the eval plumbing; low scores are expected.",
            "",
        ]
    out += [
        f"# Eval report {started:%Y-%m-%d %H:%M}",
        "",
        f"- Mode: LLM_MODE={settings.llm_mode}, EMBEDDER={settings.embedder}",
        f"- Data release id: {release_id}",
        f"- Cases: {s['cases']} ({s['activities']} expected activities)",
        "",
        "| Metric | Value | Bar |",
        "|---|---|---|",
        f"| KBLI top-1 | {s['top1']:.3f} | |",
        f"| KBLI top-3 | {s['top3']:.3f} | >= {BAR_TOP3:.2f} {_mark(s['top3'] >= BAR_TOP3)} |",
        f"| Permit exact match ({s['permit_cases']} cases) | {s['permit_exact']:.3f} | |",
        f"| Risk match when primary exact ({s['risk_cases']} cases) | {s['risk_match']:.3f} | |",
        f"| Scope accuracy | {s['scope']:.3f} | "
        f">= {BAR_SCOPE:.2f} {_mark(s['scope'] >= BAR_SCOPE)} |",
        f"| Clarification rate | {s['clarification_rate']:.3f} | |",
        f"| Invented codes/permits | {s['invented']} | == 0 {_mark(s['invented'] == 0)} |",
        f"| Average cost per case (USD) | {s['avg_cost']:.4f} | |",
        f"| Total cost (USD) | {s['total_cost']:.4f} | |",
        f"| Latency p50 / p95 (s) | {s['p50']:.1f} / {s['p95']:.1f} | |",
        "",
        "Cases that ended in clarification were re-run once with each question answered by its",
        "first option; the second pass is the one scored. Vague cases are scored for scope only.",
        "",
    ]
    failed = [r for r in results if r.failures]
    out.append(f"## Failed cases ({len(failed)})")
    out.append("")
    if failed:
        out += ["| id | description | failures |", "|---|---|---|"]
        for r in failed:
            desc = r.case.description.replace("|", "/")
            fails = "<br>".join(f.replace("|", "/") for f in r.failures)
            out.append(f"| {r.case.id} | {desc} | {fails} |")
    else:
        out.append("None.")
    return "\n".join(out) + "\n"


def check_release(conn: Conn, settings: Settings) -> str | None:
    """Error text if the loaded release was embedded with a different embedder than configured;
    prints a reminder if that is not recorded."""
    row = conn.execute(
        "select notes from data_release where id = %s", [current_release_id(conn)]
    ).fetchone()
    notes = row[0] if row else ""
    if "embedder=" not in notes:
        print(
            "WARNING: the loaded data release does not record which embedder it used. For a real "
            "run, run `make data-load` WITHOUT EMBEDDER=fake first.",
            file=sys.stderr,
        )
        return None
    recorded = notes.split("embedder=", 1)[1].split()[0]
    if recorded != settings.embedder:
        return (
            f"data release was embedded with '{recorded}' but EMBEDDER={settings.embedder}; "
            "run `make data-load` with the matching embedder first"
        )
    return None


def load_data_codes(conn: Conn, release_id: int) -> tuple[DataCodes, dict[str, str]]:
    codes = {
        r[0] for r in conn.execute("select code from kbli where data_release_id = %s", [release_id])
    }
    perms = {
        r[0]: r[1]
        for r in conn.execute(
            "select name, id from permit where data_release_id = %s", [release_id]
        )
    }
    return DataCodes(codes=codes, permit_names=set(perms)), perms


def main(argv: list[str], env: Mapping[str, str] | None = None) -> int:
    env = os.environ if env is None else env
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--yes", action="store_true", help="allow calls to the real Claude API")
    parser.add_argument("--cases", type=Path, default=CASES_PATH)
    parser.add_argument("--limit", type=int, default=None, help="run only the first N cases")
    parser.add_argument("--reports-dir", type=Path, default=REPORTS_DIR)
    args = parser.parse_args(argv)

    settings = Settings.from_env()
    cases = load_cases(args.cases)
    if args.limit is not None:
        cases = cases[: args.limit]
    confirmed = args.yes or env.get("EVAL_CONFIRM") == "1"
    if settings.llm_mode == "real" and not confirmed:
        print(
            f"{len(cases)} cases, ~{CALLS_PER_CASE} LLM calls each. Rough cost estimate: "
            f"${estimate_cost(len(cases)):.2f} (6k in + 1k out tokens per call at $4/$20 per 1M), "
            "plus clarification re-runs."
        )
        print("Not calling the real API. Re-run with --yes (or EVAL_CONFIRM=1) to proceed.")
        return 0

    started = datetime.now()
    llm = build_llm(settings)
    embedder = build_embedder(settings)
    with connect(settings.database_url) as conn:
        problem = check_release(conn, settings) if settings.llm_mode == "real" else None
        if problem:
            print(f"error: {problem}", file=sys.stderr)
            return 1
        release_id = current_release_id(conn)
        data, name_to_id = load_data_codes(conn, release_id)
        results: list[CaseResult] = []
        for i, case in enumerate(cases, start=1):
            resp, clarified, cost, latency, error = run_case(
                conn, llm, embedder, case, date.today()
            )
            res = score_case(case, resp, clarified, cost, latency, error, name_to_id, data)
            results.append(res)
            print(
                f"[{i}/{len(cases)}] {case.id}: {'ok' if not res.failures else 'FAIL'}", flush=True
            )

    report = render_report(results, settings, release_id, started)
    fake = settings.llm_mode == "fake" or settings.embedder == "fake"
    args.reports_dir.mkdir(parents=True, exist_ok=True)
    name = f"{'fake-' if fake else ''}{started:%Y%m%d-%H%M}.md"
    path = args.reports_dir / name
    path.write_text(report, encoding="utf-8")
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
