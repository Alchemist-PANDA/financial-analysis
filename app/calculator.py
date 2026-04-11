"""
calculator.py — Pure Python financial metric calculations.

No AI here — just math. Takes raw company data and returns
a dict of computed ratios used by the agent for analysis.
"""

def numeric_value(data: dict, key: str, default: float | None = 0.0) -> float | None:
    value = data.get(key, default)
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_div(numerator: float, denominator: float, fallback: float = 0.0) -> float:
    """Safe division. Returns fallback if denominator is zero or near-zero."""
    if abs(denominator) < 0.001:
        return fallback
    return numerator / denominator

def calculate_metrics(historical_data: list[dict]) -> dict:
    """
    Calculate 5-year financial trends and classification signals.
    Expects 5 years of data in chronological order (Y-4 to Y0).
    """
    if len(historical_data) < 2:
        raise ValueError("Institutional standard requires at least 2 years of data.")

    years_metrics = []
    for data in historical_data:
        rev = numeric_value(data, "revenue", None)
        ebitda = numeric_value(data, "ebitda", None)
        ni = numeric_value(data, "net_income", None)
        cash = numeric_value(data, "cash", None)
        debt = numeric_value(data, "debt", None)
        assets = numeric_value(data, "total_assets", None)
        equity = numeric_value(data, "equity", None)
        wc = numeric_value(data, "working_capital", None)
        re = numeric_value(data, "retained_earnings", None)
        ebit = numeric_value(data, "ebit", None)
        mve = numeric_value(data, "market_value_equity", None)

        ebitda_margin = (
            round((ebitda / rev) * 100, 1)
            if ebitda is not None and rev is not None and rev > 0
            else None
        )
        net_margin = (
            round((ni / rev) * 100, 1)
            if ni is not None and rev is not None and rev > 0
            else None
        )
        net_debt = round(debt - cash, 1) if debt is not None and cash is not None else None
        leverage = (
            round(net_debt / ebitda, 2)
            if net_debt is not None and ebitda is not None and ebitda > 0
            else None
        )

        # DuPont Components
        asset_turnover = (
            round(rev / assets, 2)
            if rev is not None and assets is not None and assets > 0
            else None
        )
        equity_multiplier = (
            round(assets / equity, 2)
            if assets is not None and equity is not None and equity > 0
            else None
        )
        roe = (
            round(net_margin * asset_turnover * equity_multiplier, 1)
            if net_margin is not None and asset_turnover is not None and equity_multiplier is not None
            else None
        )

        # Efficiency & Profitability Metrics
        ar = numeric_value(data, "accounts_receivable", None)
        inv = numeric_value(data, "inventory", None)
        capex = numeric_value(data, "capex", None)
        cogs = numeric_value(data, "cogs", None)

        dso = (
            round((ar / rev) * 365, 0)
            if ar is not None and rev is not None and rev > 0
            else None
        )
        inv_turnover = (
            round(rev / inv, 1)
            if inv is not None and inv > 0 and rev is not None
            else None
        )
        fcf_conv = (
            round(((ebitda - capex) / ebitda) * 100, 1)
            if ebitda is not None and ebitda > 0 and capex is not None
            else None
        )
        roa = (
            round((ni / assets) * 100, 1)
            if ni is not None and assets is not None and assets > 0
            else None
        )
        gross_margin = (
            round(((rev - cogs) / rev) * 100, 1)
            if rev is not None and rev > 0 and cogs is not None
            else None
        )

        # Capital Structure & Solvency
        int_exp = numeric_value(data, "interest_expense", None)
        curr_assets = numeric_value(data, "current_assets", None)
        curr_liab = numeric_value(data, "current_liabilities", None)

        debt_equity = (
            round(debt / equity, 2)
            if debt is not None and equity is not None and equity > 0
            else None
        )
        curr_ratio = (
            round(curr_assets / curr_liab, 2)
            if curr_assets is not None and curr_liab is not None and curr_liab > 0
            else None
        )
        quick_ratio = (
            round((curr_assets - inv) / curr_liab, 2)
            if curr_assets is not None and inv is not None and curr_liab is not None and curr_liab > 0
            else None
        )
        cash_ratio = (
            round(cash / curr_liab, 2)
            if cash is not None and curr_liab is not None and curr_liab > 0
            else None
        )
        int_coverage = (
            round(ebit / int_exp, 2)
            if ebit is not None and int_exp is not None and int_exp > 0
            else None
        )

        # Valuation
        pe_ratio = (
            round(mve / ni, 1)
            if mve is not None and ni is not None and ni > 0
            else None
        )
        pb_ratio = (
            round(mve / equity, 1)
            if mve is not None and equity is not None and equity > 0
            else None
        )
        ev_ebitda = (
            round((mve + debt - cash) / ebitda, 1)
            if mve is not None
            and debt is not None
            and cash is not None
            and ebitda is not None
            and ebitda > 0
            else None
        )

        # Altman Z-Score Calculation
        z_score = None
        if (
            wc is not None
            and re is not None
            and ebit is not None
            and assets is not None
            and assets > 0
            and mve is not None
            and debt is not None
            and rev is not None
        ):
            a_factor = wc / assets
            b_factor = re / assets
            c_factor = ebit / assets
            d_factor = (mve / debt) if debt > 0 else 10.0
            e_factor = rev / assets
            z_score = round(
                1.2 * a_factor + 1.4 * b_factor + 3.3 * c_factor + 0.6 * d_factor + 1.0 * e_factor,
                2,
            )

        years_metrics.append(
            {
                "year": data["year"],
                "revenue": rev,
                "ebitda": ebitda,
                "net_income": ni,
                "ebitda_margin": ebitda_margin,
                "net_margin": net_margin,
                "net_debt": net_debt,
                "leverage": leverage,
                "asset_turnover": asset_turnover,
                "equity_multiplier": equity_multiplier,
                "roe": roe,
                "dso": dso,
                "inventory_turnover": inv_turnover,
                "fcf_conversion_pct": fcf_conv,
                "z_score": z_score,
                "roa": roa,
                "gross_margin": gross_margin,
                "debt_equity": debt_equity,
                "current_ratio": curr_ratio,
                "quick_ratio": quick_ratio,
                "cash_ratio": cash_ratio,
                "interest_coverage": int_coverage,
                "pe_ratio": pe_ratio,
                "pb_ratio": pb_ratio,
                "ev_ebitda": ev_ebitda,
            }
        )

    # 1. Revenue CAGR Calculation
    years_count = len(historical_data)
    y0_rev = numeric_value(historical_data[-1], "revenue", None)
    y_first_rev = numeric_value(historical_data[0], "revenue", None)
    if y0_rev is not None and y_first_rev is not None and y_first_rev > 0 and years_count > 1:
        cagr = round(((y0_rev / y_first_rev) ** (1 / (years_count - 1)) - 1) * 100, 1)
    else:
        cagr = None

    # 2. Revenue Trajectory
    recent_years = historical_data[-5:]
    growths = []
    for i in range(1, len(recent_years)):
        prev_revenue = numeric_value(recent_years[i - 1], "revenue", None)
        current_revenue = numeric_value(recent_years[i], "revenue", None)
        if prev_revenue is None or prev_revenue <= 0 or current_revenue is None:
            g = 0.0
        else:
            g = (current_revenue / prev_revenue) - 1
        growths.append(g)

    if len(growths) >= 2:
        if all(growths[i] > growths[i - 1] for i in range(1, len(growths))):
            trajectory = "ACCELERATING"
        elif all(abs(growths[i] - growths[i - 1]) < 0.02 for i in range(1, len(growths))):
            trajectory = "STEADY"
        elif growths[-1] < growths[-2] and growths[-1] > 0:
            trajectory = "DECELERATING"
        else:
            trajectory = "STALLING"
    else:
        trajectory = "STALLING"

    # 3. Margin & Debt Trends
    margin_diff = None
    if years_metrics[-1]["ebitda_margin"] is not None and years_metrics[-2]["ebitda_margin"] is not None:
        margin_diff = years_metrics[-1]["ebitda_margin"] - years_metrics[-2]["ebitda_margin"]
    if margin_diff is not None and margin_diff >= 0.5:
        margin_signal = "EXPANDING"
    elif margin_diff is not None and margin_diff <= -2.0:
        margin_signal = "COLLAPSING"
    else:
        margin_signal = "STABLE"

    lev_y0 = years_metrics[-1]["leverage"]
    lev_y1 = years_metrics[-2]["leverage"]
    if lev_y0 is not None and lev_y1 is not None and lev_y0 < lev_y1:
        debt_signal = "DELEVERAGING"
    elif lev_y0 is not None and lev_y0 > 5.0:
        debt_signal = "OVERLEVERAGED"
    else:
        debt_signal = "STABLE"

    # 4. Solvency Signal (Altman Z)
    z0 = years_metrics[-1]["z_score"]
    if z0 is not None and z0 > 2.99:
        solvency_signal = "SAFE"
    elif z0 is not None and z0 > 1.8:
        solvency_signal = "GREY_ZONE"
    else:
        solvency_signal = "DISTRESS"

    return {
        "yearly": years_metrics,
        "revenue_cagr_pct": cagr,
        "revenue_trajectory": trajectory,
        "margin_signal": margin_signal,
        "debt_signal": debt_signal,
        "solvency_signal": solvency_signal,
        "current_z_score": z0,
        "current_roe": years_metrics[-1]["roe"],
        "current_roa": years_metrics[-1]["roa"],
        "current_gross_margin": years_metrics[-1]["gross_margin"],
        "current_debt_equity": years_metrics[-1]["debt_equity"],
        "current_ratio": years_metrics[-1]["current_ratio"],
        "current_quick_ratio": years_metrics[-1]["quick_ratio"],
        "current_cash_ratio": years_metrics[-1]["cash_ratio"],
        "current_interest_coverage": years_metrics[-1]["interest_coverage"],
        "current_pe_ratio": years_metrics[-1]["pe_ratio"],
        "current_pb_ratio": years_metrics[-1]["pb_ratio"],
        "current_ev_ebitda": years_metrics[-1]["ev_ebitda"],
        "current_dso": years_metrics[-1]["dso"],
        "current_inventory_turnover": years_metrics[-1]["inventory_turnover"],
        "current_fcf_conversion_pct": years_metrics[-1]["fcf_conversion_pct"],
    }


