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
from app.evals.score import DataCodes, invented, match_primaries, score_kbli, score_permits
from app.pipeline.analyze import NeedsClarification, Ok, OutOfScope, analyze
from app.retrieval.embedder import Embedder

REPORTS_DIR = REPO_ROOT / "evals" / "reports"
BAR_TOP3 = 0.90
BAR_OUT_OF_SCOPE = 0.95  # applies to out-of-scope accuracy (ruling R22)
# Rough cost model for the pre-run estimate: ~2 LLM calls per case, ~6k in + ~1k out each.
CALLS_PER_CASE = 2
IN_TOK, OUT_TOK = 6_000, 1_000
IN_USD, OUT_USD = 4.00, 20.00


def estimate_cost(n_cases: int) -> float:
    per_call = (IN_TOK * IN_USD + OUT_TOK * OUT_USD) / 1_000_000
    return n_cases * CALLS_PER_CASE * per_call


@dataclass
class CaseRun:
    """What running one case produced (before scoring)."""

    resp: NeedsClarification | OutOfScope | Ok | None
    clarified: bool  # the first pass asked; the questions were auto-answered with option 1
    cost_usd: float  # every logged request of the case, failed ones included
    latency_s: float
    error: str | None = None
    logged_scope: str | None = None  # understanding.scope logged for the final request


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


def got_scope(resp: NeedsClarification | OutOfScope | Ok, logged_scope: str | None) -> str:
    """Scope the system answered with. For an `ok` answer this is the understanding's scope as
    logged in `query_log` (in or partial), not something inferred from the scope note."""
    if isinstance(resp, OutOfScope):
        return "out"
    if isinstance(resp, NeedsClarification):
        return "clarify"
    return logged_scope if logged_scope in ("in", "partial") else "in"


def _logged(conn: Conn, request_id: Any) -> tuple[float, str | None]:
    """(cost_usd, understanding scope) of a logged request."""
    row = conn.execute(
        "select cost_usd, attributes->>'scope' from query_log where request_uuid = %s",
        [request_id],
    ).fetchone()
    if row is None:
        return 0.0, None
    return (float(row[0]) if row[0] is not None else 0.0), row[1]


def first_option_answers(q: NeedsClarification) -> dict[str, str]:
    return {x.id: (x.options[0] if x.options else "tidak tahu") for x in q.questions}


def run_case(
    conn: Conn, llm: AnyLlm, embedder: Embedder, case: Case, today: date, commit: bool = True
) -> CaseRun:
    """Run one case (and its auto-answered clarification round, if asked).

    Commits after every request (like the API does) unless `commit` is False (tests). An
    `ApiError` becomes `CaseRun.error`; the cost of the failed request is still counted.
    """

    def done() -> None:
        if commit:
            conn.commit()

    started = time.perf_counter()
    run = CaseRun(None, False, 0.0, 0.0)

    def request(answers: dict[str, str] | None) -> NeedsClarification | OutOfScope | Ok:
        try:
            resp = analyze(conn, llm, embedder, case.description, answers, today)
        except ApiError as e:
            done()
            if e.request_id is not None:
                run.cost_usd += _logged(conn, e.request_id)[0]
            raise
        done()
        cost, run.logged_scope = _logged(conn, resp.request_id)
        run.cost_usd += cost
        return resp

    try:
        resp = request(case.answers)
        if isinstance(resp, NeedsClarification):
            run.clarified = True
            resp = request(first_option_answers(resp))
        run.resp = resp
    except ApiError as e:
        run.error = f"{e.code}: {e.message}"
    run.latency_s = time.perf_counter() - started
    return run


