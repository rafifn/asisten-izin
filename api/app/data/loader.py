import os
import sys
from pathlib import Path
from typing import Any

import yaml
from pgvector import Vector
from psycopg.types.json import Jsonb
from pydantic import BaseModel, ValidationError

from app.data.schemas import Kbli2020MapRow, KbliScopeRow, PermitRow, RuleRow
from app.db import Conn, connect
from app.retrieval.embedder import BgeM3Embedder, Embedder, FakeEmbedder


class DataError(ValueError):
    """Invalid data file; the message names the file, the row (0-based) and the problem."""


def _read[M: BaseModel](data_dir: Path, name: str, model: type[M]) -> list[M]:
    path = data_dir / name
    try:
        raw: Any = yaml.safe_load(path.read_text())
    except (OSError, yaml.YAMLError) as e:
        raise DataError(f"{name}: cannot read file: {e}") from e
    if not isinstance(raw, list):
        raise DataError(f"{name}: expected a list of rows")
    rows: list[M] = []
    for i, item in enumerate(raw):
        try:
            rows.append(model.model_validate(item))
        except ValidationError as e:
            problems = "; ".join(
                f"{'.'.join(str(p) for p in err['loc']) or 'row'}: {err['msg']}"
                for err in e.errors()
            )
            raise DataError(f"{name}: row {i}: {problems}") from e
    return rows


def _check_unique(name: str, keys: list[str], what: str) -> None:
    seen: set[str] = set()
    for i, k in enumerate(keys):
        if k in seen:
            raise DataError(f"{name}: row {i}: duplicate {what} {k}")
        seen.add(k)


def _validate(
    data_dir: Path,
) -> tuple[list[KbliScopeRow], list[Kbli2020MapRow], list[PermitRow], list[RuleRow]]:
    kbli = _read(data_dir, "kbli_scope.yaml", KbliScopeRow)
    mapping = _read(data_dir, "kbli_2020_map.yaml", Kbli2020MapRow)
    permits = _read(data_dir, "permits.yaml", PermitRow)
    rules = _read(data_dir, "rules.yaml", RuleRow)

    _check_unique("kbli_scope.yaml", [k.code for k in kbli], "code")
    _check_unique("permits.yaml", [p.id for p in permits], "id")
    codes = {k.code for k in kbli}
    permit_ids = {p.id for p in permits}
    for i, m in enumerate(mapping):
        for c in m.code_2025:
            if c not in codes:
                raise DataError(f"kbli_2020_map.yaml: row {i}: unknown code_2025 {c}")
    for i, r in enumerate(rules):
        if r.kbli_code not in codes:
            raise DataError(f"rules.yaml: row {i}: unknown kbli_code {r.kbli_code}")
        if r.permit_id not in permit_ids:
            raise DataError(f"rules.yaml: row {i}: unknown permit_id {r.permit_id}")
    ruled = {r.kbli_code for r in rules}
    for k in kbli:
        if k.in_scope and k.code not in ruled:
            raise DataError(f"rules.yaml: no rule for in-scope code {k.code}")
    return kbli, mapping, permits, rules


def current_release_id(conn: Conn) -> int:
    row = conn.execute("select max(id) from data_release").fetchone()
    if row is None or row[0] is None:
        raise LookupError("no data release loaded")
    return int(row[0])


def load_data(conn: Conn, data_dir: Path, embedder: Embedder, notes: str = "") -> int:
    """Validate every file, then insert a new data_release atomically. Returns its id."""
    kbli, mapping, permits, rules = _validate(data_dir)
    vectors = embedder.embed([f"{k.title}. {k.definition}" for k in kbli])

    with conn.transaction():
        row = conn.execute("insert into data_release (notes) values (%s) returning id", [notes])
        release = int(row.fetchone()[0])  # type: ignore[index]
        for k, vec in zip(kbli, vectors, strict=True):
            conn.execute(
                "insert into kbli (code, data_release_id, title, definition, in_scope, embedding)"
                " values (%s, %s, %s, %s, %s, %s)",
                [k.code, release, k.title, k.definition, k.in_scope, Vector(vec)],
            )
        for m in mapping:
            for c in m.code_2025:
                conn.execute(
                    "insert into kbli_2020_map (data_release_id, code_2020, code_2025)"
                    " values (%s, %s, %s) on conflict do nothing",
                    [release, m.code_2020, c],
                )
        for p in permits:
            conn.execute(
                "insert into permit (id, data_release_id, name, issuer, description, how_to,"
                " source_regulation, source_article, source_url, valid_from, valid_to,"
                " last_verified, regional_note) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                [
                    p.id, release, p.name, p.issuer, p.description, p.how_to,
                    p.source_regulation, p.source_article, p.source_url, p.valid_from,
                    p.valid_to, p.last_verified, p.regional_note,
                ],
            )  # fmt: skip
        for r in rules:
            conn.execute(
                "insert into permit_rule (data_release_id, kbli_code, conditions, risk_level,"
                " permit_id, step_order, source_regulation, source_url, valid_from, valid_to,"
                " last_verified) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                [
                    release, r.kbli_code, Jsonb(r.conditions), r.risk_level, r.permit_id,
                    r.step_order, r.source_regulation, r.source_url, r.valid_from,
                    r.valid_to, r.last_verified,
                ],
            )  # fmt: skip
    return release


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python -m app.data.loader <data_dir>", file=sys.stderr)
        return 2
    name = "fake" if os.environ.get("EMBEDDER") == "fake" else "bge"
    embedder: Embedder = FakeEmbedder() if name == "fake" else BgeM3Embedder()
    try:
        with connect() as conn:
            # The embedder is recorded so the eval runner can check retrieval is real.
            rid = load_data(conn, Path(argv[1]), embedder, notes=f"embedder={name}")
    except DataError as e:
        print(f"data error: {e}", file=sys.stderr)
        return 1
    print(f"loaded data release {rid}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
