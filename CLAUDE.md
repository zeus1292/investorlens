# InvestorLens — Claude Session Context

## What Is This Project?
InvestorLens is a persona-driven company intelligence search engine for the Enterprise AI / Data Infrastructure sector. The same query returns fundamentally different results depending on the investor persona (Value Investor, PE Firm, Growth VC, Strategic Acquirer, Enterprise Buyer).

## Tech Stack
- **Frontend:** React + Vite + Tailwind CSS v4, react-force-graph-2d
- **Backend API:** FastAPI (Python)
- **Orchestration:** LangGraph (LangChain)
- **Observability:** LangSmith
- **Knowledge Graph:** Neo4j (Docker, local — `neo4j-investorlens` container)
- **LLM Enrichment:** OpenAI GPT-4o via LangChain (LangChain-OpenAI). Anthropic support built in but unused (no credits).
- **LLM Evaluation:** GPT-4o-mini as judge via LangSmith `evaluate()`
- **Data Ingestion:** SEC EDGAR API (primary), yfinance (seeded fallback — Yahoo rate-limits from local env)
- **Deployment:** Vercel (frontend) + Render free tier (backend) + Neo4j Aura

## Project Structure
```
InvestorLens/
├── render.yaml                # Render deployment config (free tier, build + start commands)
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
│   ├── evals/
│   │   ├── __init__.py
│   │   ├── dataset.py             # 6 verified demo queries with reference outputs for LangSmith
│   │   ├── evaluators.py          # 3 LLM-as-judge + 5 deterministic evaluators
│   │   └── run_evals.py           # CLI runner: --no-llm for fast structural check
│   └── api/
│       ├── __init__.py
│       ├── main.py                # FastAPI app, CORS (ALLOWED_ORIGINS env var), LangSmith setup
│       ├── models.py              # Pydantic request/response models
│       └── routes/
│           ├── __init__.py
│           ├── health.py          # GET /health
│           ├── search.py          # POST /api/search
│           ├── companies.py       # GET /api/companies, /api/companies/{id}
│           └── personas.py        # GET /api/personas
├── frontend/
│   ├── vite.config.js             # Vite config with Tailwind + dev proxy to localhost:8000
│   ├── package.json
│   ├── src/
│   │   ├── main.jsx               # React entry point
│   │   ├── App.jsx                # Landing/results view switcher; tab state (Rankings / Relationship Map); cold start banner; node click handler
│   │   ├── index.css              # Tailwind @theme — light pastel green palette
│   │   ├── api/
│   │   │   └── client.js          # API client (BASE from VITE_API_URL env var)
│   │   ├── hooks/
│   │   │   ├── useSearch.js       # Search + explanation state management
│   │   │   ├── usePersonas.js     # Fetch personas from API
│   │   │   └── useCompanies.js    # Fetch companies from API
│   │   ├── components/
│   │   │   ├── SearchBar.jsx      # mode="landing" (hero) / mode="header" (compact)
│   │   │   ├── PersonaSelector.jsx # compact (pills) / default (large cards with descriptions)
│   │   │   ├── DemoQueries.jsx    # 3 curated queries per persona (PERSONA_QUERIES map)
│   │   │   ├── common/            # ErrorBanner, LoadingSpinner, MetadataBar
│   │   │   ├── results/           # ResultCard (collapsible + Strong/Moderate/Weak badge),
│   │   │   │                      # ScoreBreakdown (pie chart), ResultsContainer (info icon tooltip),
│   │   │   │                      # Competitor/Compare/Acquisition/AttributeResults (CSS columns layout)
│   │   │   ├── graph/             # GraphPanel — force-directed, clickable nodes, sector colors, legend
│   │   │   ├── explanation/       # ExplanationPanel — NL analysis + key insights
│   │   │   └── crossPersona/      # CrossPersonaTable — 5-persona side-by-side
│   │   └── utils/
│   │       ├── colors.js          # PERSONA_COLORS, PERSONA_BG_COLORS, EDGE_COLORS, SECTOR_COLORS
│   │       └── format.js          # formatCompositeScore, formatAttributeName, formatElapsed
├── .env                           # API keys: OPENAI_API_KEY, ANTHROPIC_API_KEY, NEO4J creds, etc.
├── .env.example                   # Template for .env
├── .gitignore
└── CLAUDE.md                      # This file
```

