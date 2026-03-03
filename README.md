# InvestorLens

A persona-driven company intelligence search engine for the Enterprise AI and Data Infrastructure sector. The same query returns fundamentally different results depending on who is asking — and why.

---

## The Problem

Generic company search treats all users the same. A growth-stage VC evaluating Snowflake cares about developer momentum and TAM capture. A PE firm looking at the same company cares about EBITDA margins and operational improvement potential. An enterprise buyer cares about SOC2 compliance and ecosystem integrations. These are not the same question.

InvestorLens makes persona the first-class input to search.

---

## Five Investor Personas

| Persona | Priorities |
|---------|-----------|
| **Value Investor** | Durable moats, free cash flow, switching costs, margin of safety |
| **PE Firm** | EBITDA margins, operational improvement upside, revenue predictability |
| **Growth VC** | Developer traction, TAM capture rate, disruptors, market timing |
| **Strategic Acquirer** | Tech differentiation, integration fit, threat neutralization |
| **Enterprise Buyer** | Product maturity, enterprise readiness, ecosystem integrations, TCO |

---

## How It Works

### 1. Knowledge Graph
37 companies across 6 sectors are modeled as a graph in Neo4j, with typed relationships:
- `COMPETES_WITH` — direct competitive edges with strength scores
- `DISRUPTS` — asymmetric disruption relationships
- `PARTNERS_WITH` — ecosystem partnerships
- `TARGETS_SAME_SEGMENT` — shared market segments
- `SHARES_INVESTMENT_THEME` — thematic overlaps (e.g. open source, consumption pricing)

Each company node carries LLM-enriched scores (moat durability, developer adoption, enterprise readiness, etc.) alongside SEC EDGAR financial data.

### 2. Agentic Data Gathering
Queries are handled by a GPT-4o-mini ReAct agent that decides which graph traversal strategies to run based on the query and active persona. Rather than always executing a fixed pipeline, the agent reasons about which data is relevant:

- A Growth VC query surfaces disruptors before direct competitors
- A Strategic Acquirer query first profiles the target, then finds acquisition candidates
- An ambiguous query gets broadened automatically if the initial candidate set is too narrow

The agent has access to six tools covering competitors, adjacent companies, company profiles, head-to-head comparisons, acquisition targets, and attribute rankings.

### 3. Persona-Weighted Ranking
Once the agent finishes gathering candidates, a deterministic scoring engine ranks them using persona-specific weights across LLM scores, financial metrics, and graph relationship signals. Rankings are reproducible and explainable.

### 4. Natural Language Explanation
An optional GPT-4o explanation pass generates a 2–4 paragraph investment-grade narrative and 3–5 key takeaway bullets, written in the voice of the active persona.

---

## Company Universe

**37 companies across 6 sectors:**

- Cloud Data Platforms — Snowflake, Databricks, BigQuery, Redshift, Azure Synapse, Teradata, Cloudera, MotherDuck
- AI/ML Platforms — C3 AI, Palantir, Dataiku, DataRobot, H2O.ai, Scale AI, Weights & Biases, Hugging Face
- Data Integration/ETL — Fivetran, dbt Labs, Airbyte, Informatica, Talend, Matillion
- Data Observability/Governance — Monte Carlo, Atlan, Alation, Great Expectations, Collibra
- Vector/AI Infrastructure — Pinecone, Weaviate, Chroma, Zilliz/Milvus, Qdrant
- Emerging/Disruptors — Firebolt, ClickHouse, StarRocks, Neon, Supabase

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React, Vite, Tailwind CSS v4, react-force-graph-2d |
| Backend API | FastAPI (Python) |
| Agentic Orchestration | LangGraph (ReAct loop) |
| LLM | OpenAI GPT-4o / GPT-4o-mini |
| Knowledge Graph | Neo4j |
| Observability | LangSmith |
| Data Sources | SEC EDGAR XBRL API, seeded market data |
| Deployment | Vercel (frontend), Render (backend), Neo4j Aura (graph) |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                     Frontend                        │
│   Persona selector → Search bar → Results / Graph  │
└────────────────────────┬────────────────────────────┘
                         │ REST
┌────────────────────────▼────────────────────────────┐
│                   FastAPI Backend                   │
│                                                     │
│  ┌──────────────────────────────────────────────┐   │
│  │           LangGraph Agent Pipeline           │   │
│  │                                              │   │
│  │  data_gathering ◄──► tools    (ReAct loop)  │   │
│  │         │                                    │   │
│  │       rank          (deterministic)          │   │
│  │         │                                    │   │
│  │      explain        (GPT-4o, optional)       │   │
│  │         │                                    │   │
│  │     synthesize                               │   │
│  └──────────────────────────────────────────────┘   │
└──────────┬──────────────────────────────────────────┘
           │ Bolt
┌──────────▼──────────┐
│      Neo4j Graph    │
│  37 nodes, 384 edges│
└─────────────────────┘
```

---

## Demo Queries

| Query | What it demonstrates |
|-------|---------------------|
| Competitors to Snowflake | Persona differentiation — Growth VC surfaces disruptors, Value Investor surfaces established moats |
| Compare Databricks vs Snowflake through a PE lens | Head-to-head with financial metrics |
| Best acquisition target for Google to compete with Palantir | Multi-hop graph reasoning |
| Competitors to C3 AI | AI/ML platform competitive landscape |
| Compare Pinecone vs Weaviate through a VC lens | Emerging vector DB space |
| Which data infrastructure companies have the strongest moats? | Attribute-based ranking |

---

## Running Locally

### Prerequisites
- Python 3.11
- Node.js 18+
- Docker (for local Neo4j) or Neo4j Aura credentials
- OpenAI API key

### Backend

```bash
# Clone and set up Python environment
git clone https://github.com/zeus1292/investorlens.git
cd investorlens
python3.11 -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt

# Copy and fill in environment variables
cp .env.example .env
# Edit .env with your API keys and Neo4j credentials

# Start local Neo4j (or point to Aura in .env)
docker run -d \
  --name neo4j-investorlens \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/investorlens \
  neo4j:5

# Load the knowledge graph
python3 backend/graph/loader.py

# Start the API
uvicorn backend.api.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

### Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `NEO4J_URI` | Neo4j connection URI |
| `NEO4J_USER` | Neo4j username |
| `NEO4J_PASSWORD` | Neo4j password |
| `LANGSMITH_API_KEY` | LangSmith API key (optional, for tracing) |
| `SEC_EDGAR_USER_AGENT` | User agent string for SEC EDGAR API |

---

## Evaluations

The project includes a LangSmith-based evaluation suite with both LLM-as-judge and deterministic evaluators covering result quality, hallucination detection, persona alignment, and structural correctness.

```bash
# Run structural checks (no LLM cost)
python backend/evals/run_evals.py --no-llm

# Full suite
python backend/evals/run_evals.py
```
