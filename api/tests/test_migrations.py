from pathlib import Path

import psycopg
import pytest

from app.db import Conn, migrate


def test_migrate_creates_tables_and_is_idempotent(raw_conn: Conn) -> None:
    assert "001_init.sql" in migrate(raw_conn)
    assert migrate(raw_conn) == []
    tables = {
        r[0]
        for r in raw_conn.execute(
            "select table_name from information_schema.tables where table_schema='public'"
        )
    }
    assert {"data_release", "kbli", "kbli_2020_map", "permit", "permit_rule", "query_log"} <= tables


def test_db_fixture_is_migrated(db: Conn) -> None:
    db.execute("insert into data_release (notes) values ('x')")
    row = db.execute("select count(*) from data_release").fetchone()
    assert row is not None and row[0] == 1


def test_failed_migration_rolls_back_and_keeps_earlier_files(
    raw_conn: Conn, tmp_path: Path
) -> None:
    (tmp_path / "001_good.sql").write_text("create table good (id int);")
    (tmp_path / "002_bad.sql").write_text("create table half (id int); select nope();")
    with pytest.raises(psycopg.Error):
        migrate(raw_conn, tmp_path)
    # connection is still usable; good file recorded, bad one not
    names = [r[0] for r in raw_conn.execute("select name from schema_migrations")]
    assert names == ["001_good.sql"]
    tables = {
        r[0]
        for r in raw_conn.execute(
            "select table_name from information_schema.tables where table_schema='public'"
        )
    }
    assert "good" in tables and "half" not in tables


def test_nested_transaction_in_db_fixture_is_rolled_back(db: Conn) -> None:
    with db.transaction():
        db.execute("insert into data_release (notes) values ('nested')")
    row = db.execute("select count(*) from data_release where notes='nested'").fetchone()
    assert row is not None and row[0] == 1


def test_db_fixture_changes_do_not_persist(db: Conn) -> None:
    row = db.execute("select count(*) from data_release where notes in ('nested', 'x')").fetchone()
    assert row is not None and row[0] == 0
