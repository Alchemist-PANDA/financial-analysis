SCORING_MODEL_VERSION = "v1.0"

# ── CREDIT MODE WEIGHTS (Safety-first. For lenders.) ──────────
CREDIT_MODE_WEIGHTS = {
    "safety": 40,
    "business_quality": 25,
    "cash_flow": 25,
    "growth": 10,
    "valuation": 0,
}

# ── INVESTMENT MODE WEIGHTS (Full 5-pillar) ───────────────────
INVESTMENT_MODE_WEIGHTS = {
    "business_quality": 25,
    "cash_flow": 20,
    "safety": 25,
    "growth": 15,
    "valuation": 15,
}

# ── METRIC WEIGHTS WITHIN EACH PILLAR ────────────────────────
BUSINESS_QUALITY_WEIGHTS = {
    "roic": 10,
    "ebit_margin": 6,
    "gross_margin": 4,
    "roe": 3,
    "asset_turnover": 1,
    "operating_leverage": 1,
}

CASH_FLOW_WEIGHTS = {
    "cfo_to_ebitda": 6,
    "fcf_to_net_income": 6,
    "fcf_margin": 4,
    "working_capital_change": 4,
}

SAFETY_WEIGHTS = {
    "net_debt_to_ebitda": 8,
    "interest_coverage": 7,
    "current_ratio": 4,
    "quick_ratio": 3,
    "altman_z": 3,
}

GROWTH_WEIGHTS = {
    "revenue_cagr": 5,
    "ebit_cagr": 5,
    "fcf_growth": 5,
}

VALUATION_WEIGHTS = {
    "ev_to_ebitda": 5,
    "pe_ratio": 4,
    "fcf_yield": 6,
}

# ── THRESHOLDS PER METRIC ─────────────────────────────────────
# Format: (excellent_threshold, good_threshold, weak_threshold)
# Above excellent = full points, below weak = 0 points, interpolated between

THRESHOLDS = {
    "roic": (0.20, 0.12, 0.06),
    "ebit_margin": (0.20, 0.12, 0.05),
    "gross_margin": (0.50, 0.30, 0.15),
    "roe": (0.20, 0.12, 0.05),
    "asset_turnover": (1.5, 0.8, 0.4),
    "operating_leverage": (2.0, 1.2, 0.5),
    "cfo_to_ebitda": (0.85, 0.65, 0.40),
    "fcf_to_net_income": (1.0, 0.75, 0.40),
    "fcf_margin": (0.15, 0.08, 0.02),
    "working_capital_change": (0.05, 0.0, -0.10),
    "net_debt_to_ebitda": (1.0, 2.5, 4.5),
    "interest_coverage": (5.0, 2.5, 1.5),
    "current_ratio": (2.0, 1.3, 1.0),
    "quick_ratio": (1.5, 1.0, 0.7),
    "altman_z": (3.0, 2.5, 1.81),
    "revenue_cagr": (0.20, 0.10, 0.0),
    "ebit_cagr": (0.20, 0.10, 0.0),
    "fcf_growth": (0.20, 0.10, 0.0),
    "ev_to_ebitda": (8.0, 12.0, 18.0),
    "pe_ratio": (12.0, 18.0, 28.0),
    "fcf_yield": (0.08, 0.05, 0.02),
}

# ── HEALTH BANDS ──────────────────────────────────────────────
HEALTH_BANDS = [
    (85, 100, "Exceptional", "green"),
    (70, 84, "Healthy", "green"),
    (55, 69, "Adequate", "amber"),
    (40, 54, "Watch", "amber"),
    (25, 39, "Stressed", "red"),
    (0, 24, "Distressed", "red"),
]

# ── DEBT MATURITY WALL FLAG ───────────────────────────────────
DEBT_MATURITY_THRESHOLD = 0.35

# ── DATA CONFIDENCE LABELS ────────────────────────────────────
CONFIDENCE_LEVELS = {
    "manual": "User-entered (unverified)",
    "ticker": "Market data (live)",
    "uploaded": "Document-parsed",
}

INVERTED_METRICS = {
    "net_debt_to_ebitda",
    "ev_to_ebitda",
    "pe_ratio",
    "operating_leverage",
}
