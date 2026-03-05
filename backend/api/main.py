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

_DESCRIPTION = """
## InvestorLens API

A **persona-driven company intelligence search engine** for the Enterprise AI & Data Infrastructure sector.

The same query returns fundamentally different results depending on who is asking — and why.

### Five investor personas
| Persona | Key Priorities |
|---------|---------------|
| `value_investor` | Durable moats, free cash flow, switching costs |
| `pe_firm` | EBITDA margins, operational improvement upside |
| `growth_vc` | Developer traction, TAM capture rate, disruptors |
| `strategic_acquirer` | Tech differentiation, integration fit, threat neutralisation |
| `enterprise_buyer` | Product maturity, enterprise readiness, ecosystem integrations |

### How it works
1. A **ReAct LangGraph agent** (GPT-4o-mini) decides which Neo4j graph-traversal tools to call based on the query + persona.
2. A **deterministic scoring engine** ranks candidates using persona-specific weights.
3. An optional **GPT-4o pass** generates a 2–4 paragraph investment-grade narrative.

### Company universe
37 companies across 6 sectors — Cloud Data Platforms, AI/ML Platforms, Data Integration/ETL,
Data Observability/Governance, Vector/AI Infrastructure, Emerging Disruptors.
"""

_TAGS = [
    {
        "name": "Search",
        "description": "Persona-driven company intelligence search. Core endpoint.",
    },
    {
        "name": "Personas",
        "description": "List the five investor personas and their scoring weights.",
    },
    {
        "name": "Companies",
        "description": "Browse the 37-company universe with key financials and LLM scores.",
    },
    {
        "name": "Health",
        "description": "Service health check — verifies Neo4j connectivity.",
    },
]

app = FastAPI(
    title="InvestorLens API",
    description=_DESCRIPTION,
    version="0.3.0",
    contact={
        "name": "InvestorLens",
        "url": "https://github.com/zeus1292/investorlens",
    },
    license_info={
        "name": "MIT",
    },
    openapi_tags=_TAGS,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — read from env var in production, fall back to localhost for dev
_raw_origins = os.environ.get("ALLOWED_ORIGINS", "")
_extra_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]
_origins = [
    "http://localhost:5173",   # Vite dev server
    "http://localhost:3000",   # Alternative frontend dev
] + _extra_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(health.router)
app.include_router(search.router)
app.include_router(companies.router)
app.include_router(personas.router)
