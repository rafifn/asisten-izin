from datetime import date
from uuid import uuid4

from app.evals.score import DataCodes, invented, score_kbli, score_permits
from app.pipeline.analyze import ActivityOut, AlternativeOut, PrimaryOut, Result
from app.pipeline.schemas import PermitItem, Source


def exp(primary: str, acceptable: list[str]) -> dict[str, object]:
    return {"primary": primary, "acceptable": acceptable}


def got(primary: str, alts: list[str] | None = None, label: str = "x") -> ActivityOut:
    return ActivityOut(
        label=label,
        primary=PrimaryOut(code=primary, title="t", definition="d", reason="r", risk_level=None),
        alternatives=[
            AlternativeOut(code=c, title="t", definition="d", when_to_choose="w", risk_level=None)
            for c in alts or []
        ],
    )


def permit(name: str, for_kbli: list[str] | None = None) -> PermitItem:
    return PermitItem(
        order=1,
        name=name,
        issuer="i",
        description="d",
        how_to="h",
        for_kbli=for_kbli or [],
        condition_note=None,
        regional_note=None,
        source=Source(regulation="r", article=None, url="https://example.go.id"),
        last_verified=date(2026, 11, 1),
    )


def result(activities: list[ActivityOut], permits: list[PermitItem]) -> Result:
    return Result(
        activities=activities,
        permits=permits,
        assumptions=[],
        scope_note=None,
        kbli_2020_mapping=None,
        data_as_of=date(2026, 11, 1),
        stale_warning=False,
        request_id=uuid4(),
    )


def test_top1_hit_when_primary_acceptable():
    assert score_kbli([exp("10792", ["10792"])], [got("10792")]) == {"top1": 1.0, "top3": 1.0}


def test_top1_hit_on_acceptable_alternative_code():
    assert score_kbli([exp("10792", ["10792", "10710"])], [got("10710")]) == {
        "top1": 1.0,
        "top3": 1.0,
    }


def test_top3_hit_on_alternative():
    assert score_kbli([exp("10791", ["10791"])], [got("10792", ["10791"])]) == {
        "top1": 0.0,
        "top3": 1.0,
    }


def test_complete_miss():
    assert score_kbli([exp("10791", ["10791"])], [got("10792", ["10710"])]) == {
        "top1": 0.0,
        "top3": 0.0,
    }


def test_missing_activity_counts_as_miss():
    scores = score_kbli(
        [exp("10792", ["10792"]), exp("56303", ["56303"])], [got("10792", label="a")]
    )
    assert scores == {"top1": 0.5, "top3": 0.5}


def test_no_got_activities_scores_zero():
    assert score_kbli([exp("10792", ["10792"])], []) == {"top1": 0.0, "top3": 0.0}


def test_one_got_activity_matches_only_one_expected():
    scores = score_kbli(
        [exp("10792", ["10792"]), exp("10792", ["10792"])], [got("10792", label="a")]
    )
    assert scores == {"top1": 0.5, "top3": 0.5}


def test_exact_primary_preferred_over_alternative_match():
    scores = score_kbli(
        [exp("10792", ["10792"])],
        [got("10710", ["10792"], label="a"), got("10792", label="b")],
    )
    assert scores == {"top1": 1.0, "top3": 1.0}


IDS = {"A name": "a", "B name": "b", "C name": "c"}


def pexp(primary: str, permits: dict[str, list[str]]) -> dict[str, object]:
    return {"primary": primary, "acceptable": list(permits), "permits": permits}


WARUNG = pexp("56101", {"56101": ["a", "b"], "56102": ["a", "c"]})


def test_permit_set_order_insensitive():
    items = [permit("B name"), permit("A name")]
    assert score_permits([WARUNG], [got("56101")], items, IDS)


def test_permit_check_uses_chosen_acceptable_alternative():
    # 56102 is acceptable; its own permit set is the expected one.
    assert score_permits([WARUNG], [got("56102")], [permit("A name"), permit("C name")], IDS)
    # ...and the primary's permit set no longer matches when 56102 was chosen.
    assert not score_permits([WARUNG], [got("56102")], [permit("A name"), permit("B name")], IDS)


def test_permit_check_fails_for_unacceptable_primary():
    items = [permit("A name"), permit("B name")]
    assert not score_permits([WARUNG], [got("10710", ["56101"])], items, IDS)


def test_permit_set_must_match_exactly():
    assert not score_permits([WARUNG], [got("56101")], [permit("A name")], IDS)
    assert not score_permits(
        [WARUNG], [got("56101")], [permit("A name"), permit("B name"), permit("C name")], IDS
    )


def test_permit_check_multi_activity_unions_and_rejects_extras():
    exp2 = [pexp("56101", {"56101": ["a", "b"]}), pexp("10710", {"10710": ["b", "c"]})]
    both = [got("10710", label="x"), got("56101", label="y")]
    assert score_permits(exp2, both, [permit(n) for n in IDS.keys()], IDS)
    assert not score_permits(exp2, both[:1], [permit("B name"), permit("C name")], IDS)
    assert not score_permits(
        [WARUNG], [got("56101"), got("10710", label="z")], [permit("A name"), permit("B name")], IDS
    )


def test_unknown_permit_name_never_matches():
    assert not score_permits([pexp("56101", {"56101": ["a"]})], [got("56101")], [permit("?")], IDS)


DATA = DataCodes(codes={"10792", "10710"}, permit_names={"NIB"})


def test_invented_empty_for_known_codes_and_permits():
    r = result([got("10792", ["10710"])], [permit("NIB", ["10792"])])
    assert invented(r, DATA) == []


def test_invented_detects_unknown_code():
    r = result([got("99999", ["10710"])], [])
    assert invented(r, DATA) == ["code:99999"]


def test_invented_detects_unknown_alternative_and_permit_and_for_kbli():
    r = result([got("10792", ["88888"])], [permit("Izin Palsu", ["77777"])])
    assert invented(r, DATA) == ["code:88888", "permit:Izin Palsu", "code:77777"]
