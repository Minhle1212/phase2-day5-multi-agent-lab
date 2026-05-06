"""Command-line entrypoint for the lab starter."""

from typing import Annotated

import json
import logging
import os

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.schemas import AgentName, AgentResult, ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import run_benchmark
from multi_agent_research_lab.evaluation.report import render_markdown_report
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.services.storage import LocalArtifactStore
from multi_agent_research_lab.services.llm_client import LLMClient

try:
    from langsmith import traceable
except Exception:  # noqa: BLE001 - optional dependency
    traceable = None

try:
    from langsmith import Client as LangSmithClient
except Exception:  # noqa: BLE001 - optional dependency
    LangSmithClient = None

app = typer.Typer(help="Multi-Agent Research Lab starter CLI")
console = Console()


def _init() -> None:
    load_dotenv()
    settings = get_settings()
    configure_logging(settings.log_level)
    if os.getenv("LANGSMITH_TRACING", "").lower() == "true" and not os.getenv(
        "LANGSMITH_TRACING_V2"
    ):
        os.environ["LANGSMITH_TRACING_V2"] = "true"
    logger = logging.getLogger(__name__)
    logger.info(
        "LangSmith tracing=%s project=%s endpoint=%s api_key_set=%s",
        os.getenv("LANGSMITH_TRACING"),
        os.getenv("LANGSMITH_PROJECT"),
        os.getenv("LANGSMITH_ENDPOINT"),
        bool(os.getenv("LANGSMITH_API_KEY")),
    )


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run a minimal single-agent baseline placeholder."""

    _init()

    def _run() -> ResearchState:
        request = ResearchQuery(query=query)
        state = ResearchState(request=request)
        system_prompt = "You are a research assistant. Provide a concise, sourced answer."
        user_prompt = f"Query: {query}\n\nAnswer in 3-6 paragraphs with citations if possible."
        response = LLMClient().complete(system_prompt, user_prompt)
        state.final_answer = response.content
        state.agent_results.append(
            AgentResult(
                agent=AgentName.WRITER,
                content=response.content,
                metadata={
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                },
            )
        )
        return state

    if traceable is None:
        state = _run()
    else:
        traced = traceable(
            name="cli_baseline",
            run_type="chain",
            project_name=os.getenv("LANGSMITH_PROJECT"),
        )(_run)
        state = traced()

    console.print(Panel.fit(state.final_answer, title="Single-Agent Baseline"))


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow skeleton."""

    _init()
    def _run() -> ResearchState:
        state = ResearchState(request=ResearchQuery(query=query))
        workflow = MultiAgentWorkflow()
        return workflow.run(state)

    try:
        if LangSmithClient is not None:
            client = LangSmithClient()
            project_name = os.getenv("LANGSMITH_PROJECT")
            try:
                run = client.create_run(
                    name="cli_multi_agent_manual",
                    run_type="chain",
                    inputs={"query": query},
                    project_name=project_name,
                )
                logging.getLogger(__name__).info(
                    "LangSmith manual run created: id=%s project=%s",
                    getattr(run, "id", None),
                    project_name,
                )
            except Exception as exc:  # noqa: BLE001 - diagnostics for manual run
                logging.getLogger(__name__).error(
                    "LangSmith manual run failed: project=%s error=%s",
                    project_name,
                    exc,
                )
        if traceable is None:
            result = _run()
        else:
            traced = traceable(
                name="cli_multi_agent",
                run_type="chain",
                project_name=os.getenv("LANGSMITH_PROJECT"),
            )(_run)
            result = traced()
    except StudentTodoError as exc:
        console.print(Panel.fit(str(exc), title="Expected TODO", style="yellow"))
        raise typer.Exit(code=2) from exc

    console.print(result.model_dump_json(indent=2))


@app.command()
def benchmark(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run baseline + multi-agent and write local report + trace."""

    _init()
    store = LocalArtifactStore()

    def run_baseline(run_query: str) -> ResearchState:
        request = ResearchQuery(query=run_query)
        state = ResearchState(request=request)
        system_prompt = "You are a research assistant. Provide a concise, sourced answer."
        user_prompt = f"Query: {run_query}\n\nAnswer in 3-6 paragraphs with citations if possible."
        response = LLMClient().complete(system_prompt, user_prompt)
        state.final_answer = response.content
        state.agent_results.append(
            AgentResult(
                agent=AgentName.WRITER,
                content=response.content,
                metadata={
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                },
            )
        )
        return state

    def run_multi_agent(run_query: str) -> ResearchState:
        state = ResearchState(request=ResearchQuery(query=run_query))
        workflow = MultiAgentWorkflow()
        return workflow.run(state)

    baseline_state, baseline_metrics = run_benchmark("baseline", query, run_baseline)
    multi_state, multi_metrics = run_benchmark("multi-agent", query, run_multi_agent)

    report = render_markdown_report([baseline_metrics, multi_metrics])
    store.write_text("benchmark_report.md", report)
    store.write_text("traces/multi_agent_trace.json", json.dumps(multi_state.trace, indent=2))
    store.write_text("traces/multi_agent_state.json", multi_state.model_dump_json(indent=2))

    console.print(Panel.fit("Benchmark report and traces written to reports/", title="Done"))


if __name__ == "__main__":
    app()
