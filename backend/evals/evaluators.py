"""
Evaluators for InvestorLens.

LLM-as-judge (require OpenAI):
  - hallucination_free     Does the explanation stay within the structured results?
  - answer_relevance       Does the explanation address what was asked?
  - persona_alignment      Does the explanation use the right persona's framing?

Deterministic (no LLM, fast):
  - graph_loaded           graph_data has non-empty nodes and edges
  - results_populated      results list is non-empty; every item has name,
                           composite_score, and score_breakdown
  - score_in_range         all composite_score values are 0 ≤ x ≤ 1
  - rationale_present      every result has ≥ 2 score_breakdown factors with
                           non-zero contribution values
  - expected_companies_in_results
                           at least one reference expected_company appears in
                           the top-5 ranked results (by company_id)

All evaluators return {"key": str, "score": 0|1, "comment": str}.
"""
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


# ── Shared LLM judge (gpt-4o-mini keeps eval costs low) ─────────────────────

class _JudgeScore(BaseModel):
    score: int = Field(description="1 = pass, 0 = fail")
    reasoning: str = Field(description="One-sentence explanation of the score")


_judge = ChatOpenAI(model="gpt-4o-mini", temperature=0).with_structured_output(_JudgeScore)


def _fmt_results(results: list) -> str:
    """Compact text representation of ranked results for judge context."""
    lines = []
    for r in results[:8]:
        breakdown = ", ".join(
            f"{k}={v:.1f}" for k, v in (r.get("score_breakdown") or {}).items()
        )
        lines.append(f"  #{r['rank']} {r['name']} (score={r['composite_score']:.2f}) [{breakdown}]")
    return "\n".join(lines) if lines else "  (no results)"


_PERSONA_FOCUS = {
    "value_investor":    "moat durability, free cash flow, switching costs, low debt, revenue predictability",
    "pe_firm":           "operating margins, operational improvement potential, revenue predictability, valuation",
    "growth_vc":         "growth rate, market timing, developer adoption, GitHub traction, early-stage upside",
    "strategic_acquirer":"tech differentiation, partnership fit, competitive threat neutralisation, acquirability",
    "enterprise_buyer":  "product maturity, enterprise readiness, ecosystem integrations, low lock-in risk",
}


# ── LLM-as-judge evaluators ──────────────────────────────────────────────────

