"""
Persona scoring configurations for InvestorLens.
Each persona defines weights for company attributes and preferred graph edge types.
"""
from dataclasses import dataclass


@dataclass
class PersonaConfig:
    name: str
    display_name: str
    description: str
    weights: dict[str, float]           # attribute → weight (must sum to 1.0)
    graph_priority: list[str]           # edge types this persona cares about most
    inverted_attributes: list[str]      # attributes where lower raw value = higher score
    binary_attributes: dict[str, str]   # attribute → condition description


PERSONAS: dict[str, PersonaConfig] = {
    "value_investor": PersonaConfig(
        name="value_investor",
        display_name="Value Investor",
        description="Seeks durable moats, strong free cash flow, high switching costs, and reasonable valuations.",
        weights={
            "moat_durability": 0.25,
            "free_cash_flow_positive": 0.20,
            "customer_switching_cost": 0.20,
            "low_debt": 0.15,
            "revenue_predictability": 0.10,
            "valuation_margin": 0.10,
        },
        graph_priority=["SHARES_INVESTMENT_THEME", "COMPETES_WITH"],
        inverted_attributes=["low_debt", "valuation_margin"],
        binary_attributes={"free_cash_flow_positive": "fcf > 0"},
    ),
    "pe_firm": PersonaConfig(
        name="pe_firm",
        display_name="PE Firm",
        description="Targets high margins, operational improvement upside, predictable revenue, and reasonable valuation multiples.",
        weights={
            "operating_margin": 0.25,
            "operational_improvement_potential": 0.20,
            "revenue_predictability": 0.20,
            "valuation_margin": 0.15,
            "customer_switching_cost": 0.10,
            "enterprise_readiness_score": 0.10,
        },
        graph_priority=["TARGETS_SAME_SEGMENT", "COMPETES_WITH"],
        inverted_attributes=["valuation_margin"],
        binary_attributes={},
    ),
    "growth_vc": PersonaConfig(
        name="growth_vc",
        display_name="Growth VC",
        description="Prioritizes fast growth, TAM capture, developer traction, and market timing over profitability.",
        weights={
            "yoy_employee_growth": 0.25,
            "market_timing_score": 0.25,
            "developer_adoption_score": 0.20,
            "github_stars_normalized": 0.15,
            "product_maturity_inverse": 0.15,
        },
        graph_priority=["DISRUPTS", "TARGETS_SAME_SEGMENT"],
        inverted_attributes=["product_maturity_inverse"],
        binary_attributes={},
    ),
    "strategic_acquirer": PersonaConfig(
        name="strategic_acquirer",
        display_name="Strategic Acquirer",
        description="Evaluates tech differentiation, partnership fit, competitive threat neutralization, and acquirability.",
        weights={
            "moat_durability": 0.25,
            "partnership_fit": 0.20,
            "competitive_threat": 0.20,
            "developer_adoption_score": 0.15,
            "small_enough_to_acquire": 0.10,
            "product_maturity_score": 0.10,
        },
        graph_priority=["DISRUPTS", "PARTNERS_WITH", "COMPETES_WITH"],
        inverted_attributes=["small_enough_to_acquire"],
        binary_attributes={},
    ),
    "enterprise_buyer": PersonaConfig(
        name="enterprise_buyer",
        display_name="Enterprise Buyer",
        description="Values product maturity, enterprise readiness, ecosystem integrations, and low vendor lock-in risk.",
        weights={
            "product_maturity_score": 0.25,
            "enterprise_readiness_score": 0.20,
            "partnership_count": 0.20,
            "customer_switching_cost_inverse": 0.15,
            "revenue_predictability": 0.10,
            "developer_adoption_score": 0.10,
        },
        graph_priority=["TARGETS_SAME_SEGMENT", "PARTNERS_WITH"],
        inverted_attributes=["customer_switching_cost_inverse"],
        binary_attributes={},
    ),
}

# Mapping from scoring attribute names to the raw data field they come from
ATTRIBUTE_SOURCE_MAP = {
    # LLM-enriched scores (1-10 scale, normalize by /10)
    "moat_durability": ("llm", "moat_durability"),
    "customer_switching_cost": ("llm", "customer_switching_cost"),
    "revenue_predictability": ("llm", "revenue_predictability"),
    "operational_improvement_potential": ("llm", "operational_improvement_potential"),
    "enterprise_readiness_score": ("llm", "enterprise_readiness_score"),
    "developer_adoption_score": ("llm", "developer_adoption_score"),
    "product_maturity_score": ("llm", "product_maturity_score"),
    "market_timing_score": ("llm", "market_timing_score"),

    # Financial metrics (need min-max normalization across candidate set)
    "operating_margin": ("financial", "operating_margin"),
    "valuation_margin": ("financial", "price_to_sales"),        # inverted
    "low_debt": ("financial", "debt_to_equity"),                # inverted
    "free_cash_flow_positive": ("financial", "free_cash_flow_b"),  # binary
    "small_enough_to_acquire": ("financial", "market_cap_b"),   # inverted

    # Growth signals
    "yoy_employee_growth": ("growth", "yoy_employee_growth"),
    "github_stars_normalized": ("growth", "github_stars"),

    # Computed from graph context (handled in ranker)
    "partnership_fit": ("graph", "partnership_fit"),
    "competitive_threat": ("graph", "competitive_threat"),
    "partnership_count": ("graph", "partnership_count"),

    # Derived / inverted
    "product_maturity_inverse": ("llm", "product_maturity_score"),       # inverted
    "customer_switching_cost_inverse": ("llm", "customer_switching_cost"),  # inverted
}


def get_persona(name: str) -> PersonaConfig:
    """Get persona config by name. Raises KeyError if not found."""
    return PERSONAS[name]


def list_personas() -> list[str]:
    """List all available persona names."""
    return list(PERSONAS.keys())
