"""
LangSmith evaluation dataset for InvestorLens.

Each example has:
  inputs           — query + persona fed into run_agent()
  reference_outputs — ground truth for deterministic evaluators
                      (expected_companies, query_type, min_results)

Expected companies are company_id values from companies.json.
They are verified against Phase 2 search results documented in CLAUDE.md.
"""
from langsmith import Client

DATASET_NAME = "investorlens-eval-v1"

EVAL_EXAMPLES = [
    # ── Query 1: Competitors to Snowflake (Value Investor) ─────────────────
    {
        "inputs": {
            "query": "Competitors to Snowflake",
            "persona": "value_investor",
        },
        "reference_outputs": {
            "query_type": "competitors_to",
            "min_results": 3,
            "expected_companies": ["bigquery", "redshift", "azure_synapse", "databricks"],
        },
    },
    # ── Query 2: Competitors to C3 AI (Value Investor) ─────────────────────
    {
        "inputs": {
            "query": "Competitors to C3 AI",
            "persona": "value_investor",
        },
        "reference_outputs": {
            "query_type": "competitors_to",
            "min_results": 3,
            "expected_companies": ["palantir", "datarobot", "scale_ai"],
        },
    },
    # ── Query 3: Compare Databricks vs Snowflake (PE Firm) ─────────────────
    {
        "inputs": {
            "query": "Compare Databricks vs Snowflake through a PE lens",
            "persona": "pe_firm",
        },
        "reference_outputs": {
            "query_type": "compare",
            "min_results": 1,
            "expected_companies": ["databricks", "snowflake"],
        },
    },
    # ── Query 4: Acquisition target (Strategic Acquirer) ───────────────────
    {
        "inputs": {
            "query": "Best acquisition target for Google to compete with Palantir",
            "persona": "strategic_acquirer",
        },
        "reference_outputs": {
            "query_type": "acquisition_target",
            "min_results": 3,
            "expected_companies": ["scale_ai", "c3ai", "dataiku"],
        },
    },
    # ── Query 5: Competitors to Pinecone (Growth VC) ───────────────────────
    {
        "inputs": {
            "query": "Compare Pinecone vs Weaviate through a VC lens",
            "persona": "growth_vc",
        },
        "reference_outputs": {
            "query_type": "compare",
            "min_results": 1,
            "expected_companies": ["pinecone", "weaviate"],
        },
    },
    # ── Query 6: Attribute search — strongest moats (Value Investor) ────────
    {
        "inputs": {
            "query": "Which data infrastructure companies have the strongest moats?",
            "persona": "value_investor",
        },
        "reference_outputs": {
            "query_type": "attribute_search",
            "min_results": 3,
            "expected_companies": ["snowflake", "databricks", "palantir"],
        },
    },
]


def create_or_load_dataset(client: Client) -> str:
    """
    Create the LangSmith dataset if it doesn't exist.
    Returns the dataset name (safe to pass to evaluate()).
    """
    existing = [d.name for d in client.list_datasets()]
    if DATASET_NAME in existing:
        print(f"Dataset '{DATASET_NAME}' already exists — reusing.")
        return DATASET_NAME

    print(f"Creating dataset '{DATASET_NAME}' with {len(EVAL_EXAMPLES)} examples...")
    dataset = client.create_dataset(
        DATASET_NAME,
        description=(
            "InvestorLens evaluation set — 6 demo queries across 5 personas. "
            "Covers competitor search, head-to-head compare, acquisition targeting, "
            "and attribute ranking query types."
        ),
    )
    client.create_examples(
        inputs=[ex["inputs"] for ex in EVAL_EXAMPLES],
        outputs=[ex["reference_outputs"] for ex in EVAL_EXAMPLES],
        dataset_id=dataset.id,
    )
    print(f"Dataset created: {dataset.id}")
    return DATASET_NAME
