"""
Neo4j Graph Loader.
Reads enriched companies.json and loads everything into Neo4j:
  - Company nodes with all attributes
  - Segment nodes + TARGETS_SAME_SEGMENT edges
  - InvestmentTheme nodes + SHARES_INVESTMENT_THEME edges
  - Inter-company relationship edges from LLM enrichment
"""
import json
import sys
import os

from neo4j import GraphDatabase

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, COMPANIES_FILE

SCHEMA_FILE = os.path.join(os.path.dirname(__file__), "schema.cypher")

# Map sector codes to display names
SEGMENT_NAMES = {
    "cloud_data_platforms": "Cloud Data Platforms",
    "ai_ml_platforms": "AI/ML Platforms",
    "data_integration_etl": "Data Integration & ETL",
    "data_observability_governance": "Data Observability & Governance",
    "vector_ai_infrastructure": "Vector & AI Infrastructure",
    "emerging_disruptors": "Emerging Disruptors",
}

# Relationship types that are bidirectional (create both directions)
BIDIRECTIONAL = {"COMPETES_WITH", "PARTNERS_WITH", "SIMILAR_FINANCIAL_PROFILE", "SHARES_INVESTMENT_THEME"}


def run_schema(driver):
    """Execute schema.cypher to create constraints and indexes."""
    with open(SCHEMA_FILE, "r") as f:
        schema_text = f.read()

    statements = [s.strip() for s in schema_text.split(";") if s.strip() and not s.strip().startswith("//")]

    with driver.session() as session:
        for stmt in statements:
            try:
                session.run(stmt)
            except Exception as e:
                if "already exists" in str(e).lower() or "equivalent" in str(e).lower():
                    pass
                else:
                    print(f"  Schema warning: {e}")

    print("Schema constraints and indexes created.")


def clear_graph(driver):
    """Remove all existing nodes and relationships."""
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    print("Cleared existing graph data.")


def load_companies(driver, companies: list):
    """Create Company nodes with all attributes."""
    query = """
    MERGE (c:Company {company_id: $company_id})
    SET c.name = $name,
        c.ticker = $ticker,
        c.status = $status,
        c.sector = $sector,
        c.description = $description,
        c.founded_year = $founded_year,
        c.hq = $hq,
        c.market_cap_b = $market_cap_b,
        c.revenue_ttm_b = $revenue_ttm_b,
        c.gross_margin = $gross_margin,
        c.operating_margin = $operating_margin,
        c.ebitda_b = $ebitda_b,
        c.free_cash_flow_b = $free_cash_flow_b,
        c.debt_to_equity = $debt_to_equity,
        c.pe_ratio = $pe_ratio,
        c.price_to_sales = $price_to_sales,
        c.employee_count_est = $employee_count_est,
        c.github_stars = $github_stars,
        c.moat_durability = $moat_durability,
        c.moat_reasoning = $moat_reasoning,
        c.enterprise_readiness_score = $enterprise_readiness_score,
        c.operational_improvement_potential = $operational_improvement_potential,
        c.financial_profile_cluster = $financial_profile_cluster,
        c.developer_adoption_score = $developer_adoption_score,
        c.product_maturity_score = $product_maturity_score,
        c.customer_switching_cost = $customer_switching_cost,
        c.revenue_predictability = $revenue_predictability,
        c.market_timing_score = $market_timing_score
    """

    with driver.session() as session:
        for c in companies:
            fin = c.get("financials", {})
            growth = c.get("growth_signals", {})
            llm = c.get("llm_enriched", {})

            params = {
                "company_id": c["company_id"],
                "name": c["name"],
                "ticker": c.get("ticker"),
                "status": c["status"],
                "sector": c["sector"],
                "description": c.get("description", ""),
                "founded_year": c.get("founded_year"),
                "hq": c.get("hq"),
                # Financials
                "market_cap_b": fin.get("market_cap_b"),
                "revenue_ttm_b": fin.get("revenue_ttm_b"),
                "gross_margin": fin.get("gross_margin"),
                "operating_margin": fin.get("operating_margin"),
                "ebitda_b": fin.get("ebitda_b"),
                "free_cash_flow_b": fin.get("free_cash_flow_b"),
                "debt_to_equity": fin.get("debt_to_equity"),
                "pe_ratio": fin.get("pe_ratio"),
                "price_to_sales": fin.get("price_to_sales"),
                # Growth signals
                "employee_count_est": growth.get("employee_count_est"),
                "github_stars": growth.get("github_stars"),
                # LLM enriched
                "moat_durability": llm.get("moat_durability"),
                "moat_reasoning": llm.get("moat_reasoning"),
                "enterprise_readiness_score": llm.get("enterprise_readiness_score"),
                "operational_improvement_potential": llm.get("operational_improvement_potential"),
                "financial_profile_cluster": llm.get("financial_profile_cluster"),
                "developer_adoption_score": llm.get("developer_adoption_score"),
                "product_maturity_score": llm.get("product_maturity_score"),
                "customer_switching_cost": llm.get("customer_switching_cost"),
                "revenue_predictability": llm.get("revenue_predictability"),
                "market_timing_score": llm.get("market_timing_score"),
            }
            session.run(query, params)

    print(f"Loaded {len(companies)} Company nodes.")


