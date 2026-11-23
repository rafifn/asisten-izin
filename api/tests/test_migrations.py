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
