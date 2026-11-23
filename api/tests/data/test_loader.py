import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml

from app.data.loader import DataError, current_release_id, load_data
from app.db import Conn
from app.retrieval.embedder import FakeEmbedder
from tests.fixtures.codes import FIXTURE_CODES, FIXTURE_OUT_OF_SCOPE_CODE

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "data"

Mutation = Callable[[Path], None]


def _edit(file: str, fn: Callable[[list[dict[str, Any]]], None]) -> Mutation:
    def mutate(root: Path) -> None:
        path = root / file
        rows = yaml.safe_load(path.read_text())
        fn(rows)
        path.write_text(yaml.safe_dump(rows, allow_unicode=True))

    return mutate


def drop_field(file: str, idx: int, field: str) -> Mutation:
    return _edit(file, lambda rows: rows[idx].pop(field))


def set_field(file: str, idx: int, field: str, value: Any) -> Mutation:
    return _edit(file, lambda rows: rows[idx].__setitem__(field, value))


@pytest.fixture
def fixture_dir() -> Path:
    return FIXTURE


@pytest.fixture
def tmp_fixture(tmp_path: Path) -> Path:
    dest = tmp_path / "data"
    shutil.copytree(FIXTURE, dest)
    return dest


def count(db: Conn, table: str, rid: int) -> int:
    row = db.execute(f"select count(*) from {table} where data_release_id=%s", [rid]).fetchone()
    assert row is not None
    return int(row[0])


def test_load_valid_fixture_creates_release(db: Conn, fixture_dir: Path) -> None:
    rid = load_data(db, fixture_dir, FakeEmbedder(), notes="t")
    assert current_release_id(db) == rid
    assert count(db, "kbli", rid) == 4
    assert count(db, "permit", rid) == 3
    assert count(db, "permit_rule", rid) == 5
    assert count(db, "kbli_2020_map", rid) == 4
    row = db.execute(
        "select embedding from kbli where data_release_id=%s limit 1", [rid]
    ).fetchone()
    assert row is not None and len(row[0].to_list()) == 1024


def test_fixture_codes_match_constants(db: Conn, fixture_dir: Path) -> None:
    rid = load_data(db, fixture_dir, FakeEmbedder())
    rows = db.execute(
        "select code from kbli where data_release_id=%s and in_scope", [rid]
    ).fetchall()
    assert sorted(r[0] for r in rows) == sorted(FIXTURE_CODES)
    out = db.execute(
        "select in_scope from kbli where data_release_id=%s and code=%s",
        [rid, FIXTURE_OUT_OF_SCOPE_CODE],
    ).fetchone()
    assert out == (False,)


def test_second_load_creates_new_release_and_keeps_old(db: Conn, fixture_dir: Path) -> None:
    a = load_data(db, fixture_dir, FakeEmbedder())
    b = load_data(db, fixture_dir, FakeEmbedder())
    assert b > a
    assert count(db, "kbli", a) == 4
    assert current_release_id(db) == b


@pytest.mark.parametrize(
    "mutation, msg",
    [
        (drop_field("permits.yaml", 0, "source_url"), "source_url"),
        (set_field("rules.yaml", 0, "kbli_code", "99999"), "unknown kbli_code 99999"),
        (set_field("rules.yaml", 0, "permit_id", "nope"), "unknown permit_id nope"),
        (set_field("rules.yaml", 0, "conditions", {"colour": True}), "unknown attribute colour"),
        (set_field("kbli_scope.yaml", 0, "code", "1071"), "code"),
        (set_field("rules.yaml", 0, "risk_level", "sedang"), "risk_level"),
        (set_field("kbli_2020_map.yaml", 0, "code_2025", ["12345"]), "unknown code_2025 12345"),
    ],
)
def test_invalid_data_is_rejected_and_nothing_written(
    db: Conn, tmp_fixture: Path, mutation: Mutation, msg: str
) -> None:
    mutation(tmp_fixture)
    with pytest.raises(DataError, match=msg):
        load_data(db, tmp_fixture, FakeEmbedder())
    row = db.execute("select count(*) from data_release").fetchone()
    assert row is not None and row[0] == 0


def test_error_message_names_file_and_row(db: Conn, tmp_fixture: Path) -> None:
    set_field("rules.yaml", 2, "permit_id", "nope")(tmp_fixture)
    with pytest.raises(DataError, match=r"rules\.yaml.*row 2.*unknown permit_id nope"):
        load_data(db, tmp_fixture, FakeEmbedder())


def test_in_scope_code_without_rule_is_rejected(db: Conn, tmp_fixture: Path) -> None:
    _edit("rules.yaml", lambda rows: rows[:] and rows.__delitem__(slice(0, 2)))(tmp_fixture)
    with pytest.raises(DataError, match="no rule for in-scope code 90001"):
        load_data(db, tmp_fixture, FakeEmbedder())
    row = db.execute("select count(*) from data_release").fetchone()
    assert row is not None and row[0] == 0


def test_write_failure_rolls_back_whole_release(db: Conn, fixture_dir: Path) -> None:
    class Boom(FakeEmbedder):
        def embed(self, texts: list[str]) -> list[list[float]]:
            raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        load_data(db, fixture_dir, Boom())
    row = db.execute("select count(*) from data_release").fetchone()
    assert row is not None and row[0] == 0
