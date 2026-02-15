"""
Search pipeline orchestrator for InvestorLens.
Orchestrates: parse → retrieve → rank.
"""
import sys
import os
import time
from dataclasses import dataclass, field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from graph.queries import get_driver
from search.query_parser import parse_query, ParsedQuery
from search.persona_configs import PERSONAS, get_persona, list_personas
from search.graph_traversal import (
    get_competitors_to, get_compare_data, get_acquisition_targets,
    get_attribute_ranked, get_graph_data,
)
from search.persona_ranker import rank_candidates, RankedResult


@dataclass
class SearchResult:
    query: ParsedQuery
    persona: str
    persona_display: str
    results: list[RankedResult] = field(default_factory=list)
    compare_data: dict | None = None        # for compare queries
    graph_data: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)


def search(query: str, persona: str = "value_investor") -> SearchResult:
    """Execute a search query with persona-based ranking.

    Args:
        query: Natural language query string
        persona: Persona name (value_investor, pe_firm, growth_vc, strategic_acquirer, enterprise_buyer)

    Returns:
        SearchResult with ranked companies, graph data, and metadata
    """
    t_start = time.time()

    # 1. Parse
    parsed = parse_query(query)

    # 2. Resolve persona: query-embedded persona takes precedence
    active_persona = parsed.persona or persona
    if active_persona not in PERSONAS:
        active_persona = "value_investor"
    persona_config = get_persona(active_persona)

    driver = get_driver()
    try:
        # 3. Retrieve candidates based on query type
        if parsed.query_type == "competitors_to":
            candidates = get_competitors_to(driver, parsed.target_company, active_persona)
            ranked = rank_candidates(candidates, persona_config)
            company_ids = [parsed.target_company] + [r.company_id for r in ranked[:10]]
            graph = get_graph_data(driver, company_ids, center_id=parsed.target_company)

            return SearchResult(
                query=parsed,
                persona=active_persona,
                persona_display=persona_config.display_name,
                results=ranked,
                graph_data=graph,
                metadata=_meta(t_start, len(candidates)),
            )

        elif parsed.query_type == "compare":
            compare_data = get_compare_data(driver, parsed.target_company, parsed.compare_company)
            # Rank the two companies + common competitors together
            all_candidates = []
            for key in ("company_a", "company_b"):
                if compare_data[key]:
                    all_candidates.append(compare_data[key])
            all_candidates.extend(compare_data.get("common_competitors", []))
            ranked = rank_candidates(all_candidates, persona_config)

            company_ids = [parsed.target_company, parsed.compare_company] + [c.company_id for c in compare_data.get("common_competitors", [])]
            graph = get_graph_data(driver, company_ids)

            return SearchResult(
                query=parsed,
                persona=active_persona,
                persona_display=persona_config.display_name,
                results=ranked,
                compare_data=compare_data,
                graph_data=graph,
                metadata=_meta(t_start, len(all_candidates)),
            )

        elif parsed.query_type == "acquisition_target":
            candidates = get_acquisition_targets(driver, parsed.acquirer, parsed.target_company)
            # Always use strategic_acquirer persona for acquisition queries
            acq_persona = get_persona("strategic_acquirer")
            ranked = rank_candidates(candidates, acq_persona, acquirer=parsed.acquirer)

            company_ids = [parsed.acquirer, parsed.target_company] + [r.company_id for r in ranked[:10]]
            graph = get_graph_data(driver, company_ids, center_id=parsed.target_company)

            return SearchResult(
                query=parsed,
                persona="strategic_acquirer",
                persona_display=acq_persona.display_name,
                results=ranked,
                graph_data=graph,
                metadata=_meta(t_start, len(candidates)),
            )

        elif parsed.query_type == "attribute_search":
            candidates = get_attribute_ranked(driver, parsed.attribute or "moat_durability")
            ranked = rank_candidates(candidates, persona_config)

            company_ids = [r.company_id for r in ranked[:10]]
            graph = get_graph_data(driver, company_ids)

            return SearchResult(
                query=parsed,
                persona=active_persona,
                persona_display=persona_config.display_name,
                results=ranked,
                graph_data=graph,
                metadata=_meta(t_start, len(candidates)),
            )

        # Fallback
        return SearchResult(
            query=parsed,
            persona=active_persona,
            persona_display=persona_config.display_name,
            metadata={"error": "Unknown query type", "elapsed_ms": _elapsed(t_start)},
        )

    finally:
        driver.close()


def search_all_personas(query: str) -> dict[str, SearchResult]:
    """Run a query across all 5 personas. Returns {persona_name: SearchResult}."""
    results = {}
    for persona_name in list_personas():
        results[persona_name] = search(query, persona=persona_name)
    return results


def _meta(t_start: float, candidate_count: int) -> dict:
    return {
        "elapsed_ms": _elapsed(t_start),
        "candidate_count": candidate_count,
    }


def _elapsed(t_start: float) -> int:
    return int((time.time() - t_start) * 1000)
