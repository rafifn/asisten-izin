import shutil
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import yaml

from app.data.loader import load_data
from app.db import Conn
from app.pipeline.schemas import Attributes
from app.retrieval.embedder import FakeEmbedder
from app.rules.engine import ATTR_LABELS, NEG_LABELS, lookup_permits, risk_for
from tests.fixtures.codes import FIXTURE_CATERING_CODE, FIXTURE_DRINK_CODE, FIXTURE_PACKAGED_CODE

TODAY = date(2026, 11, 23)
A = FIXTURE_PACKAGED_CODE  # nib + spp-irt (packaged)
B = FIXTURE_CATERING_CODE  # nib + slhs
C = FIXTURE_DRINK_CODE  # nib
FIXTURE_DIR = Path(__file__).parents[1] / "fixtures" / "data"
FR_NOTE_TRUE = "Berlaku jika usaha berbentuk restoran"
FR_NOTE_FALSE = "Berlaku jika bukan usaha berbentuk restoran"


def attrs(**kw: bool | None) -> Attributes:
    base: dict[str, bool | None] = dict.fromkeys(Attributes.model_fields)
    base.update(kw)
    return Attributes(**base)


def rule(
    code: str, permit: str, risk: str, order: int, conditions: dict[str, bool]
) -> dict[str, Any]:
    return {
        "kbli_code": code,
        "conditions": conditions,
        "risk_level": risk,
        "permit_id": permit,
        "step_order": order,
        "source_regulation": "PP 28 Tahun 2025",
        "source_url": "https://example.go.id/pp-28-2025",
        "valid_from": date(2025, 10, 5),
        "last_verified": date(2026, 11, 1),
    }


def load_variant(db: Conn, tmp_path: Path, extra_rules: list[dict[str, Any]]) -> int:
    d = tmp_path / "data"
    shutil.copytree(FIXTURE_DIR, d)
    rules = yaml.safe_load((d / "rules.yaml").read_text()) + extra_rules
    (d / "rules.yaml").write_text(yaml.safe_dump(rules))
    return load_data(db, d, FakeEmbedder())


def branching(db: Conn, tmp_path: Path, true_risk: str, false_risk: str) -> int:
    """Code C gets nib (rendah, unconditional) plus a formal_restaurant branch pair."""
    return load_variant(
        db,
        tmp_path,
        [
            rule(C, "slhs", true_risk, 2, {"formal_restaurant": True}),
            rule(C, "spp-irt", false_risk, 3, {"formal_restaurant": False}),
        ],
    )


def test_labels_cover_all_attributes() -> None:
    assert set(ATTR_LABELS) == set(Attributes.model_fields)


def test_neg_labels_cover_all_attributes() -> None:
    assert set(NEG_LABELS) == set(Attributes.model_fields)


def test_future_valid_from_ignored(db: Conn, tmp_path: Path) -> None:
    future = rule(B, "spp-irt", "tinggi", 3, {})
    future["valid_from"] = TODAY + timedelta(days=1)
    release = load_variant(db, tmp_path, [future])
    items, _ = lookup_permits(db, release, [(B, attrs())], TODAY)
    assert "SPP-IRT" not in {i.name for i in items}
    assert risk_for(db, release, B, attrs(), TODAY) == "menengah_rendah"
    items, _ = lookup_permits(db, release, [(B, attrs())], TODAY + timedelta(days=1))
    assert "SPP-IRT" in {i.name for i in items}


def test_merges_and_labels_shared_permit(db: Conn, loaded_fixture: int) -> None:
    items, _ = lookup_permits(db, loaded_fixture, [(A, attrs()), (B, attrs())], TODAY)
    nib = next(i for i in items if i.name == "NIB")
    assert nib.for_kbli == sorted([A, B]) and nib.order == 1
    assert nib.condition_note is None
    assert [i.order for i in items] == list(range(1, len(items) + 1))
    assert nib.source.regulation == "PP 28 Tahun 2025"


def test_order_is_min_step_then_name(db: Conn, loaded_fixture: int) -> None:
    items, _ = lookup_permits(db, loaded_fixture, [(A, attrs(packaged=True)), (B, attrs())], TODAY)
    # nib step 1; spp-irt (A, step 2) and slhs (B, step 2) tie -> by name
    assert [i.name for i in items] == ["NIB", "SLHS", "SPP-IRT"]


