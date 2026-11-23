"""Scoring for the eval set: KBLI top-1/top-3, permit exact match, invented items."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from app.pipeline.analyze import ActivityOut, Result
from app.pipeline.schemas import PermitItem


@dataclass(frozen=True)
class DataCodes:
    """Codes and permit names present in the loaded data release."""

    codes: set[str]
    permit_names: set[str]


def _acceptable(expected: Mapping[str, Any]) -> set[str]:
    return {str(expected["primary"]), *map(str, expected.get("acceptable", []))}


def score_kbli(
    expected_activities: Sequence[Mapping[str, Any]], got_activities: Sequence[ActivityOut]
) -> dict[str, float]:
    """Fraction of expected activities hit as primary (top1) / primary-or-alternative (top3).

    Each expected activity is matched to one got activity (each got activity at most once),
    preferring one whose primary is acceptable. An expected activity with no match is a miss.
    """
    if not expected_activities:
        raise ValueError("score_kbli needs at least one expected activity")
    unused = list(got_activities)
    top1 = top3 = 0
    for exp in expected_activities:
        ok = _acceptable(exp)
        primary_match = next((g for g in unused if g.primary.code in ok), None)
        if primary_match is not None:
            unused.remove(primary_match)
            top1 += 1
            top3 += 1
            continue
        alt_match = next((g for g in unused if any(a.code in ok for a in g.alternatives)), None)
        if alt_match is not None:
            unused.remove(alt_match)
            top3 += 1
    n = len(expected_activities)
    return {"top1": top1 / n, "top3": top3 / n}


def match_primaries(
    expected_activities: Sequence[Mapping[str, Any]], got_activities: Sequence[ActivityOut]
) -> list[ActivityOut | None]:
    """For each expected activity, the (unused) got activity whose primary is acceptable."""
    unused = list(got_activities)
    matched: list[ActivityOut | None] = []
    for exp in expected_activities:
        ok = _acceptable(exp)
        hit = next((g for g in unused if g.primary.code in ok), None)
        if hit is not None:
            unused.remove(hit)
        matched.append(hit)
    return matched


def score_permits(
    expected_activities: Sequence[Mapping[str, Any]],
    got_activities: Sequence[ActivityOut],
    got_items: Sequence[PermitItem],
    name_to_id: Mapping[str, str],
) -> bool:
    """Exact set equality of permit ids, for the primaries the system actually chose.

    Each expected activity stores its permits per acceptable code. The expected set is the
    union of those for the chosen primaries. Every chosen primary must be acceptable for a
    distinct expected activity (no misses, no extra activities), otherwise the check fails.
    Items are identified by name (the API has no id).
    """
    matched = match_primaries(expected_activities, got_activities)
    if any(m is None for m in matched) or len(got_activities) != len(expected_activities):
        return False
    want: set[str] = set()
    for exp, m in zip(expected_activities, matched, strict=True):
        assert m is not None
        want |= set(exp["permits"][m.primary.code])
    got = {name_to_id.get(i.name, f"?{i.name}") for i in got_items}
    return got == want


def invented(got: Result, data: DataCodes) -> list[str]:
    """KBLI codes or permits in the result that are not in the data release (must be empty)."""
    found: list[str] = []
    for a in got.activities:
        for code in [a.primary.code, *(alt.code for alt in a.alternatives)]:
            if code not in data.codes:
                found.append(f"code:{code}")
    for p in got.permits:
        if p.name not in data.permit_names:
            found.append(f"permit:{p.name}")
        found.extend(f"code:{c}" for c in p.for_kbli if c not in data.codes)
    return found
