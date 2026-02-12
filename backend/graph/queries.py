"""
Cypher query templates for InvestorLens.
Reusable graph queries for the search pipeline.
"""
import sys
import os

from neo4j import GraphDatabase

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD


def get_driver():
    """Get a Neo4j driver instance."""
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def get_company(driver, company_id: str) -> dict | None:
    """Get a single company node with all attributes."""
    query = """
    MATCH (c:Company {company_id: $company_id})
    RETURN c
    """
    with driver.session() as session:
        result = session.run(query, {"company_id": company_id}).single()
        if result:
            return dict(result["c"])
    return None


def get_competitors(driver, company_id: str, limit: int = 20) -> list[dict]:
    """Get competitors via COMPETES_WITH edges, ordered by strength."""
    query = """
    MATCH (c:Company {company_id: $company_id})-[r:COMPETES_WITH]-(t:Company)
    RETURN t.company_id AS company_id, t.name AS name, t.sector AS sector,
           r.strength AS strength, r.reasoning AS reasoning,
           t.moat_durability AS moat_durability,
           t.market_cap_b AS market_cap_b,
           t.revenue_ttm_b AS revenue_ttm_b,
           t.operating_margin AS operating_margin,
           t.enterprise_readiness_score AS enterprise_readiness_score,
           t.developer_adoption_score AS developer_adoption_score,
           t.financial_profile_cluster AS financial_profile_cluster
    ORDER BY r.strength DESC
    LIMIT $limit
    """
    with driver.session() as session:
        results = session.run(query, {"company_id": company_id, "limit": limit})
        return [dict(r) for r in results]


def get_competitors_via_segment(driver, company_id: str, limit: int = 20) -> list[dict]:
    """Get companies in the same segment (indirect competitors)."""
    query = """
    MATCH (c:Company {company_id: $company_id})-[:TARGETS_SAME_SEGMENT]->(s:Segment)<-[:TARGETS_SAME_SEGMENT]-(t:Company)
    WHERE t.company_id <> $company_id
    RETURN t.company_id AS company_id, t.name AS name, t.sector AS sector,
           s.display_name AS shared_segment,
           t.moat_durability AS moat_durability,
           t.market_cap_b AS market_cap_b,
           t.revenue_ttm_b AS revenue_ttm_b,
           t.operating_margin AS operating_margin,
           t.enterprise_readiness_score AS enterprise_readiness_score,
           t.developer_adoption_score AS developer_adoption_score,
           t.financial_profile_cluster AS financial_profile_cluster
    LIMIT $limit
    """
    with driver.session() as session:
        results = session.run(query, {"company_id": company_id, "limit": limit})
        return [dict(r) for r in results]


def get_companies_sharing_themes(driver, company_id: str, limit: int = 20) -> list[dict]:
    """Get companies sharing investment themes."""
    query = """
    MATCH (c:Company {company_id: $company_id})-[:SHARES_INVESTMENT_THEME]->(t:InvestmentTheme)<-[:SHARES_INVESTMENT_THEME]-(other:Company)
    WHERE other.company_id <> $company_id
    WITH other, collect(t.name) AS shared_themes, count(t) AS theme_overlap
    RETURN other.company_id AS company_id, other.name AS name, other.sector AS sector,
           shared_themes, theme_overlap,
           other.moat_durability AS moat_durability,
           other.market_cap_b AS market_cap_b,
           other.financial_profile_cluster AS financial_profile_cluster
    ORDER BY theme_overlap DESC
    LIMIT $limit
    """
    with driver.session() as session:
        results = session.run(query, {"company_id": company_id, "limit": limit})
        return [dict(r) for r in results]


def get_disruption_targets(driver, company_id: str) -> list[dict]:
    """Get companies that disrupt or are disrupted by this company."""
    query = """
    MATCH (c:Company {company_id: $company_id})-[r:DISRUPTS]-(t:Company)
    RETURN t.company_id AS company_id, t.name AS name,
           r.strength AS strength, r.reasoning AS reasoning,
           CASE WHEN startNode(r) = c THEN 'disrupts' ELSE 'disrupted_by' END AS direction
    ORDER BY r.strength DESC
    """
    with driver.session() as session:
        results = session.run(query, {"company_id": company_id})
        return [dict(r) for r in results]


