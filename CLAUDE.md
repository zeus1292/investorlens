# InvestorLens — Claude Session Context

## What Is This Project?
InvestorLens is a persona-driven company intelligence search engine for the Enterprise AI / Data Infrastructure sector. The same query returns fundamentally different results depending on the investor persona (Value Investor, PE Firm, Growth VC, Strategic Acquirer, Enterprise Buyer).

## Tech Stack
- **Frontend:** React + Vite, vis.js / react-force-graph
- **Backend API:** FastAPI (Python)
- **Orchestration:** LangGraph (LangChain)
- **Observability:** LangSmith
- **Knowledge Graph:** Neo4j (Docker, local — `neo4j-investorlens` container)
- **LLM Enrichment:** OpenAI GPT-4o via LangChain (LangChain-OpenAI). Anthropic support built in but unused (no credits).
- **Data Ingestion:** SEC EDGAR API (primary), yfinance (seeded fallback — Yahoo rate-limits from local env)
- **Deployment:** Vercel (frontend) + Railway/Render (backend) + Neo4j Aura

## Project Structure
```
InvestorLens/
├── backend/
│   ├── config.py                  # Centralized env config (.env loading)
│   ├── requirements.txt           # Python dependencies
│   ├── venv/                      # Python virtual environment
│   ├── data/
│   │   ├── companies.json         # Single source of truth — 37 companies with financials + LLM enrichment
│   │   ├── ingest_yfinance.py     # Yahoo Finance pull (seeded fallback when rate-limited)
│   │   ├── ingest_edgar.py        # SEC EDGAR XBRL API pull (works reliably)
│   │   └── enrich_llm.py          # LLM enrichment pipeline (OpenAI/Anthropic via --provider flag)
│   ├── graph/
│   │   ├── schema.cypher          # Neo4j constraints & indexes
│   │   ├── loader.py              # Load companies.json → Neo4j (nodes + edges)
│   │   └── queries.py             # Cypher query templates + verification
│   ├── search/
│   │   ├── query_parser.py        # Query classification + entity extraction (pattern matching)
│   │   ├── persona_configs.py     # 5 persona weight configurations
│   │   ├── graph_traversal.py     # Neo4j candidate retrieval per query type
│   │   ├── persona_ranker.py      # Scoring + ranking engine with graph relevance boost
│   │   ├── search_pipeline.py     # Orchestrator: parse → retrieve → rank
│   │   └── test_queries.py        # Verification script for all 6 demo queries × 5 personas
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── state.py               # AgentState TypedDict for LangGraph
│   │   ├── prompts.py             # 4 ChatPromptTemplates + persona voice hints
│   │   ├── explainer.py           # NL explanation generator (GPT-4o)
│   │   ├── nodes.py               # search_node, explain_node, synthesize_node
│   │   └── graph.py               # LangGraph StateGraph: search→explain→synthesize
│   └── api/
│       ├── __init__.py
│       ├── main.py                # FastAPI app, CORS, LangSmith setup
│       ├── models.py              # Pydantic request/response models
│       └── routes/
│           ├── __init__.py
│           ├── health.py          # GET /health
│           ├── search.py          # POST /api/search
│           ├── companies.py       # GET /api/companies, /api/companies/{id}
│           └── personas.py        # GET /api/personas
├── frontend/                      # (Phase 4 — not yet built)
├── .env                           # API keys: OPENAI_API_KEY, ANTHROPIC_API_KEY, NEO4J creds, etc.
├── .env.example                   # Template for .env
├── .gitignore
└── CLAUDE.md                      # This file
```

## Build Phases
1. **Phase 1: Data Pipeline + Knowledge Graph** — COMPLETED
2. **Phase 2: Search + Persona Ranking Engine** — COMPLETED
3. **Phase 3: LangGraph Orchestration + NL Explanations + FastAPI API** — COMPLETED
4. **Phase 4: Frontend** — React UI with search, results, graph viz, trace viewer

## Phase 1 Completed — What's In the Graph
- **37 Company nodes** across 6 sectors, all with LLM-enriched scores
- **6 Segment nodes** (Cloud Data Platforms, AI/ML Platforms, etc.)
- **23 InvestmentTheme nodes** (data_gravity, open_source, consumption_pricing, etc.)
- **384 total edges**: 128 COMPETES_WITH, 128 SHARES_INVESTMENT_THEME, 70 PARTNERS_WITH, 37 TARGETS_SAME_SEGMENT, 18 DISRUPTS, 3 SUPPLIES_TO
- **Financial data** for 8 public companies from SEC EDGAR + seeded market data
- **LLM-enriched attributes** per company: moat_durability, enterprise_readiness_score, developer_adoption_score, operational_improvement_potential, product_maturity_score, customer_switching_cost, revenue_predictability, market_timing_score, financial_profile_cluster, investment_themes, competitive_relationships

### Verified Demo Query Results
**Snowflake competitors (COMPETES_WITH):** Redshift (0.9), BigQuery (0.9), Databricks (0.9), Cloudera (0.8), Teradata (0.8), Azure Synapse (0.8), ClickHouse (0.7), Firebolt (0.7), MotherDuck (0.5)

**C3 AI competitors (COMPETES_WITH):** Palantir (0.7), Scale AI (0.6), DataRobot (0.6), Hugging Face (0.5)

### How to Re-run Phase 1 Pipelines
```bash
cd /Users/achilles92/Documents/Projects/InvestorLens
source backend/venv/bin/activate

# Re-ingest financial data
python3 backend/data/ingest_edgar.py
python3 backend/data/ingest_yfinance.py

# Re-run LLM enrichment (skips already enriched unless --force)
python3 backend/data/enrich_llm.py --provider openai
python3 backend/data/enrich_llm.py --provider openai --force  # re-enrich all

# Reload graph (clears and rebuilds from companies.json)
python3 backend/graph/loader.py

# Verify graph
python3 backend/graph/queries.py
```

