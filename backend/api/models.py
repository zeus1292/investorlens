"""
Pydantic request/response models for the InvestorLens API.
"""
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., description="Natural language search query", min_length=1)
    persona: str = Field(
        default="value_investor",
        description="Persona: value_investor, pe_firm, growth_vc, strategic_acquirer, enterprise_buyer",
    )
    include_explanation: bool = Field(
        default=True,
        description="Generate NL explanation (adds ~2-4s latency)",
    )
    all_personas: bool = Field(
        default=False,
        description="Run query across all 5 personas",
    )


class ScoreBreakdown(BaseModel):
    class Config:
        extra = "allow"


class RankedResultResponse(BaseModel):
    rank: int
    company_id: str
    name: str
    composite_score: float
    score_breakdown: dict = {}
    graph_context: list = []


class QueryInfo(BaseModel):
    query_type: str = ""
    raw_query: str = ""
    target_company: str = ""
    compare_company: str = ""
    acquirer: str = ""
    persona: str | None = None
    attribute: str | None = None


class PersonaTopResults(BaseModel):
    persona_display: str = ""
    top_results: list[RankedResultResponse] = []


class SearchResponse(BaseModel):
    query: QueryInfo | None = None
    persona: str = ""
    persona_display: str = ""
    results: list[RankedResultResponse] = []
    compare_data: dict | None = None
    graph_data: dict = {}
    explanation: str | None = None
    explanation_highlights: list[str] | None = None
    all_personas: dict[str, PersonaTopResults] | None = None
    metadata: dict = {}


class PersonaResponse(BaseModel):
    name: str
    display_name: str
    description: str
    weights: dict[str, float]


class CompanyResponse(BaseModel):
    company_id: str
    name: str
    sector: str = ""
    status: str = ""
    description: str = ""
    market_cap_b: float | None = None
    revenue_ttm_b: float | None = None
    moat_durability: float | None = None
    enterprise_readiness_score: float | None = None
    developer_adoption_score: float | None = None
    financial_profile_cluster: str | None = None


class HealthResponse(BaseModel):
    status: str
    neo4j: str
    company_count: int = 0
