"""Benchmark report rendering."""

from multi_agent_research_lab.core.schemas import BenchmarkMetrics


def render_markdown_report(metrics: list[BenchmarkMetrics]) -> str:
    """Render benchmark metrics to markdown.

    Add richer analysis, examples, screenshots, and trace links as needed.
    """

    lines = [
        "# Benchmark Report",
        "",
        "| Run | Latency (s) | Cost (USD) | Quality | Citation Coverage | Notes |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for item in metrics:
        cost = "" if item.estimated_cost_usd is None else f"{item.estimated_cost_usd:.4f}"
        quality = "" if item.quality_score is None else f"{item.quality_score:.1f}"
        coverage = "" if item.citation_coverage is None else f"{item.citation_coverage:.2f}"
        lines.append(
            f"| {item.run_name} | {item.latency_seconds:.2f} | {cost} | {quality} | {coverage} | {item.notes} |"
        )
    lines.extend(["", "Notes:", "- Add qualitative review scores and trace links per run."])
    return "\n".join(lines) + "\n"