def get_subgraph(driver, company_id: str, depth: int = 2, limit: int = 50) -> dict:
    """Get the neighborhood subgraph for visualization.
    Returns nodes and edges suitable for graph rendering.
    """
    query = """
    MATCH path = (c:Company {company_id: $company_id})-[r*1..""" + str(depth) + """]->(t)
    WHERE ALL(rel IN r WHERE type(rel) IN ['COMPETES_WITH', 'DISRUPTS', 'PARTNERS_WITH', 'TARGETS_SAME_SEGMENT', 'SHARES_INVESTMENT_THEME'])
    WITH nodes(path) AS ns, relationships(path) AS rs
    UNWIND ns AS n
    WITH COLLECT(DISTINCT n) AS nodes, COLLECT(DISTINCT rs) AS all_rels
    UNWIND all_rels AS rel_list
    UNWIND rel_list AS rel
    WITH nodes, COLLECT(DISTINCT rel) AS edges
    RETURN
      [n IN nodes | {
        id: CASE WHEN n:Company THEN n.company_id
             WHEN n:Segment THEN n.name
             WHEN n:InvestmentTheme THEN n.name
             END,
        label: CASE WHEN n:Company THEN n.name
               WHEN n:Segment THEN n.display_name
               WHEN n:InvestmentTheme THEN n.name
               END,
        type: CASE WHEN n:Company THEN 'company'
              WHEN n:Segment THEN 'segment'
              WHEN n:InvestmentTheme THEN 'theme'
              END,
        sector: CASE WHEN n:Company THEN n.sector ELSE null END,
        market_cap_b: CASE WHEN n:Company THEN n.market_cap_b ELSE null END,
        moat_durability: CASE WHEN n:Company THEN n.moat_durability ELSE null END
      }][0..50] AS nodes,
      [e IN edges | {
        source: CASE WHEN startNode(e):Company THEN startNode(e).company_id
                WHEN startNode(e):Segment THEN startNode(e).name
                WHEN startNode(e):InvestmentTheme THEN startNode(e).name
                END,
        target: CASE WHEN endNode(e):Company THEN endNode(e).company_id
                WHEN endNode(e):Segment THEN endNode(e).name
                WHEN endNode(e):InvestmentTheme THEN endNode(e).name
                END,
        type: type(e),
        strength: e.strength
      }][0..100] AS edges
    """
    with driver.session() as session:
        result = session.run(query, {"company_id": company_id}).single()
        if result:
            return {"nodes": result["nodes"], "edges": result["edges"]}
    return {"nodes": [], "edges": []}


def get_all_companies(driver) -> list[dict]:
    """Get all companies with key attributes."""
    query = """
    MATCH (c:Company)
    RETURN c.company_id AS company_id, c.name AS name, c.sector AS sector,
           c.status AS status, c.market_cap_b AS market_cap_b,
           c.moat_durability AS moat_durability,
           c.enterprise_readiness_score AS enterprise_readiness_score,
           c.developer_adoption_score AS developer_adoption_score,
           c.financial_profile_cluster AS financial_profile_cluster
    ORDER BY c.market_cap_b DESC
    """
    with driver.session() as session:
        results = session.run(query)
        return [dict(r) for r in results]


def get_similar_financial_profiles(driver, company_id: str, limit: int = 10) -> list[dict]:
    """Get companies with similar financial profiles."""
    query = """
    MATCH (c:Company {company_id: $company_id})-[r:SIMILAR_FINANCIAL_PROFILE]-(t:Company)
    RETURN t.company_id AS company_id, t.name AS name,
           r.strength AS similarity, r.reasoning AS reasoning,
           t.market_cap_b AS market_cap_b,
           t.financial_profile_cluster AS financial_profile_cluster
    ORDER BY r.strength DESC
    LIMIT $limit
    """
    with driver.session() as session:
        results = session.run(query, {"company_id": company_id, "limit": limit})
        return [dict(r) for r in results]


def get_partnerships(driver, company_id: str) -> list[dict]:
    """Get partner companies."""
    query = """
    MATCH (c:Company {company_id: $company_id})-[r:PARTNERS_WITH]-(t:Company)
    RETURN t.company_id AS company_id, t.name AS name,
           r.strength AS strength, r.reasoning AS reasoning
    ORDER BY r.strength DESC
    """
    with driver.session() as session:
        results = session.run(query, {"company_id": company_id})
        return [dict(r) for r in results]


# --- Verification queries ---

def verify_graph(driver):
    """Run verification queries and print summary."""
    with driver.session() as session:
        # Node counts
        company_count = session.run("MATCH (c:Company) RETURN count(c) AS n").single()["n"]
        segment_count = session.run("MATCH (s:Segment) RETURN count(s) AS n").single()["n"]
        theme_count = session.run("MATCH (t:InvestmentTheme) RETURN count(t) AS n").single()["n"]

        # Edge counts by type
        edge_types = session.run("""
            MATCH ()-[r]->()
            RETURN type(r) AS type, count(r) AS count
            ORDER BY count DESC
        """)
        edge_summary = [(r["type"], r["count"]) for r in edge_types]

        # Sector distribution
        sectors = session.run("""
            MATCH (c:Company)
            RETURN c.sector AS sector, count(c) AS count
            ORDER BY count DESC
        """)
        sector_summary = [(r["sector"], r["count"]) for r in sectors]

    print("=== Graph Verification ===")
    print(f"Companies: {company_count}")
    print(f"Segments: {segment_count}")
    print(f"Investment Themes: {theme_count}")
    print()
    print("Edge types:")
    for etype, count in edge_summary:
        print(f"  {etype}: {count}")
    print()
    print("Sector distribution:")
    for sector, count in sector_summary:
        print(f"  {sector}: {count}")
    print()

    return {
        "companies": company_count,
        "segments": segment_count,
        "themes": theme_count,
        "edges": edge_summary,
        "sectors": sector_summary,
    }


if __name__ == "__main__":
    driver = get_driver()
    try:
        verify_graph(driver)

        # Test Snowflake competitors
        print("\n=== Snowflake Competitors (COMPETES_WITH) ===")
        for c in get_competitors(driver, "snowflake", limit=10):
            print(f"  {c['name']} (strength: {c['strength']}) — {c['reasoning']}")

        # Test C3 AI competitors
        print("\n=== C3 AI Competitors (COMPETES_WITH) ===")
        for c in get_competitors(driver, "c3ai", limit=10):
            print(f"  {c['name']} (strength: {c['strength']}) — {c['reasoning']}")

    finally:
        driver.close()
