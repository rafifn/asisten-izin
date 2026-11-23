from datetime import date, datetime
from pathlib import Path

import pytest

from app.config import Settings
from app.data.loader import current_release_id, load_data
from app.db import Conn
from app.evals import runner
from app.evals.cases import DATA_DIR, load_cases
from app.llm.fake import FakeLlm
from app.pipeline.analyze import NeedsClarification, Ok
from app.pipeline.schemas import Question
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
        resp, clarified, cost, latency, err = runner.run_case(
            db, FakeLlm.canned(), FakeEmbedder(), case, date(2026, 11, 23), commit=False
        )
        assert err is None and isinstance(resp, Ok)
        results.append(runner.score_case(case, resp, clarified, cost, latency, err, names, data))
    assert all(not r.invented for r in results)
    settings = Settings(llm_mode="fake", embedder="fake")
    text = runner.render_report(results, settings, release, datetime(2026, 11, 23, 12, 0))
    assert text.startswith("> **FAKE MODE REPORT")
    assert "KBLI top-3" in text and "Failed cases" in text


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
    resp, clarified, _, _, err = runner.run_case(
        db, llm, FakeEmbedder(), case, date(2026, 11, 23), commit=False
    )
    assert err is None and clarified and isinstance(resp, Ok)
    assert "q1: Kopi bubuk" in llm.calls[1][1]
    r = runner.score_case(case, resp, clarified, 0.0, 0.0, err, {}, runner.DataCodes(set(), set()))
    assert r.got_scope == "in" and r.failures == []


def test_report_file_name_marks_fake(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    # main() in fake mode needs a database; only the dry-run gate is covered here.
    monkeypatch.setenv("LLM_MODE", "real")
    monkeypatch.setenv("EMBEDDER", "bge")
    assert runner.main(["--limit", "2", "--reports-dir", str(tmp_path)], env={}) == 0
    assert list(tmp_path.iterdir()) == []
