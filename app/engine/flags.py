"""
FLAGS ENGINE
Identifies strengths, risks, and critical alerts.
Deterministic rule-based logic only.
"""

from .constants import THRESHOLDS, DEBT_MATURITY_THRESHOLD, INVERTED_METRICS

METRIC_LABELS = {
    "roic": "Return on Invested Capital",
    "incremental_roic": "Incremental ROIC",
    "ebit_margin": "EBIT Margin",
    "gross_margin": "Gross Margin",
    "cfo_to_ebitda": "Cash Conversion (CFO/EBITDA)",
    "fcf_to_net_income": "FCF Quality (FCF/Net Income)",
    "net_debt_to_ebitda": "Leverage (Net Debt/EBITDA)",
    "interest_coverage": "Interest Coverage",
    "current_ratio": "Current Ratio",
    "quick_ratio": "Quick Ratio",
    "altman_z": "Altman Z-Score",
    "revenue_cagr": "Revenue CAGR",
    "operating_leverage": "Operating Leverage",
    "fcf_margin": "FCF Margin",
    "working_capital_change": "Working Capital Trend",
}

TABLE_METRICS = [
    "roic",
    "incremental_roic",
    "ebit_margin",
    "net_debt_to_ebitda",
    "interest_coverage",
    "current_ratio",
    "quick_ratio",
    "altman_z",
    "cfo_to_ebitda",
    "fcf_to_net_income",
    "revenue_cagr",
    "operating_leverage",
]


def classify_metric(name: str, value: float) -> str:
    """Returns STRONG / ADEQUATE / WEAK / CRITICAL for a given metric value."""
    if name not in THRESHOLDS:
        return "ADEQUATE"
    excellent, good, weak = THRESHOLDS[name]
    inverted = name in INVERTED_METRICS or excellent < weak

    if inverted:
        if value <= excellent:
            return "STRONG"
        if value <= good:
            return "ADEQUATE"
        if value <= weak:
            return "WEAK"
        return "CRITICAL"

    if value >= excellent:
        return "STRONG"
    if value >= good:
        return "ADEQUATE"
    if value >= weak:
        return "WEAK"
    return "CRITICAL"


def generate_flags(metrics: dict) -> dict:
    strengths = []
    risks = []
    critical_alerts = []

    for name, label in METRIC_LABELS.items():
        value = metrics.get(name)
        if value is None:
            continue
        status = classify_metric(name, value)
        if status == "STRONG":
            strengths.append({"metric": label, "value": value, "status": status})
        elif status in ("WEAK", "CRITICAL"):
            risks.append({"metric": label, "value": value, "status": status})
            if status == "CRITICAL":
                critical_alerts.append(
                    f"CRITICAL: {label} at {value:.2f} is in danger territory"
                )

    if metrics.get("net_debt_to_ebitda", 0) == 999:
        critical_alerts.append(
            "CRITICAL: Negative EBITDA - company cannot service debt from operations"
        )
    if metrics.get("altman_z", 3) < 1.81:
        critical_alerts.append(
            f"CRITICAL: Altman Z-Score {metrics['altman_z']:.2f} - Distress Zone"
        )
    if metrics.get("interest_coverage", 5) < 1.5:
        critical_alerts.append(
            "CRITICAL: Interest coverage below 1.5x - earnings barely cover debt service"
        )

    std = metrics.get("short_term_debt", 0)
    td = metrics.get("total_debt", 0)
    maturity_wall = (std / max(td, 0.001)) > DEBT_MATURITY_THRESHOLD if td > 0 else False
    if maturity_wall:
        critical_alerts.append(
            f"CRITICAL: Debt Maturity Wall - {std:.1f}M of debt maturing short-term "
            f"({(std/max(td,0.001)*100):.0f}% of total debt)"
        )

    strengths = sorted(strengths, key=lambda x: x["value"], reverse=True)[:3]
    risks = sorted(risks, key=lambda x: x["status"] == "CRITICAL", reverse=True)[:3]

    return {
        "top_strengths": strengths,
        "top_risks": risks,
        "critical_alerts": critical_alerts,
        "debt_maturity_wall": maturity_wall,
    }


def metric_statuses(metrics: dict) -> dict:
    return {name: classify_metric(name, metrics.get(name, 0)) for name in TABLE_METRICS}


def metric_benchmarks() -> dict:
    benchmarks = {}
    for name in TABLE_METRICS:
        if name not in THRESHOLDS:
            continue
        excellent, good, weak = THRESHOLDS[name]
        if name in INVERTED_METRICS or excellent < weak:
            benchmarks[name] = f"Excellent ≤ {excellent:.2f} | Weak ≥ {weak:.2f}"
        else:
            benchmarks[name] = f"Excellent ≥ {excellent:.2f} | Weak ≤ {weak:.2f}"
    return benchmarks
