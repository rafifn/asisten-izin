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
