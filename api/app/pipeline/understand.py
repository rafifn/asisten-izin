from pathlib import Path
from typing import Protocol

from app.llm.client import LlmResult
from app.pipeline.schemas import Understanding

MAX_QUESTIONS = 2
_SYSTEM = (Path(__file__).parent / "prompts" / "understand.md").read_text(encoding="utf-8")


class _Llm(Protocol):
    def parse(
        self,
        system: str,
        user: str,
        schema: type[Understanding],
        effort: str,
    ) -> LlmResult[Understanding]: ...


class UnderstandRefused(Exception):
    """The model refused to analyse the description."""


def _build_user(description: str, answers: dict[str, str] | None) -> str:
    parts = [f"## Deskripsi usaha\n{description}"]
    if answers:
        lines = "\n".join(f"- {qid}: {ans}" for qid, ans in answers.items())
        parts.append(
            "## Jawaban pengguna atas pertanyaan sebelumnya\n"
            f"{lines}\n\nJangan ajukan pertanyaan lagi; kosongkan `questions`."
        )
    return "\n\n".join(parts)


def understand(
    llm: _Llm, description: str, answers: dict[str, str] | None
) -> tuple[Understanding, LlmResult[Understanding]]:
    result = llm.parse(_SYSTEM, _build_user(description, answers), Understanding, "medium")
    if result.refused or result.parsed is None:
        raise UnderstandRefused("model refused to analyse the description")
    u = result.parsed.model_copy(deep=True)
    u.questions = [] if answers else u.questions[:MAX_QUESTIONS]
    if u.size == "menengah_besar":
        u.scope = "out"
    return u, result
