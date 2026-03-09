"""Quick Neo4j connection test — run from repo root with venv active."""
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

uri = os.environ["NEO4J_URI"]
user = os.environ["NEO4J_USER"]
password = os.environ["NEO4J_PASSWORD"]

print(f"URI:  {uri}")
print(f"User: {user}")
print(f"Pass: {'*' * len(password)} ({len(password)} chars)")
print()

try:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as s:
        result = s.run("RETURN 1 AS ok").single()["ok"]
        print(f"Connection OK — test query returned: {result}")
    driver.close()
except Exception as e:
    print(f"FAILED: {e}")
