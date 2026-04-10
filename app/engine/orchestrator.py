"""
MASTER ORCHESTRATOR
Single entry point for all engine computations.
Takes raw inputs dict → returns complete structured result dict.
"""

from datetime import datetime

from app.calculator import (
    numeric_value,
    safe_div,
    calc_nopat,
    calc_invested_capital,
    calc_roic,
    calc_incremental_roic,
    calc_ebit,
    calc_gross_margin,
    calc_ebit_margin,
    calc_roe,
    calc_asset_turnover,
    calc_operating_leverage,
    calc_fcf,
    calc_cfo_to_ebitda,
    calc_fcf_to_net_income,
    calc_fcf_margin,
    calc_cash_conversion_cycle,
    calc_working_capital_change,
    calc_net_debt,
    calc_net_debt_to_ebitda,
    calc_interest_coverage,
    calc_current_ratio,
    calc_quick_ratio,
    calc_cagr,
    calc_ev_to_ebitda,
    calc_pe_ratio,
    calc_fcf_yield,
    calc_altman_z,
)
from .constants import SCORING_MODEL_VERSION, CONFIDENCE_LEVELS
from .scoring import (
    score_business_quality,
    score_cash_flow,
    score_safety,
    score_growth,
    score_valuation,
    aggregate_health_score,
)
from .flags import generate_flags, metric_statuses, metric_benchmarks


