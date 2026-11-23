import shutil
from collections.abc import Callable, Iterator
from datetime import date
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.data.loader import load_data
from app.db import Conn, connect
from app.deps import get_conn, get_embedder, get_llm, get_today
from app.llm.client import LlmUnavailable
from app.llm.fake import FakeLlm
from app.main import create_app
from app.pipeline.analyze import OUT_OF_SCOPE_MESSAGE, UNSURE_NOTE
from app.pipeline.schemas import (
    Activity,
    ActivitySelection,
    Attributes,
    Pick,
    Question,
    Selection,
    Understanding,
)
from app.retrieval.embedder import FakeEmbedder
from tests.fixtures.codes import (
    FIXTURE_CATERING_CODE,
    FIXTURE_CODES,
    FIXTURE_DRINK_CODE,
    FIXTURE_PACKAGED_CODE,
)

TODAY = date(2026, 11, 23)
FIXTURE_DATA = Path(__file__).parent / "fixtures" / "data"

MakeClient = Callable[[FakeLlm], TestClient]


def und(**kw: object) -> Understanding:
    attrs = Attributes(
        packaged=True,
        served_on_site=False,
        has_seating=False,
        sells_online=True,
        animal_products=False,
        formal_restaurant=False,
    )
    base: dict[str, object] = {
        "activities": [Activity(label="keripik", attributes=attrs)],
        "size": "mikro_kecil",
        "scope": "in",
        "scope_note": None,
        "kbli_2020_codes": [],
        "questions": [],
    }
    return Understanding.model_validate(base | kw)


def sel(code: str = FIXTURE_PACKAGED_CODE, alts: list[str] | None = None) -> Selection:
    return Selection(
        activities=[
            ActivitySelection(
                activity_label="keripik",
                primary=Pick(code=code, text="Alasan."),
                alternatives=[Pick(code=c, text="Pilih jika.") for c in alts or []],
            )
        ],
        unsure=False,
    )


@pytest.fixture
def make_client(db: Conn, loaded_fixture: int) -> MakeClient:
    def make(llm: FakeLlm) -> TestClient:
        app = create_app()
        app.dependency_overrides[get_conn] = lambda: db
        app.dependency_overrides[get_llm] = lambda: llm
        app.dependency_overrides[get_embedder] = lambda: FakeEmbedder()
        app.dependency_overrides[get_today] = lambda: TODAY
        return TestClient(app)

    return make


def post(c: TestClient, description: str = "keripik pisang dikemas dijual online", **kw: object):  # type: ignore[no-untyped-def]
    return c.post("/v1/analyze", json={"description": description, **kw})


def rows(db: Conn) -> int:
    r = db.execute("select count(*) from query_log").fetchone()
    assert r is not None
    return int(r[0])


def test_ok_path_shapes_result(db: Conn, make_client: MakeClient) -> None:
    c = make_client(FakeLlm([und(), sel(alts=[FIXTURE_DRINK_CODE])]))
    body = post(c).json()
    assert body["status"] == "ok"
    r = body["result"]
    act = r["activities"][0]
    assert act["label"] == "keripik"
    assert act["primary"]["code"] in FIXTURE_CODES
    assert act["primary"]["risk_level"] == "rendah"
    assert act["primary"]["reason"] == "Alasan."
    assert act["alternatives"][0]["code"] == FIXTURE_DRINK_CODE
    assert act["alternatives"][0]["when_to_choose"] == "Pilih jika."
    assert r["permits"][0]["source"]["url"].startswith("http") and r["data_as_of"]
    assert r["data_as_of"] == "2026-11-01"
    assert r["assumptions"] == ["Dianggap usaha mikro/kecil"]
    assert r["kbli_2020_mapping"] is None and r["scope_note"] is None
    assert r["stale_warning"] is False
    assert r["request_id"] == body["request_id"]
    assert rows(db) == 1
    row = db.execute(
        "select input, attributes, output, data_release_id, model, latency_ms from query_log"
    ).fetchone()
    assert row is not None
    assert row[1]["size"] == "mikro_kecil" and row[2]["status"] == "ok" and row[3] is not None
    assert row[4] and row[5] >= 0


def test_medium_large_business_is_out_of_scope(make_client: MakeClient) -> None:
    c = make_client(FakeLlm([und(size="menengah_besar", scope="in")]))
    assert post(c).json()["status"] == "out_of_scope"


def test_first_round_returns_questions(db: Conn, make_client: MakeClient) -> None:
    qs = [Question(id=f"q{i}", text="Apa?", options=["a", "b"]) for i in range(3)]
    c = make_client(FakeLlm([und(questions=qs)]))
    body = post(c).json()
    assert body["status"] == "needs_clarification"
    assert 1 <= len(body["questions"]) <= 2
    assert rows(db) == 1


