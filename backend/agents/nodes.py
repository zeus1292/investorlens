"""
LangGraph node functions for InvestorLens agent.
Each node is a pure function: AgentState -> AgentState update.

Node pipeline:
  data_gathering_node ↔ tools_node   (ReAct loop)
       ↓ (no more tool calls)
    rank_node
       ↓
    explain_node  (optional)
       ↓
    synthesize_node
"""
import json
import sys
import os
import time
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from search.search_pipeline import search, search_all_personas, SearchResult
from agents.explainer import generate_explanation


# ---------------------------------------------------------------------------
# Shared serialization helpers
# ---------------------------------------------------------------------------

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


def _dicts_to_candidates(candidate_dicts: list[dict]) -> list:
    """Convert a list of candidate dicts (from tools) back to CandidateCompany objects."""
    from search.graph_traversal import CandidateCompany
    candidates = []
    for d in candidate_dicts:
        if not d or not d.get("company_id"):
            continue
        c = CandidateCompany(
            company_id=d["company_id"],
            name=d.get("name", ""),
            sector=d.get("sector", ""),
            moat_durability=d.get("moat_durability"),
            enterprise_readiness_score=d.get("enterprise_readiness_score"),
            developer_adoption_score=d.get("developer_adoption_score"),
            product_maturity_score=d.get("product_maturity_score"),
            customer_switching_cost=d.get("customer_switching_cost"),
            revenue_predictability=d.get("revenue_predictability"),
            market_timing_score=d.get("market_timing_score"),
            operational_improvement_potential=d.get("operational_improvement_potential"),
            market_cap_b=d.get("market_cap_b"),
            revenue_ttm_b=d.get("revenue_ttm_b"),
            gross_margin=d.get("gross_margin"),
            operating_margin=d.get("operating_margin"),
            ebitda_b=d.get("ebitda_b"),
            free_cash_flow_b=d.get("free_cash_flow_b"),
            debt_to_equity=d.get("debt_to_equity"),
            pe_ratio=d.get("pe_ratio"),
            price_to_sales=d.get("price_to_sales"),
            yoy_employee_growth=d.get("yoy_employee_growth"),
            github_stars=d.get("github_stars"),
            graph_edges=d.get("graph_edges") or [],
            competition_strength=d.get("competition_strength") or 0.0,
            partnership_count=d.get("partnership_count") or 0,
            partnership_fit=d.get("partnership_fit") or 0.0,
            competitive_threat=d.get("competitive_threat") or 0.0,
        )
        candidates.append(c)
    return candidates


def _build_ranked_result_dicts(ranked) -> list[dict]:
    """Serialize a list of RankedResult to JSON-compatible dicts."""
    return [
        {
            "rank": r.rank,
            "company_id": r.company_id,
            "name": r.name,
            "composite_score": r.composite_score,
            "score_breakdown": r.score_breakdown,
            "graph_context": r.graph_context,
        }
        for r in ranked
    ]


# ---------------------------------------------------------------------------
# ReAct node 1: data_gathering_node
# ---------------------------------------------------------------------------

