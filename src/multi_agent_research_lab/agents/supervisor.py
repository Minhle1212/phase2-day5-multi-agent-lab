"""Supervisor / router skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.state import ResearchState

try:
    from langsmith import traceable
except Exception:  # noqa: BLE001 - optional dependency
    traceable = None


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop."""

    name = "supervisor"

    def run(self, state: ResearchState) -> ResearchState:
        """Update `state.route_history` with the next route.

        Suggested steps:
        - Inspect request, current notes, and missing fields.
        - Choose one of: researcher, analyst, writer, done.
        - Enforce max iterations and failure fallback.
        """

        def _run(current: ResearchState) -> ResearchState:
            settings = get_settings()
            if current.iteration >= settings.max_iterations:
                current.record_route("done")
                current.add_trace_event("route", {"next": "done", "reason": "max_iterations"})
                return current

            if not current.research_notes:
                next_route = "researcher"
            elif not current.analysis_notes:
                next_route = "analyst"
            elif not current.final_answer:
                next_route = "writer"
            else:
                next_route = "done"

            current.record_route(next_route)
            current.add_trace_event("route", {"next": next_route})
            return current

        if traceable is None:
            return _run(state)
        traced = traceable(name="supervisor", run_type="chain")(_run)
        return traced(state)
