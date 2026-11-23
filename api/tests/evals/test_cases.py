from collections import Counter
from datetime import date

import yaml

from app.data.loader import current_release_id, load_data
from app.db import Conn
from app.evals.cases import CASES_PATH, DATA_DIR, load_cases
from app.evals.expected import compute_expected, review_markdown
from app.retrieval.embedder import FakeEmbedder


def _scope() -> dict[str, bool]:
    raw = yaml.safe_load((DATA_DIR / "kbli_scope.yaml").read_text(encoding="utf-8"))
    return {k["code"]: k["in_scope"] for k in raw}


def test_cases_load_with_unique_ids():
    cases = load_cases()
    assert len(cases) >= 50
    assert len({c.id for c in cases}) == len(cases)


def test_expected_codes_exist_and_are_in_scope():
    scope = _scope()
    for case in load_cases():
        for a in case.expect.activities:
            for code in a.acceptable:
                assert scope.get(code) is True, f"{case.id}: {code} missing or not in scope"


def test_case_mix():
    kinds = Counter(c.id.split("-")[0] for c in load_cases())
    assert kinds["multi"] == 5
    assert kinds["partial"] == 5
    assert kinds["out"] == 5
    assert kinds["vague"] == 3
    assert kinds["old"] == 2
    assert kinds["single"] >= 30


def test_scope_and_expectations_are_consistent():
    for case in load_cases():
        e = case.expect
        if e.scope == "out":
            assert not e.activities, case.id
        if e.clarify:
            assert not e.activities, case.id
        if e.activities:
            for a in e.activities:
                assert a.permits and a.risk, f"{case.id}: not generated (run make eval-gen)"


def test_committed_expected_permits_and_risk_match_the_engine(db: Conn):
    release = load_data(db, DATA_DIR, FakeEmbedder())
    assert release == current_release_id(db)
    today = date(2026, 11, 23)
    for case in load_cases(CASES_PATH):
        computed = compute_expected(db, release, case, today)
        if computed is None:
            continue
        for act, (permits, risk) in zip(case.expect.activities, computed, strict=True):
            assert act.permits == permits, case.id
            assert act.risk == risk, case.id


def test_review_lists_every_case_with_titles():
    cases = load_cases()
    text = review_markdown(cases)
    for c in cases:
        assert f"| {c.id} |" in text
    assert "Aktivitas Penyediaan Makanan di Bangunan Tetap" in text


def test_attributes_are_null_unless_the_description_states_them():
    # Spot checks of the null-by-default rule (review round 1).
    by_id = {c.id: c for c in load_cases()}
    warung = by_id["single-warung-02"].expect.activities[0].attributes
    assert warung.animal_products is None
    p1 = by_id["partial-01"].expect.activities[0].attributes
    assert p1.has_seating is None and p1.served_on_site is None
    assert by_id["single-coklat-01"].expect.activities[0].attributes.animal_products is None


def test_widened_acceptable_codes_each_have_their_own_permits():
    act = {c.id: c for c in load_cases()}["single-warung-02"].expect.activities[0]
    assert act.permits is not None
    assert act.permits["56101"] != act.permits["56102"]
