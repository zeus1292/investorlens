import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "investorlens")
LANGSMITH_TRACING = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "investorlens")

SEC_EDGAR_USER_AGENT = os.getenv("SEC_EDGAR_USER_AGENT", "InvestorLens dev@example.com")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
COMPANIES_FILE = os.path.join(DATA_DIR, "companies.json")
