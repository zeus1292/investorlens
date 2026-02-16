"""
FastAPI application for InvestorLens API.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import LANGSMITH_API_KEY, LANGSMITH_PROJECT, LANGSMITH_TRACING
from api.routes import health, search, companies, personas

# Enable LangSmith tracing if configured
if LANGSMITH_TRACING and LANGSMITH_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT

app = FastAPI(
    title="InvestorLens API",
    description="Persona-driven company intelligence search engine for Enterprise AI / Data Infrastructure",
    version="0.3.0",
)

# CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",   # Alternative frontend dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(health.router)
app.include_router(search.router)
app.include_router(companies.router)
app.include_router(personas.router)
