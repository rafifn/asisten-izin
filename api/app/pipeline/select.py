from pathlib import Path
from typing import Protocol

from app.llm.client import LlmResult
from app.pipeline.schemas import (
    ActivitySelection,
    Candidate,
    Pick,
    Selection,
    Understanding,
)

MAX_ALTERNATIVES = 2
_SYSTEM = (Path(__file__).parent / "prompts" / "select.md").read_text(encoding="utf-8")


class _Llm(Protocol):
    def parse(
        self,
        system: str,
        user: str,
        schema: type[Selection],
        effort: str,
    ) -> LlmResult[Selection]: ...


def _unsure() -> Selection:
    return Selection(activities=[], unsure=True)


def _tri(value: bool | None) -> str:
    return "tidak diketahui" if value is None else ("ya" if value else "tidak")


def _build_user(understanding: Understanding, candidates: dict[str, list[Candidate]]) -> str:
    attrs = {a.label: a.attributes for a in understanding.activities}
    parts: list[str] = []
    for label, cands in candidates.items():
        lines = [f"## Aktivitas: {label}"]
        a = attrs.get(label)
        if a is not None:
            facts = [
                ("dikemas", a.packaged),
                ("disajikan di tempat", a.served_on_site),
                ("ada tempat duduk", a.has_seating),
                ("jual daring", a.sells_online),
                ("produk hewani", a.animal_products),
                ("restoran formal", a.formal_restaurant),
            ]
            lines.append("Atribut: " + "; ".join(f"{k}={_tri(v)}" for k, v in facts))
        lines.append("Kandidat:")
        for c in cands:
            lines.append(f"- {c.code}: {c.title}")
            if c.definition:
                lines.append(f"  Definisi: {c.definition}")
        parts.append("\n".join(lines))
    return "\n\n".join(parts)


def _retry_system(candidates: dict[str, list[Candidate]]) -> str:
    allowed = "\n".join(
        f"- {label}: {', '.join(c.code for c in cands)}" for label, cands in candidates.items()
    )
    return (
        f"{_SYSTEM}\n\n## Koreksi\nJawaban sebelumnya memuat kode yang tidak ada dalam daftar "
        f"kandidat. Gunakan hanya kode berikut untuk tiap aktivitas:\n{allowed}"
    )


def _clean(sel: Selection, candidates: dict[str, list[Candidate]]) -> Selection | None:
    """Validate against the candidates; None means a violation (invalid primary)."""
    if not sel.activities:
        return None
    union = {c.code for cands in candidates.values() for c in cands}
    cleaned: list[ActivitySelection] = []
    for act in sel.activities:
        if act.activity_label in candidates:
            allowed = {c.code for c in candidates[act.activity_label]}
        else:
            allowed = union  # unmatched label: possibly a merge of several activities
        if act.primary.code not in allowed:
            return None
        alts: list[Pick] = []
        seen = {act.primary.code}
        for alt in act.alternatives:
            if alt.code in allowed and alt.code not in seen:
                alts.append(alt)
                seen.add(alt.code)
        cleaned.append(act.model_copy(update={"alternatives": alts[:MAX_ALTERNATIVES]}))
    return Selection(activities=cleaned, unsure=sel.unsure)


def select_codes(
    llm: _Llm, understanding: Understanding, candidates: dict[str, list[Candidate]]
) -> tuple[Selection, list[LlmResult[Selection]]]:
    """Let the model choose KBLI codes, only from the given candidates (keyed by activity label).

    Activities without candidates are not sent to the model. An invalid primary code
    triggers one retry with the allowed codes listed; a second violation or a refusal
    yields `unsure`. `LlmUnavailable` propagates.
    """
    candidates = {label: cands for label, cands in candidates.items() if cands}
    if not candidates:
        return _unsure(), []
    user = _build_user(understanding, candidates)
    results: list[LlmResult[Selection]] = []
    for system in (_SYSTEM, _retry_system(candidates)):
        result = llm.parse(system, user, Selection, "medium")
        results.append(result)
        if result.refused or result.parsed is None:
            return _unsure(), results
        cleaned = _clean(result.parsed, candidates)
        if cleaned is not None:
            return cleaned, results
    return _unsure(), results