def calc_nopat(ebit: float, tax_rate: float = 0.25) -> float:
    return ebit * (1 - tax_rate)


def calc_invested_capital(total_debt: float, total_equity: float, cash: float) -> float:
    return max(total_debt + total_equity - cash, 0.001)


def calc_roic(nopat: float, invested_capital: float) -> float:
    return safe_div(nopat, invested_capital)


def calc_incremental_roic(
    nopat_current: float, nopat_prior: float, ic_current: float, ic_prior: float
) -> float:
    delta_nopat = nopat_current - nopat_prior
    delta_ic = ic_current - ic_prior
    return safe_div(delta_nopat, delta_ic)


def calc_ebit(ebitda: float, da_estimate: float = None, revenue: float = None) -> float:
    if da_estimate is not None:
        return ebitda - da_estimate
    if revenue is not None:
        return ebitda - (revenue * 0.03)
    return ebitda


def calc_gross_margin(gross_profit: float, revenue: float) -> float:
    return safe_div(gross_profit, revenue)


def calc_ebit_margin(ebit: float, revenue: float) -> float:
    return safe_div(ebit, revenue)


def calc_roe(net_income: float, total_equity: float) -> float:
    return safe_div(net_income, total_equity)


def calc_asset_turnover(revenue: float, total_assets: float) -> float:
    return safe_div(revenue, total_assets)


