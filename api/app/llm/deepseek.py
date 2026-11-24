"""DeepSeek provider, through DeepSeek's OpenAI-compatible API.

Same `parse(system, user, schema, effort)` contract as `LlmClient` (Claude). DeepSeek has no
schema-enforced structured output (only JSON mode, `response_format={"type": "json_object"}`),
so the JSON Schema goes into the system prompt and every reply is validated with Pydantic.
A blank, truncated or invalid reply is retried once; if it fails again the result is returned
as `refused=True`, which the pipeline already treats as "cannot process" / "unsure".
Docs: https://api-docs.deepseek.com/guides/json_mode
"""

import json
import os
from typing import Any, Literal

import openai
from pydantic import BaseModel, ValidationError

from app.llm.client import LlmResult, LlmUnavailable

BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-flash"
MAX_TOKENS = 16000
TIMEOUT_S = 60
MAX_RETRIES = 1
ATTEMPTS = 2  # one retry on a blank, truncated or invalid JSON reply

# USD per 1M tokens (input cache miss, output) at DeepSeek's *peak* rates, so logged cost
# errs high (off-peak is half; cache hits are far cheaper). Checked 2026-11-24 against
# https://api-docs.deepseek.com/quick_start/pricing
PRICES: dict[str, tuple[float, float]] = {
    "deepseek-flash": (0.30, 1.20),
    "deepseek-v4-pro": (1.32, 3.96),
}

# Our effort levels → DeepSeek `reasoning_effort` ("none" turns thinking off).
REASONING_EFFORT: dict[str, str] = {"low": "none", "medium": "low", "high": "high"}

JSON_INSTRUCTION = (
    "\n\n# Format jawaban\n"
    "Balas HANYA dengan satu objek json yang valid, tanpa teks lain dan tanpa blok kode. "
    "Objek json itu harus sesuai dengan JSON Schema berikut (nama field persis sama):\n"
)


class DeepSeekClient:
    def __init__(self, sdk: Any = None, model: str | None = None) -> None:
        self.model = model or os.environ.get("DEEPSEEK_MODEL", DEFAULT_MODEL)
        if sdk is not None:
            self._sdk = sdk
            return
        api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
        if not api_key:
            raise ValueError(
                "DEEPSEEK_API_KEY is not set. Add it to .env (see .env.example), "
                "or use LLM_MODE=fake to run without an API key."
            )
        self._sdk = openai.OpenAI(
            api_key=api_key, base_url=BASE_URL, timeout=TIMEOUT_S, max_retries=MAX_RETRIES
        )

    def parse[T: BaseModel](
        self,
        system: str,
        user: str,
        schema: type[T],
        effort: Literal["low", "medium", "high"],
    ) -> LlmResult[T]:
        schema_json = json.dumps(schema.model_json_schema(), ensure_ascii=False)
        messages = [
            {"role": "system", "content": system + JSON_INSTRUCTION + schema_json},
            {"role": "user", "content": user},
        ]
        tokens_in = tokens_out = 0
        model = self.model
        for _ in range(ATTEMPTS):
            response = self._create(messages, effort)
            usage = response.usage
            tokens_in += usage.prompt_tokens
            tokens_out += usage.completion_tokens
            model = response.model
            choice = response.choices[0]
            if choice.finish_reason == "content_filter":
                break
            if choice.finish_reason == "length":
                continue
            content = (choice.message.content or "").strip()
            if not content:
                continue
            try:
                parsed = schema.model_validate_json(content)
            except ValidationError:
                continue
            return self._result(parsed, False, tokens_in, tokens_out, model)
        return self._result(None, True, tokens_in, tokens_out, model)

    def _create(self, messages: list[dict[str, str]], effort: str) -> Any:
        try:
            return self._sdk.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
                max_tokens=MAX_TOKENS,
                extra_body={"reasoning_effort": REASONING_EFFORT[effort]},
            )
        except openai.RateLimitError as e:
            raise LlmUnavailable("rate limited") from e
        except openai.APITimeoutError as e:
            raise LlmUnavailable("timeout") from e
        except openai.APIConnectionError as e:
            raise LlmUnavailable("connection error") from e
        except openai.APIStatusError as e:
            if e.status_code >= 500:
                raise LlmUnavailable(f"server error {e.status_code}") from e
            raise

    def _result[T: BaseModel](
        self, parsed: T | None, refused: bool, tokens_in: int, tokens_out: int, model: str
    ) -> LlmResult[T]:
        return LlmResult(
            parsed=parsed,
            refused=refused,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            model=model,
            usd_per_mtok=PRICES.get(self.model, PRICES[DEFAULT_MODEL]),
        )
