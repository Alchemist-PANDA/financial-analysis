"""
agent.py — Calls the Groq API (free, works globally) to produce a
structured financial analysis using LLaMA 3.3 70B.
"""

import json
import sys
import os

from config import GROQ_API_KEY, MODEL_NAME, MAX_TOKENS
from app.engine.narrative import build_narrative_prompt, validate_narrative


def run_snapshot_agent(company_data: dict, metrics: dict, search_results: list = None) -> dict:
    """Call Groq and return a structured institutional-grade financial trend analysis."""

    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set.")

    # [ENHANCED SCRAPER] Add extended metrics if ticker is available
    ticker = company_data.get("ticker")
    if ticker:
        company_data.update(scrape_extended_financials(ticker))

    # Prepare data for prompt
    data_summary = json.dumps({
        "company": company_data,
        "5yr_metrics_table": metrics["yearly"],
        "senior_indicators": {
            "revenue_cagr": f"{metrics['revenue_cagr_pct']}%",
            "revenue_trajectory": metrics["revenue_trajectory"],
            "margin_signal": metrics["margin_signal"],
            "solvency_signal": metrics["solvency_signal"],
            "current_z_score": metrics["current_z_score"],
            "current_roe": f"{metrics['current_roe']}%",
            "current_dso": metrics["current_dso"],
            "current_inventory_turnover": metrics["current_inventory_turnover"],
            "current_fcf_conversion": f"{metrics['current_fcf_conversion_pct']}%",
            "debt_trajectory": metrics["debt_signal"]
        },
        "recent_news": search_results or []
    }, indent=2)

    prompt = f"""## IDENTITY & INSTITUTIONAL STANDARD
You are a Senior Institutional Partner & Global Head of Equities. Your mandate is to provide a BRUTALLY HONEST, forensics-first analysis of the provided 5-year financial dataset. You do not hedge. You do not use "could" or "might". You provide cold, hard institutional verdicts.

## ANALYTICAL DIRECTIVES: "THE PARTNER STANDARD"
1. **Forensic Quality of Earnings**: 
   - Analyze **DSO** (Days Sales Outstanding) and **Inventory Turnover**. Are they hiding bad debt or obsolete stock? 
   - Analyze **FCF Conversion**. Is EBITDA converting to cash, or is it a "paper profit"?
2. **DuPont & Solvency**: 
   - Use the **Altman Z-Score** to identify "Metabolic Distress".
   - Break down **ROE** into Margin, Turnover, and Leverage. Is the return earned through efficiency or just borrowing money?
3. **Pattern Diagnosis Archetypes**:
   - **THE CANNIBAL**: Flat revenue/EBITDA but aggressive buybacks driving EPS. "Eating itself to look healthy."
   - **THE CAPITAL DESTROYER**: High growth/revenue but negative FCF conversion and falling ROE. "Burning furniture to keep the house warm."
   - **THE MARGIN SCISSOR**: Revenue up, EBITDA margins down. "Scale is a myth here."
   - **ASSET-LIGHT FLYER**: High Asset Turnover (>1.5x) and high FCF conversion.

## DATA INPUTS
{data_summary}

## OUTPUT FORMAT — JSON STRICT
Return a valid JSON object with these EXACT keys:

pattern_diagnosis: (4-6 sentences) Start with the diagnosis (e.g. "DIAGNOSIS: THE CANNIBAL"). Explain exactly which forensic metrics (DSO, FCF, Z-Score) justify this verdict.
flags: (List of objects) {{"emoji", "name", "explanation"}}. Focus on "Red Flags" (e.g., Hidden Leverage, Working Capital Bloat) or "Green Lights" (e.g., Capital Efficiency).
analyst_verdict_archetype: [COMPOUNDER, VALUE TRAP, THE CANNIBAL, CAPITAL DESTROYER, ASSET-LIGHT FLYER, DISTRESSED]
analyst_verdict_summary: (One aggressive paragraph) Senior Partner tone. What is the #1 structural risk? Should an institutional fund hold this?
retail_verdict: (MAX 10 WORDS) A simple "Credit Karma" style sentence for retail investors. (e.g., "Safe dividend powerhouse with pristine assets" or "High-risk zombie company burning cash fast").

Return ONLY the JSON object."""

    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)

    response = client.chat.completions.create(
        model=MODEL_NAME,
        max_tokens=MAX_TOKENS,
        messages=[
            {
                "role": "system",
                "content": "You are a senior equity research analyst. Always respond with valid JSON only. No extra text. No hedging."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={"type": "json_object"},
    )

    raw_text = (response.choices[0].message.content or "").strip()

    try:
        analysis = json.loads(raw_text)
    except Exception:
        analysis = {"analysis_raw": raw_text}

    return {
        "company_name":       company_data["company_name"],
        "raw_inputs":         company_data,
        "calculated_metrics": metrics,
        "search_results":     search_results,
        "analysis":           analysis,
    }


def scrape_extended_financials(ticker: str) -> dict:
    """
    Scrapes COGS, Interest Expense, Current Assets, Current Liabilities
    from Yahoo Finance using yfinance. 
    Runs in a background thread with a 5-second timeout to prevent blocking.
    """
    import concurrent.futures

    def _fetch():
        extended = {
            "cogs": 0,
            "interest_expense": 0,
            "current_assets": 0,
            "current_liabilities": 0,
        }
        try:
            import yfinance as yf
            stock = yf.Ticker(ticker)

            # Income Statement
            income_stmt = stock.financials
            if income_stmt is not None and not income_stmt.empty:
                if "Cost Of Revenue" in income_stmt.index:
                    extended["cogs"] = float(income_stmt.loc["Cost Of Revenue"].iloc[0]) / 1_000_000
                if "Interest Expense" in income_stmt.index:
                    extended["interest_expense"] = abs(float(income_stmt.loc["Interest Expense"].iloc[0])) / 1_000_000

            # Balance Sheet
            balance_sheet = stock.balance_sheet
            if balance_sheet is not None and not balance_sheet.empty:
                if "Current Assets" in balance_sheet.index:
                    extended["current_assets"] = float(balance_sheet.loc["Current Assets"].iloc[0]) / 1_000_000
                if "Current Liabilities" in balance_sheet.index:
                    extended["current_liabilities"] = float(balance_sheet.loc["Current Liabilities"].iloc[0]) / 1_000_000
                if "Total Assets" in balance_sheet.index:
                    extended["total_assets"] = float(balance_sheet.loc["Total Assets"].iloc[0]) / 1_000_000
        except Exception:
            pass
        return extended

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_fetch)
        try:
            return future.result(timeout=1)  # Strict 1s timeout
        except concurrent.futures.TimeoutError:
            print(f"[SCRAPER TIMEOUT] Failed to fetch extended data for {ticker} in 1s.")
            return {
                "cogs": 0,
                "interest_expense": 0,
                "current_assets": 0,
                "current_liabilities": 0,
            }


def get_llm_client():
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set.")
    from groq import Groq
    return Groq(api_key=GROQ_API_KEY)


def generate_scorecard_narrative(result: dict) -> str:
    prompt = build_narrative_prompt(result)
    client = get_llm_client()

    narrative = ""
    for attempt in range(2):
        response = client.chat.completions.create(
            model=MODEL_NAME,
            max_tokens=MAX_TOKENS,
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior equity and credit analyst. Respond with the required structure only.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        narrative = (response.choices[0].message.content or "").strip()
        if validate_narrative(narrative):
            return narrative
        if attempt == 0:
            print("WARN: Narrative failed validation (missing numbers). Retrying...")

    return "[AUTO-GENERATED - verify numbers] " + narrative
