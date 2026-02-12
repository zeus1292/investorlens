# InvestorLens — Claude Session Context

## What Is This Project?
InvestorLens is a persona-driven company intelligence search engine for the Enterprise AI / Data Infrastructure sector. The same query returns fundamentally different results depending on the investor persona (Value Investor, PE Firm, Growth VC, Strategic Acquirer, Enterprise Buyer).

## Tech Stack
- **Frontend:** React + Vite, vis.js / react-force-graph
- **Backend API:** FastAPI (Python)
- **Orchestration:** LangGraph (LangChain)
- **Observability:** LangSmith
- **Knowledge Graph:** Neo4j (Docker or Aura free tier)
- **LLM:** Claude (Anthropic API)
- **Data Ingestion:** yfinance, SEC EDGAR API, GitHub API
- **Deployment:** Vercel (frontend) + Railway/Render (backend) + Neo4j Aura

## Project Structure
```
investorlens/
├── backend/
│   ├── data/           # Company universe, ingestion scripts, LLM enrichment
│   ├── graph/          # Neo4j schema, Cypher query templates, graph loader
│   ├── search/         # Query parsing, persona ranking, search pipeline
│   ├── agents/         # LangGraph workflows, agent nodes, prompt templates
│   │   └── prompts/    # Persona-specific explanation prompts
│   └── api/            # FastAPI app, routes, Pydantic models
├── frontend/
│   └── src/
│       ├── components/ # SearchBar, PersonaSelector, ResultsPanel, GraphPanel, TracePanel
│       └── hooks/      # useSearch, useGraph
├── .env                # API keys (not committed)
└── CLAUDE.md           # This file
```

## Build Phases
1. **Phase 1: Data Pipeline + Knowledge Graph** — Ingest, enrich, load ~37 companies into Neo4j
2. **Phase 2: Search + Persona Ranking Engine** — Query parsing, graph traversal, persona-specific scoring
3. **Phase 3: LangChain Orchestration + NL Explanations** — LangGraph agents, LangSmith tracing, NL generation
4. **Phase 4: Frontend** — React UI with search, results, graph viz, trace viewer

## Company Universe
~37 companies across 6 categories:
- Cloud Data Platforms (8): Snowflake, Databricks, BigQuery, Redshift, Azure Synapse, Teradata, Cloudera, MotherDuck
- AI/ML Platforms (8): C3 AI, Palantir, Dataiku, DataRobot, H2O.ai, Scale AI, Weights & Biases, Hugging Face
- Data Integration/ETL (6): Fivetran, dbt Labs, Airbyte, Informatica, Talend, Matillion
- Data Observability/Governance (5): Monte Carlo, Atlan, Alation, Great Expectations, Collibra
- Vector/AI Infrastructure (5): Pinecone, Weaviate, Chroma, Zilliz/Milvus, Qdrant
- Emerging/Disruptors (5): Firebolt, ClickHouse, StarRocks, Neon, Supabase

## 5 Personas (Scoring Weights)
- **Value Investor:** moat_durability, fcf_consistency, switching_costs, low_debt, management, valuation
- **PE Firm:** ebitda_margin, operational_improvement, revenue_predictability, valuation_multiple, concentration_risk, rollup
- **Growth VC:** revenue_growth, tam_capture, developer_adoption, funding_momentum, product_velocity, market_timing
- **Strategic Acquirer:** tech_differentiation, integration_fit, threat_neutralization, team_ip, price, regulatory
- **Enterprise Buyer:** product_maturity, enterprise_readiness, integration_ecosystem, tco, satisfaction, lock_in_risk

## 6 Demo Queries
1. "Competitors to Snowflake" — hero query, must show distinct top-3 per persona
2. "Compare Databricks vs Snowflake through a PE lens" — head-to-head with PE metrics
3. "Best acquisition target for Google to compete with Palantir" — multi-hop graph reasoning
4. "Competitors to C3 AI" — personally validatable (user worked at C3 AI)
5. "Compare Pinecone vs Weaviate through a VC lens" — emerging vector DB space
6. "Which data infrastructure companies have the strongest moats?" — stretch, attribute search

## Current Status
- **Phase:** Pre-build (spec received)
- **What's been done:** CLAUDE.md created, project directory initialized
- **What's next:** Phase 1 — project scaffolding, data pipeline, Neo4j setup

## Key Decisions Made
_(none yet — will be updated as we build)_

## Important Notes
- The user worked at C3 AI — Query 4 results must be personally validatable
- Ranking is a product philosophy, not a technical detail — this is the core insight
- Ship Value Investor/PE/VC personas first, add Acquirer/Buyer in Phase 3
- Start with yfinance for financials; EDGAR is enrichment, not dependency
