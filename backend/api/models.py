"""
Pydantic request/response models for the InvestorLens API.
"""
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., description="Natural language search query", min_length=1)
    persona: str = Field(
        default="value_investor",
        description=(
            "Investor persona — controls ranking weights and tool-selection strategy. "
            "One of: value_investor, pe_firm, growth_vc, strategic_acquirer, enterprise_buyer."
        ),
    )
    include_explanation: bool = Field(
        default=True,
        description=(
            "Generate an investment-grade natural-language explanation (GPT-4o). "
            "Set to false for fast structured-only results (~1–2 s vs ~10–15 s)."
        ),
    )
    all_personas: bool = Field(
        default=False,
        description="Run the query across all 5 personas and return a side-by-side comparison.",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "summary": "Competitor search (fast)",
                    "value": {
                        "query": "Competitors to Snowflake",
                        "persona": "growth_vc",
                        "include_explanation": False,
                        "all_personas": False,
                    },
                },
                {
                    "summary": "Head-to-head with explanation",
                    "value": {
                        "query": "Compare Databricks vs Snowflake through a PE lens",
                        "persona": "pe_firm",
                        "include_explanation": True,
                        "all_personas": False,
                    },
                },
                {
                    "summary": "Acquisition multi-hop",
                    "value": {
                        "query": "Best acquisition target for Google to compete with Palantir",
                        "persona": "strategic_acquirer",
                        "include_explanation": False,
                        "all_personas": False,
                    },
                },
                {
                    "summary": "All-personas comparison",
                    "value": {
                        "query": "Competitors to C3 AI",
                        "persona": "value_investor",
                        "include_explanation": False,
                        "all_personas": True,
                    },
                },
            ]
        }
    }


class ScoreBreakdown(BaseModel):
    class Config:
        extra = "allow"


class RankedResultResponse(BaseModel):
    rank: int = Field(..., description="1-based rank within this persona's results")
    company_id: str = Field(..., description="Unique company identifier (snake_case)")
    name: str = Field(..., description="Display name of the company")
    composite_score: float = Field(..., description="Weighted composite score in [0, 1]")
    score_breakdown: dict = Field(
        default={},
        description="Per-factor scores used to compute the composite (values in [0, 1])",
    )
    graph_context: list = Field(
        default=[],
        description="Graph relationship badges shown in the UI (e.g. 'Direct competitor (0.9)')",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "rank": 1,
                "company_id": "databricks",
                "name": "Databricks",
                "composite_score": 0.74,
                "score_breakdown": {
                    "moat_durability": 0.82,
                    "developer_adoption": 0.91,
                    "market_timing": 0.78,
                },
                "graph_context": ["Direct competitor (0.9)", "Targets same segment"],
            }
        }
    }


class QueryInfo(BaseModel):
    query_type: str = Field(default="", description="Classified query type: competitors_to, compare, acquisition_target, attribute_search")
    raw_query: str = Field(default="", description="Original user query string")
    target_company: str = Field(default="", description="Primary company entity resolved from query")
    compare_company: str = Field(default="", description="Secondary company for head-to-head queries")
    acquirer: str = Field(default="", description="Acquirer company for acquisition-target queries")
    persona: str | None = Field(default=None, description="Active persona name")
    attribute: str | None = Field(default=None, description="Attribute name for attribute_search queries")


class PersonaTopResults(BaseModel):
    persona_display: str = Field(default="", description="Human-readable persona label")
    top_results: list[RankedResultResponse] = Field(
        default=[],
        description="Top-ranked results for this persona",
    )


class SearchResponse(BaseModel):
    query: QueryInfo | None = Field(default=None, description="Parsed query metadata")
    persona: str = Field(default="", description="Active persona key")
    persona_display: str = Field(default="", description="Active persona display name")
    results: list[RankedResultResponse] = Field(
        default=[],
        description="Ranked results for the active persona",
    )
    compare_data: dict | None = Field(
        default=None,
        description="Head-to-head comparison data (only populated for compare queries)",
    )
    graph_data: dict = Field(
        default={},
        description="Force-graph nodes and edges for the Relationship Map visualisation",
    )
    explanation: str | None = Field(
        default=None,
        description="GPT-4o investment-grade narrative (null when include_explanation=false)",
    )
    explanation_highlights: list[str] | None = Field(
        default=None,
        description="3–5 key-takeaway bullets extracted from the explanation",
    )
    all_personas: dict[str, PersonaTopResults] | None = Field(
        default=None,
        description="Per-persona top results (only populated when all_personas=true)",
    )
    metadata: dict = Field(
        default={},
        description="Timing and diagnostic info: total_elapsed_ms, tool calls, etc.",
    )


class PersonaResponse(BaseModel):
    name: str = Field(..., description="Persona key used in API requests")
    display_name: str = Field(..., description="Human-readable persona label")
    description: str = Field(..., description="One-line description of the persona's priorities")
    weights: dict[str, float] = Field(
        ...,
        description="Scoring-factor weights that sum to ~1.0",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "growth_vc",
                "display_name": "Growth VC",
                "description": "Early-stage momentum, developer traction, TAM capture",
                "weights": {
                    "revenue_growth": 0.25,
                    "developer_adoption": 0.20,
                    "market_timing": 0.15,
                },
            }
        }
    }


class CompanyResponse(BaseModel):
    company_id: str = Field(..., description="Unique company identifier (snake_case)")
    name: str = Field(..., description="Display name")
    sector: str = Field(default="", description="Sector within the universe (e.g. Cloud Data Platforms)")
    status: str = Field(default="", description="public / private / acquired")
    description: str = Field(default="", description="One-paragraph company description")
    market_cap_b: float | None = Field(default=None, description="Market capitalisation in USD billions")
    revenue_ttm_b: float | None = Field(default=None, description="Trailing-twelve-month revenue in USD billions")
    moat_durability: float | None = Field(default=None, description="LLM-scored moat durability [0–10]")
    enterprise_readiness_score: float | None = Field(default=None, description="LLM-scored enterprise readiness [0–10]")
    developer_adoption_score: float | None = Field(default=None, description="LLM-scored developer adoption [0–10]")
    financial_profile_cluster: str | None = Field(default=None, description="Qualitative financial cluster (e.g. high_growth_unprofitable)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "company_id": "snowflake",
                "name": "Snowflake",
                "sector": "Cloud Data Platforms",
                "status": "public",
                "description": "Cloud-native data platform with consumption-based pricing.",
                "market_cap_b": 47.2,
                "revenue_ttm_b": 3.24,
                "moat_durability": 8.2,
                "enterprise_readiness_score": 9.1,
                "developer_adoption_score": 7.8,
                "financial_profile_cluster": "high_growth_unprofitable",
            }
        }
    }


class HealthResponse(BaseModel):
    status: str = Field(..., description="Always 'ok' when the API is reachable")
    neo4j: str = Field(..., description="Neo4j connection status: connected / disconnected / error")
    company_count: int = Field(default=0, description="Number of Company nodes in the graph")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "ok",
                "neo4j": "connected",
                "company_count": 37,
            }
        }
    }
