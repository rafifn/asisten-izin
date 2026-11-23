from app.db import Conn
from app.retrieval.embedder import FakeEmbedder
from app.retrieval.search import map_2020_codes, search_kbli
from tests.fixtures.codes import (
    FIXTURE_CATERING_CODE,
    FIXTURE_DRINK_CODE,
    FIXTURE_OUT_OF_SCOPE_CODE,
    FIXTURE_OUT_OF_SCOPE_TITLE,
    FIXTURE_PACKAGED_CODE,
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
    assert FIXTURE_DRINK_CODE in {c.code for c in result}


def test_out_of_scope_extra_code_ignored(db: Conn, loaded_fixture: int) -> None:
    result = search_kbli(
        db, loaded_fixture, "zzz", FakeEmbedder(), extra_codes=[FIXTURE_OUT_OF_SCOPE_CODE]
    )
    assert FIXTURE_OUT_OF_SCOPE_CODE not in {c.code for c in result}


def test_limit_and_no_duplicates(db: Conn, loaded_fixture: int) -> None:
    result = search_kbli(
        db, loaded_fixture, "keripik", FakeEmbedder(), extra_codes=[FIXTURE_PACKAGED_CODE], limit=2
    )
    codes = [c.code for c in result]
    assert len(codes) == len(set(codes)) == 2


def test_vector_only_match_still_returned(db: Conn, loaded_fixture: int) -> None:
    assert search_kbli(db, loaded_fixture, "zzz", FakeEmbedder())


def test_map_2020_codes(db: Conn, loaded_fixture: int) -> None:
    assert map_2020_codes(db, loaded_fixture, ["11051", "10794", "00000"]) == [
        "90001",
        "90003",
    ]  # 90004 is out of scope; unknown 2020 code maps to nothing
