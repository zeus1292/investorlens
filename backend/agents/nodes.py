"""
LangGraph node functions for InvestorLens agent.
Each node is a pure function: AgentState -> AgentState update.
"""
import sys
import os
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from search.search_pipeline import search, search_all_personas, SearchResult
from agents.explainer import generate_explanation


def _search_result_to_dict(sr: SearchResult) -> dict:
    """Convert a SearchResult dataclass to a JSON-serializable dict."""
    d = {}
    # ParsedQuery
    d["query"] = {
        "query_type": sr.query.query_type,
        "raw_query": sr.query.raw_query,
        "target_company": sr.query.target_company,
        "compare_company": sr.query.compare_company,
        "acquirer": sr.query.acquirer,
        "persona": sr.query.persona,
        "attribute": sr.query.attribute,
    }
    d["persona"] = sr.persona
    d["persona_display"] = sr.persona_display
    # RankedResults
    d["results"] = [
        {
            "rank": r.rank,
            "company_id": r.company_id,
            "name": r.name,
            "composite_score": r.composite_score,
            "score_breakdown": r.score_breakdown,
            "graph_context": r.graph_context,
        }
        for r in sr.results
    ]
    # Compare data — convert CandidateCompany objects to dicts
    if sr.compare_data:
        cd = {}
        for key in ("company_a", "company_b"):
            obj = sr.compare_data.get(key)
            if obj:
                cd[key] = {
                    "company_id": obj.company_id,
                    "name": obj.name,
                    "sector": obj.sector,
                    "moat_durability": obj.moat_durability,
                    "enterprise_readiness_score": obj.enterprise_readiness_score,
                    "developer_adoption_score": obj.developer_adoption_score,
                    "product_maturity_score": obj.product_maturity_score,
                    "customer_switching_cost": obj.customer_switching_cost,
                    "revenue_predictability": obj.revenue_predictability,
                    "market_timing_score": obj.market_timing_score,
                    "operational_improvement_potential": obj.operational_improvement_potential,
                    "market_cap_b": obj.market_cap_b,
                    "revenue_ttm_b": obj.revenue_ttm_b,
                    "operating_margin": obj.operating_margin,
                }
            else:
                cd[key] = None
        cd["shared_edges"] = sr.compare_data.get("shared_edges", [])
        cd["common_competitors"] = [
            {"company_id": c.company_id, "name": c.name}
            for c in sr.compare_data.get("common_competitors", [])
        ]
        cd["shared_segments"] = sr.compare_data.get("shared_segments", [])
        cd["shared_themes"] = sr.compare_data.get("shared_themes", [])
        d["compare_data"] = cd
    else:
        d["compare_data"] = None
    d["graph_data"] = sr.graph_data
    d["metadata"] = sr.metadata
    return d


def search_node(state: dict) -> dict:
    """Execute the Phase 2 search pipeline."""
    try:
        query = state["query"]
        persona = state.get("persona", "value_investor")
        all_personas = state.get("all_personas", False)

        result = search(query, persona=persona)
        search_dict = _search_result_to_dict(result)

        all_persona_dicts = None
        if all_personas:
            all_results = search_all_personas(query)
            all_persona_dicts = {
                p: _search_result_to_dict(sr)
                for p, sr in all_results.items()
            }

        return {
            "search_result": search_dict,
            "all_persona_results": all_persona_dicts,
        }
    except Exception as e:
        return {"error": f"Search failed: {e}\n{traceback.format_exc()}"}


def explain_node(state: dict) -> dict:
    """Generate NL explanation using GPT-4o."""
    try:
        sr = state.get("search_result")
        if not sr:
            return {"error": "No search results to explain"}

        query_type = sr["query"]["query_type"]
        persona = sr["persona"]

        narrative, highlights = generate_explanation(
            search_result=sr,
            query_type=query_type,
            persona=persona,
            all_persona_results=state.get("all_persona_results"),
        )
        return {
            "explanation": narrative,
            "explanation_highlights": highlights,
        }
    except Exception as e:
        return {"error": f"Explanation failed: {e}\n{traceback.format_exc()}"}


def synthesize_node(state: dict) -> dict:
    """Merge structured search results + NL explanation into final response."""
    sr = state.get("search_result", {})
    if not sr:
        return {"synthesized": {"error": state.get("error", "No results")}}

    response = {
        "query": sr.get("query"),
        "persona": sr.get("persona"),
        "persona_display": sr.get("persona_display"),
        "results": sr.get("results", []),
        "compare_data": sr.get("compare_data"),
        "graph_data": sr.get("graph_data", {}),
        "explanation": state.get("explanation"),
        "explanation_highlights": state.get("explanation_highlights"),
        "all_personas": None,
        "metadata": sr.get("metadata", {}),
    }

    # Add cross-persona top-3 summaries if available
    all_persona = state.get("all_persona_results")
    if all_persona:
        persona_summaries = {}
        for p_name, p_result in all_persona.items():
            persona_summaries[p_name] = {
                "persona_display": p_result.get("persona_display"),
                "top_results": [
                    {
                        "rank": r["rank"],
                        "company_id": r["company_id"],
                        "name": r["name"],
                        "composite_score": r["composite_score"],
                    }
                    for r in p_result.get("results", [])[:5]
                ],
            }
        response["all_personas"] = persona_summaries

    return {"synthesized": response}