def test_unknown_attribute_includes_permit_with_note(db: Conn, loaded_fixture: int) -> None:
    items, _ = lookup_permits(db, loaded_fixture, [(A, attrs(packaged=None))], TODAY)
    spp = next(i for i in items if i.name == "SPP-IRT")
    assert spp.condition_note == "Berlaku jika produk dijual dalam kemasan"
    nib = next(i for i in items if i.name == "NIB")
    assert nib.condition_note is None


def test_true_attribute_includes_permit_without_note(db: Conn, loaded_fixture: int) -> None:
    items, _ = lookup_permits(db, loaded_fixture, [(A, attrs(packaged=True))], TODAY)
    spp = next(i for i in items if i.name == "SPP-IRT")
    assert spp.condition_note is None


def test_false_attribute_excludes_conditional_permit(db: Conn, loaded_fixture: int) -> None:
    items, _ = lookup_permits(db, loaded_fixture, [(A, attrs(packaged=False))], TODAY)
    assert "SPP-IRT" not in {i.name for i in items}


def test_regional_note_and_metadata_passed_through(db: Conn, loaded_fixture: int) -> None:
    items, _ = lookup_permits(db, loaded_fixture, [(B, attrs())], TODAY)
    slhs = next(i for i in items if i.name == "SLHS")
    assert slhs.regional_note and slhs.source.article == "Pasal 12"
    assert slhs.issuer and slhs.how_to and slhs.description


def test_unknown_code_gives_nothing(db: Conn, loaded_fixture: int) -> None:
    assert lookup_permits(db, loaded_fixture, [("00000", attrs())], TODAY) == ([], False)
    assert risk_for(db, loaded_fixture, "00000", attrs()) is None


def test_expired_rows_ignored(db: Conn, tmp_path: Path) -> None:
    expired = rule(B, "spp-irt", "tinggi", 3, {})
    expired["valid_to"] = TODAY
    ok = rule(B, "spp-irt", "rendah", 4, {"packaged": True})
    ok["valid_to"] = TODAY + timedelta(days=1)
    release = load_variant(db, tmp_path, [expired, ok])
    items, _ = lookup_permits(db, release, [(B, attrs(packaged=True))], TODAY)
    spp = next(i for i in items if i.name == "SPP-IRT")
    assert spp.order == 3  # NIB 1, SLHS 2, SPP-IRT (not step 3 rule - expired; step 4 rule)
    assert risk_for(db, release, B, attrs(packaged=True)) == "menengah_rendah"  # not tinggi


def test_expired_permit_ignored(db: Conn, tmp_path: Path) -> None:
    d = tmp_path / "data"
    shutil.copytree(FIXTURE_DIR, d)
    permits = yaml.safe_load((d / "permits.yaml").read_text())
    for p in permits:
        if p["id"] == "slhs":
            p["valid_to"] = TODAY
    (d / "permits.yaml").write_text(yaml.safe_dump(permits))
    release = load_data(db, d, FakeEmbedder())
    items, _ = lookup_permits(db, release, [(B, attrs())], TODAY)
    assert {i.name for i in items} == {"NIB"}


def _stale(db: Conn, tmp_path: Path, days: int) -> bool:
    d = tmp_path / "data"
    shutil.copytree(FIXTURE_DIR, d)
    permits = yaml.safe_load((d / "permits.yaml").read_text())
    for p in permits:
        p["last_verified"] = TODAY - timedelta(days=days)
    (d / "permits.yaml").write_text(yaml.safe_dump(permits))
    rules = yaml.safe_load((d / "rules.yaml").read_text())
    for r in rules:
        r["last_verified"] = TODAY - timedelta(days=days)
    (d / "rules.yaml").write_text(yaml.safe_dump(rules))
    release = load_data(db, d, FakeEmbedder())
    return lookup_permits(db, release, [(B, attrs())], TODAY)[1]


