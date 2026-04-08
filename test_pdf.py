import io
from app.reporter import generate_financial_pdf

# Dummy data
ticker = "AAPL"
company_name = "Apple Inc."
analysis_data = {
    "metrics": {
        "yearly": [
            {"year": 2020, "revenue": 100, "ebitda": 20, "net_income": 10, "ebitda_margin": 20, "leverage": 1.5, "z_score": 3.5, "roe": 15},
            {"year": 2021, "revenue": 110, "ebitda": 25, "net_income": 12, "ebitda_margin": 23, "leverage": 1.4, "z_score": 3.6, "roe": 16},
            {"year": 2022, "revenue": 120, "ebitda": 30, "net_income": 15, "ebitda_margin": 25, "leverage": 1.3, "z_score": 3.7, "roe": 17},
            {"year": 2023, "revenue": 130, "ebitda": 35, "net_income": 18, "ebitda_margin": 27, "leverage": 1.2, "z_score": 3.8, "roe": 18},
            {"year": 2024, "revenue": 140, "ebitda": 40, "net_income": 20, "ebitda_margin": 29, "leverage": 1.1, "z_score": 3.9, "roe": 19},
        ]
    },
    "analysis_result": {
        "analysis": {
            "analyst_verdict_archetype": "COMPOUNDER",
            "analyst_verdict_summary": "Strong growth and margins.",
            "pattern_diagnosis": "Positive trend consistent with high-quality compounding.",
            "flags": [
                {"emoji": "🚀", "name": "Growth Acceleration", "explanation": "Revenue CAGR is exceptional."}
            ]
        }
    }
}

try:
    print("Starting PDF generation test...")
    pdf_buffer = generate_financial_pdf(ticker, company_name, analysis_data)
    with open("test_report.pdf", "wb") as f:
        f.write(pdf_buffer.getbuffer())
    print("SUCCESS: PDF generated as test_report.pdf")
except Exception as e:
    print(f"FAILED: PDF generation failed with error: {e}")
