"""Researcher agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient

try:
    from langsmith import traceable
except Exception:  # noqa: BLE001 - optional dependency
    traceable = None


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.sources` and `state.research_notes`.

        Implement search, source filtering, citation capture, and notes.
        """
        def _run(current: ResearchState) -> ResearchState:
            try:
                search_client = SearchClient()
                sources = search_client.search(
                    current.request.query, max_results=current.request.max_sources
                )
            except Exception as exc:  # noqa: BLE001 - allow LLM-only fallback
                current.errors.append(f"search_failed: {exc}")
                sources = []

            try:
                current.sources = sources

                sources_text = "\n".join(
                    f"[{idx + 1}] {item.title} - {item.url or 'no url'}\n{item.snippet}"
                    for idx, item in enumerate(sources)
                )

                system_prompt = (
                    "You are a research assistant. Create concise research notes with citations. "
                    "Prefer sources that directly answer the query."
                )
                user_prompt = (
                    f"Query: {current.request.query}\n\nSources:\n{sources_text}\n\n"
                    "Write 6-10 bullet notes. Each bullet must include a citation like [1]."
                )

                llm = LLMClient()
                response = llm.complete(system_prompt, user_prompt)
                current.research_notes = response.content
                current.agent_results.append(
                    AgentResult(
                        agent=AgentName.RESEARCHER,
                        content=response.content,
                        metadata={
                            "input_tokens": response.input_tokens,
                            "output_tokens": response.output_tokens,
                            "cost_usd": response.cost_usd,
                            "sources": len(sources),
                        },
                    )
                )
                current.add_trace_event("researcher", {"sources": len(sources)})
            except Exception as exc:  # noqa: BLE001 - capture agent failures for state visibility
                current.errors.append(str(exc))
                raise

            return current

        if traceable is None:
            return _run(state)
        traced = traceable(name="researcher", run_type="chain")(_run)
        return traced(state)
