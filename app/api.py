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
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
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
origins = ["*"] # Simplification for debug

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Chart Intelligence Logic ──────────────────────────────────────────────────

def detect_signals(ticker: str, history_df: Any, news: list) -> dict:
    import pandas as pd
    if history_df.empty or len(history_df) < 2:
        return {"news": None, "volume": None, "technical": None, "price_change": 0}

    # 1. Price Change
    latest_close = float(history_df['Close'].iloc[-1])
    prev_close = float(history_df['Close'].iloc[-2])
    price_change = ((latest_close / prev_close) - 1) * 100

    # 2. News Detection
    IMPACT_KEYWORDS = ["earnings", "beat", "miss", "merger", "fda", "lawsuit", "ceo", "guidance", "acquisition"]
    news_signal = None
    for item in news:
        headline = item.get("title", "").lower()
        if any(kw in headline for kw in IMPACT_KEYWORDS):
            news_signal = {"has_news": True, "headline": item.get("title"), "event": "Catalyst Detected"}
            break

    # 3. Volume Detection (20-day avg)
    volume_signal = {"volume_spike": False, "ratio": 1.0, "explanation": "Data unavailable"}
    if 'Volume' in history_df.columns and not history_df['Volume'].empty and len(history_df) > 1:
        try:
            avg_vol = history_df['Volume'].iloc[:-1].mean()
            current_vol = history_df['Volume'].iloc[-1]
            vol_ratio = current_vol / avg_vol if avg_vol > 0 else 1
            volume_signal = {
                "volume_spike": bool(vol_ratio > 1.8),
                "ratio": round(float(vol_ratio), 2),
                "explanation": "Unusually high volume" if vol_ratio > 2.0 else "Normal volume"
            }
        except: pass

    # 4. Technical Detection (20-day breakout)
    technical_signal = {"pattern": "neutral", "level": 0.0}
    if 'High' in history_df.columns and 'Low' in history_df.columns and not history_df.empty and len(history_df) > 5:
        try:
            lookback = history_df.iloc[-21:-1] if len(history_df) > 21 else history_df.iloc[:-1]
            res_level = lookback['High'].max()
            sup_level = lookback['Low'].min()
            
            if latest_close > res_level * 1.001:
                technical_signal = {"pattern": "breakout", "level": round(float(res_level), 2)}
            elif latest_close < sup_level * 0.999:
                technical_signal = {"pattern": "breakdown", "level": round(float(sup_level), 2)}
        except: pass

    return {
        "news": news_signal,
        "volume": volume_signal,
        "technical": technical_signal,
        "price_change": round(float(price_change), 2)
    }

def generate_chart_explanation(ticker: str, signals: dict) -> dict:
    import json
    import requests
    from config import GROQ_API_KEY, MODEL_NAME
    
    # 1. Base rule-based explanation as fallback
    parts = []
    confidence = 0.1
    pc = signals["price_change"]
    direction = "up" if pc > 0 else "down"
    
    if signals["news"]:
        parts.append(f"Stock {direction} {abs(pc):.1f}% following news: '{signals['news']['headline']}'")
        confidence += 0.5
    elif abs(pc) > 2.5:
        parts.append(f"Stock {direction} {abs(pc):.1f}% on significant momentum")
        confidence += 0.2
    else:
        parts.append(f"Stock showing stable movement ({pc:.1f}%)")

    if signals["volume"]["volume_spike"]:
        parts.append(f"supported by {signals['volume']['ratio']}x average volume indicating institutional activity")
        confidence += 0.3
    
    if signals["technical"]:
        parts.append(f"breaking {'above' if pc > 0 else 'below'} key {signals['technical']['pattern']} levels")
        confidence += 0.2

    base_explanation = ". ".join(parts).capitalize()
    if len(parts) > 1:
        base_explanation = ", ".join(parts[:-1]) + ", and " + parts[-1]

    # 2. AI Enhancement using Groq
    ai_explanation = base_explanation
    if GROQ_API_KEY:
        try:
            # Create a serializable copy of signals
            serializable_signals = {
                "news": signals.get("news"),
                "volume": {
                    "volume_spike": bool(signals["volume"]["volume_spike"]),
                    "ratio": float(signals["volume"]["ratio"]),
                    "explanation": str(signals["volume"]["explanation"])
                } if signals.get("volume") else None,
                "technical": signals.get("technical"),
                "price_change": float(signals["price_change"])
            }
            
            prompt = f"""You are a Senior Institutional Analyst. Explain why {ticker} moved {pc:.1f}% given these signals:
- News: {json.dumps(serializable_signals['news'])}
- Volume: {json.dumps(serializable_signals['volume'])}
- Technical: {json.dumps(serializable_signals['technical'])}

Write a concise, professional 1-sentence institutional verdict (max 30 words).
Use terms like 'catalyst-driven', 'institutional accumulation', 'resistance breach', or 'momentum exhaustion'.
Be brutally direct. Cite the price change of {pc:.1f}%."""

            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": MODEL_NAME,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "max_tokens": 100
                },
                timeout=5
            )
            if response.ok:
                ai_explanation = response.json()["choices"][0]["message"]["content"].strip().strip('"')
        except Exception as e:
            print(f"[AI EXPLAIN ERROR] {e}")

    return {
        "ticker": ticker,
        "price_change": pc,
        "explanation": ai_explanation,
        "confidence": min(confidence, 1.0),
        "timestamp": datetime.now().isoformat(),
        "signals": signals
    }

