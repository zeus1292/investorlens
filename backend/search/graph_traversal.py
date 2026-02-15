"""
Graph traversal for InvestorLens search pipeline.
Retrieves candidate companies from Neo4j based on query type.
"""
import sys
import os
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from graph.queries import get_driver


@dataclass
class CandidateCompany:
    """A candidate company retrieved from the graph with full attributes."""
    company_id: str
    name: str
    sector: str
    # LLM scores
    moat_durability: float | None = None
    enterprise_readiness_score: float | None = None
    developer_adoption_score: float | None = None
    product_maturity_score: float | None = None
    customer_switching_cost: float | None = None
    revenue_predictability: float | None = None
    market_timing_score: float | None = None
    operational_improvement_potential: float | None = None
    # Financials
    market_cap_b: float | None = None
    revenue_ttm_b: float | None = None
    gross_margin: float | None = None
    operating_margin: float | None = None
    ebitda_b: float | None = None
    free_cash_flow_b: float | None = None
    debt_to_equity: float | None = None
    pe_ratio: float | None = None
    price_to_sales: float | None = None
    # Growth
    yoy_employee_growth: float | None = None
    github_stars: int | None = None
    # Graph context
    graph_edges: list = None       # edges that connected this candidate
    competition_strength: float = 0.0
    partnership_count: int = 0
    partnership_fit: float = 0.0   # partnership with acquirer specifically
    competitive_threat: float = 0.0  # shared competitors with target

    def __post_init__(self):
        if self.graph_edges is None:
            self.graph_edges = []


def _full_company_query() -> str:
    """Return Cypher RETURN clause for all company attributes."""
    return """
        t.company_id AS company_id, t.name AS name, t.sector AS sector,
        t.moat_durability AS moat_durability,
        t.enterprise_readiness_score AS enterprise_readiness_score,
        t.developer_adoption_score AS developer_adoption_score,
        t.product_maturity_score AS product_maturity_score,
        t.customer_switching_cost AS customer_switching_cost,
        t.revenue_predictability AS revenue_predictability,
        t.market_timing_score AS market_timing_score,
        t.operational_improvement_potential AS operational_improvement_potential,
        t.market_cap_b AS market_cap_b,
        t.revenue_ttm_b AS revenue_ttm_b,
        t.gross_margin AS gross_margin,
        t.operating_margin AS operating_margin,
        t.ebitda_b AS ebitda_b,
        t.free_cash_flow_b AS free_cash_flow_b,
        t.debt_to_equity AS debt_to_equity,
        t.pe_ratio AS pe_ratio,
        t.price_to_sales AS price_to_sales,
        t.yoy_employee_growth AS yoy_employee_growth,
        t.github_stars AS github_stars
    """


def _record_to_candidate(record: dict, edges: list | None = None) -> CandidateCompany:
    """Convert a Neo4j record dict to CandidateCompany."""
    return CandidateCompany(
        company_id=record["company_id"],
        name=record["name"],
        sector=record.get("sector", ""),
        moat_durability=record.get("moat_durability"),
        enterprise_readiness_score=record.get("enterprise_readiness_score"),
        developer_adoption_score=record.get("developer_adoption_score"),
        product_maturity_score=record.get("product_maturity_score"),
        customer_switching_cost=record.get("customer_switching_cost"),
        revenue_predictability=record.get("revenue_predictability"),
        market_timing_score=record.get("market_timing_score"),
        operational_improvement_potential=record.get("operational_improvement_potential"),
        market_cap_b=record.get("market_cap_b"),
        revenue_ttm_b=record.get("revenue_ttm_b"),
        gross_margin=record.get("gross_margin"),
        operating_margin=record.get("operating_margin"),
        ebitda_b=record.get("ebitda_b"),
        free_cash_flow_b=record.get("free_cash_flow_b"),
        debt_to_equity=record.get("debt_to_equity"),
        pe_ratio=record.get("pe_ratio"),
        price_to_sales=record.get("price_to_sales"),
        yoy_employee_growth=record.get("yoy_employee_growth"),
        github_stars=record.get("github_stars"),
        graph_edges=edges or [],
    )


