"""
main.py — Entry point for the Financial Snapshot Agent.

Runs the full LangGraph pipeline using sample company data and
pretty-prints the structured analysis to the console.

Usage:
    cd my_agent/app
    python main.py
"""

import sys
import os
import warnings

warnings.filterwarnings(
    "ignore",
    message=r"Core Pydantic V1 functionality isn't compatible with Python 3\.14 or greater\.",
    category=UserWarning,
)
warnings.simplefilter("ignore", RuntimeWarning)
# ── Path fix: allow running from inside app/ ──────────────────────────────────
_APP_DIR  = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.join(_APP_DIR, "..")

sys.path.insert(0, _APP_DIR)   # so: from graph import graph
sys.path.insert(0, _ROOT_DIR)  # so: from config import ...

from graph import graph
from sample_data import SEED_DATA

SAMPLE_COMPANY = SEED_DATA[0]
HISTORICAL_DATA = SAMPLE_COMPANY["data"]["metrics"]["yearly"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def print_section(title: str, width: int = 70) -> None:
    """Print a styled section header."""
    print(f"\n{title.upper()}")
    print("-" * len(title))


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("\n[*] Initializing Institutional-Grade Trend Analysis Engine...")

    # Build initial state and invoke the graph pipeline
    initial_state = {
        "company_data":    SAMPLE_COMPANY,
        "historical_data": HISTORICAL_DATA,
        "metrics":         None,
        "search_query":    "",
        "search_results":  None,
        "analysis_result": None,
    }

    try:
        final_state = graph.invoke(initial_state)
    except Exception as err:
        print(f"\n[CRITICAL FAILURE] {err}\n")
        sys.exit(1)

    metrics  = final_state["metrics"]
    result   = final_state["analysis_result"]
    analysis = result["analysis"]

    # ── OUTPUT 1: TREND SUMMARY TABLE ─────────────────────────────────────────
    width = 80
    print(f"\n{'=' * width}")
    print(f"  EQUITY RESEARCH: {result['company_name'].upper()} ({SAMPLE_COMPANY.get('ticker', 'N/A')})")
    print(f"{'=' * width}")

    print_section("OUTPUT 1: TREND SUMMARY TABLE")
    print("| Metric | " + " | ".join([y["year"] for y in metrics["yearly"]]) + " | Trend | Signal |")
    # Dynamically generate the correct number of column dividers based on the dataset length
    cols = len(metrics["yearly"])
    print("| :--- | " + " | ".join([":---:" for _ in range(cols)]) + " | :---: | :---: |")
    
    # Revenue Row
    rev_row = "| Revenue ($M) | " + " | ".join([f"{y['revenue']}" for y in metrics["yearly"]])
    rev_row += f" | {metrics['revenue_cagr_pct']}% CAGR | {metrics['revenue_trajectory']} |"
    print(rev_row)

    # Turnover/DSO Row
    dso_row = "| DSO (Days) | " + " | ".join([f"{y['dso']}" for y in metrics["yearly"]])
    dso_row += f" | {metrics['current_dso']} | COLLECTION |"
    print(dso_row)

    # Inv Turnover Row
    inv_row = "| Inv Turnover | " + " | ".join([f"{y['inventory_turnover']}x" for y in metrics["yearly"]])
    inv_row += f" | {metrics['current_inventory_turnover']}x | VELOCITY |"
    print(inv_row)

    # FCF Conversion Row
    fcf_row = "| FCF Conv % | " + " | ".join([f"{y['fcf_conversion_pct']}%" for y in metrics["yearly"]])
    fcf_row += f" | {metrics['current_fcf_conversion_pct']}% | CASH_GEN |"
    print(fcf_row)

    # EBITDA Margin Row
    ebitda_row = "| EBITDA Margin % | " + " | ".join([f"{y['ebitda_margin']}%" for y in metrics["yearly"]])
    ebitda_row += f" | STABLE | {metrics['margin_signal']} |"
    print(ebitda_row)

    # Leverage Row
    lev_row = "| Debt/EBITDA | " + " | ".join([f"{y['leverage']}x" for y in metrics["yearly"]])
    lev_row += f" | {metrics['debt_signal']} |"
    print(lev_row)

    # Altman Z-Score Row
    z_row = "| Altman Z-Score | " + " | ".join([f"{y['z_score']}" for y in metrics["yearly"]])
    z_row += f" | {metrics['solvency_signal']} |"
    print(z_row)

    # ROE Row
    roe_row = "| Return on Equity | " + " | ".join([f"{y['roe']}%" for y in metrics["yearly"]])
    roe_row += f" | {metrics['current_roe']}% | ROE |"
    print(roe_row)

    # ── OUTPUT 2: PATTERN DIAGNOSIS ───────────────────────────────────────────
    print_section("OUTPUT 2: PATTERN DIAGNOSIS")
    print(analysis.get("pattern_diagnosis", "N/A"))

    # ── OUTPUT 3: FLAG SUMMARY ────────────────────────────────────────────────
    print_section("OUTPUT 3: FLAG SUMMARY")
    flags = analysis.get("flags", [])
    if flags:
        for flag in flags:
            print(f"[!] {flag['name']}: {flag['explanation']}")
    else:
        print("No critical flags triggered.")

    # ── OUTPUT 4: ANALYST VERDICT ─────────────────────────────────────────────
    print_section(f"OUTPUT 4: ANALYST VERDICT — {analysis.get('analyst_verdict_archetype', 'N/A')}")
    print(analysis.get("analyst_verdict_summary", "N/A"))

    print(f"\n{'=' * width}\n")


if __name__ == "__main__":
    main()

