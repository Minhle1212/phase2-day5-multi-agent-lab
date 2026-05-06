"""LLM client abstraction.

Production note: agents should depend on this interface instead of importing an SDK directly.
"""

from dataclasses import dataclass
import logging
from typing import Literal

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from multi_agent_research_lab.core.config import get_settings

try:
    from langsmith import traceable
except Exception:  # noqa: BLE001 - optional dependency
    traceable = None


logger = logging.getLogger(__name__)

# OpenAI pricing per 1M tokens (as of 2024)
# Format: model_name -> (input_cost_per_1m, output_cost_per_1m)
OPENAI_PRICING: dict[str, tuple[float, float]] = {
    "gpt-4o": (5.00, 15.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4-turbo": (10.00, 30.00),
    "gpt-4": (30.00, 60.00),
    "gpt-3.5-turbo": (0.50, 1.50),
}


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float | None:
    """Calculate cost in USD based on token usage and model pricing.

    Uses OpenAI's current pricing. Returns None if model pricing is unknown.
    """
    if model not in OPENAI_PRICING:
        logger.warning("Unknown model '%s' - cost calculation skipped", model)
        return None

    input_cost_per_m, output_cost_per_m = OPENAI_PRICING[model]
    total_cost = (input_tokens / 1_000_000) * input_cost_per_m
    total_cost += (output_tokens / 1_000_000) * output_cost_per_m
    return round(total_cost, 6)


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None


class LLMClient:
    """Provider-agnostic LLM client skeleton."""

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a model completion.

        Keep retry, timeout, and token logging here rather than inside agents.
        """

        settings = get_settings()
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for LLMClient.complete")

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install extras with 'pip install .[llm]' to use OpenAI") from exc

        client = OpenAI(api_key=settings.openai_api_key)

        @retry(
            retry=retry_if_exception_type(Exception),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            stop=stop_after_attempt(3),
            reraise=True,
        )
        def _call() -> LLMResponse:
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                timeout=settings.timeout_seconds,
            )
            message = response.choices[0].message.content or ""
            usage = response.usage
            input_tokens = getattr(usage, "prompt_tokens", None) if usage else None
            output_tokens = getattr(usage, "completion_tokens", None) if usage else None
            cost_usd = calculate_cost(settings.openai_model, input_tokens or 0, output_tokens or 0)
            logger.debug("LLM completion used %s/%s tokens, cost=$%.6f", input_tokens, output_tokens, cost_usd or 0)
            return LLMResponse(
                content=message.strip(),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd,
            )

        if traceable is None:
            return _call()

        traced_call = traceable(
            name="llm_complete",
            metadata={"model": settings.openai_model},
        )(_call)
        return traced_call()