def get_competitors_to(driver, company_id: str, persona: str | None = None) -> list[CandidateCompany]:
    """Get competitor candidates via multiple traversal strategies.

    Merges results from COMPETES_WITH, TARGETS_SAME_SEGMENT,
    SHARES_INVESTMENT_THEME, and optionally DISRUPTS.
    """
    candidates: dict[str, CandidateCompany] = {}

    # 1. Direct COMPETES_WITH edges
    query = f"""
    MATCH (c:Company {{company_id: $cid}})-[r:COMPETES_WITH]-(t:Company)
    WITH t, max(r.strength) AS strength
    RETURN {_full_company_query()}, strength
    """
    with driver.session() as session:
        for rec in session.run(query, {"cid": company_id}):
            r = dict(rec)
            cand = _record_to_candidate(r, [{"type": "COMPETES_WITH", "strength": r["strength"]}])
            cand.competition_strength = r["strength"] or 0.0
            candidates[cand.company_id] = cand

    # 2. TARGETS_SAME_SEGMENT siblings
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

    # 3. SHARES_INVESTMENT_THEME overlaps
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
            edge = {"type": "SHARES_INVESTMENT_THEME", "themes": r.get("shared_themes"), "overlap": r.get("overlap")}
            if cid in candidates:
                candidates[cid].graph_edges.append(edge)
            else:
                candidates[cid] = _record_to_candidate(r, [edge])

    # 4. DISRUPTS edges (always include, but Growth VC persona boosts these)
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
            edge = {"type": "DISRUPTS", "strength": r.get("strength"), "direction": r.get("direction")}
            if cid in candidates:
                candidates[cid].graph_edges.append(edge)
            else:
                candidates[cid] = _record_to_candidate(r, [edge])

    # Filter out candidates connected ONLY via SHARES_INVESTMENT_THEME —
    # theme overlap adds context but isn't sufficient to call something a competitor.
    filtered = {}
    for cid, cand in candidates.items():
        edge_types = {e.get("type") for e in cand.graph_edges}
        has_strong_edge = edge_types & {"COMPETES_WITH", "DISRUPTS", "TARGETS_SAME_SEGMENT"}
        if has_strong_edge:
            filtered[cid] = cand
    candidates = filtered

    # Enrich partnership counts for all candidates
    _enrich_partnership_counts(driver, candidates)

    return list(candidates.values())


def get_compare_data(driver, company_a: str, company_b: str) -> dict:
    """Get structured comparison data for two companies.

    Returns both company nodes, their shared edges, common competitors, etc.
    """
    result = {"company_a": None, "company_b": None, "shared_edges": [], "common_competitors": [], "shared_segments": [], "shared_themes": []}

    # Full node data for both
    for label, cid in [("company_a", company_a), ("company_b", company_b)]:
        query = """
        MATCH (t:Company {company_id: $cid})
        RETURN """ + _full_company_query()
        with driver.session() as session:
            rec = session.run(query, {"cid": cid}).single()
            if rec:
                result[label] = _record_to_candidate(dict(rec))

    # Direct relationships between them
    query = """
    MATCH (a:Company {company_id: $a})-[r]-(b:Company {company_id: $b})
    RETURN type(r) AS rel_type, r.strength AS strength, r.reasoning AS reasoning
    """
    with driver.session() as session:
        for rec in session.run(query, {"a": company_a, "b": company_b}):
            result["shared_edges"].append(dict(rec))

    # Common competitors
    query = f"""
    MATCH (a:Company {{company_id: $a}})-[:COMPETES_WITH]-(common:Company)-[:COMPETES_WITH]-(b:Company {{company_id: $b}})
    WHERE common.company_id <> $a AND common.company_id <> $b
    WITH DISTINCT common
    MATCH (t:Company {{company_id: common.company_id}})
    RETURN {_full_company_query()}
    """
    with driver.session() as session:
        for rec in session.run(query, {"a": company_a, "b": company_b}):
            result["common_competitors"].append(_record_to_candidate(dict(rec)))

    # Shared segments
    query = """
    MATCH (a:Company {company_id: $a})-[:TARGETS_SAME_SEGMENT]->(s:Segment)<-[:TARGETS_SAME_SEGMENT]-(b:Company {company_id: $b})
    RETURN s.name AS segment, s.display_name AS display_name
    """
    with driver.session() as session:
        for rec in session.run(query, {"a": company_a, "b": company_b}):
            result["shared_segments"].append(dict(rec))

    # Shared themes
    query = """
    MATCH (a:Company {company_id: $a})-[:SHARES_INVESTMENT_THEME]->(th:InvestmentTheme)<-[:SHARES_INVESTMENT_THEME]-(b:Company {company_id: $b})
    RETURN th.name AS theme
    """
    with driver.session() as session:
        for rec in session.run(query, {"a": company_a, "b": company_b}):
            result["shared_themes"].append(rec["theme"])

    return result


