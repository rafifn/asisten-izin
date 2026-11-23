"""Deterministic rules engine: (KBLI code + attributes) -> risk level and permit checklist.

No LLM involved. Matching rules:

1. A rule applies when, for every condition key, the attribute equals the required
   value or is unknown (None). Rules with an unknown condition key never apply.
2. Branching: if, for an unknown attribute, the applicable rules of a code include both
   `attr: true` and `attr: false` rules, only the branch with the higher risk is kept
   (tie -> true branch). Rules that do not mention the attribute are always kept.
3. A permit that is only required through rules that relied on unknown attributes gets
   a `condition_note`; a permit also required by a rule that relied on none gets none.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from app.db import Conn
from app.pipeline.schemas import Attributes, PermitItem, Source

ATTR_LABELS = {
    "packaged": "produk dijual dalam kemasan",
    "served_on_site": "makanan disantap di tempat",
    "has_seating": "ada tempat makan",
    "sells_online": "dijual online",
    "animal_products": "memakai bahan hewani",
    "formal_restaurant": "usaha berbentuk restoran",
}

NEG_LABELS = {
    "packaged": "produk tidak dijual dalam kemasan",
    "served_on_site": "makanan tidak disantap di tempat",
    "has_seating": "tidak ada tempat makan",
    "sells_online": "tidak dijual online",
    "animal_products": "tidak memakai bahan hewani",
    "formal_restaurant": "bukan usaha berbentuk restoran",
}

RISK_ORDER = ["rendah", "menengah_rendah", "menengah_tinggi", "tinggi"]
STALE_DAYS = 183


@dataclass(frozen=True)
class _Rule:
    permit_id: str
    risk_level: str
    step_order: int
    conditions: dict[str, bool]
    last_verified: date
    # permit columns
    name: str
    issuer: str
    description: str
    how_to: str
    regulation: str
    article: str | None
    url: str
    regional_note: str | None
    permit_verified: date


_SQL = """
select r.permit_id, r.risk_level, r.step_order, r.conditions, r.last_verified,
       p.name, p.issuer, p.description, p.how_to,
       p.source_regulation, p.source_article, p.source_url, p.regional_note, p.last_verified
from permit_rule r
join permit p on p.id = r.permit_id and p.data_release_id = r.data_release_id
where r.data_release_id = %s and r.kbli_code = %s
  and r.valid_from <= %s and (r.valid_to is null or r.valid_to > %s)
  and p.valid_from <= %s and (p.valid_to is null or p.valid_to > %s)
order by r.id
"""


def _fetch(conn: Conn, release_id: int, code: str, today: date) -> list[_Rule]:
    rows = conn.execute(_SQL, (release_id, code, today, today, today, today))
    return [_Rule(*row) for row in rows.fetchall()]


def _unknown_keys(rule: _Rule, values: dict[str, Any]) -> list[str] | None:
    """Condition keys that matched only because the attribute is unknown; None if no match."""
    unknown: list[str] = []
    for key, required in rule.conditions.items():
        if key not in values:
            return None
        actual = values[key]
        if actual is None:
            unknown.append(key)
        elif actual != required:
            return None
    return unknown


def _risk_rank(rule: _Rule) -> int:
    return RISK_ORDER.index(rule.risk_level)


def _applicable(rules: list[_Rule], attrs: Attributes) -> list[tuple[_Rule, list[str]]]:
    values = attrs.model_dump()
    matched: list[tuple[_Rule, list[str]]] = []
    for rule in rules:
        unknown = _unknown_keys(rule, values)
        if unknown is not None:
            matched.append((rule, unknown))
    for attr in Attributes.model_fields:
        if values[attr] is not None:
            continue
        true_rules = [m for m in matched if m[0].conditions.get(attr) is True]
        false_rules = [m for m in matched if m[0].conditions.get(attr) is False]
        if not (true_rules and false_rules):
            continue
        best_true = max(_risk_rank(r) for r, _ in true_rules)
        best_false = max(_risk_rank(r) for r, _ in false_rules)
        drop = false_rules if best_true >= best_false else true_rules
        matched = [m for m in matched if m not in drop]
    return matched


def risk_for(conn: Conn, release_id: int, code: str, attrs: Attributes, today: date) -> str | None:
    rules = _fetch(conn, release_id, code, today)
    applicable = _applicable(rules, attrs)
    if not applicable:
        return None
    return RISK_ORDER[max(_risk_rank(r) for r, _ in applicable)]


def lookup_permits(
    conn: Conn,
    release_id: int,
    primaries: list[tuple[str, Attributes]],
    today: date,
) -> tuple[list[PermitItem], bool]:
    # permit_id -> aggregate
    agg: dict[str, dict[str, Any]] = {}
    for code, attrs in primaries:
        per_code: dict[str, dict[str, Any]] = {}
        for rule, unknown in _applicable(_fetch(conn, release_id, code, today), attrs):
            e = per_code.setdefault(
                rule.permit_id,
                {
                    "rule": rule,
                    "step": rule.step_order,
                    "notes": [],
                    "unconditional": False,
                    "verified": min(rule.last_verified, rule.permit_verified),
                },
            )
            e["step"] = min(e["step"], rule.step_order)
            e["verified"] = min(e["verified"], rule.last_verified, rule.permit_verified)
            if unknown:
                e["notes"].append(_note_for(rule, unknown))
            else:
                e["unconditional"] = True
        for pid, e in per_code.items():
            a = agg.setdefault(
                pid,
                {
                    "rule": e["rule"],
                    "codes": set(),
                    "step": e["step"],
                    "notes": [],
                    "unconditional": False,
                    "verified": e["verified"],
                },
            )
            a["codes"].add(code)
            a["step"] = min(a["step"], e["step"])
            a["verified"] = min(a["verified"], e["verified"])
            if e["unconditional"]:
                a["unconditional"] = True
            else:
                a["notes"].extend(e["notes"])

    ordered = sorted(agg.values(), key=lambda a: (a["step"], a["rule"].name))
    items: list[PermitItem] = []
    for n, a in enumerate(ordered, start=1):
        r: _Rule = a["rule"]
        note = None if a["unconditional"] else "; ".join(dict.fromkeys(a["notes"]))
        items.append(
            PermitItem(
                order=n,
                name=r.name,
                issuer=r.issuer,
                description=r.description,
                how_to=r.how_to,
                for_kbli=sorted(a["codes"]),
                condition_note=note or None,
                regional_note=r.regional_note,
                source=Source(regulation=r.regulation, article=r.article, url=r.url),
                last_verified=a["verified"],
            )
        )
    cutoff = today - timedelta(days=STALE_DAYS)
    return items, any(i.last_verified < cutoff for i in items)


def _note_for(rule: _Rule, unknown: list[str]) -> str:
    labels = [(ATTR_LABELS if rule.conditions[k] else NEG_LABELS)[k] for k in unknown]
    return "Berlaku jika " + " dan ".join(labels)
