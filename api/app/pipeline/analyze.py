"""Request pipeline (design section 6.3): redact, understand, retrieve, select, rules, log."""

import logging
import time
from datetime import date
from typing import Annotated, Literal
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb
from pydantic import BaseModel, Field

from app.data.loader import current_release_id
from app.db import Conn
from app.errors import ApiError
from app.llm.client import LlmResult, LlmUnavailable
from app.pipeline.redact import redact
from app.pipeline.schemas import (
    Activity,
    Attributes,
    Candidate,
    PermitItem,
    Question,
    Selection,
    Understanding,
)
from app.pipeline.select import select_codes
from app.pipeline.understand import UnderstandRefused, understand
from app.retrieval.embedder import Embedder
from app.retrieval.search import map_2020_codes, search_kbli
from app.rules.engine import lookup_permits, risk_for

log = logging.getLogger(__name__)

OUT_OF_SCOPE_MESSAGE = (
    "Maaf, jenis usaha ini belum didukung. "
    "Saat ini kami baru membantu usaha kuliner mikro dan kecil."
)
UNSURE_NOTE = (
    "Kami belum yakin kode KBLI yang tepat. "
    "Coba ceritakan lebih rinci apa yang kamu jual dan bagaimana menjualnya."
)
REFUSED_MESSAGE = "Deskripsi ini tidak dapat diproses. Coba tulis ulang dengan kata lain."
LLM_UNAVAILABLE_MESSAGE = (
    "Layanan analisis sedang sibuk atau tidak tersedia. Silakan coba lagi beberapa saat lagi."
)
INTERNAL_MESSAGE = "Terjadi kesalahan pada server. Silakan coba lagi nanti."
MICRO_ASSUMPTION = "Dianggap usaha mikro/kecil"


class PrimaryOut(BaseModel):
    code: str
    title: str
    definition: str
    reason: str
    risk_level: str | None


class AlternativeOut(BaseModel):
    code: str
    title: str
    definition: str
    when_to_choose: str
    risk_level: str | None


class ActivityOut(BaseModel):
    label: str
    primary: PrimaryOut
    alternatives: list[AlternativeOut]


class Kbli2020Mapping(BaseModel):
    from_: str = Field(alias="from")
    to: list[str]


class Result(BaseModel):
    activities: list[ActivityOut]
    permits: list[PermitItem]
    assumptions: list[str]
    scope_note: str | None
    kbli_2020_mapping: list[Kbli2020Mapping] | None
    data_as_of: date
    stale_warning: bool
    request_id: UUID


class NeedsClarification(BaseModel):
    status: Literal["needs_clarification"] = "needs_clarification"
    request_id: UUID
    questions: list[Question]


class OutOfScope(BaseModel):
    status: Literal["out_of_scope"] = "out_of_scope"
    request_id: UUID
    message: str


class Ok(BaseModel):
    status: Literal["ok"] = "ok"
    request_id: UUID
    result: Result


AnalyzeResponse = Annotated[NeedsClarification | OutOfScope | Ok, Field(discriminator="status")]


def attrs_for(label: str, activities: list[Activity]) -> Attributes:
    """Attributes of the understood activity with this label.

    A selected activity whose label matches none (a merge or relabel) gets the combination
    over all understood activities: per field True if any is True, else None if any is
    None, else False.
    """
    for a in activities:
        if a.label == label:
            return a.attributes
    combined: dict[str, bool | None] = {}
    for field in Attributes.model_fields:
        values = [getattr(a.attributes, field) for a in activities]
        combined[field] = True if True in values else (None if None in values else False)
    return Attributes.model_validate(combined)


class _Log:
    """Accumulates what `query_log` needs; written exactly once per request."""

    def __init__(self, description: str, answers: dict[str, str] | None) -> None:
        self.description = description
        self.answers = answers
        self.started = time.perf_counter()
        self.request_id = uuid4()
        self.release_id: int | None = None
        self.selected: list[dict[str, object]] = []
        self.understanding: Understanding | None = None
        self.llm_results: list[LlmResult[Understanding] | LlmResult[Selection]] = []

    def _attributes(self) -> dict[str, object]:
        assert self.understanding is not None
        return {
            **self.understanding.model_dump(mode="json"),
            "selected_activities": self.selected,
        }

    def write(self, conn: Conn, output: BaseModel | dict[str, object]) -> None:
        out = output if isinstance(output, dict) else output.model_dump(mode="json", by_alias=True)
        model = self.llm_results[0].model if self.llm_results else None
        conn.execute(
            "insert into query_log (request_uuid, input, attributes, clarifications, output,"
            " data_release_id,"
            " model, tokens_in, tokens_out, cost_usd, latency_ms)"
            " values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            [
                self.request_id,
                self.description,
                Jsonb(self._attributes()) if self.understanding else None,
                Jsonb(self.answers) if self.answers is not None else None,
                Jsonb(out),
                self.release_id,
                model,
                sum(r.tokens_in for r in self.llm_results),
                sum(r.tokens_out for r in self.llm_results),
                round(sum(r.cost_usd for r in self.llm_results), 6),
                int((time.perf_counter() - self.started) * 1000),
            ],
        )


