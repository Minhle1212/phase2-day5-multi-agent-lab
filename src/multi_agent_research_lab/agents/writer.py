"""Writer agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

try:
    from langsmith import traceable
except Exception:  # noqa: BLE001 - optional dependency
    traceable = None


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.final_answer`.

        Synthesize a clear response with citations or source references.
        """
        def _run(current: ResearchState) -> ResearchState:
            try:
                sources_text = "\n".join(
                    f"[{idx + 1}] {item.title} - {item.url or 'no url'}"
                    for idx, item in enumerate(current.sources)
                )
                system_prompt = "You are a technical writer. Produce a clear response with citations."
                user_prompt = (
                    f"Query: {current.request.query}\n\nResearch Notes:\n{current.research_notes or ''}\n\n"
                    f"Analysis Notes:\n{current.analysis_notes or ''}\n\nSources:\n{sources_text}\n\n"
                    "Write a concise answer for technical learners. Cite sources as [n]."
                )

                llm = LLMClient()
                response = llm.complete(system_prompt, user_prompt)
                current.final_answer = response.content
                current.agent_results.append(
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
                current.add_trace_event("writer", {"sources": len(current.sources)})
            except Exception as exc:  # noqa: BLE001 - capture agent failures for state visibility
                current.errors.append(str(exc))
                raise

            return current

        if traceable is None:
            return _run(state)
        traced = traceable(name="writer", run_type="chain")(_run)
        return traced(state)
