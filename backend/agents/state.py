"""
Agent state definition for LangGraph orchestration.
"""
from typing import TypedDict


class AgentState(TypedDict, total=False):
    query: str
    persona: str
    include_explanation: bool
    all_personas: bool
    # Populated by search_node
    search_result: dict | None
    all_persona_results: dict | None
    # Populated by explain_node
    explanation: str | None
    explanation_highlights: list[str] | None
    # Populated by synthesize_node
    synthesized: dict | None
    error: str | None
