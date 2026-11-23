import re

from pgvector import Vector

from app.db import Conn
from app.pipeline.schemas import Candidate
from app.retrieval.embedder import Embedder

RRF_K = 60
_POOL = 50  # rows taken from each ranking before merging
_MAX_TERMS = 64
_WORD = re.compile(r"[^\W_]+")  # letters and digits only: nothing tsquery could parse as syntax

_KEYWORD_SQL = """
select code from (
    select code,
           greatest(ts_rank(search_tsv, to_tsquery('simple', %(tsq)s)),
                    similarity(title, %(q)s)) as score
    from kbli
    where data_release_id = %(rel)s and in_scope
) s
where score > 0
order by score desc, code
limit %(pool)s
"""

_VECTOR_SQL = """
select code from kbli
where data_release_id = %(rel)s and in_scope and embedding is not null
order by embedding <=> %(vec)s, code
limit %(pool)s
"""


def or_tsquery(query: str) -> str | None:
    """`w1 | w2 | ...` over the query's words (lowercased, unique), for `to_tsquery('simple')`.

    OR, not AND: a user's description has many words that never appear in a KBLI text, and
    `plainto_tsquery` (AND) then matches nothing. Only letters and digits survive, so no input
    can inject tsquery operators. None (SQL NULL, ignored by `greatest`) if there are no words.
    """
    words = list(dict.fromkeys(w.lower() for w in _WORD.findall(query)))[:_MAX_TERMS]
    return " | ".join(words) or None


def search_kbli(
    conn: Conn,
    release_id: int,
    query: str,
    embedder: Embedder,
    extra_codes: list[str] | None = None,
    limit: int = 20,
) -> list[Candidate]:
    """Hybrid search over in-scope KBLI rows of one release.

    Keyword rank orders by the greater of ts_rank (OR over the query words) and trigram
    similarity; vector rank
    orders by cosine distance; the two are merged with reciprocal rank fusion (k=60).
    In-scope `extra_codes` are pinned; the rest of the `limit` slots are filled in RRF order.
    """
    keyword = [
        r[0]
        for r in conn.execute(
            _KEYWORD_SQL,
            {"q": query, "tsq": or_tsquery(query), "rel": release_id, "pool": _POOL},
        )
    ]
    vec = Vector(embedder.embed([query])[0])
    vector = [
        r[0] for r in conn.execute(_VECTOR_SQL, {"vec": vec, "rel": release_id, "pool": _POOL})
    ]

    scores: dict[str, float] = {}
    for ranking in (keyword, vector):
        for rank, code in enumerate(ranking, start=1):
            scores[code] = scores.get(code, 0.0) + 1.0 / (RRF_K + rank)
    in_scope_extras = [
        r[0]
        for r in conn.execute(
            "select code from kbli where data_release_id = %s and in_scope and code = any(%s)",
            [release_id, list(extra_codes or [])],
        )
    ]
    pinned = [c for c in dict.fromkeys(extra_codes or []) if c in set(in_scope_extras)][:limit]
    ranked = [c for c in sorted(scores, key=lambda c: (-scores[c], c)) if c not in pinned]
    ordered = pinned + ranked[: limit - len(pinned)]

    rows = conn.execute(
        "select code, title, definition from kbli"
        " where data_release_id = %s and in_scope and code = any(%s)",
        [release_id, ordered],
    ).fetchall()
    by_code = {r[0]: Candidate(code=r[0], title=r[1], definition=r[2]) for r in rows}
    return [by_code[c] for c in ordered if c in by_code]


def map_2020_codes(conn: Conn, release_id: int, codes: list[str]) -> list[str]:
    """Map KBLI 2020 codes to in-scope KBLI 2025 codes (sorted, unique)."""
    rows = conn.execute(
        "select distinct m.code_2025 from kbli_2020_map m"
        " join kbli k on k.code = m.code_2025 and k.data_release_id = m.data_release_id"
        " where m.data_release_id = %s and m.code_2020 = any(%s) and k.in_scope"
        " order by m.code_2025",
        [release_id, codes],
    )
    return [r[0] for r in rows]
