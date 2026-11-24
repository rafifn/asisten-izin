import json
from types import SimpleNamespace
from typing import Any

import httpx
import openai
import pytest

from app.config import Settings
from app.deps import build_llm
from app.llm.client import LlmClient, LlmUnavailable
from app.llm.deepseek import DeepSeekClient
from app.llm.fake import FakeLlm
from app.pipeline.schemas import Understanding

VALID = FakeLlm.canned().parse("s", "u", Understanding, "medium").parsed
assert VALID is not None
VALID_JSON = VALID.model_dump_json()


def _response(content: str | None, finish: str = "stop", model: str = "deepseek-flash") -> Any:
    return SimpleNamespace(
        model=model,
        usage=SimpleNamespace(prompt_tokens=100, completion_tokens=20),
        choices=[SimpleNamespace(finish_reason=finish, message=SimpleNamespace(content=content))],
    )


class _Completions:
    def __init__(self, items: list[Any]) -> None:
        self._items = list(items)
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        item = self._items.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def stub_sdk(*items: Any) -> SimpleNamespace:
    return SimpleNamespace(chat=SimpleNamespace(completions=_Completions(list(items))))


def _client(*items: Any) -> tuple[DeepSeekClient, _Completions]:
    sdk = stub_sdk(*items)
    return DeepSeekClient(sdk=sdk, model="deepseek-flash"), sdk.chat.completions


_REQ = httpx.Request("POST", "https://api.deepseek.com/chat/completions")


def _status_error(status: int) -> openai.APIStatusError:
    return openai.APIStatusError("boom", response=httpx.Response(status, request=_REQ), body=None)


def test_valid_json_is_parsed_with_usage_and_cost() -> None:
    client, _ = _client(_response(VALID_JSON))
    r = client.parse("sys", "usr", Understanding, "medium")
    assert r.parsed == VALID and not r.refused
    assert (r.tokens_in, r.tokens_out, r.model) == (100, 20, "deepseek-flash")
    assert r.cost_usd == pytest.approx((100 * 0.30 + 20 * 1.20) / 1_000_000)


def test_request_uses_json_mode_schema_prompt_and_effort_mapping() -> None:
    client, calls = _client(_response(VALID_JSON))
    client.parse("sys", "usr", Understanding, "medium")
    kw = calls.calls[0]
    assert kw["model"] == "deepseek-flash"
    assert kw["response_format"] == {"type": "json_object"}
    assert kw["extra_body"] == {"reasoning_effort": "low"}
    system = kw["messages"][0]
    assert system["role"] == "system" and system["content"].startswith("sys")
    # DeepSeek JSON mode requires the word "json" and the expected shape in the prompt.
    assert "json" in system["content"]
    assert json.dumps(Understanding.model_json_schema(), ensure_ascii=False) in system["content"]
    assert kw["messages"][1] == {"role": "user", "content": "usr"}


@pytest.mark.parametrize(("effort", "expected"), [("low", "none"), ("high", "high")])
def test_effort_mapping(effort: Any, expected: str) -> None:
    client, calls = _client(_response(VALID_JSON))
    client.parse("s", "u", Understanding, effort)
    assert calls.calls[0]["extra_body"] == {"reasoning_effort": expected}


@pytest.mark.parametrize(
    "bad",
    [
        _response("   "),
        _response(None),
        _response("{not json"),
        _response('{"activities": "wrong"}'),
        _response(VALID_JSON[:40], finish="length"),
    ],
)
def test_bad_reply_is_retried_once_then_succeeds(bad: Any) -> None:
    client, calls = _client(bad, _response(VALID_JSON))
    r = client.parse("s", "u", Understanding, "medium")
    assert r.parsed == VALID and not r.refused
    assert len(calls.calls) == 2
    assert (r.tokens_in, r.tokens_out) == (200, 40)  # both attempts are counted


def test_two_bad_replies_return_refused() -> None:
    client, calls = _client(_response("   "), _response("{bad"))
    r = client.parse("s", "u", Understanding, "medium")
    assert r.refused and r.parsed is None and len(calls.calls) == 2


def test_content_filter_returns_refused_without_retry() -> None:
    client, calls = _client(_response(None, finish="content_filter"))
    r = client.parse("s", "u", Understanding, "medium")
    assert r.refused and len(calls.calls) == 1


@pytest.mark.parametrize(
    "error",
    [
        openai.RateLimitError("slow", response=httpx.Response(429, request=_REQ), body=None),
        openai.APITimeoutError(request=_REQ),
        openai.APIConnectionError(request=_REQ),
        _status_error(500),
        _status_error(503),
    ],
)
def test_unavailable_errors(error: Exception) -> None:
    client, _ = _client(error)
    with pytest.raises(LlmUnavailable):
        client.parse("s", "u", Understanding, "medium")


def test_other_4xx_propagates() -> None:
    client, _ = _client(_status_error(401))
    with pytest.raises(openai.APIStatusError):
        client.parse("s", "u", Understanding, "medium")


def test_missing_api_key_fails_with_clear_message(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
        DeepSeekClient()


def test_build_llm_picks_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    assert isinstance(build_llm(Settings(llm_mode="real", llm_provider="deepseek")), DeepSeekClient)
    assert isinstance(build_llm(Settings(llm_mode="real", llm_provider="claude")), LlmClient)
    assert isinstance(build_llm(Settings(llm_mode="fake", llm_provider="deepseek")), FakeLlm)


def test_settings_default_provider_is_deepseek(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    assert Settings.from_env().llm_provider == "deepseek"
    monkeypatch.setenv("LLM_PROVIDER", "claude")
    assert Settings.from_env().llm_provider == "claude"
    monkeypatch.setenv("LLM_PROVIDER", "gpt")
    with pytest.raises(ValueError):
        Settings.from_env()
