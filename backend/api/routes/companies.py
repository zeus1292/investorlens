"""
Companies endpoints — list and detail.
"""
import json
import sys
import os

from fastapi import APIRouter, HTTPException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from config import COMPANIES_FILE
from api.models import CompanyResponse

router = APIRouter(prefix="/api")

# Cache companies in memory (loaded once)
_companies_cache: list[dict] | None = None


def _load_companies() -> list[dict]:
    global _companies_cache
    if _companies_cache is None:
        with open(COMPANIES_FILE) as f:
            data = json.load(f)
        _companies_cache = data["companies"]
    return _companies_cache


def _company_to_response(c: dict) -> CompanyResponse:
    llm = c.get("llm_enriched", {}) or {}
    fin = c.get("financials", {}) or {}
    mkt = c.get("market_data", {}) or {}
    return CompanyResponse(
        company_id=c["company_id"],
        name=c["name"],
        sector=c.get("sector", ""),
        status=c.get("status", ""),
        description=c.get("description", ""),
        market_cap_b=mkt.get("market_cap_b") or fin.get("market_cap_b"),
        revenue_ttm_b=fin.get("revenue_ttm_b"),
        moat_durability=llm.get("moat_durability"),
        enterprise_readiness_score=llm.get("enterprise_readiness_score"),
        developer_adoption_score=llm.get("developer_adoption_score"),
        financial_profile_cluster=llm.get("financial_profile_cluster"),
    )


@router.get("/companies", response_model=list[CompanyResponse])
def list_companies():
    """List all companies in the universe."""
    companies = _load_companies()
    return [_company_to_response(c) for c in companies]


@router.get("/companies/{company_id}", response_model=CompanyResponse)
def get_company(company_id: str):
    """Get a single company by ID."""
    companies = _load_companies()
    for c in companies:
        if c["company_id"] == company_id:
            return _company_to_response(c)
    raise HTTPException(status_code=404, detail=f"Company '{company_id}' not found")