def get_acquisition_targets(driver, acquirer: str, compete_with: str) -> list[CandidateCompany]:
    """Find acquisition targets for an acquirer to compete with a target company.

    Strategy:
    1. Companies that COMPETES_WITH or DISRUPTS the target
    2. Bonus for companies that PARTNERS_WITH the acquirer
    3. Exclude the acquirer and the target themselves
    """
    candidates: dict[str, CandidateCompany] = {}

    # 1. Companies competing with the target
    query = f"""
    MATCH (target:Company {{company_id: $target}})-[r:COMPETES_WITH]-(t:Company)
    WHERE t.company_id <> $acquirer
    WITH t, max(r.strength) AS strength
    RETURN {_full_company_query()}, strength, 'COMPETES_WITH' AS rel_type
    """
    with driver.session() as session:
        for rec in session.run(query, {"target": compete_with, "acquirer": acquirer}):
            r = dict(rec)
            cand = _record_to_candidate(r, [{"type": "COMPETES_WITH", "target": compete_with, "strength": r["strength"]}])
            cand.competitive_threat = r["strength"] or 0.0
            candidates[cand.company_id] = cand

    # 2. Companies disrupting the target
    query = f"""
    MATCH (target:Company {{company_id: $target}})<-[r:DISRUPTS]-(t:Company)
    WHERE t.company_id <> $acquirer
    RETURN {_full_company_query()}, r.strength AS strength
    """
    with driver.session() as session:
        for rec in session.run(query, {"target": compete_with, "acquirer": acquirer}):
            r = dict(rec)
            cid = r["company_id"]
            edge = {"type": "DISRUPTS", "target": compete_with, "strength": r.get("strength")}
            if cid in candidates:
                candidates[cid].graph_edges.append(edge)
                candidates[cid].competitive_threat = max(candidates[cid].competitive_threat, r.get("strength") or 0.0)
            else:
                cand = _record_to_candidate(r, [edge])
                cand.competitive_threat = r.get("strength") or 0.0
                candidates[cid] = cand

    # 3. Companies in same segment as target (broader net)
    query = f"""
    MATCH (target:Company {{company_id: $target}})-[:TARGETS_SAME_SEGMENT]->(s:Segment)<-[:TARGETS_SAME_SEGMENT]-(t:Company)
    WHERE t.company_id <> $acquirer AND t.company_id <> $target
    RETURN {_full_company_query()}, s.display_name AS shared_segment
    """
    with driver.session() as session:
        for rec in session.run(query, {"target": compete_with, "acquirer": acquirer}):
            r = dict(rec)
            cid = r["company_id"]
            edge = {"type": "TARGETS_SAME_SEGMENT", "segment": r.get("shared_segment")}
            if cid in candidates:
                candidates[cid].graph_edges.append(edge)
            else:
                candidates[cid] = _record_to_candidate(r, [edge])

    # 4. Check partnership with acquirer — bonus for existing partners
    query = """
    MATCH (acquirer:Company {company_id: $acquirer})-[r:PARTNERS_WITH]-(t:Company)
    RETURN t.company_id AS partner_id, r.strength AS strength
    """
    acquirer_partners = {}
    with driver.session() as session:
        for rec in session.run(query, {"acquirer": acquirer}):
            acquirer_partners[rec["partner_id"]] = rec["strength"] or 0.0

    for cid, cand in candidates.items():
        if cid in acquirer_partners:
            cand.partnership_fit = acquirer_partners[cid]
            cand.graph_edges.append({"type": "PARTNERS_WITH", "partner": acquirer, "strength": acquirer_partners[cid]})

    # Enrich partnership counts
    _enrich_partnership_counts(driver, candidates)

    return list(candidates.values())


