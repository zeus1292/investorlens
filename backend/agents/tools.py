"""
LangChain tools for the InvestorLens data-gathering agent.
Each tool wraps existing graph traversal functions and returns JSON strings.
Tools share the graph_traversal primitives; each creates its own driver per call.
"""
import json
import sys
import os

from langchain_core.tools import tool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from graph.queries import get_driver, get_company
from search.graph_traversal import (
    get_competitors_to,
    get_compare_data,
    get_acquisition_targets,
    get_attribute_ranked,
    _full_company_query,
    _record_to_candidate,
    _enrich_partnership_counts,
)


def _candidate_to_dict(c) -> dict:
    """Serialize a CandidateCompany to a JSON-compatible dict."""
    return {
        "company_id": c.company_id,
        "name": c.name,
        "sector": c.sector,
        "moat_durability": c.moat_durability,
        "enterprise_readiness_score": c.enterprise_readiness_score,
        "developer_adoption_score": c.developer_adoption_score,
        "product_maturity_score": c.product_maturity_score,
        "customer_switching_cost": c.customer_switching_cost,
        "revenue_predictability": c.revenue_predictability,
        "market_timing_score": c.market_timing_score,
        "operational_improvement_potential": c.operational_improvement_potential,
        "market_cap_b": c.market_cap_b,
        "revenue_ttm_b": c.revenue_ttm_b,
        "gross_margin": c.gross_margin,
        "operating_margin": c.operating_margin,
        "ebitda_b": c.ebitda_b,
        "free_cash_flow_b": c.free_cash_flow_b,
        "debt_to_equity": c.debt_to_equity,
        "pe_ratio": c.pe_ratio,
        "price_to_sales": c.price_to_sales,
        "yoy_employee_growth": c.yoy_employee_growth,
        "github_stars": c.github_stars,
        "graph_edges": c.graph_edges,
        "competition_strength": c.competition_strength,
        "partnership_count": c.partnership_count,
        "partnership_fit": c.partnership_fit,
        "competitive_threat": c.competitive_threat,
    }


@tool
def find_competitors(company_id: str, min_strength: float = 0.3) -> str:
    """Find companies with direct COMPETES_WITH, DISRUPTS, or TARGETS_SAME_SEGMENT
    edges to the given company.

    Args:
        company_id: The company_id of the target company (e.g. 'snowflake', 'c3ai').
        min_strength: Minimum competition strength threshold 0.0-1.0 (default 0.3).
                      Only filters COMPETES_WITH edges; DISRUPTS/SEGMENT edges are always included.
    """
    driver = get_driver()
    try:
        candidates = get_competitors_to(driver, company_id)
        if min_strength > 0.0:
            filtered = []
            for c in candidates:
                has_only_competes = all(e.get("type") == "COMPETES_WITH" for e in c.graph_edges)
                if has_only_competes and c.competition_strength < min_strength:
                    continue
                filtered.append(c)
            candidates = filtered

        result = {
            "tool": "find_competitors",
            "company_id": company_id,
            "count": len(candidates),
            "summary": f"Found {len(candidates)} competitors/adjacent companies for {company_id}",
            "candidates": [_candidate_to_dict(c) for c in candidates],
        }
        return json.dumps(result)
    finally:
        driver.close()


