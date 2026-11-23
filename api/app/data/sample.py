"""Write a random sample of permit and rule rows for the owner to spot-check against sources.

Usage: python -m app.data.sample <data_dir> <out_dir>   (set SEED for a repeatable sample)
"""

import os
import random
import sys
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from app.data.schemas import PermitRow, RuleRow

SAMPLE_SIZE = 10
MIN_PERMITS = 3  # permits are few next to rules; make sure some are always checked
VERIFY_LINE = "verified by owner: yes/no, note:"

PERMIT_FIELDS = (
    "id",
    "name",
    "issuer",
    "source_regulation",
    "source_article",
    "valid_from",
    "last_verified",
    "regional_note",
)
RULE_FIELDS = (
    "kbli_code",
    "conditions",
    "risk_level",
    "permit_id",
    "step_order",
    "source_regulation",
    "valid_from",
    "last_verified",
)


def _rows(data_dir: Path) -> list[tuple[str, int, dict[str, Any]]]:
    """All permit and rule rows as (file, 0-based row index, validated fields)."""
    out: list[tuple[str, int, dict[str, Any]]] = []
    for name, model in (("permits.yaml", PermitRow), ("rules.yaml", RuleRow)):
        raw = yaml.safe_load((data_dir / name).read_text())
        for i, item in enumerate(raw):
            out.append((name, i, model.model_validate(item).model_dump()))
    return out


def _fmt(value: Any) -> str:
    if isinstance(value, dict):
        return "{" + ", ".join(f"{k}: {str(v).lower()}" for k, v in value.items()) + "}"
    return str(value)


def _entry(n: int, file: str, idx: int, row: dict[str, Any]) -> str:
    fields = PERMIT_FIELDS if file == "permits.yaml" else RULE_FIELDS
    title = row["id"] if file == "permits.yaml" else f"{row['kbli_code']} -> {row['permit_id']}"
    lines = [f"## {n}. {file} row {idx}: {title}", ""]
    lines += [f"- {f}: {_fmt(row[f])}" for f in fields if row.get(f) is not None]
    lines += [f"- source_url: {row['source_url']}", "", VERIFY_LINE, ""]
    return "\n".join(lines)


def write_sample(data_dir: Path, out_dir: Path, seed: int | None, day: date) -> Path:
    """Pick SAMPLE_SIZE random permit/rule rows and write out_dir/<day>.md. Returns the path."""
    rows = _rows(data_dir)
    rng = random.Random(seed)
    permits = [r for r in rows if r[0] == "permits.yaml"]
    n_permits = min(MIN_PERMITS, len(permits))
    picked = rng.sample(permits, n_permits)
    rest = [r for r in rows if r not in picked]
    picked += rng.sample(rest, min(SAMPLE_SIZE - n_permits, len(rest)))
    header = [
        f"# Spot-check {day.isoformat()}",
        "",
        f"{len(picked)} random rows from `permits.yaml` and `rules.yaml`, at least"
        f" {n_permits} of them permits"
        f" (seed: {seed if seed is not None else 'none'}). For each row, open the source URL,"
        " check the fields, and fill in the last line.",
        "",
    ]
    body = [_entry(n, *row) for n, row in enumerate(picked, start=1)]
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{day.isoformat()}.md"
    path.write_text("\n".join(header + body))
    return path


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: python -m app.data.sample <data_dir> <out_dir>", file=sys.stderr)
        return 2
    seed_env = os.environ.get("SEED")
    seed = int(seed_env) if seed_env else None
    path = write_sample(Path(argv[1]), Path(argv[2]), seed, date.today())
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
