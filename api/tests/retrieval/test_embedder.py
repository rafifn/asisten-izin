from app.retrieval.embedder import FakeEmbedder


def test_fake_embedder_is_deterministic_and_normalized() -> None:
    v1, v2 = FakeEmbedder().embed(["keripik pisang", "keripik pisang"])
    assert v1 == v2
    assert len(v1) == 1024
    assert abs(sum(x * x for x in v1) - 1) < 1e-6


def test_fake_embedder_similar_texts_are_closer() -> None:
    a, b, c = FakeEmbedder().embed(["keripik pisang", "keripik singkong", "bir anggur"])

    def dot(x: list[float], y: list[float]) -> float:
        return sum(i * j for i, j in zip(x, y, strict=True))

    assert dot(a, b) > dot(a, c)


def test_importing_embedder_module_does_not_import_sentence_transformers() -> None:
    import sys

    import app.retrieval.embedder  # noqa: F401

    assert "sentence_transformers" not in sys.modules
