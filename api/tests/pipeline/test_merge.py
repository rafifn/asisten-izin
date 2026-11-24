from app.pipeline.analyze import merge_same_primary
from app.pipeline.schemas import Activity, ActivitySelection, Attributes, Pick


def attrs(**kw: bool | None) -> Attributes:
    base: dict[str, bool | None] = {f: None for f in Attributes.model_fields}
    return Attributes.model_validate({**base, **kw})


def sel(label: str, code: str, alts: tuple[str, ...] = ()) -> ActivitySelection:
    return ActivitySelection(
        activity_label=label,
        primary=Pick(code=code, text=f"alasan {label}"),
        alternatives=[Pick(code=a, text=f"pilih ini jika {a}") for a in alts],
    )


UNDERSTOOD = [
    Activity(label="kerupuk udang", attributes=attrs(packaged=True, animal_products=True)),
    Activity(label="peyek kacang", attributes=attrs(packaged=None, animal_products=False)),
    Activity(label="warung", attributes=attrs(served_on_site=True)),
]


def test_same_primary_becomes_one_entry_with_combined_attributes() -> None:
    merged = merge_same_primary(
        [
            sel("kerupuk udang", "10794", ("47249",)),
            sel("peyek kacang", "10794", ("10794", "47249", "10303")),
        ],
        UNDERSTOOD,
    )
    assert len(merged) == 1
    s, a = merged[0]
    assert s.activity_label == "kerupuk udang + peyek kacang"
    assert s.primary.code == "10794" and s.primary.text == "alasan kerupuk udang"
    # Union of alternatives, without the primary and duplicates, capped at 2.
    assert [x.code for x in s.alternatives] == ["47249", "10303"]
    assert a.packaged is True and a.animal_products is True


def test_different_primaries_stay_separate_in_order() -> None:
    merged = merge_same_primary([sel("kerupuk udang", "10794"), sel("warung", "56101")], UNDERSTOOD)
    assert [s.primary.code for s, _ in merged] == ["10794", "56101"]
    assert merged[1][1].served_on_site is True
    assert merged[0][0].activity_label == "kerupuk udang"
