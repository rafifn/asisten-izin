from pathlib import Path
from typing import Any

import psycopg
from pgvector.psycopg import register_vector

from app.config import database_url

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "db" / "migrations"

Conn = psycopg.Connection[Any]


def _register(conn: Conn) -> None:
    try:
        register_vector(conn)
    except psycopg.ProgrammingError:
        # The vector extension does not exist yet (before the first migration).
        conn.rollback()


def connect(url: str | None = None) -> Conn:
    conn: Conn = psycopg.connect(url or database_url())
    _register(conn)
    return conn


def migrate(conn: Conn) -> list[str]:
    conn.execute(
        "create table if not exists schema_migrations ("
        "name text primary key, applied_at timestamptz not null default now())"
    )
    done = {r[0] for r in conn.execute("select name from schema_migrations")}
    applied: list[str] = []
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        if path.name in done:
            continue
        conn.execute(path.read_text())
        conn.execute("insert into schema_migrations (name) values (%s)", (path.name,))
        applied.append(path.name)
    conn.commit()
    if applied:
        _register(conn)
    return applied


if __name__ == "__main__":
    with connect() as c:
        print("applied:", migrate(c))
