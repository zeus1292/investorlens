"""
End-to-end verification script for InvestorLens search pipeline.
Runs all 6 demo queries across all 5 personas and prints results.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from search.search_pipeline import search, search_all_personas
from search.persona_configs import list_personas

DEMO_QUERIES = [
    "Competitors to Snowflake",
    "Compare Databricks vs Snowflake through a PE lens",
    "Best acquisition target for Google to compete with Palantir",
    "Competitors to C3 AI",
    "Compare Pinecone vs Weaviate through a VC lens",
    "Which data infrastructure companies have the strongest moats?",
]


def print_separator(char="=", width=80):
    print(char * width)


def run_single_query(query: str, persona: str = "value_investor"):
    """Run a single query and print results."""
    result = search(query, persona=persona)
    print(f"  Persona: {result.persona_display} ({result.persona})")
    print(f"  Type: {result.query.query_type}")
    print(f"  Target: {result.query.target_company}")
    if result.query.compare_company:
        print(f"  Compare: {result.query.compare_company}")
    if result.query.acquirer:
        print(f"  Acquirer: {result.query.acquirer}")
    if result.query.attribute:
        print(f"  Attribute: {result.query.attribute}")
    print(f"  Candidates: {result.metadata.get('candidate_count', '?')}")
    print(f"  Time: {result.metadata.get('elapsed_ms', '?')}ms")
    print()

    if result.results:
        for r in result.results[:5]:
            breakdown_str = "  ".join(f"{k}={v:.3f}" for k, v in sorted(r.score_breakdown.items(), key=lambda x: -x[1]))
            edge_types = [e.get("type", "?") for e in r.graph_context[:3]]
            print(f"  #{r.rank:2d}  {r.name:30s}  score={r.composite_score:.4f}  edges={edge_types}")
            print(f"       {breakdown_str}")
    else:
        print("  (no results)")


def run_multi_persona(query: str):
    """Run a query across all personas and print top-3 per persona."""
    print(f"\n  --- All Personas Top-3 ---")
    results = search_all_personas(query)
    for persona_name in list_personas():
        sr = results[persona_name]
        top3 = [f"{r.name} ({r.composite_score:.3f})" for r in sr.results[:3]]
        print(f"  {sr.persona_display:22s}: {' | '.join(top3)}")


def main():
    print()
    print_separator("=")
    print("  InvestorLens Search Pipeline — End-to-End Verification")
    print_separator("=")

    # --- Query 1: Competitors to Snowflake (HERO QUERY) ---
    print_separator("-")
    print(f"\n  QUERY 1 (Hero): \"Competitors to Snowflake\"")
    print(f"  Must show distinct top-3 per persona.\n")
    run_single_query("Competitors to Snowflake", "value_investor")
    run_multi_persona("Competitors to Snowflake")

    # --- Query 2: Compare Databricks vs Snowflake through PE lens ---
    print_separator("-")
    print(f"\n  QUERY 2: \"Compare Databricks vs Snowflake through a PE lens\"\n")
    run_single_query("Compare Databricks vs Snowflake through a PE lens")

    # --- Query 3: Acquisition target ---
    print_separator("-")
    print(f"\n  QUERY 3: \"Best acquisition target for Google to compete with Palantir\"\n")
    run_single_query("Best acquisition target for Google to compete with Palantir")

    # --- Query 4: Competitors to C3 AI (personally validatable) ---
    print_separator("-")
    print(f"\n  QUERY 4: \"Competitors to C3 AI\"\n")
    run_single_query("Competitors to C3 AI", "value_investor")
    run_multi_persona("Competitors to C3 AI")

    # --- Query 5: Compare Pinecone vs Weaviate through VC lens ---
    print_separator("-")
    print(f"\n  QUERY 5: \"Compare Pinecone vs Weaviate through a VC lens\"\n")
    run_single_query("Compare Pinecone vs Weaviate through a VC lens")

    # --- Query 6: Attribute search ---
    print_separator("-")
    print(f"\n  QUERY 6: \"Which data infrastructure companies have the strongest moats?\"\n")
    run_single_query("Which data infrastructure companies have the strongest moats?")

    print_separator("=")
    print("  Verification complete.")
    print_separator("=")


if __name__ == "__main__":
    main()
