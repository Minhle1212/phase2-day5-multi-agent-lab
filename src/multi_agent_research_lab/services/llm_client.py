"""LLM client abstraction.

Production note: agents should depend on this interface instead of importing an SDK directly.
"""

from dataclasses import dataclass
import logging

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from multi_agent_research_lab.core.config import get_settings

try:
    from langsmith import traceable
except Exception:  # noqa: BLE001 - optional dependency
    traceable = None


logger = logging.getLogger(__name__)


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
            logger.debug("LLM completion used %s/%s tokens", input_tokens, output_tokens)
            return LLMResponse(
                content=message.strip(),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=None,
            )

        if traceable is None:
            return _call()

        traced_call = traceable(
            name="llm_complete",
            metadata={"model": settings.openai_model},
        )(_call)
        return traced_call()
