from dataclasses import dataclass
from typing import Any, Literal

import anthropic
from pydantic import BaseModel

MODEL = "claude-opus-5-5"
MAX_TOKENS = 16000
FALLBACK_BETA = "server-side-fallback-2026-07-01"
# Per-request timeout (seconds) and SDK retries: bounded so a request fails with 503 well
# before the web client's own timeout (90 s) instead of hanging.
TIMEOUT_S = 60
MAX_RETRIES = 1
# Claude Opus 5.5 pricing, USD per 1M tokens.
INPUT_USD_PER_MTOK = 4.00
OUTPUT_USD_PER_MTOK = 20.00


class LlmUnavailable(Exception):
    """Connection error, timeout, 429 or 5xx after the SDK's own retries."""


@dataclass
class LlmResult[T: BaseModel]:
    parsed: T | None
    refused: bool
    tokens_in: int
    tokens_out: int
    model: str

    @property
    def cost_usd(self) -> float:
        return (
            self.tokens_in * INPUT_USD_PER_MTOK + self.tokens_out * OUTPUT_USD_PER_MTOK
        ) / 1_000_000


class LlmClient:
    def __init__(self, sdk: Any = None) -> None:
        self._sdk = (
            sdk
            if sdk is not None
            else anthropic.Anthropic(timeout=TIMEOUT_S, max_retries=MAX_RETRIES)
        )

    def parse[T: BaseModel](
        self,
        system: str,
        user: str,
        schema: type[T],
        effort: Literal["low", "medium", "high"],
    ) -> LlmResult[T]:
        try:
            response = self._sdk.beta.messages.parse(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=system,
                messages=[{"role": "user", "content": user}],
                output_format=schema,
                output_config={"effort": effort},
                betas=[FALLBACK_BETA],
                fallbacks="default",
            )
        except anthropic.RateLimitError as e:
            raise LlmUnavailable("rate limited") from e
        except anthropic.APITimeoutError as e:
            raise LlmUnavailable("timeout") from e
        except anthropic.APIConnectionError as e:
            raise LlmUnavailable("connection error") from e
        except anthropic.APIStatusError as e:
            if e.status_code >= 500:
                raise LlmUnavailable(f"server error {e.status_code}") from e
            raise
        usage = response.usage
        refused = response.stop_reason == "refusal"
        return LlmResult(
            parsed=None if refused else response.parsed_output,
            refused=refused,
            tokens_in=usage.input_tokens,
            tokens_out=usage.output_tokens,
            model=response.model,
        )
