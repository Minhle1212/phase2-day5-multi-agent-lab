"""Analyst agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

try:
    from langsmith import traceable
except Exception:  # noqa: BLE001 - optional dependency
    traceable = None


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.analysis_notes`.

        Extract key claims, compare viewpoints, and flag weak evidence.
        """
        def _run(current: ResearchState) -> ResearchState:
            try:
                research_notes = current.research_notes or ""
                system_prompt = (
                    "You are an analyst. Turn research notes into structured insights, "
                    "highlighting consensus, disagreements, and weak evidence."
                )
                user_prompt = (
                    f"Query: {current.request.query}\n\nResearch Notes:\n{research_notes}\n\n"
                    "Return: (1) Key claims, (2) Evidence gaps, (3) Open questions."
                )

                llm = LLMClient()
                response = llm.complete(system_prompt, user_prompt)
                current.analysis_notes = response.content
                current.agent_results.append(
                    AgentResult(
                        agent=AgentName.ANALYST,
                        content=response.content,
                        metadata={
                            "input_tokens": response.input_tokens,
                            "output_tokens": response.output_tokens,
                            "cost_usd": response.cost_usd,
                        },
                    )
                )
                current.add_trace_event("analyst", {"has_research_notes": bool(research_notes)})
            except Exception as exc:  # noqa: BLE001 - capture agent failures for state visibility
                current.errors.append(str(exc))
                raise

            return current

        if traceable is None:
            return _run(state)
        traced = traceable(name="analyst", run_type="chain")(_run)
        return traced(state)
