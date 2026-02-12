"""
SEC EDGAR ingestion script.
Pulls supplementary financial data from SEC EDGAR XBRL API for public companies.
Uses the Company Facts API: https://data.sec.gov/api/xbrl/companyfacts/
"""
import json
import sys
import os
import time
from datetime import datetime

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import COMPANIES_FILE, SEC_EDGAR_USER_AGENT

# Mapping of tickers to SEC CIK numbers
# CIK numbers are zero-padded to 10 digits for the API
TICKER_TO_CIK = {
    "SNOW": "0001640147",
    "TDC": "0000816761",
    "AI": "0001577526",
    "PLTR": "0001321655",
    "INFA": "0001868778",
    "AMZN": "0001018724",
    "MSFT": "0000789019",
    "GOOGL": "0001652044",
}

HEADERS = {"User-Agent": SEC_EDGAR_USER_AGENT}
BASE_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

# XBRL taxonomy keys for the data we want
FACTS_MAP = {
    "revenue": [
        "us-gaap:Revenues",
        "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
        "us-gaap:SalesRevenueNet",
    ],
    "net_income": [
        "us-gaap:NetIncomeLoss",
    ],
    "total_debt": [
        "us-gaap:LongTermDebt",
        "us-gaap:LongTermDebtNoncurrent",
    ],
    "total_assets": [
        "us-gaap:Assets",
    ],
    "rd_expense": [
        "us-gaap:ResearchAndDevelopmentExpense",
    ],
    "operating_cash_flow": [
        "us-gaap:NetCashProvidedByUsedInOperatingActivities",
    ],
}


def get_latest_annual_value(facts: dict, xbrl_keys: list) -> float | None:
    """Extract the most recent annual (10-K) value for a given XBRL concept."""
    us_gaap = facts.get("facts", {}).get("us-gaap", {})

    for key in xbrl_keys:
        concept_name = key.replace("us-gaap:", "")
        concept = us_gaap.get(concept_name, {})
        units = concept.get("units", {})

        # Financial values are in USD
        usd_entries = units.get("USD", [])
        if not usd_entries:
            continue

        # Filter to annual filings (10-K) only
        annual = [e for e in usd_entries if e.get("form") == "10-K"]
        if not annual:
            continue

        # Sort by end date, get most recent
        annual.sort(key=lambda x: x.get("end", ""), reverse=True)
        val = annual[0].get("val")
        if val is not None:
            return val

    return None


def fetch_edgar_data(ticker: str) -> dict:
    """Fetch financial data from SEC EDGAR for a single ticker."""
    cik = TICKER_TO_CIK.get(ticker)
    if not cik:
        return {"error": f"No CIK mapping for {ticker}"}

    url = BASE_URL.format(cik=cik)
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    facts = resp.json()

    result = {}
    for field_name, xbrl_keys in FACTS_MAP.items():
        value = get_latest_annual_value(facts, xbrl_keys)
        if value is not None:
            # Convert to billions
            result[f"{field_name}_annual_b"] = round(value / 1e9, 2)

    result["data_source"] = "sec_edgar"
    result["last_updated"] = datetime.now().isoformat()
    return result


def run():
    """Run SEC EDGAR ingestion for all public companies with CIK mappings."""
    with open(COMPANIES_FILE, "r") as f:
        data = json.load(f)

    public_tickers = {}
    for company in data["companies"]:
        if company.get("ticker") and company["status"] in ("public", "public_subsidiary"):
            if company["ticker"] in TICKER_TO_CIK:
                public_tickers[company["company_id"]] = company["ticker"]

    print(f"Fetching SEC EDGAR data for {len(public_tickers)} companies...")
    print()

    results = {}
    for company_id, ticker in public_tickers.items():
        try:
            print(f"  Fetching {ticker} ({company_id})...", end=" ")
            edgar_data = fetch_edgar_data(ticker)
            results[company_id] = edgar_data
            rev = edgar_data.get("revenue_annual_b", "N/A")
            rd = edgar_data.get("rd_expense_annual_b", "N/A")
            print(f"OK — annual revenue: ${rev}B, R&D: ${rd}B")
        except Exception as e:
            print(f"FAILED — {e}")
            results[company_id] = {"data_source": "sec_edgar", "error": str(e)}

        # SEC rate limit: 10 requests/second
        time.sleep(0.15)

    # Merge EDGAR data into companies.json alongside existing financials
    for company in data["companies"]:
        if company["company_id"] in results:
            edgar = results[company["company_id"]]
            if "error" not in edgar:
                company["financials"]["edgar"] = edgar

    with open(COMPANIES_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\nDone. Updated {len(results)} companies with EDGAR data.")


if __name__ == "__main__":
    run()