def test_stale_warning_after_183_days(db: Conn, tmp_path: Path, loaded_fixture: int) -> None:
    assert _stale(db, tmp_path / "x", 184) is True
    assert _stale(db, tmp_path / "y", 183) is False
    assert lookup_permits(db, loaded_fixture, [(B, attrs())], TODAY)[1] is False


def test_risk_is_highest_applicable(db: Conn, loaded_fixture: int, tmp_path: Path) -> None:
    assert risk_for(db, loaded_fixture, A, attrs(packaged=True)) == "rendah"
    assert risk_for(db, loaded_fixture, B, attrs()) == "menengah_rendah"
    release = load_variant(db, tmp_path, [rule(A, "slhs", "tinggi", 3, {"packaged": True})])
    assert risk_for(db, release, A, attrs(packaged=True)) == "tinggi"
    assert risk_for(db, release, A, attrs(packaged=False)) == "rendah"
    assert risk_for(db, release, A, attrs(packaged=None)) == "tinggi"


def test_branch_unknown_picks_higher_risk_branch(db: Conn, tmp_path: Path) -> None:
    release = branching(db, tmp_path, "menengah_tinggi", "menengah_rendah")
    a = attrs(formal_restaurant=None)
    assert risk_for(db, release, C, a, TODAY) == "menengah_tinggi"
    items, _ = lookup_permits(db, release, [(C, a)], TODAY)
    by_name = {i.name: i for i in items}
    assert set(by_name) == {"NIB", "SLHS"}  # no permit that exists only in the false branch
    assert by_name["SLHS"].condition_note == FR_NOTE_TRUE
    assert by_name["NIB"].condition_note is None


def test_branch_unknown_picks_false_when_higher(db: Conn, tmp_path: Path) -> None:
    release = branching(db, tmp_path, "menengah_rendah", "menengah_tinggi")
    a = attrs(formal_restaurant=None)
    assert risk_for(db, release, C, a, TODAY) == "menengah_tinggi"
    items, _ = lookup_permits(db, release, [(C, a)], TODAY)
    by_name = {i.name: i for i in items}
    assert set(by_name) == {"NIB", "SPP-IRT"}
    assert by_name["SPP-IRT"].condition_note == FR_NOTE_FALSE


def test_branch_tie_chooses_true(db: Conn, tmp_path: Path) -> None:
    release = branching(db, tmp_path, "menengah_rendah", "menengah_rendah")
    items, _ = lookup_permits(db, release, [(C, attrs())], TODAY)
    assert {i.name for i in items} == {"NIB", "SLHS"}


def test_branch_attribute_true_uses_only_true_branch(db: Conn, tmp_path: Path) -> None:
    release = branching(db, tmp_path, "menengah_rendah", "menengah_tinggi")
    a = attrs(formal_restaurant=True)
    assert risk_for(db, release, C, a, TODAY) == "menengah_rendah"
    items, _ = lookup_permits(db, release, [(C, a)], TODAY)
    assert {i.name for i in items} == {"NIB", "SLHS"}
    assert all(i.condition_note is None for i in items)


def test_branch_attribute_false_uses_only_false_branch(db: Conn, tmp_path: Path) -> None:
    release = branching(db, tmp_path, "menengah_tinggi", "menengah_rendah")
    a = attrs(formal_restaurant=False)
    assert risk_for(db, release, C, a, TODAY) == "menengah_rendah"
    items, _ = lookup_permits(db, release, [(C, a)], TODAY)
    assert {i.name for i in items} == {"NIB", "SPP-IRT"}
    assert all(i.condition_note is None for i in items)


def test_branch_permit_also_unconditional_has_no_note(db: Conn, tmp_path: Path) -> None:
    release = load_variant(
        db,
        tmp_path,
        [
            rule(C, "slhs", "rendah", 2, {}),
            rule(C, "slhs", "menengah_tinggi", 2, {"formal_restaurant": True}),
            rule(C, "spp-irt", "rendah", 3, {"formal_restaurant": False}),
        ],
    )
    items, _ = lookup_permits(db, release, [(C, attrs())], TODAY)
    by_name = {i.name: i for i in items}
    assert set(by_name) == {"NIB", "SLHS"}
    assert by_name["SLHS"].condition_note is None