def _data_as_of(conn: Conn, release_id: int, permits: list[PermitItem]) -> date:
    """Oldest `last_verified` among the permits shown (agrees with stale_warning);
    the release date if there are none."""
    if permits:
        return min(p.last_verified for p in permits)
    row = conn.execute("select created_at::date from data_release where id = %s", [release_id])
    found = row.fetchone()
    assert found is not None
    return found[0]  # type: ignore[no-any-return]


def analyze(
    conn: Conn,
    llm: object,
    embedder: Embedder,
    description: str,
    answers: dict[str, str] | None,
    today: date,
) -> NeedsClarification | OutOfScope | Ok:
    """Run the pipeline and log the request. Raises ApiError (after logging) on failure."""
    entry = _Log(
        redact(description),
        None if answers is None else {k: redact(v) for k, v in answers.items()},
    )
    try:
        # A savepoint, so a failed statement cannot poison the connection before we log.
        with conn.transaction():
            return _run(conn, llm, embedder, entry, today)
    except UnderstandRefused:
        entry.write(conn, {"error": "refused"})
        raise ApiError(400, "invalid_input", REFUSED_MESSAGE) from None
    except LlmUnavailable:
        log.warning("llm unavailable", exc_info=True)
        entry.write(conn, {"error": "llm_unavailable"})
        raise ApiError(503, "llm_unavailable", LLM_UNAVAILABLE_MESSAGE) from None
    except Exception:
        log.exception("analyze failed")
        entry.write(conn, {"error": "internal"})
        raise ApiError(500, "internal", INTERNAL_MESSAGE) from None


def _run(
    conn: Conn,
    llm: object,
    embedder: Embedder,
    entry: _Log,
    today: date,
) -> NeedsClarification | OutOfScope | Ok:
    release_id = current_release_id(conn)
    entry.release_id = release_id
    u, u_res = understand(llm, entry.description, entry.answers)  # type: ignore[arg-type]
    entry.understanding = u
    entry.llm_results.append(u_res)

    if u.scope == "out":
        rid = entry.request_id
        entry.write(conn, {"status": "out_of_scope", "message": OUT_OF_SCOPE_MESSAGE})
        return OutOfScope(request_id=rid, message=OUT_OF_SCOPE_MESSAGE)
    if u.questions:
        rid = entry.request_id
        entry.write(
            conn,
            {"status": "needs_clarification", "questions": [q.model_dump() for q in u.questions]},
        )
        return NeedsClarification(request_id=rid, questions=u.questions)

    mapping: list[Kbli2020Mapping] | None = None
    extra: list[str] = []
    if u.kbli_2020_codes:
        mapping = [
            Kbli2020Mapping.model_validate(
                {"from": code, "to": map_2020_codes(conn, release_id, [code])}
            )
            for code in u.kbli_2020_codes
        ]
        extra = map_2020_codes(conn, release_id, u.kbli_2020_codes)

    candidates: dict[str, list[Candidate]] = {}
    for act in u.activities:
        query = f"{act.label} {entry.description}"
        candidates[act.label] = search_kbli(conn, release_id, query, embedder, extra)
    selection, s_results = select_codes(llm, u, candidates)  # type: ignore[arg-type]
    entry.llm_results.extend(s_results)

    assumptions = [] if u.size == "menengah_besar" else [MICRO_ASSUMPTION]
    scope_note = u.scope_note if u.scope == "partial" else None
    activities: list[ActivityOut] = []
    permits: list[PermitItem] = []
    stale = False
    if selection.unsure or not selection.activities:
        scope_note = UNSURE_NOTE
    else:
        by_code = {c.code: c for cands in candidates.values() for c in cands}
        primaries: list[tuple[str, Attributes]] = []
        for sel in selection.activities:
            attrs = attrs_for(sel.activity_label, u.activities)

            def risk(code: str, attrs: Attributes = attrs) -> str | None:
                return risk_for(conn, release_id, code, attrs, today)

            p = by_code[sel.primary.code]
            activities.append(
                ActivityOut(
                    label=sel.activity_label,
                    primary=PrimaryOut(
                        code=p.code,
                        title=p.title,
                        definition=p.definition,
                        reason=sel.primary.text,
                        risk_level=risk(p.code),
                    ),
                    alternatives=[
                        AlternativeOut(
                            code=a.code,
                            title=by_code[a.code].title,
                            definition=by_code[a.code].definition,
                            when_to_choose=a.text,
                            risk_level=risk(a.code),
                        )
                        for a in sel.alternatives
                    ],
                )
            )
            primaries.append((p.code, attrs))
            entry.selected.append({"label": sel.activity_label, "attributes": attrs.model_dump()})
        permits, stale = lookup_permits(conn, release_id, primaries, today)

    rid = entry.request_id
    result = Result(
        activities=activities,
        permits=permits,
        assumptions=assumptions,
        scope_note=scope_note,
        kbli_2020_mapping=mapping,
        data_as_of=_data_as_of(conn, release_id, permits),
        stale_warning=stale,
        request_id=rid,
    )
    ok = Ok(request_id=rid, result=result)
    entry.write(conn, ok)
    return ok
