import sys
import os
import warnings
from datetime import datetime
from typing import Any, List, Optional
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Suppress upstream compatibility warning noise under Python 3.14.
warnings.filterwarnings(
    "ignore",
    message=r"Core Pydantic V1 functionality isn't compatible with Python 3\.14 or greater\.",
    category=UserWarning,
)
warnings.simplefilter("ignore", RuntimeWarning)

# Ensure app/ is on the path for sibling imports
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__))) # Root dir for config

from app.graph import graph
from config import APP_NAME, APP_VERSION
from app.database import init_db, get_db, async_session
from app.models import AnalysisHistory, ScorecardAnalysis
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
import json
from contextlib import asynccontextmanager
from fastapi.responses import StreamingResponse
import asyncio
from app.calculator import numeric_value
from app.engine.orchestrator import run_full_analysis
from app.agent import generate_scorecard_narrative

GRAPH_TIMEOUT_SECONDS = float(os.getenv("GRAPH_TIMEOUT_SECONDS", "45"))

# ── FastAPI App Setup ────────────────────────────────────────────────────────

from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database
    try:
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
    except Exception as e:
        print(f"[DB INIT ERROR] {e}")
    
    yield

app = FastAPI(title=f"{APP_NAME} SaaS API", version=APP_VERSION, lifespan=lifespan)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# CORS configuration
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
]

frontend_env = os.getenv("FRONTEND_URL")
if frontend_env:
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


def default_retail_verdict(analysis: dict | None, color_signal: str) -> str:
    if analysis and analysis.get("retail_verdict"):
        return analysis["retail_verdict"]
    if color_signal == "GREEN":
        return "Financial profile is resilient and lower risk."
    if color_signal == "RED":
        return "High-risk setup. Capital loss risk is elevated."
    return "Mixed fundamentals. Position size with caution."


def build_response_payload(ticker: str, company_name: str, metrics: dict | None, analysis: dict | None) -> dict:
    safe_metrics = dict(metrics or {})
    z_score_raw = safe_metrics.get("current_z_score")
    if z_score_raw is None:
        solvency = str(safe_metrics.get("solvency_signal", "")).upper()
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
        "ticker": ticker.upper() if ticker else "UNKNOWN",
        "company_name": company_name or "Unknown",
        "metrics": safe_metrics,
        "analysis": normalized_analysis,
        "color_signal": color_signal,
    }


def score_for_comparison(payload: dict | None) -> float:
    if not payload:
        return 0.0
    metrics = dict(payload.get("metrics", {}) or {})
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
    if not metrics:
        return {
            "pattern_diagnosis": "No sufficient quantitative data was available for this ticker to generate a trend diagnosis.",
            "flags": [{"emoji": "!", "name": "Data Insufficient", "explanation": "Required 5-year financial history is missing or incomplete."}],
            "analyst_verdict_archetype": "DATA_INSUFFICIENT",
            "analyst_verdict_summary": "We could not find enough public financial data to analyze this company's performance trends.",
        }

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


