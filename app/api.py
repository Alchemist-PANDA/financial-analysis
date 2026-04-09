import sys
import os
from datetime import datetime
from typing import Any, List, Optional
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Ensure app/ is on the path for sibling imports
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__))) # Root dir for config

from app.graph import graph
from config import APP_NAME, APP_VERSION
from app.database import init_db, get_db, async_session
from app.models import AnalysisHistory
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
import json
from contextlib import asynccontextmanager
from fastapi.responses import StreamingResponse
import asyncio

# ── FastAPI App Setup ────────────────────────────────────────────────────────

from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database
    await init_db()
    
    # Check if we need to seed
    async with async_session() as db:
        result = await db.execute(select(AnalysisHistory).limit(1))
        if not result.scalars().first():
            from app.sample_data import SEED_DATA
            for item in SEED_DATA:
                history = AnalysisHistory(
                    ticker=item["ticker"],
                    company_name=item["company_name"],
                    archetype=item["archetype"],
                    analysis_data=item["data"]
                )
                db.add(history)
            await db.commit()
    
    yield

app = FastAPI(title=f"{APP_NAME} SaaS API", version=APP_VERSION, lifespan=lifespan)

# CORS configuration
# In production, specify your frontend URLs in the FRONTEND_URL environment variable (comma-separated).
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
]