def test_clarification_round_logs_answers_in_new_row(db: Conn, make_client: MakeClient) -> None:
    qs = [Question(id="q1", text="Apa?", options=["a"])]
    llm = FakeLlm([und(questions=qs), und(), sel()])
    c = make_client(llm)
    assert post(c).json()["status"] == "needs_clarification"
    body = post(c, answers={"q1": "dijual online"}).json()
    assert body["status"] == "ok"
    assert rows(db) == 2
    r = db.execute("select clarifications from query_log order by id desc limit 1").fetchone()
    assert r is not None and r[0] == {"q1": "dijual online"}


def test_blank_answers_do_not_loop(make_client: MakeClient) -> None:
    qs = [Question(id="a", text="Apa?", options=["x"])]
    c = make_client(FakeLlm([und(questions=qs), sel()]))
    assert post(c, answers={"a": ""}).json()["status"] == "ok"


def test_out_of_scope(make_client: MakeClient) -> None:
    c = make_client(FakeLlm([und(scope="out", scope_note=None)]))
    body = post(c).json()
    assert body["status"] == "out_of_scope"
    assert body["message"] == OUT_OF_SCOPE_MESSAGE
    assert body["message"].startswith("Maaf, jenis usaha ini belum didukung.")


def test_partial_scope_note_passed_through(make_client: MakeClient) -> None:
    c = make_client(FakeLlm([und(scope="partial", scope_note="Hanya sebagian."), sel()]))
    assert post(c).json()["result"]["scope_note"] == "Hanya sebagian."


def test_unsure_selection_gives_empty_activities(make_client: MakeClient) -> None:
    c = make_client(
        FakeLlm(
            [und(), Selection(activities=[], unsure=True), Selection(activities=[], unsure=True)]
        )
    )
    body = post(c).json()
    assert body["status"] == "ok"
    assert body["result"]["activities"] == [] and body["result"]["permits"] == []
    assert body["result"]["scope_note"] == UNSURE_NOTE
    assert body["result"]["data_as_of"]  # release date when no permits


def test_old_kbli_mapping_lists_in_scope_targets_only(make_client: MakeClient) -> None:
    # fixture maps 11051 -> 90003 (in scope) and 90004 (out of scope)
    c = make_client(FakeLlm([und(kbli_2020_codes=["11051"]), sel(FIXTURE_DRINK_CODE)]))
    r = post(c).json()["result"]
    assert r["kbli_2020_mapping"] == [{"from": "11051", "to": [FIXTURE_DRINK_CODE]}]


def test_pii_never_reaches_llm_or_log(db: Conn, make_client: MakeClient) -> None:
    llm = FakeLlm([und(), sel()])
    c = make_client(llm)
    post(c, "keripik pisang, hubungi WA 081234567890 atau a@b.com", answers=None)
    sent = " ".join(user for _, user, _ in llm.calls)
    assert "081234567890" not in sent and "a@b.com" not in sent
    r = db.execute("select input from query_log").fetchone()
    assert r is not None and "081234567890" not in r[0] and "[TELEPON]" in r[0]


def test_pii_in_answers_redacted_in_log(db: Conn, make_client: MakeClient) -> None:
    c = make_client(FakeLlm([und(), sel()]))
    post(c, answers={"q": "WA 081234567890"})
    r = db.execute("select clarifications::text from query_log").fetchone()
    assert r is not None and "081234567890" not in r[0]


def test_llm_failure_returns_503(db: Conn, make_client: MakeClient) -> None:
    c = make_client(FakeLlm([LlmUnavailable()]))
    resp = post(c)
    assert resp.status_code == 503 and resp.json()["error"]["code"] == "llm_unavailable"
    assert rows(db) == 1


def test_llm_failure_in_select_logs_partial_tokens(db: Conn, make_client: MakeClient) -> None:
    c = make_client(FakeLlm([und(), LlmUnavailable()]))
    assert post(c).status_code == 503
    assert rows(db) == 1


def test_refusal_returns_400(db: Conn, make_client: MakeClient) -> None:
    from app.llm.client import LlmResult

    class Refusing(FakeLlm):
        def parse(self, system, user, schema, effort):  # type: ignore[no-untyped-def]
            return LlmResult(parsed=None, refused=True, tokens_in=1, tokens_out=0, model="m")

    resp = post(make_client(Refusing()))
    assert resp.status_code == 400
    assert resp.json()["error"] == {
        "code": "invalid_input",
        "message": "Deskripsi ini tidak dapat diproses. Coba tulis ulang dengan kata lain.",
    }
    assert rows(db) == 1


