from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, StringConstraints, field_validator

from app.db import Conn
from app.deps import AnyLlm, get_conn, get_embedder, get_llm, get_today
from app.errors import ApiError
from app.pipeline.analyze import AnalyzeResponse, analyze, data_as_of
from app.pipeline.redact import redact
from app.pipeline.schemas import Attributes, PermitItem
from app.retrieval.embedder import Embedder
from app.rules.engine import lookup_permits

router = APIRouter()

MAX_ANSWERS = 10
MAX_ANSWER_LEN = 500


class AnalyzeRequest(BaseModel):
    description: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=3, max_length=2000)
    ]
    answers: dict[str, str] | None = None

    @field_validator("answers")
    @classmethod
    def _answers_limits(cls, v: dict[str, str] | None) -> dict[str, str] | None:
        if v is not None and (
            len(v) > MAX_ANSWERS
            or any(len(a) > MAX_ANSWER_LEN or len(k) > 64 for k, a in v.items())
        ):
            raise ValueError("answers too large")
        return v


class PermitsRequest(BaseModel):
    request_id: UUID
    primary_codes: list[str]

    @field_validator("primary_codes")
    @classmethod
    def _non_empty(cls, v: list[str]) -> list[str]:
        if not v or len(v) > 10:
            raise ValueError("primary_codes must have 1-10 items")
        return v


class PermitsResponse(BaseModel):
    permits: list[PermitItem]
    data_as_of: date
    stale_warning: bool


class FeedbackRequest(BaseModel):
    request_id: UUID
    helpful: bool
    comment: Annotated[str, StringConstraints(max_length=2000)] | None = None


@router.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/v1/analyze", response_model=AnalyzeResponse)
def post_analyze(
    body: AnalyzeRequest,
    conn: Annotated[Conn, Depends(get_conn, scope="function")],
    llm: Annotated[AnyLlm, Depends(get_llm)],
    embedder: Annotated[Embedder, Depends(get_embedder)],
    today: Annotated[date, Depends(get_today)],
) -> object:
    return analyze(conn, llm, embedder, body.description, body.answers, today)


@router.post("/v1/permits", response_model=PermitsResponse)
def post_permits(
    body: PermitsRequest,
    conn: Annotated[Conn, Depends(get_conn, scope="function")],
    today: Annotated[date, Depends(get_today)],
) -> PermitsResponse:
    row = conn.execute(
        "select attributes, output, data_release_id from query_log where request_uuid = %s",
        [body.request_id],
    ).fetchone()
    if row is None:
        raise ApiError(404, "not_found", "Permintaan tidak ditemukan.")
    attributes, output, release_id = row
    activities = (output or {}).get("result", {}).get("activities", [])
    if not attributes or release_id is None or not activities:
        raise ApiError(400, "invalid_input", "Kode tidak termasuk dalam hasil analisis ini.")
    stored = {
        a["label"]: Attributes.model_validate(a["attributes"])
        for a in attributes.get("selected_activities", [])
    }

    primaries: list[tuple[str, Attributes]] = []
    for code in dict.fromkeys(body.primary_codes):
        label = next(
            (
                a["label"]
                for a in activities
                if code == a["primary"]["code"]
                or code in [alt["code"] for alt in a["alternatives"]]
            ),
            None,
        )
        if label is None:
            raise ApiError(400, "invalid_input", "Kode tidak termasuk dalam hasil analisis ini.")
        primaries.append((code, stored[label]))
    permits, stale = lookup_permits(conn, release_id, primaries, today)
    return PermitsResponse(
        permits=permits, data_as_of=data_as_of(conn, release_id, permits), stale_warning=stale
    )


@router.post("/v1/feedback", status_code=204)
def post_feedback(
    body: FeedbackRequest, conn: Annotated[Conn, Depends(get_conn, scope="function")]
) -> Response:
    comment = None if body.comment is None else redact(body.comment)
    cur = conn.execute(
        "update query_log set helpful = %s, comment = %s where request_uuid = %s",
        [body.helpful, comment, body.request_id],
    )
    if cur.rowcount == 0:
        raise ApiError(404, "not_found", "Permintaan tidak ditemukan.")
    return Response(status_code=204)