frontend_env = os.getenv("FRONTEND_URL")
if frontend_env:
    # Support comma-separated list of origins
    origins.extend([url.strip() for url in frontend_env.split(",") if url.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Analysis Helper ──────────────────────────────────────────────────────────

def derive_color_signal(z_score: float) -> str:
    if z_score > 2.99:
        return "GREEN"
    if z_score > 1.8:
        return "YELLOW"
    return "RED"


def default_retail_verdict(analysis: dict, color_signal: str) -> str:
    if analysis.get("retail_verdict"):
        return analysis["retail_verdict"]
    if color_signal == "GREEN":
        return "Financial profile is resilient and lower risk."
    if color_signal == "RED":
        return "High-risk setup. Capital loss risk is elevated."
    return "Mixed fundamentals. Position size with caution."


def build_response_payload(ticker: str, company_name: str, metrics: dict, analysis: dict) -> dict:
    z_score_raw = metrics.get("current_z_score")
    if z_score_raw is None:
        solvency = str(metrics.get("solvency_signal", "")).upper()
        if solvency == "SAFE":
            z_score_raw = 3.1
        elif solvency in {"GREY_ZONE", "YELLOW"}:
            z_score_raw = 2.1
        else:
            z_score_raw = 1.2
    color_signal = derive_color_signal(float(z_score_raw or 0.0))
    normalized_analysis = dict(analysis or {})
    flags = normalized_analysis.get("flags", [])
    if not isinstance(flags, list):
        normalized_analysis["flags"] = []
    else:
        normalized_analysis["flags"] = flags
    normalized_analysis["retail_verdict"] = default_retail_verdict(normalized_analysis, color_signal)
    return {
        "ticker": ticker.upper(),
        "company_name": company_name,
        "metrics": metrics,
        "analysis": normalized_analysis,
        "color_signal": color_signal,
    }


def score_for_comparison(payload: dict) -> float:
    metrics = payload.get("metrics", {})
    z_score = float(metrics.get("current_z_score", 0.0) or 0.0)
    cagr = float(metrics.get("revenue_cagr_pct", 0.0) or 0.0)
    fcf = float(metrics.get("current_fcf_conversion_pct", 0.0) or 0.0)
    roe = float(metrics.get("current_roe", 0.0) or 0.0)
    dso = float(metrics.get("current_dso", 0.0) or 0.0)

    return (z_score * 4.0) + (cagr * 0.8) + (fcf * 0.2) + (roe * 0.15) - (max(dso - 60.0, 0.0) * 0.15)


def build_comparison_verdict(left: dict, right: dict) -> dict:
    left_score = score_for_comparison(left)
    right_score = score_for_comparison(right)
    if left_score >= right_score:
        winner = left["ticker"]
        loser = right["ticker"]
    else:
        winner = right["ticker"]
        loser = left["ticker"]
    summary = (
        f"shows the stronger blended solvency and cash quality profile versus {loser}. "
        f"Review both verdict notes before position sizing."
    )
    return {"winner": winner, "summary": summary}


def fallback_analysis_from_metrics(metrics: dict) -> dict:
    z_score = float(metrics.get("current_z_score", 0.0) or 0.0)
    margin_signal = str(metrics.get("margin_signal", "STABLE")).upper()
    debt_signal = str(metrics.get("debt_signal", "STABLE")).upper()
    revenue_cagr = float(metrics.get("revenue_cagr_pct", 0.0) or 0.0)

    if z_score >= 3.0 and revenue_cagr > 8:
        archetype = "COMPOUNDER"
        summary = "Strong solvency and growth momentum suggest resilient fundamentals."
    elif z_score < 1.8:
        archetype = "DISTRESSED"
        summary = "Balance-sheet stress is elevated and downside risk is material."
    elif margin_signal == "COLLAPSING":
        archetype = "MARGIN SCISSOR"
        summary = "Revenue quality is weakening as margins compress across the period."
    elif debt_signal == "OVERLEVERAGED":
        archetype = "VALUE TRAP"
        summary = "Leverage is high versus earnings capacity; recovery quality is uncertain."
    else:
        archetype = "TRANSITION"
        summary = "Signals are mixed, so treat this as a selective-risk setup."

    flags = []
    if z_score < 1.8:
        flags.append({"emoji": "!", "name": "Solvency Risk", "explanation": "Altman Z-Score is in distress range."})
    if debt_signal == "OVERLEVERAGED":
        flags.append({"emoji": "!", "name": "Leverage Pressure", "explanation": "Debt load is high relative to EBITDA."})
    if not flags:
        flags.append({"emoji": "+", "name": "Operational Stability", "explanation": "No severe structural stress detected."})

    return {
        "pattern_diagnosis": (
            f"Fallback diagnosis generated from quantitative signals. Revenue CAGR is {revenue_cagr:.1f}%, "
            f"margin trend is {margin_signal}, and solvency is anchored by a Z-score of {z_score:.2f}."
        ),
        "flags": flags,
        "analyst_verdict_archetype": archetype,
        "analyst_verdict_summary": summary,
    }


async def run_analysis_for_ticker(
    ticker: str,
    db: Optional[AsyncSession] = None,
    manual_data: Optional[dict] = None,
    save_history: bool = True,
) -> dict:
    requested_ticker = (ticker or "N/A").upper()

    if manual_data:
        company_payload = manual_data["company"]
        initial_state = {
            "company_data": company_payload,
            "historical_data": manual_data["historical_data"],
            "metrics": None,
            "search_query": "",
            "search_results": [],
            "analysis_result": None,
        }
        resolved_ticker = company_payload.get("ticker", requested_ticker or "CUSTOM")
        company_name = company_payload.get("company_name", "Private Company")
    else:
        from app.sample_data import SEED_DATA

        record = next((item for item in SEED_DATA if item["ticker"].upper() == requested_ticker), SEED_DATA[0])
        resolved_ticker = record["ticker"]
        company_name = record["company_name"]
        initial_state = {
            "company_data": {
                "ticker": record["ticker"],
                "company_name": record["company_name"],
            },
            "historical_data": record["data"]["metrics"]["yearly"],
            "metrics": None,
            "search_query": f"{record['ticker']} news",
            "search_results": [],
            "analysis_result": None,
        }

    try:
        final_state = await asyncio.to_thread(graph.invoke, initial_state)
        result = final_state.get("analysis_result", {}) or {}
        analysis = result.get("analysis", {}) or {}
        metrics = final_state.get("metrics", {}) or {}
        response_payload = build_response_payload(resolved_ticker, company_name, metrics, analysis)

        if save_history and db:
            try:
                analysis_history = AnalysisHistory(
                    ticker=resolved_ticker.upper(),
                    company_name=company_name,
                    archetype=response_payload["analysis"].get("analyst_verdict_archetype", "UNKNOWN"),
                    analysis_data=final_state,
                )
                db.add(analysis_history)
                await db.commit()
            except Exception as db_err:
                print(f"Failed to save history: {db_err}")

        return response_payload
    except Exception as graph_error:
        print(f"Graph invocation failed: {graph_error}")
        if manual_data:
            from app.calculator import calculate_metrics

            fallback_metrics = calculate_metrics(manual_data["historical_data"])
            fallback_analysis = fallback_analysis_from_metrics(fallback_metrics)
            return build_response_payload(resolved_ticker, company_name, fallback_metrics, fallback_analysis)

        from app.sample_data import SEED_DATA
        from app.calculator import calculate_metrics

        record = next((item for item in SEED_DATA if item["ticker"].upper() == requested_ticker), SEED_DATA[0])
        # Seed metrics contain raw 5-year inputs, not the computed forensic table the UI expects.
        seed_metrics = record.get("data", {}).get("metrics", {}) or {}
        seed_yearly = seed_metrics.get("yearly", [])
        try:
            fallback_metrics = calculate_metrics(seed_yearly)
        except Exception:
            fallback_metrics = seed_metrics

        fallback_analysis = record.get("data", {}).get("analysis", {}) or fallback_analysis_from_metrics(fallback_metrics)
        return build_response_payload(record["ticker"], record["company_name"], fallback_metrics, fallback_analysis)

@app.get("/api/analyze/stream")
async def analyze_stream(ticker: str, db: AsyncSession = Depends(get_db)):
    async def event_generator():
        yield f"data: {json.dumps({'type':'progress','step':'fetching','label':'Fetching 5-year data'})}\n\n"
        await asyncio.sleep(0.5)
        yield f"data: {json.dumps({'type':'progress','step':'normalizing','label':'Normalizing GAAP figures'})}\n\n"
        await asyncio.sleep(0.5)
        yield f"data: {json.dumps({'type':'progress','step':'trend_engine','label':'Running Trend Engine'})}\n\n"
        await asyncio.sleep(0.5)
        yield f"data: {json.dumps({'type':'progress','step':'verdict','label':'Generating Retail Verdict'})}\n\n"
        
        try:
            result = await run_analysis_for_ticker(ticker, db)
            yield f"data: {json.dumps({'type':'result','payload': result})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type':'error','message': str(e)})}\n\n"
        yield "data: [DONE]\n\n"
        
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/compare")
async def compare_tickers(ticker_a: str, ticker_b: str):
    """Run two analyses and return a comparison verdict payload."""
    left, right = await asyncio.gather(
        run_analysis_for_ticker(ticker_a, db=None, save_history=False),
        run_analysis_for_ticker(ticker_b, db=None, save_history=False),
    )
    return {
        "left": left,
        "right": right,
        "verdict": build_comparison_verdict(left, right),
    }

# ── API Security ─────────────────────────────────────────────────────────────
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "dev_default_key")

if API_SECRET_KEY == "dev_default_key" and os.getenv("RENDER"):
    print("\n[WARNING] Using default API key in production environment!\n")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_SECRET_KEY:
        return api_key_header
    raise HTTPException(status_code=403, detail="Could not validate API key")


# ── Pydantic Models ──────────────────────────────────────────────────────────

class HistoricalYear(BaseModel):
    year: str
    revenue: float
    ebitda: float
    net_income: float
    cash: float
    debt: float
    total_assets: Optional[float] = None
    equity: Optional[float] = None
    working_capital: Optional[float] = None
    retained_earnings: Optional[float] = None
    ebit: Optional[float] = None
    market_value_equity: Optional[float] = None
    accounts_receivable: Optional[float] = None
    inventory: Optional[float] = None
    capex: Optional[float] = None

class CompanyData(BaseModel):
    company_name: str
    sector: Optional[str] = "Unknown"
    ticker: Optional[str] = "CUSTOM"

class AnalysisRequest(BaseModel):
    company: CompanyData
    historical_data: List[HistoricalYear] = Field(
        ..., min_length=5, description="At least 5 years of historical financial data (Y-4 through Y0)"
    )


# Serve the frontend UI

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/history", dependencies=[Depends(get_api_key)])
async def get_history(db: AsyncSession = Depends(get_db)):
    """Fetch the last 20 analyses from the history."""
    result = await db.execute(
        select(AnalysisHistory).order_by(AnalysisHistory.created_at.desc()).limit(20)
    )
    history = result.scalars().all()
    return [{"ticker": h.ticker, "name": h.company_name, "archetype": h.archetype, "date": h.created_at} for h in history]

@app.get("/api/export/pdf", dependencies=[Depends(get_api_key)])
async def export_pdf(ticker: str, db: AsyncSession = Depends(get_db)):
    """Generate and return a professional PDF report for the given ticker."""
    from app.reporter import generate_financial_pdf
    
    # 1. Fetch the latest analysis for this ticker
    result = await db.execute(
        select(AnalysisHistory)
        .where(AnalysisHistory.ticker == ticker.upper())
        .order_by(AnalysisHistory.created_at.desc())
        .limit(1)
    )
    analysis_record = result.scalars().first()
    
    if not analysis_record:
        raise HTTPException(status_code=404, detail=f"No analysis history found for ticker: {ticker}")
    
    # 2. Generate PDF
    try:
        pdf_buffer = generate_financial_pdf(
            analysis_record.ticker, 
            analysis_record.company_name, 
            analysis_record.analysis_data
        )
        
        # 3. Stream the response
        filename = f"Analyst_Report_{ticker.upper()}_{datetime.now().strftime('%Y%m%d')}.pdf"
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

@app.post("/api/analyze", dependencies=[Depends(get_api_key)])
async def analyze_company(request: AnalysisRequest, db: AsyncSession = Depends(get_db)):
    """
    Run an institutional-grade financial trend analysis on a manual payload.
    """
    try:
        payload_dict: dict[str, Any] = {
            "company": request.company.model_dump(),
            "historical_data": [year.model_dump() for year in request.historical_data],
        }
        normalized = await run_analysis_for_ticker(
            ticker=request.company.ticker or "CUSTOM",
            db=db,
            manual_data=payload_dict,
            save_history=True,
        )
        analysis = normalized.get("analysis", {})
        metrics = normalized.get("metrics", {})

        return {
            "status": "success",
            "ticker": normalized.get("ticker"),
            "company_name": normalized.get("company_name"),
            "metrics": metrics,
            "analysis": analysis,
            "color_signal": normalized.get("color_signal"),
            # Backward-compatible keys for older callers.
            "calculated_metrics": metrics,
            "flags": analysis.get("flags", []),
            "pattern_diagnosis": analysis.get("pattern_diagnosis"),
            "retail_verdict": analysis.get("retail_verdict"),
            "analyst_verdict": {
                "archetype": analysis.get("analyst_verdict_archetype"),
                "summary": analysis.get("analyst_verdict_summary"),
            },
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Analysis engine failed: {err}")

# Serve the frontend UI (Must be at the bottom so it doesn't swallow API routes)
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
