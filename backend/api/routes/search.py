"""
Search endpoint — main query interface.
"""
import sys
import os
import time
import logging

from fastapi import APIRouter, HTTPException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from api.models import SearchRequest, SearchResponse
from agents.graph import run_agent

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)

_USER_MESSAGES = {
    "Unauthorized": "The search service is temporarily unavailable. Please try again in a moment.",
    "Unable to retrieve routing information": "The search service is temporarily unavailable. Please try again in a moment.",
    "Cannot resolve address": "The search service is temporarily unavailable. Please try again in a moment.",
}


def _user_facing_message(detail: str) -> str:
    """Return a clean user-facing message, matched from known error patterns."""
    for pattern, message in _USER_MESSAGES.items():
        if pattern in detail:
            return message
    return "Something went wrong. Please try your search again."


@router.post("/search", response_model=SearchResponse, tags=["Search"])
def search_query(req: SearchRequest):
    """Execute a persona-driven search with optional NL explanation."""
    t_start = time.time()

    valid_personas = {"value_investor", "pe_firm", "growth_vc", "strategic_acquirer", "enterprise_buyer"}
    if req.persona not in valid_personas:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid persona '{req.persona}'. Must be one of: {', '.join(sorted(valid_personas))}",
        )

    try:
        result = run_agent(
            query=req.query,
            persona=req.persona,
            include_explanation=req.include_explanation,
            all_personas=req.all_personas,
        )
    except Exception as e:
        logger.error("Agent exception for query=%r persona=%r: %s", req.query, req.persona, e, exc_info=True)
        raise HTTPException(status_code=500, detail="Something went wrong. Please try your search again.")

    if "error" in result and not result.get("results"):
        logger.error("Search pipeline error for query=%r persona=%r: %s", req.query, req.persona, result["error"])
        raise HTTPException(status_code=500, detail=_user_facing_message(result["error"]))

    # Inject total elapsed time
    elapsed = int((time.time() - t_start) * 1000)
    if "metadata" in result:
        result["metadata"]["total_elapsed_ms"] = elapsed

    return result