def calc_operating_leverage(ebit_change_pct: float, revenue_change_pct: float) -> float:
    return safe_div(ebit_change_pct, revenue_change_pct)


def calc_fcf(cfo: float, capex: float) -> float:
    return cfo - capex


def calc_cfo_to_ebitda(cfo: float, ebitda: float) -> float:
    return safe_div(cfo, ebitda)


def calc_fcf_to_net_income(fcf: float, net_income: float) -> float:
    return safe_div(fcf, net_income)


def calc_fcf_margin(fcf: float, revenue: float) -> float:
    return safe_div(fcf, revenue)


def calc_cash_conversion_cycle(
    accounts_receivable: float,
    inventory: float,
    accounts_payable: float,
    revenue: float,
    cogs: float,
) -> float:
    daily_revenue = safe_div(revenue, 365)
    daily_cogs = safe_div(cogs, 365)
    dso = safe_div(accounts_receivable, daily_revenue)
    dio = safe_div(inventory, daily_cogs)
    dpo = safe_div(accounts_payable, daily_cogs)
    return dso + dio - dpo


def calc_working_capital_change(wc_current: float, wc_prior: float, revenue: float) -> float:
    return safe_div(wc_current - wc_prior, revenue)


def calc_net_debt(total_debt: float, cash: float) -> float:
    return total_debt - cash


def calc_net_debt_to_ebitda(net_debt: float, ebitda: float) -> float:
    if ebitda <= 0:
        return 999.0
    return safe_div(net_debt, ebitda)


def calc_interest_coverage(ebit: float, interest_expense: float) -> float:
    if interest_expense <= 0:
        return 999.0
    return safe_div(ebit, interest_expense)


def calc_current_ratio(current_assets: float, current_liabilities: float) -> float:
    return safe_div(current_assets, current_liabilities)


def calc_quick_ratio(current_assets: float, inventory: float, current_liabilities: float) -> float:
    return safe_div(current_assets - inventory, current_liabilities)


def calc_cagr(value_start: float, value_end: float, years: int) -> float:
    if value_start <= 0 or years <= 0:
        return 0.0
    return (safe_div(value_end, value_start) ** (1 / years)) - 1


def calc_ev_to_ebitda(ev: float, ebitda: float) -> float:
    return safe_div(ev, ebitda)


def calc_pe_ratio(market_cap: float, net_income: float) -> float:
    if net_income <= 0:
        return 999.0
    return safe_div(market_cap, net_income)


def calc_fcf_yield(fcf: float, market_cap: float) -> float:
    return safe_div(fcf, market_cap)


def calc_altman_z(
    working_capital: float,
    retained_earnings: float,
    ebit: float,
    total_assets: float,
    market_value_equity: float,
    total_debt: float,
    revenue: float,
) -> dict:
    x1 = safe_div(working_capital, total_assets)
    x2 = safe_div(retained_earnings, total_assets)
    x3 = safe_div(ebit, total_assets)
    x4 = safe_div(market_value_equity, total_debt, fallback=10.0)
    x5 = safe_div(revenue, total_assets)
    z_score = round(1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 1.0 * x5, 2)

    if z_score > 2.99:
        zone = "Safe"
    elif z_score > 1.81:
        zone = "Grey"
    else:
        zone = "Distress"

    return {
        "z_score": z_score,
        "zone": zone,
        "x1": x1,
        "x2": x2,
        "x3": x3,
        "x4": x4,
        "x5": x5,
    }