def score_case(
    case: Case, run: CaseRun, name_to_id: Mapping[str, str], data: DataCodes
) -> CaseResult:
    """Score one run. Each failure string starts with its type (`scope:`, `kbli:`, ...)."""
    exp = case.expect
    resp, clarified, error = run.resp, run.clarified, run.error
    ok = resp if isinstance(resp, Ok) else None
    scope = "error" if resp is None else got_scope(resp, run.logged_scope)
    status = "error" if resp is None else resp.status
    r = CaseResult(case, status, clarified, scope, ok, run.cost_usd, run.latency_s, error)
    if scope != exp.scope:
        r.failures.append(f"scope: expected {exp.scope}, got {scope}")
    if exp.clarify and not clarified:
        r.failures.append("clarify: expected a clarification question on the first pass")
    if not exp.clarify and clarified:
        r.failures.append(
            "unexpected_question: asked a clarification question on a non-vague case"
            " (auto-answered with the first option)"
        )
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
    if exp.activities and exp.activities[0].permits is not None:
        dumped = [a.model_dump() for a in exp.activities]
        got_acts = ok.result.activities if ok else []
        r.permits_ok = ok is not None and score_permits(
            dumped, got_acts, ok.result.permits, name_to_id
        )
        if not r.permits_ok:
            have_ids = (
                sorted(name_to_id.get(p.name, p.name) for p in ok.result.permits) if ok else []
            )
            r.failures.append(
                f"permits: got {have_ids} for primaries {[a.primary.code for a in got_acts]}"
                " (not matching the expected set for the chosen acceptable codes)"
            )
    if ok is not None and exp.activities and exp.activities[0].risk is not None:
        matched = match_primaries([a.model_dump() for a in exp.activities], ok.result.activities)
        checks = [
            m.primary.risk_level == a.risk[m.primary.code]  # type: ignore[index]
            for a, m in zip(exp.activities, matched, strict=True)
            if m is not None
        ]
        if checks:
            r.risk_ok = all(checks)
    return r


def evaluate_case(
    conn: Conn,
    llm: AnyLlm,
    embedder: Embedder,
    case: Case,
    today: date,
    name_to_id: Mapping[str, str],
    data: DataCodes,
    commit: bool = True,
) -> CaseResult:
    """Run and score one case. Any exception becomes an error row, so one bad case never
    stops a (paid) run."""
    started = time.perf_counter()
    try:
        return score_case(
            case, run_case(conn, llm, embedder, case, today, commit), name_to_id, data
        )
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        error = f"{type(e).__name__}: {e}"
        r = CaseResult(case, "error", False, "error", None, 0.0, time.perf_counter() - started)
        r.error = error
        r.failures.append(f"error: {error}")
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
    out_cases = [r for r in results if r.case.expect.scope == "out"]
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
        "out_cases": len(out_cases),
        "out_of_scope": sum(r.got_scope == "out" for r in out_cases) / len(out_cases)
        if out_cases
        else 0.0,
        "clarification_rate": sum(r.clarified for r in results) / n,
        "invented": sum(len(r.invented) for r in results),
        "avg_cost": sum(r.cost_usd for r in results) / n,
        "total_cost": sum(r.cost_usd for r in results),
        "p50": percentile([r.latency_s for r in results], 0.50),
        "p95": percentile([r.latency_s for r in results], 0.95),
    }


