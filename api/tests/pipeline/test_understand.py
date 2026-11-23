from typing import Any

from app.llm.fake import FakeLlm
from app.pipeline.schemas import Activity, Attributes, Question, Understanding
from app.pipeline.understand import UnderstandRefused, understand


def q(i: str) -> Question:
    return Question(id=i, text=f"pertanyaan {i}?", options=["ya", "tidak"])


def understanding(**over: Any) -> Understanding:
    base: dict[str, Any] = dict(
        activities=[
            Activity(
                label="kue",
                attributes=Attributes(
                    packaged=True,
                    served_on_site=False,
                    has_seating=False,
                    sells_online=None,
                    animal_products=True,
                    formal_restaurant=False,
                ),
            )
        ],
        size="mikro_kecil",
        scope="in",
        scope_note=None,
        kbli_2020_codes=[],
        questions=[],
    )
    base.update(over)
    return Understanding(**base)


def test_understand_truncates_questions_to_two() -> None:
    llm = FakeLlm([understanding(questions=[q("a"), q("b"), q("c")])])
    u, _ = understand(llm, "jualan kue", None)
    assert [x.id for x in u.questions] == ["a", "b"]


def test_understand_with_answers_never_returns_questions() -> None:
    llm = FakeLlm([understanding(questions=[q("a")])])
    u, _ = understand(llm, "jualan kue", {"a": "ya"})
    assert u.questions == [] and "a" in llm.calls[0][1] and "ya" in llm.calls[0][1]


def test_menengah_besar_forces_out_of_scope() -> None:
    llm = FakeLlm([understanding(size="menengah_besar", scope="in")])
    u, _ = understand(llm, "pabrik roti 200 karyawan", None)
    assert u.scope == "out"


def test_prompt_and_effort() -> None:
    llm = FakeLlm([understanding()])
    understand(llm, "jualan kue", None)
    system, user, schema = llm.calls[0]
    assert schema is Understanding and "formal_restaurant" in system and "jualan kue" in user


def test_refusal_raises() -> None:
    import pytest

    from app.llm.client import LlmResult

    class Refusing(FakeLlm):
        def parse(self, *a: Any, **k: Any) -> Any:  # type: ignore[override]
            return LlmResult(parsed=None, refused=True, tokens_in=0, tokens_out=0, model="m")

    with pytest.raises(UnderstandRefused):
        understand(Refusing([]), "jualan kue", None)
