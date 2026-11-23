import re
from typing import Any, Literal, cast

from pydantic import BaseModel

from app.llm.client import MODEL, LlmResult
from app.pipeline.schemas import (
    Activity,
    ActivitySelection,
    Attributes,
    Pick,
    Selection,
    Understanding,
)

_SECTION = re.compile(r"^## Aktivitas: (.+)$", re.MULTILINE)
_CANDIDATE = re.compile(r"^- (\d{5}): ", re.MULTILINE)


def _canned_understanding() -> Understanding:
    attrs = Attributes(
        packaged=True,
        served_on_site=True,
        has_seating=True,
        sells_online=True,
        animal_products=True,
        formal_restaurant=True,
    )
    return Understanding(
        activities=[Activity(label="usaha kuliner", attributes=attrs)],
        size="mikro_kecil",
        scope="in",
        scope_note=None,
        kbli_2020_codes=[],
        questions=[],
    )


def _canned_selection(user: str) -> Selection:
    sections = _SECTION.split(user)  # [preamble, label1, body1, label2, body2, ...]
    activities = []
    for label, body in zip(sections[1::2], sections[2::2], strict=True):
        m = _CANDIDATE.search(body)
        if m:
            activities.append(
                ActivitySelection(
                    activity_label=label.strip(),
                    primary=Pick(code=m.group(1), text="Contoh alasan."),
                    alternatives=[],
                )
            )
    return Selection(activities=activities, unsure=False)


class FakeLlm:
    def __init__(self, responses: list[BaseModel | Exception] | None = None) -> None:
        self._responses = list(responses or [])
        self.calls: list[tuple[str, str, type]] = []

    @classmethod
    def canned(cls) -> "FakeLlm":
        return _CannedLlm()

    def parse[T: BaseModel](
        self,
        system: str,
        user: str,
        schema: type[T],
        effort: Literal["low", "medium", "high"],
    ) -> LlmResult[T]:
        self.calls.append((system, user, schema))
        item = self._next(schema, user)
        if isinstance(item, Exception):
            raise item
        return LlmResult(
            parsed=cast(T, item), refused=False, tokens_in=0, tokens_out=0, model=MODEL
        )

    def _next(self, schema: type[Any], user: str) -> BaseModel | Exception:
        return self._responses.pop(0)


class _CannedLlm(FakeLlm):
    def _next(self, schema: type[Any], user: str) -> BaseModel | Exception:
        if schema is Understanding:
            return _canned_understanding()
        if schema is Selection:
            return _canned_selection(user)
        raise ValueError(f"no canned response for {schema.__name__}")