def _mark(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def _f(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}"


def render_report(
    results: list[CaseResult],
    settings: Settings,
    release_id: int,
    started: datetime,
    total_cases: int | None = None,
) -> str:
    """Markdown report. `total_cases` > len(results) marks the report as an incomplete run."""
    groups = {
        "All": results,
        "Clarified": [r for r in results if r.clarified],
        "Not clarified": [r for r in results if not r.clarified],
    }
    sums = {name: summarize(rs) for name, rs in groups.items()}
    s = sums["All"]
    fake = settings.llm_mode == "fake" or settings.embedder == "fake"
    out: list[str] = []
    if fake:
        out += [
            "> **FAKE MODE REPORT: NOT A QUALITY MEASUREMENT.** "
            f"(LLM_MODE={settings.llm_mode}, EMBEDDER={settings.embedder}.) "
            "It only exercises the eval plumbing; low scores are expected.",
            "",
        ]
    if total_cases is not None and total_cases > len(results):
        out += [
            f"> **INCOMPLETE RUN: {len(results)} of {total_cases} cases.** The run stopped early "
            "(interrupted or crashed); the numbers cover only the cases listed.",
            "",
        ]
    out += [
        f"# Eval report {started:%Y-%m-%d %H:%M}",
        "",
        f"- Mode: LLM_MODE={settings.llm_mode}, EMBEDDER={settings.embedder}",
        f"- Data release id: {release_id}",
        f"- Cases: {s['cases']} ({s['activities']} expected activities)",
        "- Latency: the first case's latency includes loading the embedding model.",
        "",
        "| Metric | All | Clarified ({}) | Not clarified ({}) | Bar (on All) |".format(
            len(groups["Clarified"]), len(groups["Not clarified"])
        ),
        "|---|---|---|---|---|",
    ]

    def cell(g: str, text: str) -> str:
        return text if groups[g] else "n/a"  # an empty group has no meaningful numbers

    def row(label: str, key: str, bar: str = "", digits: int = 3) -> str:
        vals = " | ".join(cell(g, _f(sums[g][key], digits)) for g in groups)
        return f"| {label} | {vals} | {bar} |"

    out += [
        row("KBLI top-1", "top1"),
        row("KBLI top-3", "top3", f">= {BAR_TOP3:.2f} {_mark(s['top3'] >= BAR_TOP3)}"),
        row(f"Permit exact match ({s['permit_cases']} cases)", "permit_exact"),
        row(f"Risk match, primary acceptable ({s['risk_cases']} cases)", "risk_match"),
        row("Scope accuracy, 3-way (in / partial / out)", "scope"),
        row(
            f"Out-of-scope accuracy ({s['out_cases']} expected-out cases)",
            "out_of_scope",
            f">= {BAR_OUT_OF_SCOPE:.2f} {_mark(s['out_of_scope'] >= BAR_OUT_OF_SCOPE)}",
        ),
        row("Clarification rate", "clarification_rate"),
        "| Invented codes/permits | "
        + " | ".join(cell(g, str(sums[g]["invented"])) for g in groups)
        + f" | == 0 {_mark(s['invented'] == 0)} |",
        row("Average cost per case (USD)", "avg_cost", digits=4),
        row("Total cost (USD)", "total_cost", digits=4),
        "| Latency p50 / p95 (s) | "
        + " | ".join(cell(g, f"{sums[g]['p50']:.1f} / {sums[g]['p95']:.1f}") for g in groups)
        + " | |",
        "",
        "Cases that ended in clarification were re-run once with each question answered by its",
        "first option; the second pass is the one scored. Vague cases are scored for scope only.",
        "Costs include every logged request of a case, also requests that ended in an error.",
        "",
    ]
    clarified_ids = [r.case.id for r in groups["Clarified"]]
    out.append(
        f"Clarified (auto-answered) cases: {', '.join(clarified_ids) if clarified_ids else 'none'}"
    )
    out.append("")
    failed = [r for r in results if r.failures]
    out.append(f"## Failed cases ({len(failed)})")
    out.append("")
    if failed:
        types: dict[str, int] = {}
        for r in failed:
            for f in r.failures:
                kind = f.split(":", 1)[0]
                types[kind] = types.get(kind, 0) + 1
        out += ["| Failure type | Count |", "|---|---|"]
        out += [f"| {k} | {v} |" for k, v in sorted(types.items())]
        out += ["", "| id | description | failures |", "|---|---|---|"]
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
    fake = settings.llm_mode == "fake" or settings.embedder == "fake"
    args.reports_dir.mkdir(parents=True, exist_ok=True)
    path = args.reports_dir / f"{'fake-' if fake else ''}{started:%Y%m%d-%H%M}.md"
    with connect(settings.database_url) as conn:
        problem = check_release(conn, settings) if settings.llm_mode == "real" else None
        if problem:
            print(f"error: {problem}", file=sys.stderr)
            return 1
        release_id = current_release_id(conn)
        data, name_to_id = load_data_codes(conn, release_id)
        results: list[CaseResult] = []

        def write() -> None:
            text = render_report(results, settings, release_id, started, len(cases))
            path.write_text(text, encoding="utf-8")

        try:
            for i, case in enumerate(cases, start=1):
                res = evaluate_case(conn, llm, embedder, case, date.today(), name_to_id, data)
                results.append(res)
                print(
                    f"[{i}/{len(cases)}] {case.id}: {'ok' if not res.failures else 'FAIL'}",
                    flush=True,
                )
                write()  # after every case: a crash or Ctrl-C never loses paid results
        finally:
            write()
            print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
