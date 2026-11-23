import hashlib
import math
import re
from typing import TYPE_CHECKING, Any, Protocol

DIM = 1024

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return 1024-dim, L2-normalized vectors, one per text."""
        ...


class BgeM3Embedder:
    """BAAI/bge-m3 via sentence-transformers; the model loads on first use."""

    def __init__(self) -> None:
        self._model: SentenceTransformer | None = None

    def _load(self) -> Any:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer("BAAI/bge-m3")
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = self._load().encode(texts, normalize_embeddings=True)
        return [[float(x) for x in v] for v in vectors]


class FakeEmbedder:
    """Deterministic test embedder: hashes word tokens into buckets, then normalizes."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._one(t) for t in texts]

    @staticmethod
    def _one(text: str) -> list[float]:
        vec = [0.0] * DIM
        for token in re.findall(r"\w+", text.lower()):
            bucket = int.from_bytes(hashlib.sha256(token.encode()).digest()[:4], "big") % DIM
            vec[bucket] += 1.0
        norm = math.sqrt(sum(x * x for x in vec))
        if norm == 0:
            vec[0] = 1.0
            return vec
        return [x / norm for x in vec]
