"""
Query parser for InvestorLens search pipeline.
Classifies natural language queries and extracts entities using pattern matching.
"""
import json
import os
import re
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import COMPANIES_FILE


@dataclass
class ParsedQuery:
    query_type: str           # competitors_to | compare | acquisition_target | attribute_search
    raw_query: str
    target_company: str = ""  # company_id
    compare_company: str = "" # company_id for compare queries
    acquirer: str = ""        # company_id for acquisition queries
    persona: str | None = None
    attribute: str | None = None


# --- Company name resolution ---

# Canonical name → company_id mapping built from companies.json
_COMPANY_LOOKUP: dict[str, str] | None = None

# Manual aliases for common variations
_ALIASES = {
    "snow": "snowflake",
    "snowflake": "snowflake",
    "snowflake inc": "snowflake",
    "databricks": "databricks",
    "bigquery": "bigquery",
    "google bigquery": "bigquery",
    "redshift": "redshift",
    "amazon redshift": "redshift",
    "aws redshift": "redshift",
    "azure synapse": "azure_synapse",
    "synapse": "azure_synapse",
    "teradata": "teradata",
    "teradata corporation": "teradata",
    "cloudera": "cloudera",
    "motherduck": "motherduck",
    "mother duck": "motherduck",
    "c3 ai": "c3ai",
    "c3ai": "c3ai",
    "c3": "c3ai",
    "palantir": "palantir",
    "palantir technologies": "palantir",
    "dataiku": "dataiku",
    "datarobot": "datarobot",
    "data robot": "datarobot",
    "h2o": "h2o_ai",
    "h2o ai": "h2o_ai",
    "h2o.ai": "h2o_ai",
    "scale ai": "scale_ai",
    "scale": "scale_ai",
    "wandb": "wandb",
    "weights and biases": "wandb",
    "weights & biases": "wandb",
    "w&b": "wandb",
    "hugging face": "huggingface",
    "huggingface": "huggingface",
    "fivetran": "fivetran",
    "dbt": "dbt_labs",
    "dbt labs": "dbt_labs",
    "airbyte": "airbyte",
    "informatica": "informatica",
    "informatica inc": "informatica",
    "talend": "talend",
    "qlik": "talend",
    "matillion": "matillion",
    "monte carlo": "monte_carlo",
    "montecarlo": "monte_carlo",
    "atlan": "atlan",
    "alation": "alation",
    "great expectations": "great_expectations",
    "collibra": "collibra",
    "pinecone": "pinecone",
    "weaviate": "weaviate",
    "chroma": "chroma",
    "zilliz": "zilliz",
    "milvus": "zilliz",
    "zilliz milvus": "zilliz",
    "qdrant": "qdrant",
    "firebolt": "firebolt",
    "clickhouse": "clickhouse",
    "starrocks": "starrocks",
    "star rocks": "starrocks",
    "neon": "neon",
    "supabase": "supabase",
    "google": "bigquery",       # "acquisition target for Google" → bigquery as proxy
    "amazon": "redshift",
    "aws": "redshift",
    "microsoft": "azure_synapse",
}


def _build_lookup() -> dict[str, str]:
    """Build lowercase name → company_id lookup from companies.json + aliases."""
    global _COMPANY_LOOKUP
    if _COMPANY_LOOKUP is not None:
        return _COMPANY_LOOKUP

    lookup = dict(_ALIASES)
    with open(COMPANIES_FILE) as f:
        data = json.load(f)
    for c in data["companies"]:
        cid = c["company_id"]
        name_lower = c["name"].lower().strip().rstrip(".")
        lookup[name_lower] = cid
        lookup[cid] = cid  # company_id itself works
        # Without "Inc." / "Corporation" etc.
        for suffix in [" inc", " corporation", " technologies"]:
            if name_lower.endswith(suffix):
                lookup[name_lower[: -len(suffix)].strip()] = cid

    _COMPANY_LOOKUP = lookup
    return lookup