def data_gathering_node(state: dict) -> dict:
    """ReAct loop step: call GPT-4o with tools to gather graph data.

    Returns {"messages": [AIMessage(...)]} — appended to state via add_messages.
    The AIMessage either has tool_calls (→ tools_node) or is a plain stop (→ rank_node).
    """
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        from agents.prompts import ORCHESTRATOR_SYSTEM, PERSONA_STRATEGIES
        from agents.tools import TOOLS
        from search.persona_configs import PERSONAS

        persona = state.get("persona", "value_investor")
        persona_config = PERSONAS.get(persona, PERSONAS["value_investor"])
        parsed_intent = state.get("parsed_intent") or {}

        # Build resolved entities string for the system prompt
        entities = []
        if parsed_intent.get("target_company"):
            entities.append(f"target_company={parsed_intent['target_company']}")
        if parsed_intent.get("compare_company"):
            entities.append(f"compare_company={parsed_intent['compare_company']}")
        if parsed_intent.get("acquirer"):
            entities.append(f"acquirer={parsed_intent['acquirer']}")
        if parsed_intent.get("attribute"):
            entities.append(f"attribute={parsed_intent['attribute']}")
        resolved_entities = ", ".join(entities) if entities else "none resolved"

        system_content = ORCHESTRATOR_SYSTEM.format(
            persona_display=persona_config.display_name,
            persona_strategy=PERSONA_STRATEGIES.get(persona, ""),
            resolved_entities=resolved_entities,
            query_type=parsed_intent.get("query_type", "unknown"),
        )

        messages = list(state.get("messages") or [])
        if not messages:
            # First iteration: seed with the user query
            messages = [HumanMessage(content=state.get("query", ""))]

        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        llm_with_tools = llm.bind_tools(TOOLS)
        full_messages = [SystemMessage(content=system_content)] + messages
        response = llm_with_tools.invoke(full_messages)
        return {"messages": [response]}

    except Exception as e:
        # Emit an AIMessage with no tool_calls so tools_condition routes to rank_node,
        # which will fall back to the legacy search pipeline.
        from langchain_core.messages import AIMessage
        return {"messages": [AIMessage(content=f"Data gathering unavailable: {e}. Proceeding to rank.")]}


# ---------------------------------------------------------------------------
# ReAct node 2: tools_node (custom — also updates gathered_candidates)
# ---------------------------------------------------------------------------

def tools_node(state: dict) -> dict:
    """Execute tool calls from the last AIMessage and accumulate candidates in state.

    Unlike langgraph.prebuilt.ToolNode, this custom node also parses tool results
    and updates gathered_candidates, compare_data, and center_company_id.
    """
    from langchain_core.messages import ToolMessage
    from agents.tools import TOOLS

    messages = state.get("messages") or []
    if not messages:
        return {}

    last_message = messages[-1]
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return {}

    # Build tool name → callable map
    tool_map = {t.name: t for t in TOOLS}

    tool_messages = []
    # Merge into existing accumulated candidates (not replace)
    gathered_candidates = dict(state.get("gathered_candidates") or {})
    compare_data = state.get("compare_data")
    center_company_id = state.get("center_company_id")

    for tc in last_message.tool_calls:
        tool_name = tc["name"]
        tool_args = tc.get("args", {})
        tool_call_id = tc["id"]

        try:
            tool_fn = tool_map.get(tool_name)
            if not tool_fn:
                content = json.dumps({"error": f"Unknown tool: {tool_name}"})
            else:
                content = tool_fn.invoke(tool_args)

            # Parse result and update accumulated state
            try:
                result = json.loads(content)

                # Accumulate candidates from any tool that returns them
                for c_dict in result.get("candidates", []):
                    cid = c_dict.get("company_id")
                    if cid:
                        gathered_candidates[cid] = c_dict

                # Special handling for compare_companies tool
                if result.get("tool") == "compare_companies":
                    compare_data = {
                        "company_a_id": result.get("company_a"),
                        "company_b_id": result.get("company_b"),
                        "company_a": result.get("company_a_profile"),
                        "company_b": result.get("company_b_profile"),
                        "shared_edges": result.get("shared_edges", []),
                        "common_competitors": result.get("common_competitors", []),
                        "shared_segments": result.get("shared_segments", []),
                        "shared_themes": result.get("shared_themes", []),
                    }
                    # Also add both companies to gathered_candidates
                    if result.get("company_a_profile"):
                        gathered_candidates[result["company_a"]] = result["company_a_profile"]
                    if result.get("company_b_profile"):
                        gathered_candidates[result["company_b"]] = result["company_b_profile"]
                    for cc in result.get("common_competitors", []):
                        if cc.get("company_id"):
                            gathered_candidates[cc["company_id"]] = cc

                # Track center company for graph visualization (first resolved company)
                if not center_company_id and result.get("tool") in (
                    "find_competitors", "get_company_profile", "find_acquisition_targets"
                ):
                    center_company_id = result.get("company_id") or result.get("acquirer")

            except (json.JSONDecodeError, KeyError, TypeError):
                pass  # Tool content is still passed to LLM even if we can't parse it

        except Exception as e:
            content = json.dumps({"error": str(e)})

        tool_messages.append(ToolMessage(
            content=content,
            tool_call_id=tool_call_id,
        ))

    return {
        "messages": tool_messages,
        "gathered_candidates": gathered_candidates,
        "compare_data": compare_data,
        "center_company_id": center_company_id,
    }


