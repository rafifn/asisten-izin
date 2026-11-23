import pytest
from pydantic import ValidationError

from app.data.schemas import RuleRow

BASE = {
    "kbli_code": "56101",
    "risk_level": "menengah_tinggi",
    "permit_id": "nib",
    "step_order": 3,
    "source_regulation": "PP 28 Tahun 2025",
    "source_url": "https://example.go.id",
    "valid_from": "2026-06-15",
    "last_verified": "2026-11-23",
}


def test_formal_restaurant_is_an_allowed_condition() -> None:
    row = RuleRow.model_validate(BASE | {"conditions": {"formal_restaurant": True}})
    assert row.conditions == {"formal_restaurant": True}


def test_unknown_condition_still_rejected() -> None:
    with pytest.raises(ValidationError, match="unknown attribute restaurant"):
        RuleRow.model_validate(BASE | {"conditions": {"restaurant": True}})
