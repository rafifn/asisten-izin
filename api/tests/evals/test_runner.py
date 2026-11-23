from datetime import date, datetime
from pathlib import Path

import pytest

from app.config import Settings
from app.data.loader import current_release_id, load_data
from app.db import Conn
from app.evals import runner
from app.evals.cases import DATA_DIR, Case, load_cases
from app.llm.fake import FakeLlm
from app.pipeline.analyze import NeedsClarification, Ok
from app.pipeline.schemas import Question, Understanding
from app.retrieval.embedder import FakeEmbedder


def test_estimate_cost_is_rough_per_case_figure():
    assert runner.estimate_cost(50) == pytest.approx(50 * 2 * 0.044)


def test_percentile_nearest_rank():
    assert runner.percentile([1.0, 2.0, 3.0, 4.0], 0.5) == 2.0
    assert runner.percentile([1.0, 2.0, 3.0, 4.0], 0.95) == 4.0
    assert runner.percentile([], 0.5) == 0.0


def test_real_mode_without_yes_does_not_touch_api_or_db(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("LLM_MODE", "real")
    monkeypatch.setenv("EMBEDDER", "bge")
    monkeypatch.setenv("DATABASE_URL", "postgresql://nobody@127.0.0.1:1/none")

    def boom(*a: object, **k: object) -> None:
        raise AssertionError("must not build the real client without --yes")

    monkeypatch.setattr(runner, "build_llm", boom)
    assert runner.main([], env={}) == 0
    out = capsys.readouterr().out
    assert f"{len(load_cases())} cases" in out and "$" in out and "Not calling" in out


def test_first_option_answers():
    q = NeedsClarification(
        request_id="00000000-0000-0000-0000-000000000000",  # type: ignore[arg-type]
        questions=[
            Question(id="a", text="?", options=["x", "y"]),
            Question(id="b", text="?", options=[]),
        ],
    )
    assert runner.first_option_answers(q) == {"a": "x", "b": "tidak tahu"}


def test_run_and_report_in_fake_mode(db: Conn):
    release = load_data(db, DATA_DIR, FakeEmbedder(), notes="embedder=fake")
    assert release == current_release_id(db)
    data, names = runner.load_data_codes(db, release)
    cases = load_cases()[:3] + [c for c in load_cases() if c.expect.clarify][:1]
    results = []
    for case in cases:
        run = runner.run_case(
            db, FakeLlm.canned(), FakeEmbedder(), case, date(2026, 11, 23), commit=False
        )
        assert run.error is None and isinstance(run.resp, Ok) and run.logged_scope == "in"
        results.append(runner.score_case(case, run, names, data))
    assert all(not r.invented for r in results)
    settings = Settings(llm_mode="fake", embedder="fake")
    text = runner.render_report(results, settings, release, datetime(2026, 11, 23, 12, 0))
    assert text.startswith("> **FAKE MODE REPORT")
    assert "KBLI top-3" in text and "Failed cases" in text
    assert "INCOMPLETE" not in text and "includes loading the embedding model" in text


def test_clarification_is_rerun_with_first_option(db: Conn):
    from app.pipeline.schemas import Activity, Attributes, Selection, Understanding

    load_data(db, DATA_DIR, FakeEmbedder())
    attrs = Attributes(**dict.fromkeys(Attributes.model_fields, False))
    ask = Understanding(
        activities=[Activity(label="kopi", attributes=attrs)],
        size="unknown",
        scope="in",
        scope_note=None,
        kbli_2020_codes=[],
        questions=[Question(id="q1", text="Kopi apa?", options=["Kopi bubuk", "Kopi seduh"])],
    )
    answered = ask.model_copy(update={"questions": []})
    llm = FakeLlm([ask, answered, *[Selection(activities=[], unsure=True)] * 3])
    case = next(c for c in load_cases() if c.id == "vague-01")
    run = runner.run_case(db, llm, FakeEmbedder(), case, date(2026, 11, 23), commit=False)
    assert run.error is None and run.clarified and isinstance(run.resp, Ok)
    assert "q1: Kopi bubuk" in llm.calls[1][1]
    r = runner.score_case(case, run, {}, runner.DataCodes(set(), set()))
    assert r.got_scope == "in" and r.failures == []


def test_report_file_name_marks_fake(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    # main() in fake mode needs a database; only the dry-run gate is covered here.
    monkeypatch.setenv("LLM_MODE", "real")
    monkeypatch.setenv("EMBEDDER", "bge")
    assert runner.main(["--limit", "2", "--reports-dir", str(tmp_path)], env={}) == 0
    assert list(tmp_path.iterdir()) == []


def _und(**kw: object) -> Understanding:
    from app.pipeline.schemas import Activity, Attributes

    attrs = Attributes(**dict.fromkeys(Attributes.model_fields, False))
    base: dict[str, object] = {
        "activities": [Activity(label="kopi", attributes=attrs)],
        "size": "mikro_kecil",
        "scope": "in",
        "scope_note": None,
        "kbli_2020_codes": [],
        "questions": [],
    }
    return Understanding.model_validate(base | kw)


class _CostlyLlm(FakeLlm):
    """FakeLlm that reports 1000 input tokens per call ($0.004)."""

    def parse(self, system, user, schema, effort):  # type: ignore[no-untyped-def]
        r = super().parse(system, user, schema, effort)
        r.tokens_in = 1000
        return r


def _case(cid: str = "x-01", scope: str = "in", clarify: bool = False) -> Case:
    return Case.model_validate(
        {"id": cid, "description": "jual kopi", "expect": {"scope": scope, "clarify": clarify}}
    )


def test_got_scope_reads_the_logged_understanding_scope(db: Conn) -> None:
    from app.pipeline.schemas import Selection

    load_data(db, DATA_DIR, FakeEmbedder())
    unsure = Selection(activities=[], unsure=True)
    llm = FakeLlm([_und(scope="partial", scope_note="Sembako tidak dicakup."), unsure, unsure])
    run = runner.run_case(db, llm, FakeEmbedder(), _case(scope="partial"), date(2026, 11, 23),
                          commit=False)  # fmt: skip
    assert run.logged_scope == "partial" and isinstance(run.resp, Ok)
    r = runner.score_case(_case(scope="partial"), run, {}, runner.DataCodes(set(), set()))
    assert r.got_scope == "partial" and not any(f.startswith("scope") for f in r.failures)
    assert runner.got_scope(run.resp, None) == "in"


def test_errored_request_cost_is_counted(db: Conn) -> None:
    from app.llm.client import LlmUnavailable

    load_data(db, DATA_DIR, FakeEmbedder())
    llm = _CostlyLlm([_und(), LlmUnavailable("down")])
    run = runner.run_case(db, llm, FakeEmbedder(), _case(), date(2026, 11, 23), commit=False)
    assert run.resp is None and run.error and run.error.startswith("llm_unavailable")
    assert run.cost_usd == pytest.approx(0.004)


def test_case_that_raises_becomes_an_error_row(db: Conn, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*a: object, **k: object) -> None:
        raise RuntimeError("kaboom")

    monkeypatch.setattr(runner, "analyze", boom)
    r = runner.evaluate_case(
        db, FakeLlm([]), FakeEmbedder(), _case(), date(2026, 11, 23), {},
        runner.DataCodes(set(), set()), commit=False,
    )  # fmt: skip
    assert r.status == "error" and r.got_scope == "error"
    assert r.error == "RuntimeError: kaboom" and r.failures == ["error: RuntimeError: kaboom"]


def test_unexpected_question_is_its_own_failure_type() -> None:
    run = runner.CaseRun(None, True, 0.0, 0.0, error="internal: x")
    r = runner.score_case(_case(), run, {}, runner.DataCodes(set(), set()))
    assert any(f.startswith("unexpected_question:") for f in r.failures)
    vague = runner.score_case(_case(clarify=True), run, {}, runner.DataCodes(set(), set()))
    assert not any(f.startswith("unexpected_question") for f in vague.failures)


def _result(cid: str, expect: str, got: str, clarified: bool) -> runner.CaseResult:
    return runner.CaseResult(_case(cid, scope=expect), "ok", clarified, got, None, 0.01, 1.0)


def test_summary_has_out_of_scope_accuracy() -> None:
    rs = [
        _result("a", "out", "out", False),
        _result("b", "out", "in", False),
        _result("c", "in", "in", False),
        _result("d", "partial", "in", False),
    ]
    s = runner.summarize(rs)
    assert s["out_cases"] == 2 and s["out_of_scope"] == 0.5 and s["scope"] == 0.5


def test_report_splits_by_clarified_and_lists_failure_types() -> None:
    rs = [_result("a-01", "in", "in", True), _result("b-01", "out", "out", False)]
    rs[0].failures.append("unexpected_question: asked")
    text = runner.render_report(
        rs, Settings(llm_mode="real", embedder="bge"), 1, datetime(2026, 11, 23, 12, 0)
    )
    assert "| Metric | All | Clarified (1) | Not clarified (1) |" in text
    assert "Clarified (auto-answered) cases: a-01" in text
    assert "Out-of-scope accuracy (1 expected-out cases answered out) | 1.000" in text
    assert "| unexpected_question | 1 |" in text
    assert "Scope accuracy, 3-way" in text


def test_main_keeps_results_when_a_case_raises_or_the_run_is_interrupted(
    db: Conn, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from contextlib import contextmanager

    load_data(db, DATA_DIR, FakeEmbedder(), notes="embedder=fake")
    monkeypatch.setenv("LLM_MODE", "fake")
    monkeypatch.setenv("EMBEDDER", "fake")

    @contextmanager
    def same_conn(url: str):  # type: ignore[no-untyped-def]
        yield db

    calls: list[str] = []

    def fake_run(conn, llm, embedder, case, today, commit=True):  # type: ignore[no-untyped-def]
        calls.append(case.id)
        if len(calls) == 2:
            raise RuntimeError("boom")
        if len(calls) == 3:
            raise KeyboardInterrupt
        return runner.CaseRun(None, False, 0.5, 1.0, error="internal: x")

    monkeypatch.setattr(runner, "connect", same_conn)
    monkeypatch.setattr(runner, "run_case", fake_run)
    with pytest.raises(KeyboardInterrupt):
        runner.main(["--limit", "4", "--reports-dir", str(tmp_path)], env={})
    (report,) = tmp_path.iterdir()
    text = report.read_text()
    assert "INCOMPLETE RUN: 2 of 4 cases" in text
    assert calls[0] in text and calls[1] in text and "error: RuntimeError: boom" in text
    assert calls[2] not in text.split("## Failed cases")[1]
