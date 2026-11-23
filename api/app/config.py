import os
from dataclasses import dataclass, field
from typing import Literal, cast

from dotenv import load_dotenv

load_dotenv()

DEFAULT_DATABASE_URL = "postgresql://asisten:asisten@127.0.0.1:5433/asisten_izin"


def database_url() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def _choice(name: str, allowed: tuple[str, ...], default: str) -> str:
    value = os.environ.get(name, default)
    if value not in allowed:
        raise ValueError(f"{name} must be one of {allowed}, got {value!r}")
    return value


@dataclass(frozen=True)
class Settings:
    database_url: str = field(default_factory=database_url)
    llm_mode: Literal["real", "fake"] = "real"
    embedder: Literal["bge", "fake"] = "bge"

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            database_url=database_url(),
            llm_mode=cast(Literal["real", "fake"], _choice("LLM_MODE", ("real", "fake"), "real")),
            embedder=cast(Literal["bge", "fake"], _choice("EMBEDDER", ("bge", "fake"), "bge")),
        )
