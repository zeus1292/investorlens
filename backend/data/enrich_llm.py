"""
LLM Enrichment Pipeline.
Uses LangChain + Claude to score all companies on persona-relevant attributes
and extract competitive relationships for the knowledge graph.
"""
import json
import sys
import os
import time
from datetime import datetime

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import COMPANIES_FILE, ANTHROPIC_API_KEY

# Valid relationship types for the knowledge graph
RELATIONSHIP_TYPES = [
    "COMPETES_WITH",
    "TARGETS_SAME_SEGMENT",
    "SHARES_INVESTMENT_THEME",
    "SIMILAR_FINANCIAL_PROFILE",
    "DISRUPTS",
    "PARTNERS_WITH",
    "ACQUIRED",
    "SUPPLIES_TO",
]


# --- Pydantic models for structured output ---

class CompetitiveRelationship(BaseModel):
    target_company_id: str = Field(description="company_id of the related company")
    relationship_type: str = Field(description=f"One of: {', '.join(RELATIONSHIP_TYPES)}")
    strength: float = Field(description="Relationship strength from 0.0 to 1.0", ge=0.0, le=1.0)
    reasoning: str = Field(description="Brief explanation of why this relationship exists")


class CompanyEnrichment(BaseModel):
    moat_durability: int = Field(description="Durability of competitive moat, 1-10 scale", ge=1, le=10)
    moat_reasoning: str = Field(description="Explanation of what constitutes the moat")
    investment_themes: list[str] = Field(description="3-5 investment theme tags (e.g., 'data_gravity', 'open_source', 'consumption_pricing', 'enterprise_switching_costs', 'developer_led_growth', 'ai_infrastructure', 'hybrid_cloud', 'data_governance', 'mlops', 'vector_search', 'real_time_analytics', 'serverless')")
    competitive_relationships: list[CompetitiveRelationship] = Field(description="5-10 competitive relationships with other companies in the universe")
    enterprise_readiness_score: int = Field(description="Enterprise readiness, 1-10 scale", ge=1, le=10)
    operational_improvement_potential: int = Field(description="Potential for PE-style operational improvement, 1-10 scale", ge=1, le=10)
    financial_profile_cluster: str = Field(description="One of: 'high_growth_cash_burning', 'growth_approaching_profitability', 'profitable_growth', 'mature_cash_generating', 'declining_legacy', 'early_stage_pre_revenue'")
    developer_adoption_score: int = Field(description="Developer community and adoption strength, 1-10 scale", ge=1, le=10)
    product_maturity_score: int = Field(description="Product maturity and feature completeness, 1-10 scale", ge=1, le=10)
    customer_switching_cost: int = Field(description="How hard it is for customers to switch away, 1-10 scale", ge=1, le=10)
    revenue_predictability: int = Field(description="Predictability/recurring nature of revenue, 1-10 scale", ge=1, le=10)
    market_timing_score: int = Field(description="How well positioned for current market trends, 1-10 scale", ge=1, le=10)


ENRICHMENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert analyst covering Enterprise AI and Data Infrastructure companies.
You are scoring companies for a knowledge graph that powers a persona-driven investment research tool.

The company universe includes these companies (use these exact company_ids for relationships):
{company_list}

Score honestly and differentiate meaningfully — not every company is a 7/10 on everything.
Use the full 1-10 scale. A legacy company might score 2 on developer adoption but 9 on enterprise readiness.
A startup might score 9 on market timing but 3 on product maturity.

For competitive_relationships, generate 5-10 relationships using ONLY company_ids from the universe above.
Use the exact relationship types: COMPETES_WITH, TARGETS_SAME_SEGMENT, SHARES_INVESTMENT_THEME, SIMILAR_FINANCIAL_PROFILE, DISRUPTS, PARTNERS_WITH, ACQUIRED, SUPPLIES_TO.

For financial_profile_cluster, choose from: high_growth_cash_burning, growth_approaching_profitability, profitable_growth, mature_cash_generating, declining_legacy, early_stage_pre_revenue."""),
    ("human", """Analyze this company and provide enrichment scores:

**Company:** {company_name} ({company_id})
**Sector:** {sector}
**Description:** {description}
**Status:** {status}
**Financial Data:** {financials}
**Growth Signals:** {growth_signals}

Provide your structured analysis.""")
])


def build_company_list(companies: list) -> str:
    """Build a formatted list of all companies for the prompt context."""
    lines = []
    for c in companies:
        lines.append(f"  - {c['company_id']}: {c['name']} ({c['sector']})")
    return "\n".join(lines)


def enrich_company(llm, company: dict, company_list: str) -> dict:
    """Run LLM enrichment for a single company."""
    chain = ENRICHMENT_PROMPT | llm.with_structured_output(CompanyEnrichment)

    financials_str = json.dumps(company.get("financials", {}), indent=2)
    growth_str = json.dumps(company.get("growth_signals", {}), indent=2)

    result = chain.invoke({
        "company_list": company_list,
        "company_name": company["name"],
        "company_id": company["company_id"],
        "sector": company["sector"],
        "description": company["description"],
        "status": company["status"],
        "financials": financials_str,
        "growth_signals": growth_str,
    })

    # Convert to dict
    enriched = result.model_dump()

    # Validate relationship types
    valid_relationships = []
    for rel in enriched["competitive_relationships"]:
        if rel["relationship_type"] in RELATIONSHIP_TYPES:
            valid_relationships.append(rel)
    enriched["competitive_relationships"] = valid_relationships

    return enriched


def run(batch_size: int = 5, skip_existing: bool = True):
    """Run LLM enrichment for all companies."""
    with open(COMPANIES_FILE, "r") as f:
        data = json.load(f)

    companies = data["companies"]
    company_list = build_company_list(companies)

    llm = ChatAnthropic(
        model="claude-sonnet-4-5-20250929",
        api_key=ANTHROPIC_API_KEY,
        temperature=0.3,
        max_tokens=2000,
    )

    print(f"Starting LLM enrichment for {len(companies)} companies...")
    print(f"Skip existing: {skip_existing}")
    print()

    enriched_count = 0
    skipped_count = 0

    for i, company in enumerate(companies):
        cid = company["company_id"]

        # Skip if already enriched
        if skip_existing and company.get("llm_enriched") and company["llm_enriched"].get("moat_durability"):
            print(f"  [{i+1}/{len(companies)}] {cid} — SKIPPED (already enriched)")
            skipped_count += 1
            continue

        print(f"  [{i+1}/{len(companies)}] {cid}...", end=" ", flush=True)

        try:
            enriched = enrich_company(llm, company, company_list)
            company["llm_enriched"] = enriched
            enriched_count += 1

            moat = enriched.get("moat_durability")
            cluster = enriched.get("financial_profile_cluster")
            rels = len(enriched.get("competitive_relationships", []))
            print(f"OK — moat: {moat}/10, cluster: {cluster}, relationships: {rels}")

            # Save after each batch
            if enriched_count % batch_size == 0:
                with open(COMPANIES_FILE, "w") as f:
                    json.dump(data, f, indent=2)
                print(f"    [saved checkpoint — {enriched_count} enriched so far]")

        except Exception as e:
            print(f"FAILED — {e}")

        # Rate limiting
        time.sleep(1)

    # Final save
    with open(COMPANIES_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\nDone. Enriched: {enriched_count}, Skipped: {skipped_count}, Total: {len(companies)}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Re-enrich all companies, even if already done")
    parser.add_argument("--batch-size", type=int, default=5, help="Save checkpoint every N companies")
    args = parser.parse_args()
    run(batch_size=args.batch_size, skip_existing=not args.force)