## Build Phases
1. **Phase 1: Data Pipeline + Knowledge Graph** — COMPLETED
2. **Phase 2: Search + Persona Ranking Engine** — COMPLETED
3. **Phase 3: LangGraph Orchestration + NL Explanations + FastAPI API** — COMPLETED
4. **Phase 4: Frontend** — COMPLETED
5. **Phase 5: Evaluations** — COMPLETED
6. **Phase 6: Deployment** — Vercel (frontend) + Render free tier (backend) + Neo4j Aura

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
- **Render over Railway** — Render has a true free tier; Railway requires $5/month minimum. Cold start (~50s) acceptable for ≤10 users/month.
- **GPT-4o-mini for evaluation** — cheaper than GPT-4o, sufficient for LLM-as-judge scoring

## Important Notes
- The user worked at C3 AI — Query 4 results must be personally validatable
- Ranking is a product philosophy, not a technical detail — this is the core insight
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

### CORS Configuration
Production frontend URL is passed via `ALLOWED_ORIGINS` env var (comma-separated). Localhost origins are always included as fallback for local dev.

## Phase 4 Completed — Frontend

### UI Design
- **Light pastel green theme** — `surface-50` (#f4f8f5) body, white cards, green accent
- **Persona-first landing page:** Title → DataSnapshot (37/6/384/5) → "Pick your lens" persona cards → persona-specific demo queries → centered search bar
- **Landing → Results transition:** first search flips to compact sticky header (logo + persona pills + search input + all-personas checkbox)
- **Tab interface on results page:** "Rankings" tab (result cards + AI explanation) and "Relationship Map" tab (graph full-width at 620px). Tab resets to Rankings on every new search.
- **Collapsible result cards** in CSS columns layout (not CSS grid) — expanding a card pushes neighbours down naturally with no blank spaces. Collapsed shows rank + name + score + Strong/Moderate/Weak badge. Expanded shows donut pie chart breakdown + graph context badges.
- **Score labels:** Strong (≥0.70, green) / Moderate (0.50–0.69, amber) / Weak (<0.50, gray) badge on every card.
- **Info icon tooltip** in top-right of results — explains how to read the pie chart slices and score numbers. Tooltip drops below the icon (not above, avoids sticky header clip), right-aligned, white background with dark text.
- **Cold start warning banner** — amber strip shown after 2s if `/health` hasn't responded. Auto-dismisses when server replies. Appears on both landing and results views.
- **Clickable graph nodes** — hovering shows "Search: Competitors to {company}" tooltip; clicking fires that search and switches to Rankings tab.
- **SVG donut pie charts** for score breakdown (replaced horizontal bars)
- **Cross-persona comparison table** when "All personas" is checked

### How to Run Frontend
```bash
cd /Users/achilles92/Documents/Projects/InvestorLens/frontend
npm install    # first time only
npm run dev    # Vite dev server at localhost:5173, proxies /api to localhost:8000
npm run build  # production build to dist/
```

### API Base URL
- **Dev:** Vite proxy in `vite.config.js` forwards `/api` + `/health` to `http://localhost:8000`
- **Production:** Set `VITE_API_URL` env var to deployed backend URL. Read in `src/api/client.js` via `import.meta.env.VITE_API_URL`

### Frontend Key Files
| File | Purpose |
|------|---------|
| `App.jsx` | Landing/results switcher; `activeTab` state; cold start banner via `/health` ping; `handleNodeClick` fires "Competitors to X" on graph node click |
| `SearchBar.jsx` | `mode="landing"` (hero) / `mode="header"` (compact row) |
| `PersonaSelector.jsx` | `compact` prop: pills for header, large cards for landing |
| `DemoQueries.jsx` | `PERSONA_QUERIES` map — 3 curated queries per persona |
| `ResultCard.jsx` | Collapsible card + `scoreLabel()` helper for Strong/Moderate/Weak badge |
| `ScoreBreakdown.jsx` | SVG donut pie chart + color legend |
| `ResultsContainer.jsx` | Routes query_type to result component; renders `PieChartInfo` tooltip |
| `CompetitorResults.jsx` | CSS `columns-2` layout with `break-inside-avoid` — no blank spaces on expand |
| `GraphPanel.jsx` | Force-directed graph; `onNodeClick` prop triggers search from App.jsx |
| `colors.js` | PERSONA_COLORS, PERSONA_BG_COLORS, EDGE_COLORS, SECTOR_COLORS |
| `client.js` | API client — `fetchHealth` used for cold start detection on mount |

## Phase 5 Completed — Evaluations

### Overview
LangSmith-based evaluation suite covering both LLM-as-judge quality checks and deterministic structural validations. Dataset of 6 verified demo queries is stored in LangSmith and reused across runs.

### How to Run Evaluations
```bash
source backend/venv/bin/activate

# First time only — create the dataset in LangSmith
python backend/evals/run_evals.py --create-dataset

# Full suite (deterministic + LLM-as-judge, ~$0.10/run with gpt-4o-mini)
python backend/evals/run_evals.py

# Fast structural check — no LLM cost
python backend/evals/run_evals.py --no-llm
```

### Evaluators

**LLM-as-judge (GPT-4o-mini)**
| Evaluator | What it checks |
|-----------|---------------|
| `hallucination_free` | Explanation only references companies/data present in structured results |
| `answer_relevance` | Explanation directly addresses the user's query |
| `persona_alignment` | Explanation frames findings through the active persona's priorities |

**Deterministic**
| Evaluator | What it checks |
|-----------|---------------|
| `graph_loaded` | `graph_data` has ≥1 node and ≥1 edge |
| `results_populated` | Results list non-empty; every item has name, composite_score, score_breakdown |
| `score_in_range` | All `composite_score` values are within [0, 1] |
| `rationale_present` | Every result has ≥2 non-zero score_breakdown factors |
| `expected_companies_in_results` | At least one reference company appears in top-5 results |

### Key Tunable Parameters
- `_PERSONA_FOCUS` dict in `evaluators.py` — one-line priority description per persona used by the `persona_alignment` judge. Edit these to tighten/loosen what "aligned" means.
- `results[:5]` in `expected_companies_in_results` — change to `results[:3]` for stricter accuracy.
- `len(nonzero) < 2` in `rationale_present` — raise threshold for stricter rationale coverage.
- Dataset `expected_companies` lists in `dataset.py` — add/remove company_ids to refine ground truth.

### LangSmith Dataset
- **Name:** `investorlens-eval-v1`
- **Examples:** 6 (one per demo query, covering all 4 query types)
- **View at:** https://smith.langchain.com

## Deployment

### Free Hosting Stack (no credit card required)
| Service | Platform | Notes |
|---------|----------|-------|
| Frontend | Vercel free tier | Auto-deploys on push to main |
| Backend | Render free tier | Sleeps after 15min; ~50s cold start |
| Database | Neo4j Aura free | 200MB, 200k nodes — sufficient for 37 companies |

### Deployment Steps (one-time)
1. **Neo4j Aura** — create free instance at console.neo4j.io, then load data: `NEO4J_URI=neo4j+s://... python3 backend/graph/loader.py`
2. **Render** — connect `zeus1292/investorlens` repo; `render.yaml` at root is auto-detected
3. **Vercel** — connect same repo, root directory = `frontend`, set `VITE_API_URL`
4. **Wire CORS** — set `ALLOWED_ORIGINS=https://your-app.vercel.app` in Render env vars

### Backend — Render
- **Config file:** `render.yaml` (repo root)
- **Build command:** `pip install -r backend/requirements.txt`
- **Start command:** `uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT`
- **Required env vars:** `OPENAI_API_KEY`, `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `SEC_EDGAR_USER_AGENT`, `ALLOWED_ORIGINS`, `LANGCHAIN_TRACING_V2`

### Frontend — Vercel
- **Repo:** github.com/zeus1292/investorlens
- **Root Directory:** `frontend`
- **Build Command:** `npm run build`
- **Output Directory:** `dist`
- **Environment Variable:** `VITE_API_URL` = Render backend URL

### GitHub Remote
- **Origin:** `https://github.com/zeus1292/investorlens.git`