def resolve_company(name: str) -> str | None:
    """Resolve a company name/alias to its company_id. Returns None if not found."""
    lookup = _build_lookup()
    key = name.lower().strip().rstrip(".")
    if key in lookup:
        return lookup[key]
    # Try substring match — find the longest alias that appears in the name
    best_match = None
    best_len = 0
    for alias, cid in lookup.items():
        if len(alias) > best_len and alias in key:
            best_match = cid
            best_len = len(alias)
    return best_match


# --- Persona detection ---

_PERSONA_PATTERNS = {
    "value_investor": r"value\s+invest",
    "pe_firm": r"\bpe\b|private\s+equity",
    "growth_vc": r"\bvc\b|venture\s+capital|growth\b",
    "strategic_acquirer": r"strateg|acqui[rs]",
    "enterprise_buyer": r"enterprise\s+buyer|buyer",
}


def _detect_persona(query: str) -> str | None:
    """Detect persona from query text if specified."""
    q = query.lower()
    for persona, pattern in _PERSONA_PATTERNS.items():
        if re.search(pattern, q):
            return persona
    if "lens" in q:
        # "through a PE lens" etc. — try matching word before "lens"
        m = re.search(r"(\w+)\s+lens", q)
        if m:
            word = m.group(1).lower()
            if word in ("pe", "private"):
                return "pe_firm"
            if word in ("vc", "growth", "venture"):
                return "growth_vc"
            if word in ("value",):
                return "value_investor"
            if word in ("buyer", "enterprise"):
                return "enterprise_buyer"
            if word in ("acquirer", "strategic"):
                return "strategic_acquirer"
    return None


# --- Attribute detection ---

_ATTRIBUTE_MAP = {
    "moat": "moat_durability",
    "moats": "moat_durability",
    "moat durability": "moat_durability",
    "enterprise readiness": "enterprise_readiness_score",
    "enterprise ready": "enterprise_readiness_score",
    "developer adoption": "developer_adoption_score",
    "developer traction": "developer_adoption_score",
    "product maturity": "product_maturity_score",
    "mature": "product_maturity_score",
    "switching cost": "customer_switching_cost",
    "switching costs": "customer_switching_cost",
    "lock-in": "customer_switching_cost",
    "revenue predictability": "revenue_predictability",
    "predictable revenue": "revenue_predictability",
    "recurring revenue": "revenue_predictability",
    "market timing": "market_timing_score",
    "operational improvement": "operational_improvement_potential",
    "margin": "operating_margin",
    "growth": "yoy_employee_growth",
    "revenue": "revenue_ttm_b",
    "market cap": "market_cap_b",
}


def _detect_attribute(query: str) -> str | None:
    """Detect the attribute being searched for."""
    q = query.lower()
    # Check longest keys first to prefer "moat durability" over "moat"
    for key in sorted(_ATTRIBUTE_MAP, key=len, reverse=True):
        if key in q:
            return _ATTRIBUTE_MAP[key]
    return None


# --- Query classification ---

def _extract_companies_from_query(query: str) -> list[str]:
    """Extract all company references from a query, returning company_ids."""
    lookup = _build_lookup()
    found = []
    q = query.lower()

    # Try matching longest aliases first to avoid partial matches
    for alias in sorted(lookup, key=len, reverse=True):
        if alias in q and len(alias) > 2:  # skip very short aliases
            cid = lookup[alias]
            if cid not in found:
                found.append(cid)
                # Remove the matched text to avoid double-matching
                q = q.replace(alias, " ", 1)
    return found