def get_attribute_ranked(driver, attribute: str, limit: int = 20) -> list[CandidateCompany]:
    """Get all companies sorted by a specific attribute."""
    # Validate attribute exists as a Neo4j property
    valid_attrs = [
        "moat_durability", "enterprise_readiness_score", "developer_adoption_score",
        "product_maturity_score", "customer_switching_cost", "revenue_predictability",
        "market_timing_score", "operational_improvement_potential",
        "market_cap_b", "revenue_ttm_b", "operating_margin", "yoy_employee_growth",
    ]
    if attribute not in valid_attrs:
        attribute = "moat_durability"  # safe fallback

    query = f"""
    MATCH (t:Company)
    WHERE t.{attribute} IS NOT NULL
    RETURN {_full_company_query()}
    ORDER BY t.{attribute} DESC
    LIMIT $limit
    """
    candidates = []
    with driver.session() as session:
        for rec in session.run(query, {"limit": limit}):
            candidates.append(_record_to_candidate(dict(rec)))

    _enrich_partnership_counts(driver, {c.company_id: c for c in candidates})
    return candidates


def get_graph_data(driver, company_ids: list[str], center_id: str = "") -> dict:
    """Get nodes + edges for visualization, covering the given company IDs."""
    if not company_ids:
        return {"nodes": [], "edges": []}

    query = """
    MATCH (c:Company)
    WHERE c.company_id IN $ids
    OPTIONAL MATCH (c)-[r]-(other:Company)
    WHERE other.company_id IN $ids
    RETURN c.company_id AS id, c.name AS label, c.sector AS sector,
           c.market_cap_b AS market_cap_b, c.moat_durability AS moat_durability,
           collect(DISTINCT {
               source: startNode(r).company_id,
               target: endNode(r).company_id,
               type: type(r),
               strength: r.strength
           }) AS edges
    """
    nodes = []
    all_edges = {}
    with driver.session() as session:
        for rec in session.run(query, {"ids": company_ids}):
            r = dict(rec)
            nodes.append({
                "id": r["id"],
                "label": r["label"],
                "type": "company",
                "sector": r["sector"],
                "market_cap_b": r["market_cap_b"],
                "moat_durability": r["moat_durability"],
                "is_center": r["id"] == center_id,
            })
            for e in r["edges"]:
                if e.get("source") and e.get("target"):
                    key = f"{e['source']}-{e['type']}-{e['target']}"
                    if key not in all_edges:
                        all_edges[key] = e

    return {"nodes": nodes, "edges": list(all_edges.values())}


def _enrich_partnership_counts(driver, candidates: dict[str, "CandidateCompany"]):
    """Add partnership_count to each candidate."""
    if not candidates:
        return
    cids = list(candidates.keys())
    query = """
    MATCH (c:Company)-[r:PARTNERS_WITH]-(t:Company)
    WHERE c.company_id IN $cids
    RETURN c.company_id AS cid, count(DISTINCT t) AS partner_count
    """
    with driver.session() as session:
        for rec in session.run(query, {"cids": cids}):
            cid = rec["cid"]
            if cid in candidates:
                candidates[cid].partnership_count = rec["partner_count"]