# ---------------------------------------------------------------------------
# Deterministic rank_node (replaces search_node's ranking step)
# ---------------------------------------------------------------------------

def rank_node(state: dict) -> dict:
    """Rank gathered candidates using deterministic persona-weighted scoring.

    Reads gathered_candidates and compare_data populated by the ReAct loop.
    Falls back to the legacy search() pipeline if no candidates were gathered.
    """
    try:
        from search.graph_traversal import get_graph_data
        from search.persona_ranker import rank_candidates
        from search.persona_configs import PERSONAS, get_persona
        from search.query_parser import ParsedQuery
        from graph.queries import get_driver

        t_start = time.time()
        persona = state.get("persona", "value_investor")
        parsed_intent = state.get("parsed_intent") or {}
        gathered = state.get("gathered_candidates") or {}
        compare_data_raw = state.get("compare_data")
        center_id = state.get("center_company_id") or ""

        # --- Fallback: use legacy search if the ReAct loop gathered nothing ---
        if not gathered and not compare_data_raw:
            try:
                query = state.get("query", "")
                result = search(query, persona=persona)
                search_dict = _search_result_to_dict(result)
                all_persona_dicts = None
                if state.get("all_personas"):
                    all_results = search_all_personas(query)
                    all_persona_dicts = {
                        p: _search_result_to_dict(sr) for p, sr in all_results.items()
                    }
                return {"search_result": search_dict, "all_persona_results": all_persona_dicts}
            except Exception as e:
                return {"error": f"Fallback search failed: {e}\n{traceback.format_exc()}"}

        # Resolve persona (query-embedded persona from parsed_intent takes precedence)
        active_persona = parsed_intent.get("persona") or persona
        if active_persona not in PERSONAS:
            active_persona = "value_investor"
        persona_config = get_persona(active_persona)

        # Build the ParsedQuery metadata used by explain_node + synthesize_node
        parsed_query = ParsedQuery(
            query_type=parsed_intent.get("query_type", "competitors_to"),
            raw_query=state.get("query", ""),
            target_company=parsed_intent.get("target_company", ""),
            compare_company=parsed_intent.get("compare_company", ""),
            acquirer=parsed_intent.get("acquirer", ""),
            persona=active_persona,
            attribute=parsed_intent.get("attribute"),
        )

        driver = get_driver()
        try:
            if compare_data_raw:
                # --- Compare query ---
                all_candidates = _dicts_to_candidates(list(gathered.values()))
                ranked = rank_candidates(all_candidates, persona_config)

                company_ids = list(gathered.keys())
                graph = get_graph_data(driver, company_ids)

                # Build compare_data in the format downstream nodes expect
                compare_out = _serialize_compare_data(compare_data_raw)

                elapsed_ms = int((time.time() - t_start) * 1000)
                search_dict = {
                    "query": _parsed_query_to_dict(parsed_query),
                    "persona": active_persona,
                    "persona_display": persona_config.display_name,
                    "results": _build_ranked_result_dicts(ranked),
                    "compare_data": compare_out,
                    "graph_data": graph,
                    "metadata": {
                        "elapsed_ms": elapsed_ms,
                        "candidate_count": len(all_candidates),
                        "source": "agentic",
                    },
                }

            else:
                # --- Competitors / acquisition / attribute query ---
                candidates = _dicts_to_candidates(list(gathered.values()))

                # Acquisition queries always use strategic_acquirer weights
                if parsed_query.query_type == "acquisition_target":
                    rank_persona = get_persona("strategic_acquirer")
                    acquirer = parsed_query.acquirer
                else:
                    rank_persona = persona_config
                    acquirer = ""

                ranked = rank_candidates(candidates, rank_persona, acquirer=acquirer)

                # Deduplicate + prepend center company for graph
                top_ids = [r.company_id for r in ranked[:10]]
                graph_ids = list(dict.fromkeys(([center_id] if center_id else []) + top_ids))
                graph = get_graph_data(driver, graph_ids, center_id=center_id)

                elapsed_ms = int((time.time() - t_start) * 1000)
                search_dict = {
                    "query": _parsed_query_to_dict(parsed_query),
                    "persona": active_persona,
                    "persona_display": persona_config.display_name,
                    "results": _build_ranked_result_dicts(ranked),
                    "compare_data": None,
                    "graph_data": graph,
                    "metadata": {
                        "elapsed_ms": elapsed_ms,
                        "candidate_count": len(candidates),
                        "source": "agentic",
                    },
                }

            # Handle all_personas if requested (still uses legacy pipeline for speed)
            all_persona_dicts = None
            if state.get("all_personas"):
                all_results = search_all_personas(state.get("query", ""))
                all_persona_dicts = {
                    p: _search_result_to_dict(sr) for p, sr in all_results.items()
                }

            return {"search_result": search_dict, "all_persona_results": all_persona_dicts}

        finally:
            driver.close()

    except Exception as e:
        return {"error": f"Ranking failed: {e}\n{traceback.format_exc()}"}


