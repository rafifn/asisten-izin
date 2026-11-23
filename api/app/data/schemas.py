import re
from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

# Mirrors the `Attributes` model; the only keys allowed in a rule's `conditions`.
ALLOWED_ATTRIBUTES = (
    "packaged",
    "served_on_site",
    "has_seating",
    "sells_online",
    "animal_products",
    "formal_restaurant",  # usaha berbentuk restoran (vs warung/rumah makan/kedai); R8
)

KbliCode = Annotated[str, StringConstraints(pattern=r"^\d{5}$")]
NonEmpty = Annotated[str, StringConstraints(min_length=1)]


class _Row(BaseModel):
    model_config = ConfigDict(extra="forbid")


class KbliScopeRow(_Row):
    code: KbliCode
    title: NonEmpty
    definition: NonEmpty
    in_scope: bool


class Kbli2020MapRow(_Row):
    code_2020: Annotated[str, StringConstraints(pattern=r"^\d{5}$")]
    code_2025: list[KbliCode]


class PermitRow(_Row):
    id: Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")]
    name: NonEmpty
    issuer: NonEmpty
    description: NonEmpty
    how_to: NonEmpty
    source_regulation: NonEmpty
    source_article: str | None = None
    source_url: NonEmpty
    valid_from: date
    valid_to: date | None = None
    last_verified: date
    regional_note: str | None = None


class RuleRow(_Row):
    kbli_code: KbliCode
    conditions: dict[str, bool]
    risk_level: Literal["rendah", "menengah_rendah", "menengah_tinggi", "tinggi"]
    permit_id: NonEmpty
    step_order: int
    source_regulation: NonEmpty
    source_url: NonEmpty
    valid_from: date
    valid_to: date | None = None
    last_verified: date

    @field_validator("conditions")
    @classmethod
    def _known_attributes(cls, v: dict[str, bool]) -> dict[str, bool]:
        for key in v:
            if key not in ALLOWED_ATTRIBUTES:
                raise ValueError(f"unknown attribute {key}")
        return v


_ = re  # keep import used for patterns documented above