def to_number(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def pick_number(data: dict, *keys: str, default: float = 0.0) -> float:
    for key in keys:
        value = numeric_value(data, key, None)
        if value is not None:
            return to_number(value, default)
    return default


def get_seed_record(ticker: str) -> Optional[dict]:
    from app.sample_data import SEED_DATA

    requested = (ticker or "").strip().upper()
    if not requested:
        return None
    return next((item for item in SEED_DATA if item["ticker"].upper() == requested), None)


def supported_tickers() -> list[str]:
    from app.sample_data import SEED_DATA

    return [item["ticker"].upper() for item in SEED_DATA]


def build_scorecard_inputs_from_history(
    company_name: str,
    historical_data: list[dict],
    scoring_mode: str = "credit",
    data_source: str = "ticker",
) -> dict:
    latest = historical_data[-1] if historical_data else {}
    prior = historical_data[-2] if len(historical_data) > 1 else {}

    revenue = pick_number(latest, "revenue")
    ebitda = pick_number(latest, "ebitda")
    net_income = pick_number(latest, "net_income")
    total_debt = pick_number(latest, "debt", "total_debt")
    cash = pick_number(latest, "cash", "cash_equivalents")
    total_assets = pick_number(latest, "total_assets")
    total_equity = pick_number(latest, "equity", "total_equity")
    market_cap = pick_number(latest, "market_value_equity", "market_cap")
    cogs_raw = numeric_value(latest, "cogs", None)
    cogs = to_number(cogs_raw, 0.0)

    return {
        "company_name": company_name,
        "revenue": revenue,
        "ebitda": ebitda,
        "net_income": net_income,
        "interest_expense": pick_number(latest, "interest_expense"),
        "total_debt": total_debt,
        "cash_equivalents": cash,
        "total_assets": total_assets,
        "current_assets": pick_number(latest, "current_assets"),
        "current_liabilities": pick_number(latest, "current_liabilities"),
        "short_term_debt": pick_number(latest, "short_term_debt"),
        "gross_profit": revenue - cogs if cogs_raw is not None else 0.0,
        "cfo": pick_number(latest, "cfo"),
        "capex": pick_number(latest, "capex"),
        "accounts_receivable": pick_number(latest, "accounts_receivable"),
        "inventory": pick_number(latest, "inventory"),
        "accounts_payable": pick_number(latest, "accounts_payable"),
        "cogs": cogs,
        "market_cap": market_cap,
        "ev": market_cap + total_debt - cash,
        "retained_earnings": pick_number(latest, "retained_earnings"),
        "total_equity": total_equity,
        "tax_rate": pick_number(latest, "tax_rate", default=0.25),
        "revenue_prior": pick_number(prior, "revenue"),
        "ebitda_prior": pick_number(prior, "ebitda"),
        "net_income_prior": pick_number(prior, "net_income"),
        "total_debt_prior": pick_number(prior, "debt", "total_debt"),
        "cash_prior": pick_number(prior, "cash", "cash_equivalents"),
        "total_equity_prior": pick_number(prior, "equity", "total_equity"),
        "cfo_prior": pick_number(prior, "cfo"),
        "fcf_prior": pick_number(prior, "fcf"),
        "working_capital": pick_number(latest, "working_capital"),
        "working_capital_prior": pick_number(prior, "working_capital"),
        "revenue_cagr_years": max(len(historical_data) - 1, 1),
        "data_source": data_source,
        "scoring_mode": scoring_mode,
    }


def run_scorecard_analysis(inputs: dict, mode: str = "credit") -> dict:
    result = run_full_analysis(inputs, mode=mode)
    try:
        result["narrative"] = generate_scorecard_narrative(result)
    except Exception as exc:
        result["narrative"] = ""
        result["narrative_error"] = str(exc)
    return result


async def persist_scorecard_result(
    db: AsyncSession,
    inputs: dict,
    result: dict,
) -> ScorecardAnalysis:
    record = ScorecardAnalysis(
        company_name=result.get("company_name", "Unknown"),
        scoring_mode=result.get("scoring_mode", "credit"),
        scoring_model_version=result.get("scoring_model_version", "v1.0"),
        health_score=int(result.get("health_score", 0)),
        health_band=result.get("health_band", "Unknown"),
        inputs_data=inputs,
        result_data=result,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def run_analysis_for_ticker(
    ticker: str | None = None,
    manual_data: dict | None = None,
    save_history: bool = True,
    skip_external: bool = False,
    db: AsyncSession | None = None,
) -> dict:
    requested_ticker = (ticker or "N/A").upper()

    # Fast Resolution
    historical_data = None
    resolved_ticker = requested_ticker
    company_name = requested_ticker
    record = None

    if manual_data:
        company_payload = manual_data["company"]
        historical_data = manual_data["historical_data"]
        resolved_ticker = company_payload.get("ticker", "CUSTOM")
        company_name = company_payload.get("company_name", "Private Company")
    else:
        record = get_seed_record(requested_ticker)
        if record:
            historical_data = record["data"]["metrics"]["yearly"]
            resolved_ticker = record["ticker"]
            company_name = record["company_name"]

    initial_state = {
        "company_data": {"ticker": resolved_ticker, "company_name": company_name},
        "historical_data": historical_data,
        "metrics": None,
        "search_query": f"{company_name} news",
        "search_results": [],
        "analysis_result": None,
    }

    # Skip external path (for manual data or quick seed lookups)
    if skip_external and historical_data:
        from app.calculator import calculate_metrics
        metrics = calculate_metrics(historical_data)
        analysis = (record.get("data") or {}).get("analysis") if not manual_data and record else fallback_analysis_from_metrics(metrics)
        return build_response_payload(resolved_ticker, company_name, metrics, analysis)

    # Parallel Graph Execution (EXTREMELY FAST)
    final_state: dict = {}
    try:
        raw_final_state = await asyncio.wait_for(
            graph.ainvoke(initial_state),
            timeout=GRAPH_TIMEOUT_SECONDS,
        )
        final_state = dict(raw_final_state or {})
        
        # Resolve data from final state
        historical_data = final_state.get("historical_data") or historical_data
        if not historical_data and not manual_data:
             raise ValueError(f"Ticker '{resolved_ticker}' not found or no public data available.")
        
        company_name = final_state["company_data"].get("company_name", company_name)
        result = dict(final_state.get("analysis_result") or {})
        analysis = dict(result.get("analysis") or {})
        metrics = dict(final_state.get("metrics") or {})
        
        response_payload = build_response_payload(resolved_ticker, company_name, metrics, analysis)

        scorecard_inputs = None
        scorecard_result = None
        try:
            scorecard_inputs = build_scorecard_inputs_from_history(
                company_name=company_name,
                historical_data=historical_data,
                scoring_mode="credit",
                data_source="manual" if manual_data else "ticker",
            )
            scorecard_result = run_scorecard_analysis(scorecard_inputs, mode="credit")
            response_payload["scorecard"] = scorecard_result
        except Exception as scorecard_err:
            response_payload["scorecard_error"] = str(scorecard_err)

        if save_history and db:
            try:
                analysis_history = AnalysisHistory(
                    ticker=resolved_ticker.upper(),
                    company_name=company_name,
                    archetype=str(response_payload["analysis"].get("analyst_verdict_archetype", "UNKNOWN")),
                    analysis_data=final_state,
                )
                db.add(analysis_history)
                await db.commit()
                response_payload["analysis_id"] = analysis_history.id
                
                if scorecard_inputs and scorecard_result:
                    await persist_scorecard_result(db, scorecard_inputs, scorecard_result)
            except Exception as db_err:
                print(f"Failed to save history: {db_err}")

        return response_payload

    except Exception as graph_error:
        print(f"Parallel Graph failed: {graph_error}")
        raise

@app.get("/api/analyze/stream")
async def analyze_stream(ticker: str, db: AsyncSession = Depends(get_db)):
    async def event_generator():
        # Immediate start
        yield f"data: {json.dumps({'type':'progress','step':'fetching','label':'Parallel Engine Started...'})}\n\n"
        
        try:
            # Stage 1: Check Seed (Zero latency path)
            from app.calculator import calculate_metrics
            record = get_seed_record(ticker)
            if record:
                yield f"data: {json.dumps({'type':'progress','step':'normalizing','label':'Loading Seed Data'})}\n\n"
                company_name = record["company_name"]
                metrics = calculate_metrics(record["data"]["metrics"]["yearly"])
                early_payload = build_response_payload(record["ticker"], company_name, metrics, {})
                yield f"data: {json.dumps({'type':'result','payload': early_payload})}\n\n"
            
            # Stage 2: Parallel Full Analysis (Covers fetching + news + AI in one go)
            result = await run_analysis_for_ticker(ticker=ticker, db=db)
            yield f"data: {json.dumps({'type':'result','payload': result})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type':'error','message': f'Analysis failed: {str(e)}'})}\n\n"
        yield "data: [DONE]\n\n"
        
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/compare")
async def compare_tickers(ticker_a: str, ticker_b: str):
    """Run two analyses and return a comparison verdict payload."""
    try:
        left, right = await asyncio.gather(
            run_analysis_for_ticker(ticker_a, db=None, save_history=False, skip_external=True),
            run_analysis_for_ticker(ticker_b, db=None, save_history=False, skip_external=True),
        )
        return {
            "left": left,
            "right": right,
            "verdict": build_comparison_verdict(left, right),
        }
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))

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


