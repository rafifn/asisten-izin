from types import SimpleNamespace
from typing import Any

import anthropic
import httpx
import pytest

from app.data.schemas import ALLOWED_ATTRIBUTES
from app.llm.client import LlmClient, LlmResult, LlmUnavailable
from app.llm.fake import FakeLlm
from app.pipeline.schemas import Attributes, Selection, Understanding


class _Beta:
    def __init__(self, response: Any = None, raises: Exception | None = None) -> None:
        self._response = response
        self._raises = raises
        self.kwargs: dict[str, Any] = {}

    @property
    def messages(self) -> "_Beta":
        return self

    def parse(self, **kwargs: Any) -> Any:
        self.kwargs = kwargs
        if self._raises:
            raise self._raises
        return self._response


def stub_sdk(
    stop_reason: str = "end_turn", parsed: Any = None, raises: Exception | None = None
) -> SimpleNamespace:
    response = SimpleNamespace(
        stop_reason=stop_reason,
        parsed_output=parsed,
        usage=SimpleNamespace(input_tokens=10, output_tokens=5),
        model="claude-opus-5-5",
    )
    return SimpleNamespace(beta=_Beta(response, raises))


_REQ = httpx.Request("POST", "https://api.anthropic.com/v1/messages")


def _status_error(status: int) -> anthropic.APIStatusError:
    return anthropic.APIStatusError(
        "boom", response=httpx.Response(status, request=_REQ), body=None
    )


def _call(sdk: Any) -> LlmResult[Understanding]:
    return LlmClient(sdk=sdk).parse("s", "u", Understanding, "medium")


def test_cost_uses_opus_pricing() -> None:
    r = LlmResult(
        parsed=None, refused=False, tokens_in=1_000_000, tokens_out=100_000, model="claude-opus-5-5"
    )
    assert r.cost_usd == pytest.approx(4.00 + 2.00)


def test_refusal_maps_to_refused() -> None:
    r = _call(stub_sdk(stop_reason="refusal", parsed=object()))
    assert r.refused and r.parsed is None


def test_success_returns_parsed_and_usage() -> None:
    fake = FakeLlm.canned()
    parsed, _ = fake.parse("s", "u", Understanding, "medium"), None
    r = _call(stub_sdk(parsed=parsed.parsed))
    assert r.parsed == parsed.parsed and not r.refused
    assert (r.tokens_in, r.tokens_out, r.model) == (10, 5, "claude-opus-5-5")


def test_request_parameters() -> None:
    sdk = stub_sdk(parsed=None)
    LlmClient(sdk=sdk).parse("sys", "usr", Understanding, "high")
    kw = sdk.beta.kwargs
    assert kw["model"] == "claude-opus-5-5" and kw["max_tokens"] == 16000
    assert kw["system"] == "sys" and kw["messages"] == [{"role": "user", "content": "usr"}]
    assert kw["output_format"] is Understanding and kw["output_config"] == {"effort": "high"}
    assert kw["betas"] == ["server-side-fallback-2026-07-01"] and kw["fallbacks"] == "default"
    assert "thinking" not in kw and "temperature" not in kw and "top_p" not in kw


@pytest.mark.parametrize(
    "exc",
    [
        anthropic.APIConnectionError(request=_REQ),
        anthropic.APITimeoutError(request=_REQ),
        anthropic.RateLimitError("rl", response=httpx.Response(429, request=_REQ), body=None),
        _status_error(500),
        _status_error(503),
    ],
)
def test_transient_errors_raise_unavailable(exc: Exception) -> None:
    with pytest.raises(LlmUnavailable):
        _call(stub_sdk(raises=exc))


def test_other_4xx_propagates() -> None:
    with pytest.raises(anthropic.APIStatusError):
        _call(stub_sdk(raises=_status_error(400)))


def test_attributes_match_allowed_attributes() -> None:
    assert set(Attributes.model_fields) == set(ALLOWED_ATTRIBUTES)


def test_fake_returns_responses_in_order_and_records_calls() -> None:
    u = FakeLlm.canned().parse("s", "u", Understanding, "low").parsed
    fake = FakeLlm([u, RuntimeError("x")])  # type: ignore[list-item]
    assert fake.parse("s1", "u1", Understanding, "low").parsed == u
    with pytest.raises(RuntimeError):
        fake.parse("s2", "u2", Understanding, "low")
    assert fake.calls == [("s1", "u1", Understanding), ("s2", "u2", Understanding)]


def test_canned_understanding() -> None:
    u = FakeLlm.canned().parse("s", "u", Understanding, "medium").parsed
    assert u is not None
    assert len(u.activities) == 1 and u.activities[0].label == "usaha kuliner"
    assert all(v is True for v in u.activities[0].attributes.model_dump().values())
    assert (u.size, u.scope, u.questions, u.kbli_2020_codes) == ("mikro_kecil", "in", [], [])


def test_canned_selection_picks_first_candidate_per_activity() -> None:
    prompt = (
        "Deskripsi usaha: jualan\n\n"
        "## Aktivitas: warung makan\n- 56102: Warung makan\n- 56101: Restoran\n\n"
        "## Aktivitas: kue kering\n- 10711: Industri roti\n"
    )
    s = FakeLlm.canned().parse("s", prompt, Selection, "high").parsed
    assert s is not None and not s.unsure
    assert [
        (a.activity_label, a.primary.code, a.primary.text, a.alternatives) for a in s.activities
    ] == [
        ("warung makan", "56102", "Contoh alasan.", []),
        ("kue kering", "10711", "Contoh alasan.", []),
    ]


def test_default_sdk_has_bounded_timeout_and_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {}

    def fake_anthropic(**kwargs: Any) -> object:
        seen.update(kwargs)
        return object()

    monkeypatch.setattr(anthropic, "Anthropic", fake_anthropic)
    LlmClient()
    assert seen == {"timeout": 60, "max_retries": 1}
