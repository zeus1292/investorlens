"""
Agent state definition for LangGraph orchestration.
"""
from typing import TypedDict, Annotated

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    # Input (unchanged)
    query: str
    persona: str
    include_explanation: bool
    all_personas: bool

    # ReAct message history — add_messages ensures append-not-replace semantics
    messages: Annotated[list[AnyMessage], add_messages]

    # Structured data set before agent starts and accumulated during ReAct loop
    parsed_intent: dict | None      # {query_type, target_company, compare_company, acquirer, attribute}
    gathered_candidates: dict | None  # company_id → candidate dict (accumulated across iterations)
    compare_data: dict | None         # raw compare tool output (for compare queries)
    center_company_id: str | None     # company_id to center the graph visualization on

    # Populated by rank_node + explain_node + synthesize_node (unchanged)
    search_result: dict | None
    all_persona_results: dict | None
    explanation: str | None
    explanation_highlights: list[str] | None
    synthesized: dict | None
    error: str | None
