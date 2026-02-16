"""
Personas endpoint — list all 5 investor personas.
"""
import sys
import os

from fastapi import APIRouter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from search.persona_configs import PERSONAS
from api.models import PersonaResponse

router = APIRouter(prefix="/api")


@router.get("/personas", response_model=list[PersonaResponse])
def list_personas():
    """List all available investor personas with their scoring weights."""
    return [
        PersonaResponse(
            name=p.name,
            display_name=p.display_name,
            description=p.description,
            weights=p.weights,
        )
        for p in PERSONAS.values()
    ]
