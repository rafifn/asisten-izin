import os
from dataclasses import dataclass, field
from typing import Literal, cast

from dotenv import load_dotenv

load_dotenv()

DEFAULT_CORS_ORIGINS = "http://localhost:3000"
DEFAULT_DATABASE_URL = "postgresql://asisten:asisten@127.0.0.1:5433/asisten_izin"


def database_url() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def parse_origins(raw: str | None) -> tuple[str, ...]:
    """Comma-separated origins; blank or unset falls back to the local web origin."""
    origins = tuple(o.strip() for o in (raw or "").split(",") if o.strip())
    return origins or (DEFAULT_CORS_ORIGINS,)


def _choice(name: str, allowed: tuple[str, ...], default: str) -> str:
    value = os.environ.get(name, default)
    if value not in allowed:
        raise ValueError(f"{name} must be one of {allowed}, got {value!r}")
    return value


@dataclass(frozen=True)
class Settings:
    database_url: str = field(default_factory=database_url)
    llm_mode: Literal["real", "fake"] = "real"
    # Which real LLM to call when llm_mode is "real".
    llm_provider: Literal["deepseek", "claude"] = "deepseek"
    embedder: Literal["bge", "fake"] = "bge"
    cors_origins: tuple[str, ...] = (DEFAULT_CORS_ORIGINS,)

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            database_url=database_url(),
            llm_mode=cast(Literal["real", "fake"], _choice("LLM_MODE", ("real", "fake"), "real")),
            llm_provider=cast(
                Literal["deepseek", "claude"],
                _choice("LLM_PROVIDER", ("deepseek", "claude"), "deepseek"),
            ),
            embedder=cast(Literal["bge", "fake"], _choice("EMBEDDER", ("bge", "fake"), "bge")),
            cors_origins=parse_origins(os.environ.get("CORS_ORIGINS")),
        )