# --- Caching Layer ---
_chart_cache = {}

def get_from_cache(key: str):
    import time
    entry = _chart_cache.get(key)
    if entry and (time.time() - entry['timestamp'] < 300): # 5 minutes
        return entry['data']
    return None

def set_to_cache(key: str, data: Any):
    import time
    _chart_cache[key] = {'timestamp': time.time(), 'data': data}

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback
    error_details = traceback.format_exc()
    print(f"[GLOBAL ERROR] {error_details}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": str(exc),
            "traceback": error_details,
            "type": "global"
        }
    )

import numpy as np

def sanitize_for_json(obj):
    """
    Recursively converts NumPy types and NaN/Infinity to JSON-safe native Python types.
    """
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(i) for i in obj]
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, (np.integer, int)):
        return int(obj)
    elif isinstance(obj, (np.floating, float)):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    elif obj is None:
        return None
    return obj

@app.get("/api/explain-chart")
async def explain_chart(ticker: str):
    try:
        import yfinance as yf
        cache_key = f"explain_{ticker.upper()}"
        cached = get_from_cache(cache_key)
        if cached: return cached

        t = yf.Ticker(ticker)
        hist = t.history(period="30d")
        if hist.empty:
            raise HTTPException(status_code=404, detail=f"No data for {ticker}")
        
        news = []
        try: news = t.news[:5]
        except: pass
        
        signals = detect_signals(ticker, hist, news)
        result = generate_chart_explanation(ticker, signals)
        
        # DEFINITIVE FIX: Deep sanitize before returning
        safe_result = sanitize_for_json(result)
        
        set_to_cache(cache_key, safe_result)
        return safe_result
    except HTTPException: raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[API ERROR] {error_details}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "traceback": error_details,
                "ticker": ticker
            }
        )

@app.get("/api/timeline-markers")
async def timeline_markers(ticker: str):
    import yfinance as yf
    
    cache_key = f"markers_{ticker.upper()}"
    cached = get_from_cache(cache_key)
    if cached: return cached

    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="60d")
        markers = []
        if hist.empty: return []
        
        for i in range(1, len(hist)):
            prev = hist['Close'].iloc[i-1]
            curr = hist['Close'].iloc[i]
            if prev == 0: continue
            day_pc = ((curr / prev) - 1) * 100
            if abs(day_pc) > 3.5:
                markers.append({
                    "date": hist.index[i].strftime("%Y-%m-%d"),
                    "type": "momentum",
                    "price_change": round(float(day_pc), 2),
                    "price": round(float(curr), 2),
                    "icon": "⚡" if day_pc > 0 else "🚨"
                })
        # Sanitize markers for JSON
        safe_markers = sanitize_for_json(markers)
        set_to_cache(cache_key, safe_markers)
        return safe_markers
    except: return []

