"""Generate the expected permits/risk of each case from the rules engine, and REVIEW.md.

Usage (from api/): python -m app.evals.expected [--check] [--review] [--today YYYY-MM-DD]

Expected values are computed once, from the expected primary codes and attributes against the
loaded data, and written into evals/cases.yaml as literals. `--check` only verifies that the
committed literals still match the engine (exit 1 if not).
"""

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from app.data.loader import current_release_id, load_data
from app.db import Conn, connect
from app.evals.cases import CASES_PATH, DATA_DIR, REPO_ROOT, Case, load_cases
from app.retrieval.embedder import FakeEmbedder
from app.rules.engine import lookup_permits, risk_for

REVIEW_PATH = REPO_ROOT / "evals" / "REVIEW.md"


def permit_names(conn: Conn, release_id: int) -> dict[str, str]:
    rows = conn.execute("select name, id from permit where data_release_id = %s", [release_id])
    mapping = {name: pid for name, pid in rows.fetchall()}
    return mapping


def compute_expected(
    conn: Conn, release_id: int, case: Case, today: date
) -> tuple[list[str], dict[str, str]] | None:
    """Permit ids (engine order) and primary-code risk levels; None if no expected activities."""
    if not case.expect.activities:
        return None
    primaries = [(a.primary, a.attributes) for a in case.expect.activities]
    items, _ = lookup_permits(conn, release_id, primaries, today)
    ids = permit_names(conn, release_id)
    risk: dict[str, str] = {}
    for code, attrs in primaries:
        level = risk_for(conn, release_id, code, attrs, today)
        if level is not None:
            risk[code] = level
    return [ids[i.name] for i in items], risk


def _dump(cases: list[dict[str, Any]]) -> str:
    return yaml.safe_dump(
        cases, default_flow_style=None, sort_keys=False, allow_unicode=True, width=100
    )


def fill(conn: Conn, release_id: int, today: date, path: Path = CASES_PATH) -> str:
    """Return the cases file text with expected permits/risk (re)generated."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    for item in raw:
        case = Case.model_validate(item)
        expected = compute_expected(conn, release_id, case, today)
        expect = item["expect"]
        expect.pop("permits", None)
        expect.pop("risk", None)
        if expected is not None:
            expect["permits"], expect["risk"] = expected
    return _dump(raw)


def review_markdown(cases: list[Case]) -> str:
    titles = {
        str(k["code"]): str(k["title"])
        for k in yaml.safe_load((DATA_DIR / "kbli_scope.yaml").read_text(encoding="utf-8"))
    }
    lines = [
        "# Eval case review",
        "",
        "Please review each case: is the description realistic, is the expected KBLI code right,",
        "and are the listed alternatives genuinely acceptable? Write OK or a note in the last",
        "column. Expected permits and risk are generated from the rules engine, not reviewed here.",
        "",
        "`primary` is the expected code; `also ok` lists extra acceptable codes. Vague cases are",
        "expected to trigger a clarification question first; their second pass is scored for",
        "scope only.",
        "",
        "| id | description | expected scope | expected codes | OK? / note |",
        "|---|---|---|---|---|",
    ]
    for c in cases:
        if c.expect.activities:
            parts = []
            for a in c.expect.activities:
                text = f"**{a.primary}** {titles[a.primary]}"
                extra = [f"{x} {titles[x]}" for x in a.acceptable if x != a.primary]
                if extra:
                    text += " (also ok: " + "; ".join(extra) + ")"
                parts.append(text)
            codes = "<br>".join(parts)
        else:
            codes = "(clarify first)" if c.expect.clarify else "(none)"
        desc = c.description.replace("|", "/")
        lines.append(f"| {c.id} | {desc} | {c.expect.scope} | {codes} | |")
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify, do not write")
    parser.add_argument("--review", action="store_true", help="also (over)write evals/REVIEW.md")
    parser.add_argument("--today", type=date.fromisoformat, default=date.today())
    args = parser.parse_args(argv)

    conn = connect()
    try:
        conn.execute("select 1")  # open a transaction so load_data runs in a savepoint
        load_data(conn, DATA_DIR, FakeEmbedder())  # rules do not depend on embeddings
        text = fill(conn, current_release_id(conn), args.today)
    finally:
        conn.rollback()  # the scratch release is never committed
        conn.close()

    if args.check:
        if text != CASES_PATH.read_text(encoding="utf-8"):
            print(
                "cases.yaml expected permits/risk are stale; run `make eval-gen`", file=sys.stderr
            )
            return 1
        print("cases.yaml expected values are up to date")
        return 0
    CASES_PATH.write_text(text, encoding="utf-8")
    print(f"wrote {CASES_PATH}")
    if args.review:
        REVIEW_PATH.write_text(review_markdown(load_cases()), encoding="utf-8")
        print(f"wrote {REVIEW_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
