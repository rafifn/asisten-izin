from pathlib import Path
from typing import Any

import psycopg
from pgvector.psycopg import register_vector

from app.config import database_url

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "db" / "migrations"

Conn = psycopg.Connection[Any]


def _register(conn: Conn) -> None:
    row = conn.execute("select 1 from pg_extension where extname = 'vector'").fetchone()
    if row is not None:
        register_vector(conn)


def connect(url: str | None = None) -> Conn:
    conn: Conn = psycopg.connect(url or database_url())
    _register(conn)
    return conn


def migrate(conn: Conn, migrations_dir: Path | None = None) -> list[str]:
    """Apply pending migrations, one transaction per file.

    Commits any open transaction on `conn` first. A failing file is rolled back
    and re-raised; files applied before it stay committed.
    """
    conn.execute(
        "create table if not exists schema_migrations ("
        "name text primary key, applied_at timestamptz not null default now())"
    )
    done = {r[0] for r in conn.execute("select name from schema_migrations")}
    conn.commit()
    applied: list[str] = []
    for path in sorted((migrations_dir or MIGRATIONS_DIR).glob("*.sql")):
        if path.name in done:
            continue
        with conn.transaction():
            conn.execute(path.read_text())
            conn.execute("insert into schema_migrations (name) values (%s)", (path.name,))
        applied.append(path.name)
    if applied:
        _register(conn)
        conn.commit()
    return applied


if __name__ == "__main__":
    with connect() as c:
        print("applied:", migrate(c))