# ── Core Analysis Helpers ───────────────────────────────────────────────────

def derive_color_signal(z_score: float) -> str:
    if z_score > 2.99: return "GREEN"
    if z_score > 1.8: return "YELLOW"
    return "RED"

def default_retail_verdict(analysis: dict | None, color_signal: str) -> str:
    if analysis and analysis.get("retail_verdict"):
        return analysis["retail_verdict"]
    return "Financial profile is resilient and lower risk." if color_signal == "GREEN" else "Mixed fundamentals."

def build_response_payload(ticker: str, company_name: str, metrics: dict | None, analysis: dict | None) -> dict:
    safe_metrics = dict(metrics or {})
    z_score_raw = safe_metrics.get("current_z_score")
    if z_score_raw is None:
        solvency = str(safe_metrics.get("solvency_signal", "")).upper()
        z_score_raw = 3.1 if solvency == "SAFE" else (2.1 if solvency in {"GREY_ZONE", "YELLOW"} else 1.2)
    
    color_signal = derive_color_signal(float(z_score_raw or 0.0))
    normalized_analysis = dict(analysis or {})
    normalized_analysis["flags"] = normalized_analysis.get("flags", [])
    normalized_analysis["retail_verdict"] = default_retail_verdict(normalized_analysis, color_signal)
    
    return {
        "ticker": ticker.upper() if ticker else "UNKNOWN",
        "company_name": company_name or "Unknown",
        "metrics": safe_metrics,
        "analysis": normalized_analysis,
        "color_signal": color_signal,
    }

async def run_analysis_for_ticker(ticker: str, manual_data: dict = None, db: AsyncSession = None) -> dict:
    initial_state = {
        "company_data": {"ticker": ticker, "company_name": ticker},
        "historical_data": manual_data["historical_data"] if manual_data else None,
        "metrics": None,
        "search_query": f"{ticker} news",
        "search_results": [],
        "analysis_result": None,
    }
    try:
        final_state = await asyncio.wait_for(graph.ainvoke(initial_state), timeout=GRAPH_TIMEOUT_SECONDS)
        metrics = final_state.get("metrics") or {}
        analysis = (final_state.get("analysis_result") or {}).get("analysis") or {}
        return build_response_payload(ticker, ticker, metrics, analysis)
    except Exception as e:
        print(f"[PARALLEL GRAPH ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analyze/stream")
async def analyze_stream(ticker: str, db: AsyncSession = Depends(get_db)):
    async def event_generator():
        yield f"data: {json.dumps({'type':'progress','step':'fetching','label':'Parallel Engine Started...'})}\n\n"
        try:
            result = await run_analysis_for_ticker(ticker=ticker, db=db)
            yield f"data: {json.dumps({'type':'result','payload': result})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type':'error','message': str(e)})}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# ── API Paths & SPA ─────────────────────────────────────────────────────────

potential_paths = [
    os.path.join(os.getcwd(), "frontend-next", "out"),
    "/app/frontend-next/out"
]
frontend_path = next((p for p in potential_paths if os.path.exists(os.path.join(p, "index.html"))), None)

@app.get("/api/history")
async def get_history(db: AsyncSession = Depends(get_db)):
    try:
        res = await db.execute(select(AnalysisHistory).order_by(AnalysisHistory.created_at.desc()).limit(20))
        return [{"ticker": h.ticker, "name": h.company_name, "archetype": h.archetype, "date": h.created_at} for h in res.scalars().all()]
    except Exception as e:
        print(f"[HISTORY ERROR] {e}")
        return JSONResponse({"detail": "History currently unavailable."}, status_code=500)

if frontend_path:
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

@app.exception_handler(404)
async def spa_handler(request, __):
    if frontend_path and not request.url.path.startswith("/api"):
        return FileResponse(os.path.join(frontend_path, "index.html"))
    return JSONResponse({"detail": "Not Found"}, status_code=404)