class ScorecardRequest(BaseModel):
    company_name: str
    revenue: float
    ebitda: float
    net_income: float
    interest_expense: float
    total_debt: float
    cash_equivalents: float
    total_assets: float
    current_assets: float
    current_liabilities: float
    scoring_mode: str = "credit"
    data_source: Optional[str] = "manual"
    short_term_debt: Optional[float] = 0.0
    gross_profit: Optional[float] = None
    cfo: Optional[float] = None
    capex: Optional[float] = None
    accounts_receivable: Optional[float] = None
    inventory: Optional[float] = None
    accounts_payable: Optional[float] = None
    cogs: Optional[float] = None
    market_cap: Optional[float] = None
    ev: Optional[float] = None
    retained_earnings: Optional[float] = None
    total_equity: Optional[float] = None
    tax_rate: Optional[float] = None
    revenue_prior: Optional[float] = None
    ebitda_prior: Optional[float] = None
    net_income_prior: Optional[float] = None
    total_debt_prior: Optional[float] = None
    cash_prior: Optional[float] = None
    total_equity_prior: Optional[float] = None
    cfo_prior: Optional[float] = None
    fcf_prior: Optional[float] = None
    working_capital: Optional[float] = None
    working_capital_prior: Optional[float] = None
    revenue_cagr_years: Optional[int] = 3


