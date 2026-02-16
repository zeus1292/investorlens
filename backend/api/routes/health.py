"""
Health check endpoint.
"""
import sys
import os

from fastapi import APIRouter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
from api.models import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health():
    """Service health check including Neo4j connectivity."""
    neo4j_status = "disconnected"
    company_count = 0

    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        with driver.session() as session:
            result = session.run("MATCH (c:Company) RETURN count(c) AS n").single()
            company_count = result["n"]
            neo4j_status = "connected"
        driver.close()
    except Exception:
        neo4j_status = "error"

    return HealthResponse(
        status="ok",
        neo4j=neo4j_status,
        company_count=company_count,
    )