def _analyze_ok(c: TestClient, alts: list[str] | None = None) -> str:
    body = post(c).json()
    assert body["status"] == "ok"
    return str(body["request_id"])


def test_permits_for_alternative(make_client: MakeClient) -> None:
    c = make_client(FakeLlm([und(), sel(alts=[FIXTURE_CATERING_CODE])]))
    rid = _analyze_ok(c)
    resp = c.post("/v1/permits", json={"request_id": rid, "primary_codes": [FIXTURE_CATERING_CODE]})
    assert resp.status_code == 200
    names = [p["name"] for p in resp.json()["permits"]]
    assert names == ["NIB", "SLHS"] and resp.json()["stale_warning"] is False


def test_permits_uses_original_release(db: Conn, make_client: MakeClient, tmp_path: Path) -> None:
    c = make_client(FakeLlm([und(), sel()]))
    rid = _analyze_ok(c)
    data = tmp_path / "data"
    shutil.copytree(FIXTURE_DATA, data)
    permits = data / "permits.yaml"
    permits.write_text(permits.read_text().replace("name: NIB", "name: NIB Baru"))
    load_data(db, data, FakeEmbedder())
    resp = c.post("/v1/permits", json={"request_id": rid, "primary_codes": [FIXTURE_PACKAGED_CODE]})
    assert "NIB" in [p["name"] for p in resp.json()["permits"]]
    assert "NIB Baru" not in [p["name"] for p in resp.json()["permits"]]
    # a fresh analyze uses the new release
    c2 = make_client(FakeLlm([und(), sel()]))
    new = post(c2).json()["result"]["permits"]
    assert "NIB Baru" in [p["name"] for p in new]


def test_permits_rejects_code_not_offered(make_client: MakeClient) -> None:
    c = make_client(FakeLlm([und(), sel()]))
    rid = _analyze_ok(c)
    resp = c.post("/v1/permits", json={"request_id": rid, "primary_codes": [FIXTURE_DRINK_CODE]})
    assert resp.status_code == 400 and resp.json()["error"]["code"] == "invalid_input"


def test_permits_validation_and_unknown_id(make_client: MakeClient) -> None:
    c = make_client(FakeLlm([]))
    r = c.post("/v1/permits", json={"request_id": str(uuid4()), "primary_codes": []})
    assert r.status_code == 400
    r = c.post("/v1/permits", json={"request_id": str(uuid4()), "primary_codes": ["90001"]})
    assert r.status_code == 404 and r.json()["error"]["code"] == "not_found"


def test_feedback_updates_row(db: Conn, make_client: MakeClient) -> None:
    c = make_client(FakeLlm([und(), sel()]))
    rid = _analyze_ok(c)
    resp = c.post(
        "/v1/feedback",
        json={"request_id": rid, "helpful": True, "comment": "bagus, WA 081234567890"},
    )
    assert resp.status_code == 204 and resp.content == b""
    row = db.execute(
        "select helpful, comment from query_log where request_uuid = %s", [UUID(rid)]
    ).fetchone()
    assert row is not None and row[0] is True
    assert "081234567890" not in row[1] and "[TELEPON]" in row[1]


@pytest.mark.parametrize("description", ["", "ab", "   ", "x" * 2001])
def test_description_length_validation(make_client: MakeClient, description: str) -> None:
    resp = post(make_client(FakeLlm([])), description)
    assert resp.status_code == 400 and resp.json()["error"]["code"] == "invalid_input"


def test_unknown_request_id_404(make_client: MakeClient) -> None:
    resp = make_client(FakeLlm([])).post(
        "/v1/feedback", json={"request_id": str(uuid4()), "helpful": False}
    )
    assert resp.status_code == 404 and resp.json()["error"]["code"] == "not_found"


