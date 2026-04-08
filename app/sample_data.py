# sample_data.py — Institutional seed data for MSFT (Compounder) and INTC (Value Trap)

SEED_DATA = [
    {
        "ticker": "MSFT",
        "company_name": "Microsoft Corporation",
        "archetype": "COMPOUNDER",
        "data": {
            "metrics": {
                "yearly": [
                    {"year": "2020", "revenue": 143015.0, "ebitda": 52915.0, "net_income": 44298.0, "cash": 130000.0, "debt": 80000.0, "total_assets": 301000.0, "equity": 118000.0, "working_capital": 60000.0, "retained_earnings": 40000.0, "ebit": 53000.0, "market_value_equity": 1600000.0, "accounts_receivable": 32011.0, "inventory": 1895.0, "capex": 15417.0},
                    {"year": "2021", "revenue": 168088.0, "ebitda": 68916.0, "net_income": 61271.0, "cash": 135000.0, "debt": 75000.0, "total_assets": 333000.0, "equity": 142000.0, "working_capital": 75000.0, "retained_earnings": 57000.0, "ebit": 69000.0, "market_value_equity": 2200000.0, "accounts_receivable": 38043.0, "inventory": 2636.0, "capex": 20622.0},
                    {"year": "2022", "revenue": 198270.0, "ebitda": 83273.0, "net_income": 72738.0, "cash": 140000.0, "debt": 70000.0, "total_assets": 364000.0, "equity": 166000.0, "working_capital": 90000.0, "retained_earnings": 80000.0, "ebit": 83000.0, "market_value_equity": 2400000.0, "accounts_receivable": 44261.0, "inventory": 3742.0, "capex": 23886.0},
                    {"year": "2023", "revenue": 211915.0, "ebitda": 91123.0, "net_income": 72361.0, "cash": 145000.0, "debt": 65000.0, "total_assets": 411000.0, "equity": 206000.0, "working_capital": 105000.0, "retained_earnings": 100000.0, "ebit": 91000.0, "market_value_equity": 2600000.0, "accounts_receivable": 48688.0, "inventory": 4500.0, "capex": 28107.0},
                    {"year": "2024", "revenue": 245122.0, "ebitda": 107853.0, "net_income": 88143.0, "cash": 150000.0, "debt": 60000.0, "total_assets": 484000.0, "equity": 253000.0, "working_capital": 130000.0, "retained_earnings": 125000.0, "ebit": 108000.0, "market_value_equity": 3200000.0, "accounts_receivable": 54000.0, "inventory": 5000.0, "capex": 35000.0}
                ],
                "revenue_cagr_pct": 14.5,
                "revenue_trajectory": "ACCELERATING",
                "margin_signal": "FLYING",
                "debt_signal": "DELEVERAGING",
                "solvency_signal": "SAFE"
            },
            "analysis": {
                "pattern_diagnosis": "DIAGNOSIS: THE COMPOUNDER. Leading indicators show an Asset-Light Flyer model with accelerating revenue and expanding efficiency scores.",
                "flags": [
                    {"emoji": "✅", "name": "Pristine Solvency", "explanation": "Altman Z-Score > 3.0 indicates absolute metabolic health."},
                    {"emoji": "🚀", "name": "Margin Flywheel", "explanation": "ROE expanding via net margin improvement, not leverage."}
                ],
                "analyst_verdict_archetype": "COMPOUNDER",
                "analyst_verdict_summary": "Superior capitalization. Cloud dominance providing massive owner earnings yield. Reconfirming Buy rating."
            }
        }
    },
    {
        "ticker": "INTC",
        "company_name": "Intel Corporation",
        "archetype": "VALUE TRAP",
        "data": {
            "metrics": {
                "yearly": [
                    {"year": "2020", "revenue": 77867.0, "ebitda": 35040.0, "net_income": 20245.0, "cash": 25000.0, "debt": 35000.0, "total_assets": 153000.0, "equity": 81000.0, "working_capital": 15000.0, "retained_earnings": 60000.0, "ebit": 25000.0, "market_value_equity": 200000.0, "accounts_receivable": 6500.0, "inventory": 8426.0, "capex": 14259.0},
                    {"year": "2021", "revenue": 79024.0, "ebitda": 30029.0, "net_income": 19756.0, "cash": 20000.0, "debt": 35000.0, "total_assets": 168000.0, "equity": 95000.0, "working_capital": 10000.0, "retained_earnings": 70000.0, "ebit": 24000.0, "market_value_equity": 210000.0, "accounts_receivable": 8200.0, "inventory": 10776.0, "capex": 18733.0},
                    {"year": "2022", "revenue": 63054.0, "ebitda": 13871.0, "net_income": 7566.0, "cash": 15000.0, "debt": 40000.0, "total_assets": 182000.0, "equity": 103000.0, "working_capital": 5000.0, "retained_earnings": 78000.0, "ebit": 10000.0, "market_value_equity": 140000.0, "accounts_receivable": 4133.0, "inventory": 13224.0, "capex": 24833.0},
                    {"year": "2023", "revenue": 54223.0, "ebitda": 8133.0, "net_income": 1626.0, "cash": 10000.0, "debt": 45000.0, "total_assets": 191000.0, "equity": 108000.0, "working_capital": -2000.0, "retained_earnings": 80000.0, "ebit": 5000.0, "market_value_equity": 120000.0, "accounts_receivable": 3500.0, "inventory": 11000.0, "capex": 25752.0},
                    {"year": "2024", "revenue": 53000.0, "ebitda": 5300.0, "net_income": -530.0, "cash": 5000.0, "debt": 50000.0, "total_assets": 205000.0, "equity": 109000.0, "working_capital": -10000.0, "retained_earnings": 80000.0, "ebit": 2000.0, "market_value_equity": 100000.0, "accounts_receivable": 3000.0, "inventory": 12000.0, "capex": 26000.0}
                ],
                "revenue_cagr_pct": -9.2,
                "revenue_trajectory": "COLLAPSING",
                "margin_signal": "COLLAPSING",
                "debt_signal": "OVERLEVERAGED"
            },
            "analysis": {
                "pattern_diagnosis": "Intel is in a classic DEBT SPIRAL. Declining revenues combined with a massive CapEx burden for new foundries has led to collapsing margins and a dangerous leverage trajectory.",
                "flags": [
                    {"emoji": "🚩", "name": "Leverage Trap", "explanation": "Debt/EBITDA has skyrocketed to 8.5x."},
                    {"emoji": "🚩", "name": "Margin Scissor", "explanation": "Revenue is falling while operational costs remain high."}
                ],
                "analyst_verdict_archetype": "VALUE TRAP",
                "analyst_verdict_summary": "High risk of dividend cut. Foundry bet is capital intensive and years from payoff. Neutral to Sell."
            }
        }
    }
]
