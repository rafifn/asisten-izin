from collections.abc import Iterator

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg import sql

from app.config import database_url
from app.db import Conn, connect, migrate
from app.main import create_app

TEST_DB = "asisten_izin_test"


def _test_url() -> str:
    return psycopg.conninfo.make_conninfo(database_url(), dbname=TEST_DB)


@pytest.fixture(scope="session")
def test_db_url() -> str:
    admin_url = psycopg.conninfo.make_conninfo(database_url(), dbname="postgres")
    with psycopg.connect(admin_url, autocommit=True) as admin:
        exists = admin.execute("select 1 from pg_database where datname = %s", (TEST_DB,))
        if exists.fetchone() is None:
            admin.execute(sql.SQL("create database {}").format(sql.Identifier(TEST_DB)))
    return _test_url()


@pytest.fixture
def raw_conn(test_db_url: str) -> Iterator[Conn]:
    """Connection to an empty, unmigrated database."""
    conn = connect(test_db_url)
    conn.execute("drop schema public cascade")
    conn.execute("create schema public")
    conn.commit()
    yield conn
    conn.rollback()
    conn.close()


@pytest.fixture
def db(test_db_url: str) -> Iterator[Conn]:
    """Migrated database; changes are rolled back after each test."""
    conn = connect(test_db_url)
    migrate(conn)
    yield conn
    conn.rollback()
    conn.close()


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())