def hallucination_free(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
    """
    Score 1 if the NL explanation is fully grounded in the structured results.
    Score 0 if it mentions companies, metrics, or claims not present in results.
    """
    explanation = outputs.get("explanation") or ""
    if not explanation.strip():
        return {"key": "hallucination_free", "score": 1,
                "comment": "No explanation generated — nothing to hallucinate."}

    structured = _fmt_results(outputs.get("results", []))

    result = _judge.invoke([
        ("system",
         "You are an expert evaluator checking AI-generated text for hallucinations. "
         "Hallucination = any claim about a specific company, metric, or relationship "
         "NOT supported by the structured data provided."),
        ("human",
         f"STRUCTURED DATA (ground truth):\n{structured}\n\n"
         f"AI EXPLANATION:\n{explanation}\n\n"
         "Does the explanation contain ONLY information supported by the structured data? "
         "Score 1 = fully grounded, 0 = contains hallucination."),
    ])
    return {
        "key": "hallucination_free",
        "score": result.score,
        "comment": result.reasoning,
    }


def answer_relevance(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
    """
    Score 1 if the explanation directly answers the user's query.
    Score 0 if it is off-topic or fails to address the question asked.
    """
    explanation = outputs.get("explanation") or ""
    if not explanation.strip():
        return {"key": "answer_relevance", "score": 0,
                "comment": "No explanation generated — cannot assess relevance."}

    query = inputs.get("query", "")

    result = _judge.invoke([
        ("system",
         "You are an expert evaluator assessing whether an AI response is relevant "
         "to the user's question. Score 1 = directly addresses the question, "
         "0 = off-topic or does not answer what was asked."),
        ("human",
         f"USER QUERY: {query}\n\n"
         f"AI RESPONSE:\n{explanation}\n\n"
         "Does the response directly answer the query? Score 1 = yes, 0 = no."),
    ])
    return {
        "key": "answer_relevance",
        "score": result.score,
        "comment": result.reasoning,
    }


def persona_alignment(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
    """
    Score 1 if the explanation frames findings using the active persona's priorities.
    Score 0 if it ignores persona framing (e.g. a VC explanation that only talks about moats).
    """
    explanation = outputs.get("explanation") or ""
    if not explanation.strip():
        return {"key": "persona_alignment", "score": 0,
                "comment": "No explanation generated — cannot assess persona alignment."}

    persona = inputs.get("persona", "value_investor")
    focus = _PERSONA_FOCUS.get(persona, "relevant investment criteria")

    result = _judge.invoke([
        ("system",
         "You are an expert evaluator checking whether an investment analysis is "
         "written from the correct investor persona's perspective."),
        ("human",
         f"INVESTOR PERSONA: {persona.replace('_', ' ').title()}\n"
         f"THIS PERSONA FOCUSES ON: {focus}\n\n"
         f"EXPLANATION:\n{explanation}\n\n"
         "Does the explanation frame its findings through this persona's priorities? "
         "Score 1 = yes, clearly aligned, 0 = ignores persona framing."),
    ])
    return {
        "key": "persona_alignment",
        "score": result.score,
        "comment": result.reasoning,
    }


# ── Deterministic evaluators ─────────────────────────────────────────────────

def graph_loaded(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
    """Score 1 if graph_data contains at least one node and one edge."""
    gd = outputs.get("graph_data") or {}
    nodes = gd.get("nodes") or []
    edges = gd.get("edges") or []

    if nodes and edges:
        return {"key": "graph_loaded", "score": 1,
                "comment": f"{len(nodes)} nodes, {len(edges)} edges loaded."}
    missing = []
    if not nodes: missing.append("nodes")
    if not edges: missing.append("edges")
    return {"key": "graph_loaded", "score": 0,
            "comment": f"graph_data missing: {', '.join(missing)}."}


def results_populated(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
    """
    Score 1 if:
      - results list is non-empty
      - every result has: name, composite_score, score_breakdown (non-empty dict)
    """
    results = outputs.get("results") or []
    min_expected = reference_outputs.get("min_results", 1)

    if not results:
        return {"key": "results_populated", "score": 0,
                "comment": "results list is empty."}

    if len(results) < min_expected:
        return {"key": "results_populated", "score": 0,
                "comment": f"Expected ≥{min_expected} results, got {len(results)}."}

    for r in results:
        if not r.get("name"):
            return {"key": "results_populated", "score": 0,
                    "comment": f"Result rank {r.get('rank')} is missing a name."}
        if r.get("composite_score") is None:
            return {"key": "results_populated", "score": 0,
                    "comment": f"{r.get('name')} is missing composite_score."}
        if not r.get("score_breakdown"):
            return {"key": "results_populated", "score": 0,
                    "comment": f"{r.get('name')} has no score_breakdown."}

    return {"key": "results_populated", "score": 1,
            "comment": f"{len(results)} results, all fully populated."}


def score_in_range(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
    """Score 1 if every composite_score is within [0, 1]."""
    results = outputs.get("results") or []
    if not results:
        return {"key": "score_in_range", "score": 0,
                "comment": "No results to validate scores against."}

    out_of_range = [
        f"{r.get('name')} ({r.get('composite_score')})"
        for r in results
        if r.get("composite_score") is not None
        and not (0.0 <= r["composite_score"] <= 1.0)
    ]
    if out_of_range:
        return {"key": "score_in_range", "score": 0,
                "comment": f"Out-of-range scores: {', '.join(out_of_range)}."}
    return {"key": "score_in_range", "score": 1,
            "comment": "All composite scores are within [0, 1]."}


def rationale_present(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
    """
    Score 1 if every result has ≥ 2 score_breakdown factors with a non-zero value.
    This confirms the ranking engine populated rationale, not just zeroed-out scores.
    """
    results = outputs.get("results") or []
    if not results:
        return {"key": "rationale_present", "score": 0,
                "comment": "No results to validate rationale against."}

    failures = []
    for r in results:
        bd = r.get("score_breakdown") or {}
        nonzero = [k for k, v in bd.items() if isinstance(v, (int, float)) and v > 0]
        if len(nonzero) < 2:
            failures.append(f"{r.get('name')} (only {len(nonzero)} non-zero factors)")

    if failures:
        return {"key": "rationale_present", "score": 0,
                "comment": f"Thin rationale: {'; '.join(failures)}."}
    return {"key": "rationale_present", "score": 1,
            "comment": "All results have ≥ 2 non-zero score factors."}


def expected_companies_in_results(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
    """
    Score 1 if at least one of the reference expected_companies appears in the
    top-5 results (matched by company_id, case-insensitive).
    """
    expected = reference_outputs.get("expected_companies") or []
    if not expected:
        return {"key": "expected_companies_in_results", "score": 1,
                "comment": "No expected companies specified — skipped."}

    results = outputs.get("results") or []
    top5_ids = {r.get("company_id", "").lower() for r in results[:5]}

    matched = [c for c in expected if c.lower() in top5_ids]
    if matched:
        return {"key": "expected_companies_in_results", "score": 1,
                "comment": f"Found in top 5: {', '.join(matched)}."}
    return {"key": "expected_companies_in_results", "score": 0,
            "comment": (
                f"None of {expected} found in top-5 results "
                f"({sorted(top5_ids)})."
            )}


# ── Evaluator lists for the runner ───────────────────────────────────────────

LLM_EVALUATORS = [
    hallucination_free,
    answer_relevance,
    persona_alignment,
]

DETERMINISTIC_EVALUATORS = [
    graph_loaded,
    results_populated,
    score_in_range,
    rationale_present,
    expected_companies_in_results,
]

ALL_EVALUATORS = DETERMINISTIC_EVALUATORS + LLM_EVALUATORS
