"""
NARRATIVE PROMPTING
Builds the prompt and validates LLM output.
LLM calls live in app/agent.py.
"""

import re


def build_narrative_prompt(result: dict) -> str:
    m = result.get("metrics", {})
    ss = result.get("sub_scores", {})
    mode = result.get("scoring_mode")

    strengths_text = "\n".join(
        [f"- {s['metric']}: {s['value']:.2f}" for s in result.get("top_strengths", [])]
    )
    risks_text = "\n".join(
        [
            f"- {r['metric']}: {r['value']:.2f} [{r['status']}]"
            for r in result.get("top_risks", [])
        ]
    )
    alerts_text = "\n".join(result.get("critical_alerts", [])) or "None"

    return f"""
You are a senior credit and equity analyst at a top-tier institutional investment bank.
You write in precise, clinical, institutional language.
You NEVER use vague language. You ALWAYS cite specific numbers.
You write for a sophisticated audience: lenders, fund managers, credit committees.

ANALYSIS MODE: {"Credit / Lending Assessment" if mode == "credit" else "Investment Quality Assessment"}
COMPANY: {result.get("company_name")}
HEALTH SCORE: {result.get("health_score")}/100 - {result.get("health_band")}
DATA CONFIDENCE: {result.get("confidence_label")}

SUB-SCORES:
  Business Quality: {ss.get("business_quality", 0):.1f}/25
  Cash Flow Quality: {ss.get("cash_flow", 0):.1f}/20
  Safety / Solvency: {ss.get("safety", 0):.1f}/25
  Growth Quality:    {ss.get("growth", 0):.1f}/15
  {"Valuation:        " + str(ss.get("valuation", 0)) + "/15" if mode == "investment" else ""}

KEY METRICS:
  ROIC:                {m.get("roic", 0)*100:.1f}%
  Incremental ROIC:    {m.get("incremental_roic", 0)*100:.1f}%
  EBIT Margin:         {m.get("ebit_margin", 0)*100:.1f}%
  Net Debt/EBITDA:     {m.get("net_debt_to_ebitda", 0):.2f}x
  Interest Coverage:   {m.get("interest_coverage", 0):.2f}x
  Current Ratio:       {m.get("current_ratio", 0):.2f}x
  Altman Z-Score:      {m.get("altman_z", 0):.2f} ({m.get("altman_z_full", {}).get("zone", "")})
  CFO/EBITDA:          {m.get("cfo_to_ebitda", 0):.2f}x
  FCF/Net Income:      {m.get("fcf_to_net_income", 0):.2f}x
  Revenue CAGR:        {m.get("revenue_cagr", 0)*100:.1f}%
  Operating Leverage:  {m.get("operating_leverage", 0):.2f}x

TOP STRENGTHS:
{strengths_text if strengths_text else "None identified"}

TOP RISKS:
{risks_text if risks_text else "None identified"}

CRITICAL ALERTS:
{alerts_text}

{"DEBT MATURITY WALL: YES - Immediate refinancing risk." if result.get("debt_maturity_wall") else ""}

WRITE EXACTLY THIS STRUCTURE. No deviations. No extra sections.

EXECUTIVE SUMMARY (2 sentences):
[Sentence 1: Overall verdict with health score and the single most important metric driving it.]
[Sentence 2: The dominant theme - what kind of financial profile this is.]

TOP STRENGTHS (exactly 2 bullet points, each citing a specific number):
- [Strength 1]
- [Strength 2]

TOP RISKS (exactly 2 bullet points, each citing a specific number):
- [Risk 1]
- [Risk 2]

{"TREND INTERPRETATION (1 sentence about growth and quality direction):" if m.get("revenue_cagr", 0) != 0 else ""}
{"[Trend sentence]" if m.get("revenue_cagr", 0) != 0 else ""}

FINAL VERDICT (1 sentence):
[Plain English conclusion. What would a senior credit officer or portfolio manager do with this?]

RULES:
- Minimum 4 specific numbers must appear in your response.
- Never say "the company faces challenges" without naming the specific metric.
- Never exceed 250 words total.
- {"Focus on debt serviceability and survival capacity." if mode == "credit" else "Focus on quality of returns and valuation attractiveness."}
"""


def validate_narrative(narrative: str) -> bool:
    numbers = re.findall(r"\d+\.?\d*[%x]?", narrative)
    return len(numbers) >= 4
