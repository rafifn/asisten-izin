from app.db import Conn
from app.llm.client import LlmUnavailable
from app.llm.fake import FakeLlm
from app.pipeline.schemas import (
    Activity,
    ActivitySelection,
    Attributes,
    Candidate,
    Pick,
    Selection,
    Understanding,
)
from app.pipeline.select import select_codes
from app.retrieval.embedder import FakeEmbedder
from app.retrieval.search import search_kbli


def cand(code: str) -> Candidate:
    return Candidate(code=code, title=f"Judul {code}", definition=f"Definisi {code}")


def cands(*codes: str) -> list[Candidate]:
    return [cand(c) for c in codes]


def understanding(*labels: str) -> Understanding:
    attrs = Attributes(
        packaged=True,
        served_on_site=False,
        has_seating=False,
        sells_online=None,
        animal_products=False,
        formal_restaurant=False,
    )
    return Understanding(
        activities=[Activity(label=lb, attributes=attrs) for lb in labels],
        size="mikro_kecil",
        scope="in",
        scope_note=None,
        kbli_2020_codes=[],
        questions=[],
    )


def one_activity() -> Understanding:
    return understanding("keripik")


def selection(
    primary: str, alts: tuple[str, ...] = (), label: str = "keripik", unsure: bool = False
) -> Selection:
    return Selection(
        activities=[
            ActivitySelection(
                activity_label=label,
                primary=Pick(code=primary, text="alasan"),
                alternatives=[Pick(code=a, text="pilih ini jika x") for a in alts],
            )
        ],
        unsure=unsure,
    )


def test_invented_code_retried_once_then_unsure() -> None:
    llm = FakeLlm([selection(primary="99999"), selection(primary="99998")])
    sel, results = select_codes(llm, one_activity(), {"keripik": cands("10791")})
    assert sel.unsure and sel.activities == [] and len(results) == 2


def test_retry_adds_allowed_codes_note() -> None:
    llm = FakeLlm([selection(primary="99999"), selection(primary="10791")])
    select_codes(llm, one_activity(), {"keripik": cands("10791", "10792")})
    first_system, second_system = llm.calls[0][0], llm.calls[1][0]
    assert second_system.startswith(first_system) and second_system != first_system
    assert "keripik" in second_system and "10791" in second_system and "10792" in second_system
    assert llm.calls[0][1] == llm.calls[1][1]


def test_invented_code_fixed_on_retry() -> None:
    llm = FakeLlm([selection(primary="99999"), selection(primary="10791")])
    sel, results = select_codes(llm, one_activity(), {"keripik": cands("10791")})
    assert sel.activities[0].primary.code == "10791" and not sel.unsure
    assert len(results) == 2


def test_alternatives_capped_at_two_and_exclude_primary() -> None:
    llm = FakeLlm([selection("10791", alts=("10791", "10792", "10793", "10794"))])
    sel, _ = select_codes(
        llm, one_activity(), {"keripik": cands("10791", "10792", "10793", "10794")}
    )
    assert [a.code for a in sel.activities[0].alternatives] == ["10792", "10793"]


def test_invalid_alternative_dropped_silently() -> None:
    llm = FakeLlm([selection("10791", alts=("99999", "10792"))])
    sel, results = select_codes(llm, one_activity(), {"keripik": cands("10791", "10792")})
    assert [a.code for a in sel.activities[0].alternatives] == ["10792"]
    assert len(results) == 1


def test_empty_candidates_returns_unsure() -> None:
    sel, results = select_codes(FakeLlm([]), one_activity(), {"keripik": []})
    assert sel.unsure and results == []


def test_refused_is_unsure() -> None:
    class Refusing(FakeLlm):
        def parse(self, system, user, schema, effort):  # type: ignore[no-untyped-def]
            r = super().parse(system, user, schema, effort)
            r.parsed, r.refused = None, True
            return r

    sel, results = select_codes(
        Refusing([selection("10791")]), one_activity(), {"keripik": cands("10791")}
    )
    assert sel.unsure and sel.activities == [] and len(results) == 1


def test_llm_unavailable_propagates() -> None:
    import pytest

    with pytest.raises(LlmUnavailable):
        select_codes(FakeLlm([LlmUnavailable("x")]), one_activity(), {"keripik": cands("10791")})


def test_effort_medium_and_schema() -> None:
    seen: list[str] = []

    class Spy(FakeLlm):
        def parse(self, system, user, schema, effort):  # type: ignore[no-untyped-def]
            seen.append(effort)
            return super().parse(system, user, schema, effort)

    select_codes(Spy([selection("10791")]), one_activity(), {"keripik": cands("10791")})
    assert seen == ["medium"]


def test_merged_activity_accepted_when_codes_in_union() -> None:
    u = understanding("keripik", "katering")
    llm = FakeLlm([selection("90002", label="keripik dan katering")])
    sel, results = select_codes(llm, u, {"keripik": cands("10791"), "katering": cands("90002")})
    assert sel.activities[0].primary.code == "90002" and len(results) == 1


def test_unmatched_label_with_code_outside_union_is_violation() -> None:
    u = understanding("keripik", "katering")
    llm = FakeLlm([selection("55555", label="lain"), selection("10791", label="keripik")])
    sel, results = select_codes(llm, u, {"keripik": cands("10791"), "katering": cands("90002")})
    assert sel.activities[0].primary.code == "10791" and len(results) == 2


def test_matching_label_code_must_be_in_that_activitys_candidates() -> None:
    u = understanding("keripik", "katering")
    llm = FakeLlm([selection("90002", label="keripik"), selection("90002", label="keripik")])
    sel, _ = select_codes(llm, u, {"keripik": cands("10791"), "katering": cands("90002")})
    assert sel.unsure


def test_prompt_lists_candidates_per_activity() -> None:
    llm = FakeLlm([selection("10791")])
    select_codes(llm, one_activity(), {"keripik": cands("10791", "10792")})
    user = llm.calls[0][1]
    assert "## Aktivitas: keripik" in user
    assert "- 10791: Judul 10791" in user and "- 10792: Judul 10792" in user
    assert "Definisi 10791" in user


def test_canned_llm_picks_first_candidate_per_activity(db: Conn, loaded_fixture: int) -> None:
    u = understanding("keripik", "katering")
    found = {
        "keripik": search_kbli(db, loaded_fixture, "keripik", FakeEmbedder()),
        "katering": search_kbli(db, loaded_fixture, "katering", FakeEmbedder()),
    }
    sel, _ = select_codes(FakeLlm.canned(), u, found)
    assert [(a.activity_label, a.primary.code) for a in sel.activities] == [
        ("keripik", found["keripik"][0].code),
        ("katering", found["katering"][0].code),
    ]
    assert not sel.unsure
