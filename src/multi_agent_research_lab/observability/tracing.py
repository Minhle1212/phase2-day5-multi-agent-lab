"""Tracing hooks.

This file intentionally avoids binding to one provider. Students can plug in LangSmith,
Langfuse, OpenTelemetry, or simple JSON traces.
"""

from collections.abc import Iterator
from contextlib import contextmanager
import logging
from time import perf_counter
from typing import Any


@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    """Minimal span context used by the skeleton.

    Replace or augment with LangSmith/Langfuse provider spans.
    """

    logger = logging.getLogger(__name__)
    started = perf_counter()
    span: dict[str, Any] = {"name": name, "attributes": attributes or {}, "duration_seconds": None}
    try:
        yield span
        span["status"] = "ok"
    except Exception as exc:  # noqa: BLE001 - bubble error while tagging span
        span["status"] = "error"
        span["error"] = str(exc)
        raise
    finally:
        span["duration_seconds"] = perf_counter() - started
        logger.debug("trace_span %s: %s", name, span)
