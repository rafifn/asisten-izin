from datetime import date
from typing import Literal

from pydantic import BaseModel

Attr = bool | None  # None = unknown


class Attributes(BaseModel):
    packaged: Attr
    served_on_site: Attr
    has_seating: Attr
    sells_online: Attr
    animal_products: Attr
    formal_restaurant: Attr  # usaha berbentuk restoran (vs warung/rumah makan/kedai)


class Activity(BaseModel):
    label: str
    attributes: Attributes


class Question(BaseModel):
    id: str
    text: str
    options: list[str]


class Understanding(BaseModel):
    activities: list[Activity]
    size: Literal["mikro_kecil", "menengah_besar", "unknown"]
    scope: Literal["in", "partial", "out"]
    scope_note: str | None
    kbli_2020_codes: list[str]
    questions: list[Question]  # max 2


class Candidate(BaseModel):
    code: str
    title: str
    definition: str


class Pick(BaseModel):
    code: str
    text: str  # reason (primary) or when_to_choose (alt)


class ActivitySelection(BaseModel):
    activity_label: str
    primary: Pick
    alternatives: list[Pick]  # max 2


class Selection(BaseModel):
    activities: list[ActivitySelection]
    unsure: bool


class Source(BaseModel):
    regulation: str
    article: str | None
    url: str


class PermitItem(BaseModel):
    order: int
    name: str
    issuer: str
    description: str
    how_to: str
    for_kbli: list[str]
    condition_note: str | None
    regional_note: str | None
    source: Source
    last_verified: date
