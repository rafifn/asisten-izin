import logging
from collections.abc import Iterator
from datetime import date
from typing import cast

from fastapi import Request

from app.config import Settings
from app.db import Conn, connect
from app.errors import ApiError
from app.llm.client import LlmClient
from app.llm.fake import FakeLlm
from app.retrieval.embedder import BgeM3Embedder, Embedder, FakeEmbedder

AnyLlm = LlmClient | FakeLlm

log = logging.getLogger(__name__)


def embedder_mismatch(conn: Conn, embedder: str) -> str | None:
    """Warning text if the latest data release was embedded with another embedder than the
    configured one, or does not record one while `embedder=bge`; None if fine or no release."""
    row = conn.execute("select notes from data_release order by id desc limit 1").fetchone()
    if row is None:
        return None
    notes = row[0] or ""
    if "embedder=" not in notes:
        if embedder == "bge":
            return (
                "the latest data release does not record its embedder, but EMBEDDER=bge: "
                "retrieval may be poor. Run `make data-load` with EMBEDDER=bge."
            )
        return None
    recorded = notes.split("embedder=", 1)[1].split()[0]
    if recorded != embedder:
        return (
            f"the latest data release was embedded with '{recorded}' but EMBEDDER={embedder}: "
            "retrieval will be poor. Run `make data-load` with the matching EMBEDDER."
        )
    return None


def warn_on_embedder_mismatch(settings: Settings) -> None:
    """Startup check; never fails startup (the database may not be up yet)."""
    try:
        with connect(settings.database_url) as conn:
            problem = embedder_mismatch(conn, settings.embedder)
    except Exception as e:
        log.warning("could not check the data release embedder: %s", e)
        return
    if problem:
        log.warning("EMBEDDER MISMATCH: %s", problem)


def build_llm(settings: Settings) -> AnyLlm:
    return FakeLlm.canned() if settings.llm_mode == "fake" else LlmClient()


def build_embedder(settings: Settings) -> Embedder:
    return FakeEmbedder() if settings.embedder == "fake" else BgeM3Embedder()


def get_settings(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)


def get_llm(request: Request) -> AnyLlm:
    return cast(AnyLlm, request.app.state.llm)


def get_embedder(request: Request) -> Embedder:
    return cast(Embedder, request.app.state.embedder)


def get_today() -> date:
    return date.today()


def get_conn(request: Request) -> Iterator[Conn]:
    """One connection per request. Commits on success and on ApiError (log rows survive)."""
    conn = connect(cast(Settings, request.app.state.settings).database_url)
    try:
        yield conn
    except ApiError:
        conn.commit()
        raise
    except BaseException:
        conn.rollback()
        raise
    else:
        conn.commit()
    finally:
        conn.close()
