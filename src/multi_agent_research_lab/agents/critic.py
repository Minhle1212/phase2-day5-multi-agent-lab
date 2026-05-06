"""Optional critic agent skeleton for bonus work."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState

try:
    from langsmith import traceable
except Exception:  # noqa: BLE001 - optional dependency
    traceable = None


class CriticAgent(BaseAgent):
    """Optional fact-checking and safety-review agent."""

    name = "critic"

    def run(self, state: ResearchState) -> ResearchState:
        """Validate final answer and append findings.

        Add a lightweight citation coverage check.
        """
        def _run(current: ResearchState) -> ResearchState:
            findings: list[str] = []
            if not current.final_answer:
                findings.append("No final answer available for review.")
            elif "[" not in current.final_answer or "]" not in current.final_answer:
                findings.append("Final answer appears to be missing citations.")

            content = "\n".join(f"- {item}" for item in findings) or "No issues found."
            current.agent_results.append(
                AgentResult(
                    agent=AgentName.CRITIC,
                    content=content,
                    metadata={"issue_count": len(findings)},
                )
            )
            current.add_trace_event("critic", {"issue_count": len(findings)})
            return current

        if traceable is None:
            return _run(state)
        traced = traceable(name="critic", run_type="chain")(_run)
        return traced(state)
