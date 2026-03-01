"""
LangGraph StateGraph definition for InvestorLens agent.

Flow:
  data_gathering ↔ tools   (ReAct loop, max ~8 iterations)
        ↓ (no tool calls)
      rank
        ↓
  [conditional: include_explanation?]
        ↓
      explain  (optional)
        ↓
    synthesize  →  END
"""
from langgraph.graph import StateGraph, END

from agents.state import AgentState
from agents.nodes import data_gathering_node, tools_node, rank_node, explain_node, synthesize_node


def _tools_condition(state: dict) -> str:
    """Route to 'tools' if the last AIMessage has tool_calls, else to END (→ rank).

    Mirrors langgraph.prebuilt.tools_condition but compatible with langgraph 1.0.x.
    """
    messages = state.get("messages") or []
    if messages:
        last = messages[-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
    return END


def _should_explain(state: dict) -> str:
    """Conditional edge: skip explain if not requested or if ranking errored."""
    if state.get("error"):
        return "synthesize"
    if not state.get("include_explanation", True):
        return "synthesize"
    return "explain"


def build_graph() -> StateGraph:
    """Build and compile the LangGraph ReAct agent."""
    graph = StateGraph(AgentState)

    # --- Nodes ---
    graph.add_node("data_gathering", data_gathering_node)
    graph.add_node("tools", tools_node)
    graph.add_node("rank", rank_node)
    graph.add_node("explain", explain_node)
    graph.add_node("synthesize", synthesize_node)

    # --- Entry point ---
    graph.set_entry_point("data_gathering")

    # --- ReAct loop ---
    # tools_condition returns "tools" if the last AIMessage has tool_calls, else END.
    # We map END → "rank" so the agent proceeds to deterministic ranking when it stops.
    graph.add_conditional_edges(
        "data_gathering",
        _tools_condition,
        {"tools": "tools", END: "rank"},
    )
    graph.add_edge("tools", "data_gathering")

    # --- Downstream (unchanged from original) ---
    graph.add_conditional_edges(
        "rank",
        _should_explain,
        {"explain": "explain", "synthesize": "synthesize"},
    )
    graph.add_edge("explain", "synthesize")
    graph.add_edge("synthesize", END)

    return graph.compile()


# Module-level compiled graph for reuse across requests
agent = build_graph()


def run_agent(
    query: str,
    persona: str = "value_investor",
    include_explanation: bool = True,
    all_personas: bool = False,
) -> dict:
    """Run the full agent pipeline and return the synthesized response.

    Args:
        query: Natural language search query.
        persona: Persona name (value_investor, pe_firm, growth_vc, strategic_acquirer, enterprise_buyer).
        include_explanation: Whether to generate NL explanation via GPT-4o (~5-10s extra).
        all_personas: Whether to run query across all 5 personas for cross-persona comparison.

    Returns:
        Synthesized response dict ready for JSON serialization.
    """
    from langchain_core.messages import HumanMessage
    from search.query_parser import parse_query

    # Pre-resolve entities before the ReAct loop starts so the agent receives
    # clean company_ids rather than raw text it needs to resolve itself.
    parsed = parse_query(query)
    parsed_intent = {
        "query_type": parsed.query_type,
        "raw_query": parsed.raw_query,
        "target_company": parsed.target_company,
        "compare_company": parsed.compare_company,
        "acquirer": parsed.acquirer,
        "attribute": parsed.attribute,
        "persona": parsed.persona or persona,
    }

    initial_state = {
        "query": query,
        "persona": persona,
        "include_explanation": include_explanation,
        "all_personas": all_personas,
        "parsed_intent": parsed_intent,
        # Seed the message history with the user query so data_gathering_node
        # sees a proper conversation on the first and all subsequent iterations.
        "messages": [HumanMessage(content=query)],
    }

    result = agent.invoke(initial_state, {"recursion_limit": 25})
    return result.get("synthesized", {"error": result.get("error", "Unknown error")})