def test_cors_allows_local_frontend(make_client: MakeClient) -> None:
    resp = make_client(FakeLlm([])).options(
        "/v1/analyze",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert resp.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_canned_fake_llm_end_to_end(make_client: MakeClient) -> None:
    c = make_client(FakeLlm.canned())
    body = post(c).json()
    assert body["status"] == "ok" and body["result"]["activities"]


def test_data_as_of_is_oldest_permit_date(db: Conn, make_client: MakeClient) -> None:
    c = make_client(FakeLlm([und(), sel()]))
    db.execute("update permit set last_verified = '2026-10-01' where id = 'spp-irt'")
    r = post(c).json()["result"]
    assert r["data_as_of"] == "2026-10-01"


class WeirdError(Exception):
    pass


def test_unexpected_error_returns_500_and_logs(db: Conn, make_client: MakeClient) -> None:
    c = make_client(FakeLlm([und(), WeirdError("boom")]))
    resp = post(c)
    assert resp.status_code == 500 and resp.json()["error"]["code"] == "internal"
    row = db.execute("select output, tokens_in, model from query_log").fetchone()
    assert row is not None and row[0] == {"error": "internal"} and row[2]


def test_db_error_inside_pipeline_still_logs(db: Conn, make_client: MakeClient) -> None:
    class DbBreaker(FakeLlm):
        def parse(self, system, user, schema, effort):  # type: ignore[no-untyped-def]
            db.execute("select 1/0")
            raise AssertionError

    resp = post(make_client(DbBreaker()))
    assert resp.status_code == 500 and rows(db) == 1


def test_no_data_loaded_returns_500_and_logs(db: Conn) -> None:
    app = create_app()
    app.dependency_overrides[get_conn] = lambda: db
    app.dependency_overrides[get_llm] = lambda: FakeLlm([])
    app.dependency_overrides[get_embedder] = lambda: FakeEmbedder()
    app.dependency_overrides[get_today] = lambda: TODAY
    resp = post(TestClient(app))
    assert resp.status_code == 500 and resp.json()["error"]["code"] == "internal"
    assert rows(db) == 1


def _two_activities() -> Understanding:
    def attrs(packaged: bool) -> Attributes:
        return Attributes(
            packaged=packaged,
            served_on_site=False,
            has_seating=False,
            sells_online=False,
            animal_products=False,
            formal_restaurant=None,
        )

    return und(
        activities=[
            Activity(label="a", attributes=attrs(False)),
            Activity(label="b", attributes=attrs(True)),
        ]
    )


def _merged_selection() -> Selection:
    return Selection(
        activities=[
            ActivitySelection(
                activity_label="gabungan",
                primary=Pick(code=FIXTURE_PACKAGED_CODE, text="Alasan."),
                alternatives=[],
            )
        ],
        unsure=False,
    )


def test_merged_label_uses_combined_attributes(db: Conn, make_client: MakeClient) -> None:
    c = make_client(FakeLlm([_two_activities(), _merged_selection()]))
    body = post(c).json()
    # activities[0] has packaged=False; combined (any True) must give SPP-IRT
    assert "SPP-IRT" in [p["name"] for p in body["result"]["permits"]]
    row = db.execute("select attributes from query_log").fetchone()
    assert row is not None
    stored = row[0]["selected_activities"][0]
    assert stored["label"] == "gabungan"
    assert stored["attributes"]["packaged"] is True
    assert stored["attributes"]["formal_restaurant"] is None


def test_permits_uses_stored_resolved_attributes(db: Conn, make_client: MakeClient) -> None:
    c = make_client(FakeLlm([_two_activities(), _merged_selection()]))
    rid = post(c).json()["request_id"]
    payload = {"request_id": rid, "primary_codes": [FIXTURE_PACKAGED_CODE]}
    names = [p["name"] for p in c.post("/v1/permits", json=payload).json()["permits"]]
    assert "SPP-IRT" in names
    db.execute(
        "update query_log set attributes = jsonb_set(attributes,"
        " '{selected_activities,0,attributes,packaged}', 'false') where request_uuid = %s",
        [UUID(rid)],
    )
    names = [p["name"] for p in c.post("/v1/permits", json=payload).json()["permits"]]
    assert "SPP-IRT" not in names


@pytest.fixture
def committed_fixture(migrated_db_url: str) -> Iterator[str]:
    """Fixture data committed to the test DB so real per-request connections can see it."""
    conn = connect(migrated_db_url)
    load_data(conn, FIXTURE_DATA, FakeEmbedder())
    conn.commit()
    yield migrated_db_url
    conn.execute(
        "truncate query_log, kbli_2020_map, permit_rule, permit, kbli, data_release cascade"
    )
    conn.commit()
    conn.close()


def test_real_connection_commits_before_response(committed_fixture: str) -> None:
    app = create_app(Settings(database_url=committed_fixture, llm_mode="fake", embedder="fake"))
    with TestClient(app) as c:
        body = post(c).json()
        assert body["status"] == "ok"
        # a second connection sees the row as soon as the response is back
        with connect(committed_fixture) as other:
            r = other.execute(
                "select helpful from query_log where request_uuid = %s", [UUID(body["request_id"])]
            ).fetchone()
            assert r is not None
        fb = c.post("/v1/feedback", json={"request_id": body["request_id"], "helpful": True})
        assert fb.status_code == 204
        with connect(committed_fixture) as other:
            r = other.execute("select helpful from query_log").fetchone()
            assert r is not None and r[0] is True


def test_real_connection_keeps_log_row_on_503(committed_fixture: str) -> None:
    app = create_app(Settings(database_url=committed_fixture, llm_mode="fake", embedder="fake"))
    app.dependency_overrides[get_llm] = lambda: FakeLlm([LlmUnavailable()])
    with TestClient(app) as c:
        assert post(c).status_code == 503
    with connect(committed_fixture) as other:
        r = other.execute("select output from query_log").fetchone()
        assert r is not None and r[0] == {"error": "llm_unavailable"}


def test_unsure_selection_keeps_partial_scope_note(make_client: MakeClient) -> None:
    unsure = Selection(activities=[], unsure=True)
    c = make_client(
        FakeLlm([und(scope="partial", scope_note="Sembako tidak dicakup."), unsure, unsure])
    )
    note = post(c).json()["result"]["scope_note"]
    assert note.startswith("Sembako tidak dicakup.") and UNSURE_NOTE in note


def test_select_prompt_gets_the_redacted_description(make_client: MakeClient) -> None:
    llm = FakeLlm([und(), sel()])
    post(make_client(llm), "keripik pisang, WA 081234567890")
    select_user = llm.calls[1][1]
    assert "keripik pisang, WA [TELEPON]" in select_user and "081234567890" not in select_user


def test_permits_returns_data_as_of(make_client: MakeClient) -> None:
    c = make_client(FakeLlm([und(), sel(alts=[FIXTURE_CATERING_CODE])]))
    rid = _analyze_ok(c)
    resp = c.post("/v1/permits", json={"request_id": rid, "primary_codes": [FIXTURE_CATERING_CODE]})
    body = resp.json()
    assert body["data_as_of"] == min(p["last_verified"] for p in body["permits"])


def test_pii_in_answer_keys_redacted(db: Conn, make_client: MakeClient) -> None:
    llm = FakeLlm([und(), sel()])
    post(make_client(llm), answers={"WA 081234567890": "ya", "a@b.com": "x"})
    sent = " ".join(user for _, user, _ in llm.calls)
    assert "081234567890" not in sent and "a@b.com" not in sent
    r = db.execute("select clarifications::text from query_log").fetchone()
    assert r is not None and "081234567890" not in r[0] and "a@b.com" not in r[0]
    assert "[TELEPON]" in r[0] and "[EMAIL]" in r[0]


def test_unhandled_500_carries_cors_headers() -> None:
    app = create_app(Settings(cors_origins=("http://localhost:3000",)))

    def boom() -> None:
        raise RuntimeError("kaboom")

    app.add_api_route("/boom", boom)
    resp = TestClient(app).get("/boom", headers={"Origin": "http://localhost:3000"})
    assert resp.status_code == 500
    assert resp.json() == {
        "error": {"code": "internal", "message": "Terjadi kesalahan pada server."}
    }
    assert resp.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_embedder_mismatch(db: Conn) -> None:
    from app.deps import embedder_mismatch

    assert embedder_mismatch(db, "bge") is None  # no release yet
    db.execute("insert into data_release (notes) values ('')")
    assert "does not record" in (embedder_mismatch(db, "bge") or "")
    assert embedder_mismatch(db, "fake") is None
    db.execute("insert into data_release (notes) values ('embedder=fake')")
    assert "'fake' but EMBEDDER=bge" in (embedder_mismatch(db, "bge") or "")
    assert embedder_mismatch(db, "fake") is None


def test_startup_logs_embedder_mismatch(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    import app.deps as deps

    monkeypatch.setattr(deps, "connect", lambda url: _FakeConnCtx())
    monkeypatch.setattr(deps, "embedder_mismatch", lambda conn, e: f"mismatch for {e}")
    with caplog.at_level("WARNING"):
        deps.warn_on_embedder_mismatch(Settings(embedder="bge"))
    assert "EMBEDDER MISMATCH: mismatch for bge" in caplog.text


def test_startup_embedder_check_never_fails(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    import app.deps as deps

    def down(url: str) -> None:
        raise OSError("db down")

    monkeypatch.setattr(deps, "connect", down)
    with caplog.at_level("WARNING"):
        deps.warn_on_embedder_mismatch(Settings(embedder="bge"))
    assert "could not check" in caplog.text


class _FakeConnCtx:
    def __enter__(self) -> "_FakeConnCtx":
        return self

    def __exit__(self, *a: object) -> None:
        return None