def parse_query(query: str) -> ParsedQuery:
    """Parse a natural language query into a structured ParsedQuery."""
    q = query.lower().strip()
    persona = _detect_persona(query)

    # --- Type 1: competitors_to ---
    # "Competitors to Snowflake", "Who competes with C3 AI"
    comp_patterns = [
        r"competitors?\s+(?:to|of|for)\s+(.+?)(?:\s+through|\s+from|\s+in\s+a|\s*$)",
        r"who\s+competes?\s+with\s+(.+?)(?:\s+through|\s+from|\s+in\s+a|\s*$)",
        r"competition\s+(?:to|of|for)\s+(.+?)(?:\s+through|\s+from|\s+in\s+a|\s*$)",
        r"rivals?\s+(?:to|of|for)\s+(.+?)(?:\s+through|\s+from|\s+in\s+a|\s*$)",
    ]
    for pat in comp_patterns:
        m = re.search(pat, q)
        if m:
            target = resolve_company(m.group(1).strip())
            if target:
                return ParsedQuery(
                    query_type="competitors_to",
                    raw_query=query,
                    target_company=target,
                    persona=persona,
                )

    # --- Type 2: compare ---
    # "Compare Databricks vs Snowflake through a PE lens"
    cmp_patterns = [
        r"compare\s+(.+?)\s+(?:vs\.?|versus|and|with)\s+(.+?)(?:\s+through|\s+from|\s+in\s+a|\s*$)",
        r"(.+?)\s+(?:vs\.?|versus)\s+(.+?)(?:\s+through|\s+from|\s+in\s+a|\s*$)",
    ]
    for pat in cmp_patterns:
        m = re.search(pat, q)
        if m:
            a = resolve_company(m.group(1).strip())
            b = resolve_company(m.group(2).strip())
            if a and b:
                return ParsedQuery(
                    query_type="compare",
                    raw_query=query,
                    target_company=a,
                    compare_company=b,
                    persona=persona,
                )

    # --- Type 3: acquisition_target ---
    # "Best acquisition target for Google to compete with Palantir"
    acq_patterns = [
        r"acquisition\s+target\s+for\s+(.+?)\s+to\s+compete\s+with\s+(.+?)(?:\s*$)",
        r"(?:what|which|best)\s+.*?acqui\w+\s+.*?for\s+(.+?)\s+.*?(?:against|compete|rival)\s+.*?(.+?)(?:\s*$)",
        r"(.+?)\s+should\s+acqui\w+\s+to\s+compete\s+with\s+(.+?)(?:\s*$)",
    ]
    for pat in acq_patterns:
        m = re.search(pat, q)
        if m:
            acquirer = resolve_company(m.group(1).strip())
            target = resolve_company(m.group(2).strip())
            if acquirer and target:
                return ParsedQuery(
                    query_type="acquisition_target",
                    raw_query=query,
                    acquirer=acquirer,
                    target_company=target,
                    persona=persona or "strategic_acquirer",
                )

    # --- Type 4: attribute_search ---
    # "Which data infrastructure companies have the strongest moats?"
    attr = _detect_attribute(query)
    if attr and any(kw in q for kw in ["which", "strongest", "best", "highest", "top", "most", "leading"]):
        return ParsedQuery(
            query_type="attribute_search",
            raw_query=query,
            attribute=attr,
            persona=persona,
        )

    # --- Fallback: try to find any company reference and treat as competitors_to ---
    companies = _extract_companies_from_query(query)
    if len(companies) >= 2:
        return ParsedQuery(
            query_type="compare",
            raw_query=query,
            target_company=companies[0],
            compare_company=companies[1],
            persona=persona,
        )
    if len(companies) == 1:
        return ParsedQuery(
            query_type="competitors_to",
            raw_query=query,
            target_company=companies[0],
            persona=persona,
        )

    # If attribute detected without a "which/best" keyword, still use it
    if attr:
        return ParsedQuery(
            query_type="attribute_search",
            raw_query=query,
            attribute=attr,
            persona=persona,
        )

    # Last resort: return as attribute search with no attribute
    return ParsedQuery(
        query_type="attribute_search",
        raw_query=query,
        attribute="moat_durability",
        persona=persona,
    )


if __name__ == "__main__":
    test_queries = [
        "Competitors to Snowflake",
        "Compare Databricks vs Snowflake through a PE lens",
        "Best acquisition target for Google to compete with Palantir",
        "Competitors to C3 AI",
        "Compare Pinecone vs Weaviate through a VC lens",
        "Which data infrastructure companies have the strongest moats?",
        "Who competes with Databricks?",
    ]
    for q in test_queries:
        parsed = parse_query(q)
        print(f"\nQuery: {q}")
        print(f"  Type: {parsed.query_type}")
        print(f"  Target: {parsed.target_company}")
        print(f"  Compare: {parsed.compare_company}")
        print(f"  Acquirer: {parsed.acquirer}")
        print(f"  Persona: {parsed.persona}")
        print(f"  Attribute: {parsed.attribute}")
