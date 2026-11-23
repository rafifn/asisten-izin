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


def test_permit_set_order_insensitive():
    ids = {"A name": "a", "B name": "b"}
    assert score_permits(["b", "a"], [permit("A name"), permit("B name")], ids)
    assert score_permits(["a", "b"], [permit("B name"), permit("A name")], ids)


def test_permit_set_must_match_exactly():
    ids = {"A name": "a", "B name": "b"}
    assert not score_permits(["a"], [permit("A name"), permit("B name")], ids)
    assert not score_permits(["a", "b"], [permit("A name")], ids)
    assert score_permits([], [], ids)


def test_unknown_permit_name_never_matches():
    assert not score_permits(["a"], [permit("Mystery")], {"A name": "a"})


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
