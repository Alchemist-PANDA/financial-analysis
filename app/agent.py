"""
agent.py — Calls the Groq API (free, works globally) to produce a
structured financial analysis using LLaMA 3.3 70B.
"""

import json
import sys
import os

from config import GROQ_API_KEY, MODEL_NAME, MAX_TOKENS


def run_snapshot_agent(company_data: dict, metrics: dict, search_results: list = None) -> dict:
    """Call Groq and return a structured institutional-grade financial trend analysis."""

    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set.")

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