@app.get("/api/history", dependencies=[Depends(get_api_key)])
async def get_history(db: AsyncSession = Depends(get_db)):
    """Fetch the last 20 analyses from the history."""
    try:
        result = await db.execute(
            select(AnalysisHistory).order_by(AnalysisHistory.created_at.desc()).limit(20)
        )
        history = result.scalars().all()
        return [{"ticker": h.ticker, "name": h.company_name, "archetype": h.archetype, "date": h.created_at} for h in history]
    except Exception:
        return []

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


@app.post("/api/scorecard/analyze", dependencies=[Depends(get_api_key)])
async def analyze_scorecard(request: ScorecardRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = request.model_dump(exclude_none=True)
        scoring_mode = payload.pop("scoring_mode", "credit")
        result = run_scorecard_analysis(payload, mode=scoring_mode)
        record = await persist_scorecard_result(db, payload, result)
        result["analysis_id"] = record.id
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Scorecard analysis failed: {err}")


@app.get("/api/scorecard/history", dependencies=[Depends(get_api_key)])
async def get_scorecard_history(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            select(ScorecardAnalysis).order_by(ScorecardAnalysis.created_at.desc()).limit(10)
        )
        history = result.scalars().all()
        return [
            {
                "id": h.id,
                "company_name": h.company_name,
                "health_score": h.health_score,
                "health_band": h.health_band,
                "scoring_mode": h.scoring_mode,
                "scoring_model_version": h.scoring_model_version,
                "created_at": h.created_at,
                "result": h.result_data,
                "inputs": h.inputs_data,
            }
            for h in history
        ]
    except Exception:
        return []

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Multi-path detection for Hugging Face/Docker environments
potential_paths = [
    os.path.join(os.getcwd(), "frontend-next", "out"),
    os.path.join(os.getcwd(), "out"),
    "/app/frontend-next/out"
]

frontend_path = None
for p in potential_paths:
    if os.path.exists(p) and os.path.exists(os.path.join(p, "index.html")):
        frontend_path = p
        break

@app.get("/api/debug/paths")
async def debug_paths():
    import os
    results = {}
    for p in potential_paths:
        exists = os.path.exists(p)
        results[p] = {
            "exists": exists,
            "is_dir": os.path.isdir(p) if exists else False,
            "contents": os.listdir(p) if exists and os.path.isdir(p) else []
        }
    results["cwd"] = os.getcwd()
    return results

if frontend_path:
    print(f"[*] Serving frontend from: {frontend_path}")
    # Mount static files at the very end
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
else:
    print(f"WARN: Frontend 'out' directory not found in: {potential_paths}")

# Final catch-all for SPA routing (only if frontend_path exists)
@app.exception_handler(404)
async def custom_404_handler(request, __):
    if frontend_path and not request.url.path.startswith("/api"):
        return FileResponse(os.path.join(frontend_path, "index.html"))
    from fastapi.responses import JSONResponse
    return JSONResponse({"detail": "Not Found"}, status_code=404)
