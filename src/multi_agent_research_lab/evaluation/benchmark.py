"""Benchmark skeleton for single-agent vs multi-agent."""

import re
from time import perf_counter
from typing import Callable

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState


Runner = Callable[[str], ResearchState]


def run_benchmark(run_name: str, query: str, runner: Runner) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure latency and return a placeholder metric object.

    Adds estimated token cost (when available), citation coverage, and error summary.
    """

    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started
    costs = [result.metadata.get("cost_usd") for result in state.agent_results]
    total_cost = None
    if costs and all(cost is not None for cost in costs):
        total_cost = float(sum(cost for cost in costs if cost is not None))

    citation_coverage = None
    if state.final_answer:
        sentences = [segment.strip() for segment in re.split(r"[.!?]+", state.final_answer) if segment.strip()]
        if sentences:
            cited = sum(1 for segment in sentences if re.search(r"\[\d+\]", segment))
            citation_coverage = cited / len(sentences)

    notes = ""
    if state.errors:
        notes = f"errors={len(state.errors)}"

    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=latency,
        estimated_cost_usd=total_cost,
        citation_coverage=citation_coverage,
        notes=notes,
    )
    return state, metrics
