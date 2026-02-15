"""
Persona-based ranking engine for InvestorLens.
Takes candidate companies + persona config → returns re-ranked results with score breakdowns.
"""
from dataclasses import dataclass, field
from .persona_configs import PersonaConfig, ATTRIBUTE_SOURCE_MAP


@dataclass
class RankedResult:
    company_id: str
    name: str
    composite_score: float
    score_breakdown: dict = field(default_factory=dict)
    graph_context: list = field(default_factory=list)
    rank: int = 0


def _extract_raw_value(candidate, attr_name: str) -> float | None:
    """Extract the raw value for a scoring attribute from a candidate."""
    if attr_name not in ATTRIBUTE_SOURCE_MAP:
        return None

    source_type, source_field = ATTRIBUTE_SOURCE_MAP[attr_name]

    if source_type == "graph":
        # Graph-computed attributes live directly on the candidate
        return getattr(candidate, source_field, None)

    if source_type == "llm":
        return getattr(candidate, source_field, None)

    if source_type == "financial":
        return getattr(candidate, source_field, None)

    if source_type == "growth":
        return getattr(candidate, source_field, None)

    return None


def _normalize_llm_score(value: float | None) -> float:
    """Normalize LLM scores (1-10) to 0-1."""
    if value is None:
        return 0.5  # default for missing
    return max(0.0, min(1.0, value / 10.0))


def _minmax_normalize(values: list[float | None], invert: bool = False) -> list[float]:
    """Min-max normalize a list of values to 0-1. Use 0.5 default for None."""
    clean = [v for v in values if v is not None]
    if not clean:
        return [0.5] * len(values)

    vmin = min(clean)
    vmax = max(clean)
    span = vmax - vmin

    result = []
    for v in values:
        if v is None:
            result.append(0.5)
        elif span == 0:
            result.append(0.5)
        else:
            normalized = (v - vmin) / span
            result.append(1.0 - normalized if invert else normalized)
    return result


def rank_candidates(candidates: list, persona: PersonaConfig, acquirer: str = "") -> list[RankedResult]:
    """Score and rank candidates using persona-specific weights.

    Args:
        candidates: list of CandidateCompany objects
        persona: PersonaConfig with weights and settings
        acquirer: company_id of acquirer (for acquisition queries)

    Returns:
        Sorted list of RankedResult, highest composite score first.
    """
    if not candidates:
        return []

    weights = persona.weights
    inverted = set(persona.inverted_attributes)

    # Collect raw values per attribute across all candidates for normalization
    attr_raw: dict[str, list[float | None]] = {}
    for attr_name in weights:
        raw_values = []
        for cand in candidates:
            raw_values.append(_extract_raw_value(cand, attr_name))
        attr_raw[attr_name] = raw_values

    # Normalize each attribute
    attr_normalized: dict[str, list[float]] = {}
    for attr_name, raw_values in attr_raw.items():
        if attr_name not in ATTRIBUTE_SOURCE_MAP:
            attr_normalized[attr_name] = [0.5] * len(candidates)
            continue

        source_type, _ = ATTRIBUTE_SOURCE_MAP[attr_name]
        should_invert = attr_name in inverted

        if attr_name == "free_cash_flow_positive":
            # Binary: fcf > 0 → 1.0, else 0.0
            attr_normalized[attr_name] = [
                1.0 if (v is not None and v > 0) else 0.0
                for v in raw_values
            ]
        elif source_type == "llm":
            if should_invert:
                # Invert: lower raw → higher score
                attr_normalized[attr_name] = [
                    1.0 - _normalize_llm_score(v) for v in raw_values
                ]
            else:
                attr_normalized[attr_name] = [
                    _normalize_llm_score(v) for v in raw_values
                ]
        elif source_type in ("financial", "growth"):
            attr_normalized[attr_name] = _minmax_normalize(raw_values, invert=should_invert)
        elif source_type == "graph":
            attr_normalized[attr_name] = _minmax_normalize(raw_values, invert=should_invert)
        else:
            attr_normalized[attr_name] = [0.5] * len(candidates)

    # Compute composite scores with graph relevance boost
    results = []
    for i, cand in enumerate(candidates):
        breakdown = {}
        composite = 0.0

        for attr_name, weight in weights.items():
            norm_val = attr_normalized.get(attr_name, [0.5] * len(candidates))[i]
            weighted = norm_val * weight
            breakdown[attr_name] = round(weighted, 4)
            composite += weighted

        # Graph relevance boost: direct competitors rank higher than theme-only matches.
        # COMPETES_WITH → up to +0.15, DISRUPTS → +0.10, TARGETS_SAME_SEGMENT → +0.05,
        # SHARES_INVESTMENT_THEME only → no boost.
        graph_boost = 0.0
        edge_types = {e.get("type") for e in cand.graph_edges}
        if "COMPETES_WITH" in edge_types:
            graph_boost = max(graph_boost, 0.15 * cand.competition_strength) if cand.competition_strength else 0.10
        if "DISRUPTS" in edge_types:
            graph_boost = max(graph_boost, 0.10)
        if "TARGETS_SAME_SEGMENT" in edge_types and graph_boost == 0.0:
            graph_boost = 0.05

        composite += graph_boost
        breakdown["_graph_boost"] = round(graph_boost, 4)

        results.append(RankedResult(
            company_id=cand.company_id,
            name=cand.name,
            composite_score=round(composite, 4),
            score_breakdown=breakdown,
            graph_context=cand.graph_edges,
            rank=0,
        ))

    # Sort descending by composite score
    results.sort(key=lambda r: r.composite_score, reverse=True)

    # Assign ranks
    for i, r in enumerate(results):
        r.rank = i + 1

    return results
