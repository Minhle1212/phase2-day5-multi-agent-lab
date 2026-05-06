"""LangGraph workflow skeleton."""

from multi_agent_research_lab.agents import (
    AnalystAgent,
    CriticAgent,
    ResearcherAgent,
    SupervisorAgent,
    WriterAgent,
)
from multi_agent_research_lab.core.state import ResearchState

try:
    from langsmith import traceable
except Exception:  # noqa: BLE001 - optional dependency
    traceable = None


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph.

    Keep orchestration here; keep agent internals in `agents/`.
    """

    def build(self) -> object:
        """Create a LangGraph graph.

        Implement nodes, edges, conditional routing, and stop condition.
        Suggested nodes: supervisor, researcher, analyst, writer, optional critic.
        """

        try:
            from langgraph.graph import END, StateGraph
        except ImportError as exc:
            raise RuntimeError("Install extras with 'pip install .[llm]' to use LangGraph") from exc

        graph = StateGraph(ResearchState)
        graph.add_node("supervisor", SupervisorAgent().run)
        graph.add_node("researcher", ResearcherAgent().run)
        graph.add_node("analyst", AnalystAgent().run)
        graph.add_node("writer", WriterAgent().run)
        graph.add_node("critic", CriticAgent().run)

        graph.set_entry_point("supervisor")

        graph.add_edge("researcher", "supervisor")
        graph.add_edge("analyst", "supervisor")
        graph.add_edge("writer", "supervisor")
        graph.add_edge("critic", "supervisor")

        def _route(state: ResearchState) -> str:
            if not state.route_history:
                return "done"
            return state.route_history[-1]

        graph.add_conditional_edges(
            "supervisor",
            _route,
            {
                "researcher": "researcher",
                "analyst": "analyst",
                "writer": "writer",
                "critic": "critic",
                "done": END,
            },
        )
        return graph

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the graph and return final state.

        Compile graph, invoke it, and convert result back to ResearchState.
        """

        graph = self.build()
        compiled = graph.compile()

        if traceable is None:
            result = compiled.invoke(state)
        else:
            traced_invoke = traceable(name="multi_agent_workflow")(compiled.invoke)
            result = traced_invoke(state)
        if isinstance(result, ResearchState):
            return result
        return ResearchState.model_validate(result)