def run_full_analysis(inputs: dict, mode: str = "credit") -> dict:
    """
    inputs dict keys (all in $M or ratios):
      company_name, revenue, ebitda, net_income, interest_expense,
      total_debt, cash_equivalents, total_assets, current_assets,
      current_liabilities

      Optional (prior period for incremental/growth calcs):
        revenue_prior, ebitda_prior, net_income_prior,
        total_debt_prior, cash_prior, total_equity_prior,
        cfo_prior, fcf_prior

      Optional (for full metrics):
        gross_profit, cfo, capex, accounts_receivable,
        inventory, accounts_payable, cogs,
        short_term_debt, market_cap, ev,
        retained_earnings, total_equity, tax_rate

      Optional (metadata):
        data_source (str): 'manual' | 'ticker' | 'uploaded'
        revenue_cagr_years (int): number of years for CAGR calc
    """

    confidence = inputs.get("data_source", "manual")
    company_name = inputs.get("company_name", "Unknown")

    def n(key: str, default: float = 0.0) -> float:
        return numeric_value(inputs, key, default)

    revenue = n("revenue")
    ebitda = n("ebitda")
    net_income = n("net_income")
    interest_exp = n("interest_expense")
    total_debt = n("total_debt")
    cash = n("cash_equivalents", n("cash"))
    total_assets = n("total_assets")
    curr_assets = n("current_assets")
    curr_liab = n("current_liabilities")
    short_term_debt = n("short_term_debt")
    gross_profit = n("gross_profit", ebitda * 0.6)
    cfo = n("cfo", ebitda * 0.75)
    capex = n("capex", revenue * 0.04)
    ar = n("accounts_receivable")
    inventory = n("inventory")
    ap = n("accounts_payable")
    cogs = n("cogs", revenue - gross_profit)
    market_cap = n("market_cap")
    ev = n("ev")
    retained_earnings = n("retained_earnings", net_income)
    total_equity = n("total_equity", max(total_assets - total_debt, 0.001))
    tax_rate = n("tax_rate", 0.25)

    rev_prior = n("revenue_prior")
    ebitda_prior = n("ebitda_prior")
    net_inc_prior = n("net_income_prior")
    td_prior = n("total_debt_prior")
    cash_prior = n("cash_prior")
    eq_prior = n("total_equity_prior", total_equity * 0.9)
    cfo_prior = n("cfo_prior")
    fcf_prior = n("fcf_prior")
    cagr_years = int(n("revenue_cagr_years", 3))

    ebit = calc_ebit(ebitda, revenue=revenue)
    nopat = calc_nopat(ebit, tax_rate)
    invested_capital = calc_invested_capital(total_debt, total_equity, cash)
    roic = calc_roic(nopat, invested_capital)
    fcf = calc_fcf(cfo, capex)
    net_debt = calc_net_debt(total_debt, cash)

    if rev_prior > 0:
        nopat_prior = calc_nopat(calc_ebit(ebitda_prior, revenue=rev_prior), tax_rate)
        ic_prior = calc_invested_capital(td_prior, eq_prior, cash_prior)
        inc_roic = calc_incremental_roic(nopat, nopat_prior, invested_capital, ic_prior)
    else:
        inc_roic = 0.0

    if rev_prior > 0 and ebitda_prior > 0:
        rev_chg = safe_div(revenue - rev_prior, rev_prior)
        ebit_prior_val = calc_ebit(ebitda_prior, revenue=rev_prior)
        ebit_chg = safe_div(ebit - ebit_prior_val, abs(ebit_prior_val))
        op_lev = calc_operating_leverage(ebit_chg, rev_chg)
    else:
        op_lev = 0.0

    rev_cagr = calc_cagr(rev_prior, revenue, cagr_years) if rev_prior > 0 else 0.0
    ebit_cagr = calc_cagr(ebitda_prior, ebitda, cagr_years) if ebitda_prior > 0 else 0.0
    fcf_growth = calc_cagr(fcf_prior, fcf, cagr_years) if fcf_prior > 0 else 0.0

    altman = calc_altman_z(
        working_capital=n("working_capital"),
        retained_earnings=retained_earnings,
        ebit=ebit,
        total_assets=total_assets,
        market_value_equity=market_cap,
        total_debt=total_debt,
        revenue=revenue,
    )

    metrics = {
        "roic": roic,
        "incremental_roic": inc_roic,
        "nopat": nopat,
        "invested_capital": invested_capital,
        "ebit": ebit,
        "fcf": fcf,
        "gross_margin": calc_gross_margin(gross_profit, revenue),
        "ebit_margin": calc_ebit_margin(ebit, revenue),
        "roe": calc_roe(net_income, total_equity),
        "asset_turnover": calc_asset_turnover(revenue, total_assets),
        "operating_leverage": op_lev,
        "cfo_to_ebitda": calc_cfo_to_ebitda(cfo, ebitda),
        "fcf_to_net_income": calc_fcf_to_net_income(fcf, net_income),
        "fcf_margin": calc_fcf_margin(fcf, revenue),
        "cash_conversion_cycle": calc_cash_conversion_cycle(ar, inventory, ap, revenue, cogs),
        "working_capital_change": calc_working_capital_change(
            n("working_capital"),
            n("working_capital_prior"),
            revenue,
        ),
        "net_debt": net_debt,
        "net_debt_to_ebitda": calc_net_debt_to_ebitda(net_debt, ebitda),
        "interest_coverage": calc_interest_coverage(ebit, interest_exp),
        "current_ratio": calc_current_ratio(curr_assets, curr_liab),
        "quick_ratio": calc_quick_ratio(curr_assets, inventory, curr_liab),
        "altman_z": altman["z_score"],
        "revenue_cagr": rev_cagr,
        "ebit_cagr": ebit_cagr,
        "fcf_growth": fcf_growth,
        "ev_to_ebitda": calc_ev_to_ebitda(ev, ebitda),
        "pe_ratio": calc_pe_ratio(market_cap, net_income),
        "fcf_yield": calc_fcf_yield(fcf, market_cap),
        "short_term_debt": short_term_debt,
        "total_debt": total_debt,
        "altman_z_full": altman,
    }

    sub_scores = {
        "business_quality": score_business_quality(metrics),
        "cash_flow": score_cash_flow(metrics),
        "safety": score_safety(metrics),
        "growth": score_growth(metrics),
        "valuation": score_valuation(metrics),
    }

    aggregated = aggregate_health_score(
        {k: v for k, v in sub_scores.items()}, mode=mode
    )

    if ebitda <= 0:
        aggregated["health_score"] = min(aggregated["health_score"], 24)
        aggregated["health_band"] = "Distressed"
        aggregated["color"] = "red"

    flags = generate_flags(metrics)

    sub_score_values = {k: v["score"] for k, v in sub_scores.items()}
    sub_score_breakdowns = {k: v["breakdown"] for k, v in sub_scores.items()}

    return {
        "company_name": company_name,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "confidence_label": CONFIDENCE_LEVELS.get(confidence, CONFIDENCE_LEVELS["manual"]),
        "scoring_mode": mode,
        "scoring_model_version": SCORING_MODEL_VERSION,
        "health_score": aggregated["health_score"],
        "health_band": aggregated["health_band"],
        "health_color": aggregated["color"],
        "sub_scores": sub_score_values,
        "sub_score_breakdowns": sub_score_breakdowns,
        "top_strengths": flags["top_strengths"],
        "top_risks": flags["top_risks"],
        "critical_alerts": flags["critical_alerts"],
        "debt_maturity_wall": flags["debt_maturity_wall"],
        "metric_statuses": metric_statuses(metrics),
        "metric_benchmarks": metric_benchmarks(),
        "metrics": metrics,
        "altman_z_full": altman,
        "inputs": inputs,
    }