@tool
def find_adjacent(company_id: str, edge_types: list) -> str:
    """Find companies related via specified edge types.

    Args:
        company_id: The company_id to search from.
        edge_types: List of edge types to traverse. Valid values:
                    DISRUPTS, PARTNERS_WITH, TARGETS_SAME_SEGMENT, SHARES_INVESTMENT_THEME
    """
    valid_types = {"DISRUPTS", "PARTNERS_WITH", "TARGETS_SAME_SEGMENT", "SHARES_INVESTMENT_THEME"}
    edge_types = [t for t in (edge_types or []) if t in valid_types]

    if not edge_types:
        return json.dumps({
            "tool": "find_adjacent",
            "error": "No valid edge types provided. Use: DISRUPTS, PARTNERS_WITH, TARGETS_SAME_SEGMENT, SHARES_INVESTMENT_THEME",
            "candidates": [],
        })

    driver = get_driver()
    try:
        candidates: dict = {}

        for edge_type in edge_types:
            if edge_type == "DISRUPTS":
                query = f"""
                MATCH (c:Company {{company_id: $cid}})-[r:DISRUPTS]-(t:Company)
                RETURN {_full_company_query()},
                       r.strength AS strength,
                       CASE WHEN startNode(r) = c THEN 'disrupts' ELSE 'disrupted_by' END AS direction
                """
                with driver.session() as session:
                    for rec in session.run(query, {"cid": company_id}):
                        r = dict(rec)
                        cid = r["company_id"]
                        edge = {
                            "type": "DISRUPTS",
                            "strength": r.get("strength"),
                            "direction": r.get("direction"),
                        }
                        if cid in candidates:
                            candidates[cid].graph_edges.append(edge)
                        else:
                            candidates[cid] = _record_to_candidate(r, [edge])

            elif edge_type == "PARTNERS_WITH":
                query = f"""
                MATCH (c:Company {{company_id: $cid}})-[r:PARTNERS_WITH]-(t:Company)
                RETURN {_full_company_query()}, r.strength AS strength
                """
                with driver.session() as session:
                    for rec in session.run(query, {"cid": company_id}):
                        r = dict(rec)
                        cid = r["company_id"]
                        edge = {"type": "PARTNERS_WITH", "strength": r.get("strength")}
                        if cid in candidates:
                            candidates[cid].graph_edges.append(edge)
                        else:
                            candidates[cid] = _record_to_candidate(r, [edge])

            elif edge_type == "TARGETS_SAME_SEGMENT":
                query = f"""
                MATCH (c:Company {{company_id: $cid}})-[:TARGETS_SAME_SEGMENT]->(s:Segment)<-[:TARGETS_SAME_SEGMENT]-(t:Company)
                WHERE t.company_id <> $cid
                RETURN {_full_company_query()}, s.display_name AS shared_segment
                """
                with driver.session() as session:
                    for rec in session.run(query, {"cid": company_id}):
                        r = dict(rec)
                        cid = r["company_id"]
                        edge = {"type": "TARGETS_SAME_SEGMENT", "segment": r.get("shared_segment")}
                        if cid in candidates:
                            candidates[cid].graph_edges.append(edge)
                        else:
                            candidates[cid] = _record_to_candidate(r, [edge])

            elif edge_type == "SHARES_INVESTMENT_THEME":
                query = f"""
                MATCH (c:Company {{company_id: $cid}})-[:SHARES_INVESTMENT_THEME]->(th:InvestmentTheme)<-[:SHARES_INVESTMENT_THEME]-(t:Company)
                WHERE t.company_id <> $cid
                WITH t, collect(th.name) AS shared_themes, count(th) AS overlap
                RETURN {_full_company_query()}, shared_themes, overlap
                """
                with driver.session() as session:
                    for rec in session.run(query, {"cid": company_id}):
                        r = dict(rec)
                        cid = r["company_id"]
                        edge = {
                            "type": "SHARES_INVESTMENT_THEME",
                            "themes": r.get("shared_themes"),
                            "overlap": r.get("overlap"),
                        }
                        if cid in candidates:
                            candidates[cid].graph_edges.append(edge)
                        else:
                            candidates[cid] = _record_to_candidate(r, [edge])

        _enrich_partnership_counts(driver, candidates)
        candidate_list = list(candidates.values())

        result = {
            "tool": "find_adjacent",
            "company_id": company_id,
            "edge_types": edge_types,
            "count": len(candidate_list),
            "summary": f"Found {len(candidate_list)} companies via {edge_types} edges from {company_id}",
            "candidates": [_candidate_to_dict(c) for c in candidate_list],
        }
        return json.dumps(result)
    finally:
        driver.close()