## Phase 2 Completed — Search + Persona Ranking

### How to Run Search
```bash
cd /Users/achilles92/Documents/Projects/InvestorLens
source backend/venv/bin/activate

# Run verification (all 6 demo queries × 5 personas)
python3 backend/search/test_queries.py
```

### Pipeline Architecture
`query_parser` → `graph_traversal` → `persona_ranker` → `SearchResult`

- **Query types:** competitors_to, compare, acquisition_target, attribute_search
- **Entity resolution:** fuzzy name→company_id matching from companies.json
- **Candidate retrieval:** Neo4j traversal via COMPETES_WITH, DISRUPTS, TARGETS_SAME_SEGMENT, SHARES_INVESTMENT_THEME
- **Theme-only filtering:** candidates with only SHARES_INVESTMENT_THEME edges are filtered (prevents false competitors)
- **Graph relevance boost:** COMPETES_WITH +0.15×strength, DISRUPTS +0.10, TARGETS_SAME_SEGMENT +0.05
- **Scoring:** LLM scores normalized /10, financials min-max normalized, missing data defaults to 0.5

### Verified Persona Differentiation (Query 1: "Competitors to Snowflake")
- **Value Investor:** BigQuery, Redshift, Azure Synapse (established + positive FCF + moats)
- **PE Firm:** BigQuery, Azure Synapse, Cloudera (margins, operational improvement upside)
- **Growth VC:** ClickHouse, Databricks, BigQuery (disruptors surface!)
- **Strategic Acquirer:** BigQuery, Databricks, Redshift
- **Enterprise Buyer:** Databricks, BigQuery, Azure Synapse (Databricks #1 = enterprise-ready)

### Verified C3 AI Results (Query 4 — personally validatable)
- **Value Investor:** Palantir, DataRobot, Scale AI
- **Growth VC:** Hugging Face, Scale AI, Dataiku

### Neo4j Access
- **Docker container:** `neo4j-investorlens`
- **Browser UI:** http://localhost:7474
- **Bolt:** bolt://localhost:7687
- **Auth:** neo4j / investorlens
- **Start/stop:** `docker start neo4j-investorlens` / `docker stop neo4j-investorlens`

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

## Key Decisions Made
- **No Crunchbase** — skipped entirely, focusing on SEC EDGAR + Yahoo Finance for public companies
- **OpenAI for enrichment** — Anthropic account has no credits; OpenAI GPT-4o used via LangChain
- **Yahoo Finance seeded fallback** — yfinance library gets 429 rate-limited; seeded market data used as fallback with live attempt first
- **SEC EDGAR as primary** — reliable, free, provides revenue, net income, debt, R&D, operating cash flow
- **Informatica CIK** — corrected to 0001868778 (was wrong in initial mapping)
- **Neo4j via Docker** — local container, not Aura cloud
- **Bidirectional COMPETES_WITH** — edges created in both directions, queries deduplicate with `WITH t, max(r.strength)`

## Important Notes
- The user worked at C3 AI — Query 4 results must be personally validatable
- Ranking is a product philosophy, not a technical detail — this is the core insight
- Ship Value Investor/PE/VC personas first, add Acquirer/Buyer in Phase 3
- `companies.json` is the single source of truth — all pipelines read from and write back to it
- LLM enrichment supports `--provider openai` and `--provider anthropic` flags
- Neo4j container must be running for graph operations: `docker start neo4j-investorlens`

## Phase 3 Completed — LangGraph Agent + API

### Architecture
```
[FastAPI REST API]  →  [LangGraph Agent]  →  [Phase 2 Search]  →  [Neo4j]
                          search → explain → synthesize
                                    ↓
                              [GPT-4o NL gen]
```

### How to Run the API
```bash
docker start neo4j-investorlens
cd /Users/achilles92/Documents/Projects/InvestorLens
source backend/venv/bin/activate
uvicorn backend.api.main:app --reload --port 8000
```

### API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health + Neo4j status |
| `POST` | `/api/search` | Persona-driven search with optional NL explanation |
| `GET` | `/api/personas` | List 5 personas with descriptions |
| `GET` | `/api/companies` | List all 37 companies |
| `GET` | `/api/companies/{id}` | Single company detail |

### Search Request
```json
{
  "query": "Competitors to Snowflake",
  "persona": "value_investor",
  "include_explanation": true,
  "all_personas": false
}
```
- `include_explanation: false` returns structured-only results in ~270ms
- `include_explanation: true` adds GPT-4o NL explanation (~8-13s total)
- `all_personas: true` runs query across all 5 personas with cross-persona contrast

### LangGraph Agent
- **3 nodes:** `search_node` → `explain_node` → `synthesize_node`
- **Conditional edge:** skips `explain_node` when `include_explanation=false`
- **LangSmith tracing:** auto-enabled when `LANGCHAIN_TRACING_V2=true` in `.env`
- **NL generation:** 4 prompt templates (competitors, compare, acquisition, attribute) with persona-specific voice hints

### Verified All 6 Demo Queries via API
All queries return correct ranked results matching Phase 2 verification, with persona-appropriate NL explanations.

## What's Next — Phase 4
Build React frontend:
- Search interface with persona selector
- Results display with score breakdowns
- Graph visualization (vis.js / react-force-graph)
- NL explanation display
- Cross-persona comparison view
