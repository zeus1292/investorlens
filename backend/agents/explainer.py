"""
NL explanation generator for InvestorLens.
Uses GPT-4o to produce persona-specific narrative explanations of search results.
"""
import sys
import os

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import OPENAI_API_KEY
from search.persona_configs import PERSONAS
from agents.prompts import get_prompt, PERSONA_VOICES


class ExplanationOutput(BaseModel):
    narrative: str = Field(description="2-4 paragraph persona-specific explanation of the results")
    highlights: list[str] = Field(description="3-5 key takeaway bullets")


def _format_results_context(ranked_results: list[dict], top_n: int = 10) -> str:
    """Format ranked results into a context string for the prompt."""
    lines = []
    for r in ranked_results[:top_n]:
        breakdown_str = ", ".join(
            f"{k}: {v:.3f}" for k, v in r.get("score_breakdown", {}).items()
            if not k.startswith("_")
        )
        graph_boost = r.get("score_breakdown", {}).get("_graph_boost", 0)
        edges = r.get("graph_context", [])
        edge_str = ", ".join(
            f"{e.get('type')}(strength={e.get('strength', 'N/A')})"
            for e in edges[:3]
        ) if edges else "none"

        lines.append(
            f"#{r.get('rank', '?')}. {r.get('name', r.get('company_id', '?'))} "
            f"(score: {r.get('composite_score', 0):.3f})\n"
            f"   Breakdown: {breakdown_str}\n"
            f"   Graph boost: {graph_boost:.3f} | Edges: {edge_str}"
        )
    return "\n\n".join(lines)


def _format_compare_context(compare_data: dict | None) -> str:
    """Format compare-specific data."""
    if not compare_data:
        return ""
    parts = []
    for label in ("company_a", "company_b"):
        c = compare_data.get(label)
        if c:
            parts.append(f"{c.get('name', c.get('company_id', '?'))}: "
                         f"moat={c.get('moat_durability')}, "
                         f"enterprise={c.get('enterprise_readiness_score')}, "
                         f"developer={c.get('developer_adoption_score')}, "
                         f"switching_cost={c.get('customer_switching_cost')}")
    return "\n".join(parts)


def _format_weight_description(persona_name: str) -> str:
    """Format persona weights into a readable string."""
    config = PERSONAS.get(persona_name)
    if not config:
        return ""
    return ", ".join(f"{k} ({v:.0%})" for k, v in config.weights.items())


def _format_cross_persona_context(all_persona_results: dict | None) -> str:
    """Format cross-persona contrast when available."""
    if not all_persona_results:
        return ""
    lines = ["Cross-persona contrast (top 3 per persona):"]
    for persona_name, result in all_persona_results.items():
        display = PERSONAS.get(persona_name, None)
        display_name = display.display_name if display else persona_name
        top3 = result.get("results", [])[:3]
        names = [r.get("name", r.get("company_id", "?")) for r in top3]
        lines.append(f"  {display_name}: {', '.join(names)}")
    return "\n".join(lines) + "\n\n"


def generate_explanation(
    search_result: dict,
    query_type: str,
    persona: str,
    all_persona_results: dict | None = None,
) -> tuple[str, list[str]]:
    """Generate a persona-specific NL explanation of search results.

    Args:
        search_result: Serialized SearchResult dict with results, compare_data, etc.
        query_type: One of competitors_to, compare, acquisition_target, attribute_search
        persona: Persona name
        all_persona_results: Optional cross-persona results for contrast

    Returns:
        (narrative, highlights) tuple
    """
    prompt = get_prompt(query_type)
    llm = ChatOpenAI(
        model="gpt-4o",
        api_key=OPENAI_API_KEY,
        temperature=0.4,
        max_tokens=1500,
    )
    chain = prompt | llm.with_structured_output(ExplanationOutput)

    # Build common template variables
    persona_voice = PERSONA_VOICES.get(persona, PERSONA_VOICES["value_investor"])
    weight_desc = _format_weight_description(persona)
    results_context = _format_results_context(search_result.get("results", []))
    cross_persona = _format_cross_persona_context(all_persona_results)

    query_info = search_result.get("query", {})
    raw_query = query_info.get("raw_query", search_result.get("raw_query", ""))

    # Build variables dict based on query type
    variables = {
        "persona_voice": persona_voice,
        "weight_description": weight_desc,
        "raw_query": raw_query,
        "results_context": results_context,
        "cross_persona_context": cross_persona,
    }

    if query_type == "competitors_to":
        variables["target_company"] = query_info.get("target_company", "")

    elif query_type == "compare":
        variables["company_a"] = query_info.get("target_company", "")
        variables["company_b"] = query_info.get("compare_company", "")
        variables["shared_edges"] = str(search_result.get("compare_data", {}).get("shared_edges", []))
        variables["common_competitors"] = ", ".join(
            c.get("name", c.get("company_id", ""))
            for c in (search_result.get("compare_data", {}).get("common_competitors", []))
        ) or "none"

    elif query_type == "acquisition_target":
        variables["acquirer"] = query_info.get("acquirer", "")
        variables["target_company"] = query_info.get("target_company", "")

    elif query_type == "attribute_search":
        variables["attribute"] = query_info.get("attribute", "moat_durability")

    result = chain.invoke(variables)
    return result.narrative, result.highlights
