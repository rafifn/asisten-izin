import re

_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_NIK = re.compile(r"(?<!\d)\d{16}(?!\d)")
# Mobile numbers only: "08" + 8-11 digits, or "+62"/"62" + "8" + 7-10 digits
# (10-13 digits in total, optional single space or dash between digits).
_PHONE = re.compile(
    r"(?<!\d)(?:08(?:[ -]?\d){8,11}|(?:\+62|62)[ -]?8(?:[ -]?\d){7,10})(?!\d)",
)


def redact(text: str) -> str:
    """Mask personal data (email, NIK, phone) before text reaches the LLM or logs.

    Email runs first so a digit-only local part is masked as a whole. NIK runs
    before phone so a 16-digit NIK starting with 62 or 08 is not split as a phone.
    """
    text = _EMAIL.sub("[EMAIL]", text)
    text = _NIK.sub("[NIK]", text)
    return _PHONE.sub("[TELEPON]", text)
