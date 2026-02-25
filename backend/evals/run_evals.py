"""
InvestorLens evaluation runner.

Usage:
  # Full suite (deterministic + LLM-as-judge):
  python backend/evals/run_evals.py

  # Deterministic only — no OpenAI calls, fast structural check:
  python backend/evals/run_evals.py --no-llm

  # Re-create the LangSmith dataset (needed only once, or after changes):
  python backend/evals/run_evals.py --create-dataset

Results are uploaded to LangSmith automatically.
View them at: https://smith.langchain.com
"""
import sys
import os
import argparse

# Allow imports from backend/ root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from langsmith import Client, evaluate
from config import LANGSMITH_API_KEY, OPENAI_API_KEY
from agents.graph import run_agent
from evals.dataset import create_or_load_dataset, DATASET_NAME
from evals.evaluators import ALL_EVALUATORS, DETERMINISTIC_EVALUATORS


# ── Validation ────────────────────────────────────────────────────────────────

def _check_env():
    missing = []
    if not LANGSMITH_API_KEY:
        missing.append("LANGSMITH_API_KEY")
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    if missing:
        print(f"ERROR: Missing env vars: {', '.join(missing)}")
        print("Set them in .env and retry.")
        sys.exit(1)


# ── Target function ───────────────────────────────────────────────────────────

def target(inputs: dict) -> dict:
    """
    Wraps run_agent() for LangSmith evaluate().
    Always fetches the explanation so LLM judges have content to evaluate.
    """
    return run_agent(
        query=inputs["query"],
        persona=inputs.get("persona", "value_investor"),
        include_explanation=True,
        all_personas=False,
    )


# ── Runner ────────────────────────────────────────────────────────────────────

def run(no_llm: bool = False, create_dataset: bool = False):
    _check_env()

    client = Client(api_key=LANGSMITH_API_KEY)

    if create_dataset:
        create_or_load_dataset(client)

    evaluators = DETERMINISTIC_EVALUATORS if no_llm else ALL_EVALUATORS
    mode = "deterministic-only" if no_llm else "full (deterministic + LLM-as-judge)"
    print(f"\nRunning InvestorLens evals — mode: {mode}")
    print(f"Dataset : {DATASET_NAME}")
    print(f"Evaluators ({len(evaluators)}): {[e.__name__ for e in evaluators]}\n")

    results = evaluate(
        target,
        data=DATASET_NAME,
        evaluators=evaluators,
        experiment_prefix="investorlens",
        # Keep concurrency at 1 — Neo4j driver is not thread-safe across examples
        max_concurrency=1,
    )

    # Print a summary table
    print("\n── Results ──────────────────────────────────────────────────────")
    scores: dict[str, list[int]] = {}
    for r in results:
        for fb in r.get("feedback", []):
            key = fb.key
            scores.setdefault(key, []).append(int(fb.score or 0))

    if not scores:
        print("No scores returned — check LangSmith UI for details.")
    else:
        print(f"{'Evaluator':<35} {'Pass':>5} {'Fail':>5} {'Pass%':>7}")
        print("-" * 52)
        for key, vals in sorted(scores.items()):
            passed = sum(vals)
            failed = len(vals) - passed
            pct = 100 * passed / len(vals) if vals else 0
            print(f"{key:<35} {passed:>5} {failed:>5} {pct:>6.0f}%")

    print("\nFull results uploaded to LangSmith.")
    print("View at: https://smith.langchain.com")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run InvestorLens evaluations")
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Skip LLM-as-judge evaluators (fast, no OpenAI cost)",
    )
    parser.add_argument(
        "--create-dataset",
        action="store_true",
        help="Create (or verify) the LangSmith dataset before running evals",
    )
    args = parser.parse_args()
    run(no_llm=args.no_llm, create_dataset=args.create_dataset)
