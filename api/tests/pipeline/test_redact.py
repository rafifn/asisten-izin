import pytest

from app.pipeline.redact import redact


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("NIK saya 3174012345678901 ya", "NIK saya [NIK] ya"),
        ("WA 0812-3456-7890", "WA [TELEPON]"),
        ("hubungi +62 812 3456 7890", "hubungi [TELEPON]"),
        ("email budi@mail.com", "email [EMAIL]"),
        ("NIK 6212345678901234 ya", "NIK [NIK] ya"),
        ("email 0812345678@mail.com", "email [EMAIL]"),
    ],
)
def test_redacts(raw: str, expected: str) -> None:
    assert redact(raw) == expected


@pytest.mark.parametrize(
    "keep",
    [
        "KBLI lama saya 56102",
        "harga Rp 15.000 per bungkus",
        "modal 50 juta",
        "buka jam 08.00-17.00",
        "tarif +62 21 5550 1234 kantor",
        "nomor 081234567 saja",
    ],
)
def test_keeps_business_numbers(keep: str) -> None:
    assert redact(keep) == keep