def load_segments(driver, companies: list):
    """Create Segment nodes and TARGETS_SAME_SEGMENT edges."""
    with driver.session() as session:
        for segment_id, display_name in SEGMENT_NAMES.items():
            session.run(
                "MERGE (s:Segment {name: $name}) SET s.display_name = $display_name",
                {"name": segment_id, "display_name": display_name},
            )

        for c in companies:
            session.run(
                """
                MATCH (c:Company {company_id: $company_id})
                MATCH (s:Segment {name: $segment})
                MERGE (c)-[:TARGETS_SAME_SEGMENT]->(s)
                """,
                {"company_id": c["company_id"], "segment": c["sector"]},
            )

    print(f"Loaded {len(SEGMENT_NAMES)} Segment nodes with edges.")


def load_investment_themes(driver, companies: list):
    """Create InvestmentTheme nodes and SHARES_INVESTMENT_THEME edges."""
    themes_seen = set()
    with driver.session() as session:
        for c in companies:
            llm = c.get("llm_enriched", {})
            themes = llm.get("investment_themes", [])
            for theme in themes:
                if theme not in themes_seen:
                    session.run(
                        "MERGE (t:InvestmentTheme {name: $name})",
                        {"name": theme},
                    )
                    themes_seen.add(theme)
                session.run(
                    """
                    MATCH (c:Company {company_id: $company_id})
                    MATCH (t:InvestmentTheme {name: $theme})
                    MERGE (c)-[:SHARES_INVESTMENT_THEME]->(t)
                    """,
                    {"company_id": c["company_id"], "theme": theme},
                )

    print(f"Loaded {len(themes_seen)} InvestmentTheme nodes with edges.")


def load_relationships(driver, companies: list):
    """Create inter-company relationship edges from LLM enrichment."""
    # Build set of valid company_ids
    valid_ids = {c["company_id"] for c in companies}

    edge_count = 0
    skipped = 0

    with driver.session() as session:
        for c in companies:
            llm = c.get("llm_enriched", {})
            relationships = llm.get("competitive_relationships", [])

            for rel in relationships:
                target = rel.get("target_company_id", "")
                rel_type = rel.get("relationship_type", "")
                strength = rel.get("strength", 0.5)
                reasoning = rel.get("reasoning", "")

                if target not in valid_ids:
                    skipped += 1
                    continue

                # Create the edge using APOC-free approach (parameterized relationship type)
                # Neo4j doesn't support parameterized relationship types directly,
                # so we use a CASE approach with all known types
                for known_type in ["COMPETES_WITH", "DISRUPTS", "PARTNERS_WITH",
                                   "SIMILAR_FINANCIAL_PROFILE", "ACQUIRED", "SUPPLIES_TO"]:
                    if rel_type == known_type:
                        query = f"""
                        MATCH (a:Company {{company_id: $source}})
                        MATCH (b:Company {{company_id: $target}})
                        MERGE (a)-[r:{known_type}]->(b)
                        SET r.strength = $strength, r.reasoning = $reasoning
                        """
                        session.run(query, {
                            "source": c["company_id"],
                            "target": target,
                            "strength": strength,
                            "reasoning": reasoning,
                        })
                        edge_count += 1

                        # Create reverse edge for bidirectional relationships
                        if known_type in BIDIRECTIONAL:
                            reverse_query = f"""
                            MATCH (a:Company {{company_id: $target}})
                            MATCH (b:Company {{company_id: $source}})
                            MERGE (a)-[r:{known_type}]->(b)
                            SET r.strength = $strength, r.reasoning = $reasoning
                            """
                            session.run(reverse_query, {
                                "source": c["company_id"],
                                "target": target,
                                "strength": strength,
                                "reasoning": reasoning,
                            })
                        break

    print(f"Loaded {edge_count} relationship edges (skipped {skipped} invalid targets).")


def run():
    """Main loader: connect to Neo4j and load everything."""
    print("Connecting to Neo4j...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    try:
        driver.verify_connectivity()
        print(f"Connected to {NEO4J_URI}")
    except Exception as e:
        print(f"Failed to connect to Neo4j: {e}")
        print("Make sure Neo4j is running: docker start neo4j-investorlens")
        sys.exit(1)

    with open(COMPANIES_FILE, "r") as f:
        data = json.load(f)
    companies = data["companies"]

    print(f"\nLoading {len(companies)} companies into Neo4j...")
    print()

    # Clear and reload
    clear_graph(driver)
    run_schema(driver)
    load_companies(driver, companies)
    load_segments(driver, companies)
    load_investment_themes(driver, companies)
    load_relationships(driver, companies)

    # Summary
    with driver.session() as session:
        node_count = session.run("MATCH (n) RETURN count(n) AS count").single()["count"]
        edge_count = session.run("MATCH ()-[r]->() RETURN count(r) AS count").single()["count"]
        print(f"\n=== Graph Summary ===")
        print(f"Total nodes: {node_count}")
        print(f"Total edges: {edge_count}")

    driver.close()
    print("\nDone.")


if __name__ == "__main__":
    run()
