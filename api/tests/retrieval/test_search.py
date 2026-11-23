from app.db import Conn
from app.retrieval.embedder import FakeEmbedder
from app.retrieval.search import map_2020_codes, search_kbli
from tests.fixtures.codes import (
    FIXTURE_CATERING_CODE,
    FIXTURE_DRINK_CODE,
    FIXTURE_OUT_OF_SCOPE_CODE,
    FIXTURE_OUT_OF_SCOPE_TITLE,
)


def test_keyword_match_ranks_first(db: Conn, loaded_fixture: int) -> None:
    result = search_kbli(db, loaded_fixture, "katering", FakeEmbedder())
    assert result[0].code == FIXTURE_CATERING_CODE
    assert result[0].title and result[0].definition


def test_out_of_scope_codes_never_returned(db: Conn, loaded_fixture: int) -> None:
    result = search_kbli(db, loaded_fixture, FIXTURE_OUT_OF_SCOPE_TITLE, FakeEmbedder())
    assert FIXTURE_OUT_OF_SCOPE_CODE not in {c.code for c in result}


def test_extra_codes_included(db: Conn, loaded_fixture: int) -> None:
    result = search_kbli(
        db, loaded_fixture, "zzz", FakeEmbedder(), extra_codes=[FIXTURE_DRINK_CODE], limit=1
    )
    assert [c.code for c in result] == [FIXTURE_DRINK_CODE]


def test_extras_never_exceed_limit(db: Conn, loaded_fixture: int) -> None:
    result = search_kbli(
        db, loaded_fixture, "katering", FakeEmbedder(), extra_codes=[FIXTURE_DRINK_CODE], limit=2
    )
    codes = [c.code for c in result]
    assert len(codes) <= 2 and FIXTURE_DRINK_CODE in codes
    assert FIXTURE_CATERING_CODE in codes  # remaining slot filled in RRF order


def test_out_of_scope_extra_code_ignored(db: Conn, loaded_fixture: int) -> None:
    result = search_kbli(
        db, loaded_fixture, "zzz", FakeEmbedder(), extra_codes=[FIXTURE_OUT_OF_SCOPE_CODE]
    )
    assert FIXTURE_OUT_OF_SCOPE_CODE not in {c.code for c in result}


def test_limit_and_no_duplicates(db: Conn, loaded_fixture: int) -> None:
    # "katering" ranks 90002 first; the extra 90003 would rank outside a limit of 1
    result = search_kbli(
        db,
        loaded_fixture,
        "katering",
        FakeEmbedder(),
        extra_codes=[FIXTURE_DRINK_CODE] * 2,
        limit=1,
    )
    assert [c.code for c in result] == [FIXTURE_DRINK_CODE]


def test_partial_multiword_query_still_matches(db: Conn, loaded_fixture: int) -> None:
    result = search_kbli(db, loaded_fixture, "katering pernikahan xyz", FakeEmbedder())
    assert result[0].code == FIXTURE_CATERING_CODE


def test_vector_only_match_still_returned(db: Conn, loaded_fixture: int) -> None:
    assert search_kbli(db, loaded_fixture, "zzz", FakeEmbedder())


def test_map_2020_codes(db: Conn, loaded_fixture: int) -> None:
    assert map_2020_codes(db, loaded_fixture, ["11051", "10794", "00000"]) == [
        "90001",
        "90003",
    ]  # 90004 is out of scope; unknown 2020 code maps to nothing


LONG_QUERY = "saya punya usaha katering rumahan untuk acara pernikahan dan ulang tahun di kampung"


def test_or_tsquery_sanitises_words() -> None:
    from app.retrieval.search import or_tsquery

    assert or_tsquery("Katering katering, kue!") == "katering | kue"
    assert or_tsquery("a' | !b & c:* (d) <-> e_f") == "a | b | c | d | e | f"
    assert or_tsquery("!!! ''") is None


def test_long_query_with_absent_words_gets_a_text_rank(db: Conn, loaded_fixture: int) -> None:
    from app.retrieval.search import or_tsquery

    row = db.execute(
        "select search_tsv @@ plainto_tsquery('simple', %(q)s),"
        " search_tsv @@ to_tsquery('simple', %(tsq)s),"
        " ts_rank(search_tsv, to_tsquery('simple', %(tsq)s))"
        " from kbli where data_release_id = %(rel)s and code = %(code)s",
        {"q": LONG_QUERY, "tsq": or_tsquery(LONG_QUERY), "rel": loaded_fixture,
         "code": FIXTURE_CATERING_CODE},
    ).fetchone()  # fmt: skip
    assert row is not None
    assert row[0] is False  # the old AND query (plainto_tsquery) does not match
    assert row[1] is True and row[2] > 0
    assert search_kbli(db, loaded_fixture, LONG_QUERY, FakeEmbedder())[0].code == (
        FIXTURE_CATERING_CODE
    )


def test_tsquery_special_characters_do_not_break_search(db: Conn, loaded_fixture: int) -> None:
    for q in ["katering' | !", "&&& ::: <->", "!!!", "(katering"]:
        search_kbli(db, loaded_fixture, q, FakeEmbedder())