@tool
def get_company_profile(company_id: str) -> str:
    """Get the full profile for a company including LLM scores, financials, and graph relationships.

    Args:
        company_id: The company_id (e.g. 'snowflake', 'c3ai', 'databricks').
    """
    driver = get_driver()
    try:
        profile = get_company(driver, company_id)
        if not profile:
            return json.dumps({
                "tool": "get_company_profile",
                "error": f"Company '{company_id}' not found in graph",
            })

        # Get top relationships
        query = """
        MATCH (c:Company {company_id: $cid})-[r]-(other)
        RETURN type(r) AS rel_type,
               CASE WHEN other:Company THEN other.name ELSE other.name END AS other_name,
               CASE WHEN other:Company THEN other.company_id ELSE other.name END AS other_id,
               labels(other)[0] AS other_type,
               r.strength AS strength
        LIMIT 30
        """
        relationships = []
        with driver.session() as session:
            for rec in session.run(query, {"cid": company_id}):
                relationships.append(dict(rec))

        result = {
            "tool": "get_company_profile",
            "company_id": company_id,
            "profile": dict(profile),
            "relationships": relationships,
        }
        return json.dumps(result, default=str)
    finally:
        driver.close()


@tool
def compare_companies(company_a: str, company_b: str) -> str:
    """Get head-to-head comparison data: direct edges, common competitors, shared segments/themes.

    Args:
        company_a: First company_id.
        company_b: Second company_id.
    """
    driver = get_driver()
    try:
        data = get_compare_data(driver, company_a, company_b)

        result = {
            "tool": "compare_companies",
            "company_a": company_a,
            "company_b": company_b,
            "company_a_profile": _candidate_to_dict(data["company_a"]) if data.get("company_a") else None,
            "company_b_profile": _candidate_to_dict(data["company_b"]) if data.get("company_b") else None,
            "shared_edges": data.get("shared_edges", []),
            "common_competitors": [
                _candidate_to_dict(c) for c in data.get("common_competitors", [])
            ],
            "shared_segments": data.get("shared_segments", []),
            "shared_themes": data.get("shared_themes", []),
            "summary": (
                f"Comparison of {company_a} vs {company_b}: "
                f"{len(data.get('shared_edges', []))} direct edges, "
                f"{len(data.get('common_competitors', []))} common competitors, "
                f"{len(data.get('shared_themes', []))} shared themes"
            ),
        }
        return json.dumps(result)
    finally:
        driver.close()


@tool
def find_acquisition_targets(acquirer: str, compete_with: str = "") -> str:
    """Find strategic acquisition candidates for an acquirer.

    Prioritises companies that directly compete with or disrupt the target company.
    Also boosts candidates that already partner with the acquirer.

    Args:
        acquirer: The company_id of the potential acquirer (e.g. 'bigquery' for Google).
        compete_with: The company_id the acquirer wants to compete against (e.g. 'palantir').
    """
    driver = get_driver()
    try:
        candidates = get_acquisition_targets(driver, acquirer, compete_with)

        result = {
            "tool": "find_acquisition_targets",
            "acquirer": acquirer,
            "compete_with": compete_with,
            "count": len(candidates),
            "summary": f"Found {len(candidates)} acquisition targets for {acquirer} to compete with {compete_with}",
            "candidates": [_candidate_to_dict(c) for c in candidates],
        }
        return json.dumps(result)
    finally:
        driver.close()


@tool
def search_by_attribute(attribute: str, limit: int = 20) -> str:
    """Rank all companies by a specific LLM-scored or financial attribute.

    Args:
        attribute: Attribute to rank by. Valid values:
                   moat_durability, enterprise_readiness_score, developer_adoption_score,
                   product_maturity_score, customer_switching_cost, revenue_predictability,
                   market_timing_score, operational_improvement_potential,
                   market_cap_b, revenue_ttm_b, operating_margin, yoy_employee_growth
        limit: Maximum number of results (default 20, max 37).
    """
    driver = get_driver()
    try:
        candidates = get_attribute_ranked(driver, attribute, limit=limit)

        result = {
            "tool": "search_by_attribute",
            "attribute": attribute,
            "count": len(candidates),
            "summary": f"Top {len(candidates)} companies by {attribute}",
            "candidates": [_candidate_to_dict(c) for c in candidates],
        }
        return json.dumps(result)
    finally:
        driver.close()


# Export the tool list for LLM binding and ToolNode
TOOLS = [
    find_competitors,
    find_adjacent,
    get_company_profile,
    compare_companies,
    find_acquisition_targets,
    search_by_attribute,
]
