"""
LangGraph StateGraph definition for InvestorLens agent.
Orchestrates: search → [conditional] → explain → synthesize → END
"""
from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.nodes import search_node, explain_node, synthesize_node


def _should_explain(state: dict) -> str:
    """Conditional edge: skip explain if not requested or if search errored."""
    if state.get("error"):
        return "synthesize"
    if not state.get("include_explanation", True):
        return "synthesize"
    return "explain"


def build_graph() -> StateGraph:
    """Build and compile the LangGraph agent."""
    graph = StateGraph(AgentState)

    graph.add_node("search", search_node)
    graph.add_node("explain", explain_node)
    graph.add_node("synthesize", synthesize_node)

    graph.set_entry_point("search")

    graph.add_conditional_edges(
        "search",
        _should_explain,
        {"explain": "explain", "synthesize": "synthesize"},
    )
    graph.add_edge("explain", "synthesize")
    graph.add_edge("synthesize", END)

    return graph.compile()


# Module-level compiled graph for reuse
agent = build_graph()


def run_agent(
    query: str,
    persona: str = "value_investor",
    include_explanation: bool = True,
    all_personas: bool = False,
) -> dict:
    """Run the full agent pipeline and return the synthesized response.

    Args:
        query: Natural language search query
        persona: Persona name
        include_explanation: Whether to generate NL explanation (adds ~2-4s)
        all_personas: Whether to run across all 5 personas

    Returns:
        Synthesized response dict ready for JSON serialization
    """
    initial_state = {
        "query": query,
        "persona": persona,
        "include_explanation": include_explanation,
        "all_personas": all_personas,
    }

    result = agent.invoke(initial_state)
    return result.get("synthesized", {"error": result.get("error", "Unknown error")})