def _parsed_query_to_dict(pq) -> dict:
    """Serialize a ParsedQuery to a plain dict."""
    return {
        "query_type": pq.query_type,
        "raw_query": pq.raw_query,
        "target_company": pq.target_company,
        "compare_company": pq.compare_company,
        "acquirer": pq.acquirer,
        "persona": pq.persona,
        "attribute": pq.attribute,
    }


def _serialize_compare_data(raw: dict) -> dict:
    """Convert compare_data_raw from tools_node into the dict format downstream expects."""
    def _profile_fields(d: dict | None) -> dict | None:
        """Pick the subset of fields that downstream nodes/frontend uses."""
        if not d:
            return None
        return {
            "company_id": d.get("company_id"),
            "name": d.get("name"),
            "sector": d.get("sector"),
            "moat_durability": d.get("moat_durability"),
            "enterprise_readiness_score": d.get("enterprise_readiness_score"),
            "developer_adoption_score": d.get("developer_adoption_score"),
            "product_maturity_score": d.get("product_maturity_score"),
            "customer_switching_cost": d.get("customer_switching_cost"),
            "revenue_predictability": d.get("revenue_predictability"),
            "market_timing_score": d.get("market_timing_score"),
            "operational_improvement_potential": d.get("operational_improvement_potential"),
            "market_cap_b": d.get("market_cap_b"),
            "revenue_ttm_b": d.get("revenue_ttm_b"),
            "operating_margin": d.get("operating_margin"),
        }

    return {
        "company_a": _profile_fields(raw.get("company_a")),
        "company_b": _profile_fields(raw.get("company_b")),
        "shared_edges": raw.get("shared_edges", []),
        "common_competitors": [
            {"company_id": c.get("company_id"), "name": c.get("name")}
            for c in raw.get("common_competitors", [])
            if c.get("company_id")
        ],
        "shared_segments": raw.get("shared_segments", []),
        "shared_themes": raw.get("shared_themes", []),
    }


# ---------------------------------------------------------------------------
# Unchanged downstream nodes
# ---------------------------------------------------------------------------

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
