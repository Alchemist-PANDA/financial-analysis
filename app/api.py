import sys
import os
from datetime import datetime
from typing import List, Optional
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
from app.models import AnalysisHistory, Watchlist
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
                    company_name=item["name"],
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
else:
    # Fallback/Safety for local dev if no env is set
    origins.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Analysis Helper ──────────────────────────────────────────────────────────

async def run_analysis_for_ticker(ticker: str, db: Optional[AsyncSession] = None):
    """
    Bridge to the actual LangGraph agent. 
    Invokes the full pipeline to calculate 'Senior Tier' metrics dynamically.
    """
    from app.sample_data import SEED_DATA
    
    # 1. Fetch seed record
    record = next((item for item in SEED_DATA if item["ticker"].upper() == ticker.upper()), SEED_DATA[0])
    
    # 2. Build AgentState
    initial_state = {
        "company_data": {
            "ticker": record["ticker"],
            "company_name": record["company_name"]
        },
        "historical_data": record["data"]["metrics"]["yearly"],
        "metrics": None,
        "search_query": f"{record['ticker']} news",
        "search_results": [],
        "analysis_result": None,
    }

    # 3. Invoke Graph
    try:
        final_state = await asyncio.to_thread(graph.invoke, initial_state)
        
        # 4. Map to UI expectations
        result = final_state.get("analysis_result", {})
        analysis = result.get("analysis", {})
        metrics = final_state.get("metrics", {})
        
        # 5. Save to History if DB session provided
        if db:
            try:
                analysis_history = AnalysisHistory(
                    ticker=record["ticker"],
                    company_name=record["company_name"],
                    archetype=analysis.get("analyst_verdict_archetype", "UNKNOWN"),
                    analysis_data=final_state
                )
                db.add(analysis_history)
                await db.commit()
            except Exception as db_err:
                print(f"Failed to save history: {db_err}")

        return {
            "metrics": metrics,
            "analysis": analysis
        }
    except Exception as e:
        print(f"Graph invocation failed: {e}")
        # Fallback to seed data if graph fails (e.g. API key issue)
        return record["data"]

@app.get("/api/analyze/stream")
async def analyze_stream(ticker: str, db: AsyncSession = Depends(get_db)):
    async def event_generator():
        # Step 1: emit pipeline progress events
        yield f"data: {json.dumps({'type':'progress','step':'fetching','label':'Fetching 5-year financial data'})}\n\n"
        
        yield f"data: {json.dumps({'type':'progress','step':'normalizing','label':'Normalizing GAAP figures'})}\n\n"
        
        yield f"data: {json.dumps({'type':'progress','step':'trend_engine','label':'Running Trend Engine'})}\n\n"
        
        yield f"data: {json.dumps({'type':'progress','step':'flags','label':'Detecting Anomaly Patterns'})}\n\n"
        
        yield f"data: {json.dumps({'type':'progress','step':'verdict','label':'Generating Analyst Verdict'})}\n\n"
        
        # Final event: emit the complete result payload and persist to DB
        result = await run_analysis_for_ticker(ticker, db)
        yield f"data: {json.dumps({'type':'result','payload': result})}\n\n"
        yield "data: [DONE]\n\n"
        
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )

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

class CompanyData(BaseModel):
    company_name: str
    sector: Optional[str] = "Unknown"
    ticker: Optional[str] = "N/A"

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
    Run an institutional-grade financial trend analysis on the provided company dataset.
    Requires exactly 5+ years of data.
    """
    # Build LangGraph input state
    initial_state = {
        "company_data": request.company.model_dump(),
        "historical_data": [year.model_dump() for year in request.historical_data],
        "metrics": None,
        "search_query": "",
        "search_results": None,
        "analysis_result": None,
    }

    try:
        final_state = graph.invoke(initial_state)
        result = final_state.get("analysis_result", {})
        analysis = result.get("analysis", {})
        
        # Save to History
        analysis_history = AnalysisHistory(
            ticker=request.company.ticker,
            company_name=request.company.company_name,
            archetype=analysis.get("analyst_verdict_archetype", "UNKNOWN"),
            analysis_data=final_state
        )
        db.add(analysis_history)
        await db.commit()

        return {
            "status": "success",
            "company_name": result.get("company_name"),
            "calculated_metrics": final_state.get("metrics"),
            "flags": analysis.get("flags", []),
            "pattern_diagnosis": analysis.get("pattern_diagnosis"),
            "analyst_verdict": {
                "archetype": analysis.get("analyst_verdict_archetype"),
                "summary": analysis.get("analyst_verdict_summary")
            }
        }
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Analysis engine failed: {err}")

# Serve the frontend UI (Must be at the bottom so it doesn't swallow API routes)
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
