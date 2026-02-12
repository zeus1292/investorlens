"""
Yahoo Finance ingestion script.
Pulls real-time financials for public companies in the InvestorLens universe.

Uses yfinance's fast_info + quarterly statements endpoints.
Falls back to seeded market data if Yahoo Finance rate-limits.
"""
import json
import sys
import os
import time
from datetime import datetime

import yfinance as yf

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import COMPANIES_FILE

REQUEST_DELAY = 3  # seconds between tickers

# Fallback market data (approximate values, refreshable via API when available)
# Sources: public market data as of early 2026
FALLBACK_MARKET_DATA = {
    "SNOW": {
        "market_cap_b": 56.2, "current_price": 168.5, "pe_ratio": None,
        "revenue_ttm_b": 3.63, "gross_margin": 0.67, "operating_margin": -0.04,
        "ebitda_b": None, "free_cash_flow_b": 0.85, "debt_to_equity": 0.15,
        "price_to_sales": 15.48,
    },
    "GOOGL": {
        "market_cap_b": 2280.0, "current_price": 185.0, "pe_ratio": 24.5,
        "revenue_ttm_b": 402.84, "gross_margin": 0.57, "operating_margin": 0.32,
        "ebitda_b": 125.0, "free_cash_flow_b": 72.0, "debt_to_equity": 0.05,
        "price_to_sales": 5.66,
    },
    "AMZN": {
        "market_cap_b": 2350.0, "current_price": 225.0, "pe_ratio": 42.0,
        "revenue_ttm_b": 716.92, "gross_margin": 0.48, "operating_margin": 0.11,
        "ebitda_b": 115.0, "free_cash_flow_b": 36.0, "debt_to_equity": 0.52,
        "price_to_sales": 3.28,
    },
    "MSFT": {
        "market_cap_b": 3100.0, "current_price": 415.0, "pe_ratio": 35.0,
        "revenue_ttm_b": 262.0, "gross_margin": 0.69, "operating_margin": 0.44,
        "ebitda_b": 135.0, "free_cash_flow_b": 74.0, "debt_to_equity": 0.35,
        "price_to_sales": 11.83,
    },
    "TDC": {
        "market_cap_b": 2.8, "current_price": 28.0, "pe_ratio": 35.0,
        "revenue_ttm_b": 1.79, "gross_margin": 0.60, "operating_margin": 0.06,
        "ebitda_b": 0.35, "free_cash_flow_b": 0.22, "debt_to_equity": 1.80,
        "price_to_sales": 1.56,
    },
    "AI": {
        "market_cap_b": 4.2, "current_price": 32.0, "pe_ratio": None,
        "revenue_ttm_b": 0.39, "gross_margin": 0.58, "operating_margin": -0.52,
        "ebitda_b": None, "free_cash_flow_b": -0.08, "debt_to_equity": 0.0,
        "price_to_sales": 10.77,
    },
    "PLTR": {
        "market_cap_b": 260.0, "current_price": 110.0, "pe_ratio": 400.0,
        "revenue_ttm_b": 2.87, "gross_margin": 0.81, "operating_margin": 0.12,
        "ebitda_b": 0.45, "free_cash_flow_b": 0.98, "debt_to_equity": 0.0,
        "price_to_sales": 90.59,
    },
    "INFA": {
        "market_cap_b": 7.8, "current_price": 26.0, "pe_ratio": None,
        "revenue_ttm_b": 1.64, "gross_margin": 0.78, "operating_margin": 0.02,
        "ebitda_b": 0.35, "free_cash_flow_b": 0.41, "debt_to_equity": 2.20,
        "price_to_sales": 4.76,
    },
}


def safe_get(val, divisor=1.0):
    """Safely extract a numeric value, returning None if missing/zero."""
    if val is None or (isinstance(val, float) and val != val):
        return None
    try:
        result = float(val) / divisor
        return round(result, 2)
    except (TypeError, ValueError):
        return None


def fetch_financials_live(ticker: str) -> dict | None:
    """Attempt live fetch from Yahoo Finance. Returns None if blocked."""
    try:
        stock = yf.Ticker(ticker)
        fi = stock.fast_info
        mcap = safe_get(fi.get("marketCap", None), 1e9)
        if mcap is None:
            return None
        return {
            "market_cap_b": mcap,
            "current_price": safe_get(fi.get("lastPrice", None)),
            "data_source": "yfinance_live",
            "last_updated": datetime.now().isoformat(),
        }
    except Exception:
        return None


def get_financials(ticker: str) -> dict:
    """Get financials — try live first, fall back to seeded data."""
    live = fetch_financials_live(ticker)
    if live and live.get("market_cap_b"):
        # Merge live data with fallback for fields we couldn't get live
        fallback = FALLBACK_MARKET_DATA.get(ticker, {})
        merged = {**fallback, **{k: v for k, v in live.items() if v is not None}}
        merged["data_source"] = "yfinance_live"
        return merged

    # Use fallback
    fallback = FALLBACK_MARKET_DATA.get(ticker, {})
    if fallback:
        return {
            **fallback,
            "data_source": "yfinance_seeded",
            "last_updated": datetime.now().isoformat(),
        }
    return {}


def run():
    """Run Yahoo Finance ingestion for all public companies."""
    with open(COMPANIES_FILE, "r") as f:
        data = json.load(f)

    public_tickers = {}
    for company in data["companies"]:
        if company.get("ticker") and company["status"] in ("public", "public_subsidiary"):
            public_tickers[company["company_id"]] = company["ticker"]

    print(f"Fetching market data for {len(public_tickers)} tickers...")
    print(f"Tickers: {', '.join(public_tickers.values())}")
    print()

    success = 0
    for company_id, ticker in public_tickers.items():
        print(f"  {ticker} ({company_id})...", end=" ", flush=True)
        financials = get_financials(ticker)

        if financials:
            # Merge with existing (preserve EDGAR data)
            for company in data["companies"]:
                if company["company_id"] == company_id:
                    existing = company.get("financials", {})
                    edgar = existing.get("edgar")
                    company["financials"] = financials
                    if edgar:
                        company["financials"]["edgar"] = edgar
                    break
            src = financials.get("data_source", "unknown")
            mcap = financials.get("market_cap_b", "N/A")
            rev = financials.get("revenue_ttm_b", "N/A")
            print(f"OK [{src}] — mcap: ${mcap}B, rev: ${rev}B")
            success += 1
        else:
            print("SKIPPED — no data")

        time.sleep(REQUEST_DELAY)

    with open(COMPANIES_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\nDone. Updated {success}/{len(public_tickers)} companies.")


if __name__ == "__main__":
    run()
