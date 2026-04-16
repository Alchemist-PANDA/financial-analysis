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
import time
from contextlib import asynccontextmanager
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
import asyncio
from app.calculator import numeric_value
from app.engine.orchestrator import run_full_analysis
from app.agent import generate_scorecard_narrative, generate_chart_intel_verdict
from app.cache import get_cached_entry, set_cached
from app.precompute import precompute_loop, trigger_compute, warm_startup_cache
from app.startup_hub.schemas import StartupAgentQueryRequest
from app.startup_hub.service import (
    compare_companies as startup_hub_compare_companies,
    get_company_detail as startup_hub_get_company_detail,
    get_company_ranking as startup_hub_get_company_ranking,
    get_home_payload as startup_hub_get_home_payload,
    list_companies as startup_hub_list_companies,
    list_ipos as startup_hub_list_ipos,
    list_private_opportunities as startup_hub_list_private_opportunities,
    query_agent as startup_hub_query_agent,
)
from app.startup_hub.tasks import (
    recompute_all_rankings as startup_hub_recompute_all_rankings,
    refresh_startup_hub_data as startup_hub_refresh_all,
    seed_startup_hub_data as startup_hub_seed_all,
)

# ── APP SECURITY ─────────────────────────────────────────────────────────────

API_SECRET_KEY = os.getenv("API_SECRET_KEY", "dev_default_key")

if API_SECRET_KEY == "dev_default_key" and os.getenv("RENDER"):
    print("\n[WARNING] Using default API key in production environment!\n")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_SECRET_KEY:
        return api_key_header
    raise HTTPException(status_code=403, detail="Could not validate API key")

GRAPH_TIMEOUT_SECONDS = float(os.getenv("GRAPH_TIMEOUT_SECONDS", "45"))
COMPARE_CACHE_TTL_SECONDS = float(os.getenv("COMPARE_CACHE_TTL_SECONDS", "300"))
COMPARE_CACHE: dict[tuple[str, str], dict[str, Any]] = {}

# ── FastAPI App Setup ────────────────────────────────────────────────────────

from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    precompute_task: asyncio.Task | None = None
    startup_warm_task: asyncio.Task | None = None
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
    
    try:
        if os.getenv("DISABLE_ANALYSIS_PREWARM", "0").strip() != "1":
            startup_warm_task = asyncio.create_task(warm_startup_cache())
            precompute_task = asyncio.create_task(precompute_loop())
    except Exception as e:
        print(f"[CACHE WARM INIT ERROR] {e}")

    try:
        yield
    finally:
        if startup_warm_task is not None:
            startup_warm_task.cancel()
            try:
                await startup_warm_task
            except asyncio.CancelledError:
                pass
        if precompute_task is not None:
            precompute_task.cancel()
            try:
                await precompute_task
            except asyncio.CancelledError:
                pass

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
    from config import GROQ_API_KEY
    
    # 1. Base rule-based explanation as fallback
    parts = []
    confidence = 0.1
    pc = signals["price_change"]
    direction = "up" if pc > 0 else "down"
    
    if signals.get("news") and isinstance(signals["news"], dict):
        parts.append(f"Stock {direction} {abs(pc):.1f}% following news: '{signals['news'].get('headline', 'Market Catalyst')}'")
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

    # 2. AI Enhancement (must call via app/agent.py)
    ai_explanation = base_explanation
    if GROQ_API_KEY:
        try:
            enhanced = generate_chart_intel_verdict(ticker=ticker, price_change=float(pc), signals=signals)
            if enhanced:
                ai_explanation = enhanced
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

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        if isinstance(obj, (np.floating, np.float64)):
            return float(obj) if not (np.isnan(obj) or np.isinf(obj)) else None
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

def sanitize_for_json(obj):
    """The Nuclear Option: Force native Python types via JSON round-trip with custom encoder."""
    return json.loads(json.dumps(obj, cls=NumpyEncoder))


def prepare_cached_payload(ticker: str) -> tuple[dict | None, bool]:
    entry = get_cached_entry(ticker)
    if not entry:
        return None, False

    payload = dict(entry["data"] or {})
    is_stale = bool(entry.get("stale"))
    if is_stale:
        payload["stale"] = True
    else:
        payload.pop("stale", None)
    return payload, is_stale

@app.get("/api/explain-chart", dependencies=[Depends(get_api_key)])
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

@app.get("/api/timeline-markers", dependencies=[Depends(get_api_key)])
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

    # Contract hardening for the Next.js frontend.
    flags = normalized_analysis.get("flags", [])
    normalized_analysis["flags"] = flags if isinstance(flags, list) else []

    archetype = normalized_analysis.get("analyst_verdict_archetype")
    if isinstance(archetype, list):
        archetype = archetype[0] if archetype else "TRANSITION"
    if not isinstance(archetype, str) or not archetype.strip():
        archetype = "TRANSITION"
    normalized_analysis["analyst_verdict_archetype"] = archetype

    diag = normalized_analysis.get("pattern_diagnosis")
    if isinstance(diag, dict):
        normalized_analysis["pattern_diagnosis"] = json.dumps(diag, cls=NumpyEncoder)

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
    scorecard = dict(payload.get("scorecard", {}) or {})
    metrics = dict(payload.get("metrics", {}) or {})
    color_signal = str(payload.get("color_signal", "") or "").upper()
    z_score = float(metrics.get("current_z_score", 0.0) or 0.0)
    cagr = float(metrics.get("revenue_cagr_pct", 0.0) or 0.0)
    fcf = float(metrics.get("current_fcf_conversion_pct", 0.0) or 0.0)
    roe = float(metrics.get("current_roe", 0.0) or 0.0)
    dso = float(metrics.get("current_dso", 0.0) or 0.0)
    health_score = float(scorecard.get("health_score", 0.0) or 0.0)
    signal_bonus = {"GREEN": 8.0, "YELLOW": 4.0, "RED": 0.0}.get(color_signal, 0.0)
    return (
        (health_score * 0.5)
        + (z_score * 4.0)
        + (cagr * 0.8)
        + (fcf * 0.2)
        + (roe * 0.15)
        + signal_bonus
        - (max(dso - 60.0, 0.0) * 0.15)
    )


def build_comparison_verdict(left: dict, right: dict) -> dict:
    left_score = score_for_comparison(left)
    right_score = score_for_comparison(right)
    if left_score >= right_score:
        winner = left.get("ticker", "LEFT")
        loser = right.get("ticker", "RIGHT")
    else:
        winner = right.get("ticker", "RIGHT")
        loser = left.get("ticker", "LEFT")
        winner_payload = right
        loser_payload = left
        winner_score = right_score
        loser_score = left_score
    if left_score >= right_score:
        winner_payload = left
        loser_payload = right
        winner_score = left_score
        loser_score = right_score

    winner_metrics = dict(winner_payload.get("metrics", {}) or {})
    loser_metrics = dict(loser_payload.get("metrics", {}) or {})
    winner_scorecard = dict(winner_payload.get("scorecard", {}) or {})
    loser_scorecard = dict(loser_payload.get("scorecard", {}) or {})

    reasons: list[str] = []
    winner_health = float(winner_scorecard.get("health_score", 0.0) or 0.0)
    loser_health = float(loser_scorecard.get("health_score", 0.0) or 0.0)
    if winner_health > loser_health:
        reasons.append("health score")

    winner_z = float(winner_metrics.get("current_z_score", 0.0) or 0.0)
    loser_z = float(loser_metrics.get("current_z_score", 0.0) or 0.0)
    if winner_z > loser_z:
        reasons.append("solvency")

    winner_cagr = float(winner_metrics.get("revenue_cagr_pct", 0.0) or 0.0)
    loser_cagr = float(loser_metrics.get("revenue_cagr_pct", 0.0) or 0.0)
    if winner_cagr > loser_cagr:
        reasons.append("growth trend")

    winner_fcf = float(winner_metrics.get("current_fcf_conversion_pct", 0.0) or 0.0)
    loser_fcf = float(loser_metrics.get("current_fcf_conversion_pct", 0.0) or 0.0)
    if winner_fcf > loser_fcf:
        reasons.append("cash conversion")

    if not reasons:
        reasons.append("overall blended score")

    summary = f"{winner} leads on {', '.join(reasons[:3])} versus {loser}."
    return {
        "winner": winner,
        "summary": summary,
        "winner_score": round(winner_score, 2),
        "loser_score": round(loser_score, 2),
        "score_gap": round(abs(left_score - right_score), 2),
    }


def get_compare_cache_key(left_ticker: str, right_ticker: str) -> tuple[str, str]:
    return tuple(sorted([left_ticker.upper(), right_ticker.upper()]))


def get_cached_compare(left_ticker: str, right_ticker: str) -> dict | None:
    key = get_compare_cache_key(left_ticker, right_ticker)
    entry = COMPARE_CACHE.get(key)
    if not entry:
        return None
    age_seconds = time.time() - float(entry["time"])
    if age_seconds > COMPARE_CACHE_TTL_SECONDS:
        COMPARE_CACHE.pop(key, None)
        return None
    return dict(entry["data"] or {})


def set_cached_compare(left_ticker: str, right_ticker: str, data: dict) -> None:
    key = get_compare_cache_key(left_ticker, right_ticker)
    COMPARE_CACHE[key] = {
        "data": dict(data or {}),
        "time": time.time(),
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

    # Provide both latest and prior to enable deltas/CAGR where present.
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
        "gross_profit": revenue - cogs if cogs_raw is not None else pick_number(latest, "gross_profit", default=0.0),
        "cfo": pick_number(latest, "cfo"),
        "capex": pick_number(latest, "capex"),
        "accounts_receivable": pick_number(latest, "accounts_receivable"),
        "inventory": pick_number(latest, "inventory"),
        "accounts_payable": pick_number(latest, "accounts_payable"),
        "cogs": cogs,
        "market_cap": market_cap,
        "retained_earnings": pick_number(latest, "retained_earnings", default=net_income),
        "working_capital": pick_number(latest, "working_capital"),
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
        "working_capital_prior": pick_number(prior, "working_capital"),
        "revenue_cagr_years": 3,
        "data_source": data_source,
        "scoring_mode": scoring_mode,
    }


def run_scorecard_analysis(inputs: dict, mode: str = "credit") -> dict:
    result = dict(run_full_analysis(inputs, mode=mode) or {})
    narrative = ""
    narrative_error = ""
    try:
        narrative = generate_scorecard_narrative(result)
    except Exception as e:
        narrative_error = str(e)
    if narrative:
        result["narrative"] = narrative
    if narrative_error:
        result["narrative_error"] = narrative_error
    return result


async def persist_scorecard_result(db: AsyncSession, inputs: dict, result: dict) -> ScorecardAnalysis:
    record = ScorecardAnalysis(
        company_name=result.get("company_name", inputs.get("company_name", "Unknown")),
        scoring_mode=result.get("scoring_mode", inputs.get("scoring_mode", "credit")),
        scoring_model_version=result.get("scoring_model_version", "unknown"),
        health_score=int(result.get("health_score", 0) or 0),
        health_band=str(result.get("health_band", "Unknown")),
        inputs_data=inputs,
        result_data=result,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def run_analysis_for_ticker(
    ticker: str,
    manual_data: dict | None = None,
    db: AsyncSession | None = None,
    save_history: bool = True,
    include_scorecard: bool = True,
) -> dict:
    company = dict((manual_data or {}).get("company") or {})
    company_name = company.get("company_name") or ticker
    initial_state = {
        "company_data": {"ticker": ticker, "company_name": company_name},
        "historical_data": (manual_data or {}).get("historical_data"),
        "metrics": None,
        "search_query": f"{ticker} news",
        "search_results": [],
        "analysis_result": None,
    }

    try:
        final_state = await asyncio.wait_for(graph.ainvoke(initial_state), timeout=GRAPH_TIMEOUT_SECONDS)
        company_data = dict(final_state.get("company_data") or {})
        resolved_name = company_data.get("company_name") or company_name or ticker
        resolved_ticker = company_data.get("ticker") or ticker

        metrics = dict(final_state.get("metrics") or {})
        analysis = dict((final_state.get("analysis_result") or {}).get("analysis") or {})
        payload = build_response_payload(resolved_ticker, resolved_name, metrics, analysis)

        if include_scorecard:
            try:
                historical = list(final_state.get("historical_data") or [])
                if historical:
                    inputs = build_scorecard_inputs_from_history(
                        company_name=resolved_name,
                        historical_data=historical,
                        scoring_mode="credit",
                        data_source="manual" if manual_data else "ticker",
                    )
                    scorecard = run_scorecard_analysis(inputs, mode="credit")
                    payload["scorecard"] = scorecard
                    if db and save_history:
                        record = await persist_scorecard_result(db, inputs, scorecard)
                        scorecard["analysis_id"] = record.id
            except Exception as scorecard_err:
                payload["scorecard_error"] = str(scorecard_err)

        if db and save_history:
            try:
                archetype = str((payload.get("analysis") or {}).get("analyst_verdict_archetype", "UNKNOWN"))
                safe_payload = sanitize_for_json(payload)
                set_cached(str(resolved_ticker or ticker), safe_payload)
                history = AnalysisHistory(
                    ticker=str(resolved_ticker or ticker).upper(),
                    company_name=str(resolved_name or company_name or ticker),
                    archetype=archetype,
                    analysis_data=safe_payload,
                )
                db.add(history)
                await db.commit()
            except Exception as db_err:
                print(f"[HISTORY SAVE ERROR] {db_err}")
        else:
            set_cached(str(resolved_ticker or ticker), sanitize_for_json(payload))

        return payload
    except Exception as e:
        print(f"[PARALLEL GRAPH ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── API Models ──────────────────────────────────────────────────────────────

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
    cogs: Optional[float] = None
    interest_expense: Optional[float] = None
    current_assets: Optional[float] = None
    current_liabilities: Optional[float] = None


class CompanyData(BaseModel):
    company_name: str
    sector: Optional[str] = "Unknown"
    ticker: Optional[str] = "CUSTOM"


class AnalysisRequest(BaseModel):
    company: CompanyData
    historical_data: List[HistoricalYear] = Field(
        ..., min_length=1, description="Historical financial data (prefer 5 years Y-4 through Y0)."
    )


class ScorecardRequest(BaseModel):
    company_name: str
    scoring_mode: str = "credit"
    data_source: Optional[str] = "manual"

    revenue: float
    ebitda: float
    net_income: float
    interest_expense: float = 0.0
    total_debt: float
    cash_equivalents: float
    total_assets: float
    current_assets: float = 0.0
    current_liabilities: float = 0.0

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


@app.post("/api/analyze", dependencies=[Depends(get_api_key)])
async def analyze_company(request: AnalysisRequest, db: AsyncSession = Depends(get_db)):
    payload_dict: dict[str, Any] = {
        "company": request.company.model_dump(),
        "historical_data": [year.model_dump() for year in request.historical_data],
    }
    ticker = (request.company.ticker or "CUSTOM").strip().upper()
    return await run_analysis_for_ticker(
        ticker=ticker,
        manual_data=payload_dict,
        db=db,
        save_history=True,
        include_scorecard=True,
    )


@app.get("/api/analyze", dependencies=[Depends(get_api_key)])
async def analyze_company_get(ticker: str):
    """Cache-only live analysis endpoint. No full compute happens on request."""
    normalized = (ticker or "").strip().upper()
    if not normalized:
        raise HTTPException(status_code=400, detail="ticker is required")

    cached, is_stale = prepare_cached_payload(normalized)
    if cached is not None:
        if is_stale:
            trigger_compute(normalized)
        return cached

    trigger_compute(normalized)
    raise HTTPException(status_code=503, detail="Analysis cache miss. Background warm triggered; retry shortly.")


@app.post("/api/scorecard/analyze", dependencies=[Depends(get_api_key)])
async def analyze_scorecard(request: ScorecardRequest, db: AsyncSession = Depends(get_db)):
    inputs = request.model_dump(exclude_none=True)
    mode = str(inputs.pop("scoring_mode", "credit") or "credit")
    inputs.setdefault("data_source", request.data_source or "manual")
    result = run_scorecard_analysis(inputs, mode=mode)
    record = await persist_scorecard_result(db, inputs, result)
    result["analysis_id"] = record.id
    return sanitize_for_json(result)


@app.get("/api/scorecard/history", dependencies=[Depends(get_api_key)])
async def get_scorecard_history(db: AsyncSession = Depends(get_db)):
    try:
        res = await db.execute(
            select(ScorecardAnalysis).order_by(ScorecardAnalysis.created_at.desc()).limit(10)
        )
        history = res.scalars().all()
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
    except Exception as e:
        print(f"[SCORECARD HISTORY ERROR] {e}")
        return JSONResponse({"detail": "Scorecard history currently unavailable."}, status_code=500)


@app.get("/api/compare", dependencies=[Depends(get_api_key)])
async def compare_tickers(
    ticker_a: str | None = None,
    ticker_b: str | None = None,
    t1: str | None = None,
    t2: str | None = None,
):
    left_ticker = (ticker_a or t1 or "").strip().upper()
    right_ticker = (ticker_b or t2 or "").strip().upper()

    if not left_ticker or not right_ticker:
        raise HTTPException(status_code=400, detail="ticker_a/ticker_b or t1/t2 are required")
    if left_ticker == right_ticker:
        raise HTTPException(status_code=400, detail="Use two different tickers for comparison.")

    cached_compare = get_cached_compare(left_ticker, right_ticker)
    if cached_compare is not None:
        return sanitize_for_json(cached_compare)

    left, left_stale = prepare_cached_payload(left_ticker)
    right, right_stale = prepare_cached_payload(right_ticker)

    missing: list[str] = []
    if left is None:
        trigger_compute(left_ticker)
        missing.append(left_ticker)
    if right is None:
        trigger_compute(right_ticker)
        missing.append(right_ticker)

    if missing:
        missing_list = ", ".join(missing)
        raise HTTPException(
            status_code=503,
            detail=f"Comparison cache miss for {missing_list}. Background warm triggered; retry shortly.",
        )

    if left_stale:
        trigger_compute(left_ticker)
    if right_stale:
        trigger_compute(right_ticker)

    payload = sanitize_for_json(
        {
            "left": left,
            "right": right,
            "verdict": build_comparison_verdict(left, right),
            "left_stale": left_stale,
            "right_stale": right_stale,
        }
    )
    set_cached_compare(left_ticker, right_ticker, payload)
    return payload


@app.get("/api/startup-hub/home", dependencies=[Depends(get_api_key)])
async def startup_hub_home(db: AsyncSession = Depends(get_db)):
    return await startup_hub_get_home_payload(db=db)


@app.get("/api/startup-hub/companies", dependencies=[Depends(get_api_key)])
async def startup_hub_companies(
    entity_type: str | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    filters = {
        "entity_type": entity_type,
        "search": search,
    }
    return await startup_hub_list_companies(filters, db=db)


@app.get("/api/startup-hub/company/{slug}", dependencies=[Depends(get_api_key)])
async def startup_hub_company_detail(slug: str, db: AsyncSession = Depends(get_db)):
    try:
        return await startup_hub_get_company_detail(slug, db=db)
    except LookupError:
        raise HTTPException(status_code=404, detail=f"Startup Hub company not found: {slug}")


@app.get("/api/startup-hub/company/{slug}/ranking", dependencies=[Depends(get_api_key)])
async def startup_hub_company_ranking(slug: str, db: AsyncSession = Depends(get_db)):
    try:
        return await startup_hub_get_company_ranking(slug, db=db)
    except LookupError:
        raise HTTPException(status_code=404, detail=f"Startup Hub company not found: {slug}")


@app.get("/api/startup-hub/compare", dependencies=[Depends(get_api_key)])
async def startup_hub_compare(left: str, right: str, db: AsyncSession = Depends(get_db)):
    try:
        return await startup_hub_compare_companies(left, right, db=db)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=f"Startup Hub company not found: {exc.args[0]}")


@app.get("/api/startup-hub/ipos", dependencies=[Depends(get_api_key)])
async def startup_hub_ipos(db: AsyncSession = Depends(get_db)):
    return await startup_hub_list_ipos(db=db)


@app.get("/api/startup-hub/private", dependencies=[Depends(get_api_key)])
async def startup_hub_private(db: AsyncSession = Depends(get_db)):
    return await startup_hub_list_private_opportunities(db=db)


@app.post("/api/startup-hub/agent/query", dependencies=[Depends(get_api_key)])
async def startup_hub_agent_query(
    request: StartupAgentQueryRequest,
    db: AsyncSession = Depends(get_db),
):
    return await startup_hub_query_agent(request, db=db)


@app.post("/api/startup-hub/admin/seed", dependencies=[Depends(get_api_key)])
async def startup_hub_admin_seed(db: AsyncSession = Depends(get_db)):
    return await startup_hub_seed_all(db=db)


@app.post("/api/startup-hub/admin/refresh", dependencies=[Depends(get_api_key)])
async def startup_hub_admin_refresh(db: AsyncSession = Depends(get_db)):
    return await startup_hub_refresh_all(db=db)


@app.post("/api/startup-hub/admin/recompute-rankings", dependencies=[Depends(get_api_key)])
async def startup_hub_admin_recompute_rankings(db: AsyncSession = Depends(get_db)):
    return await startup_hub_recompute_all_rankings(db=db)


@app.get("/api/export/pdf", dependencies=[Depends(get_api_key)])
async def export_pdf(ticker: str, db: AsyncSession = Depends(get_db)):
    from app.reporter import generate_financial_pdf

    requested = (ticker or "").strip().upper()
    if not requested:
        raise HTTPException(status_code=400, detail="ticker is required")

    res = await db.execute(
        select(AnalysisHistory)
        .where(AnalysisHistory.ticker == requested)
        .order_by(AnalysisHistory.created_at.desc())
        .limit(1)
    )
    analysis_record = res.scalars().first()
    if not analysis_record:
        raise HTTPException(status_code=404, detail=f"No analysis history found for ticker: {requested}")

    pdf_buffer = generate_financial_pdf(
        analysis_record.ticker,
        analysis_record.company_name,
        analysis_record.analysis_data,
    )
    filename = f"Analyst_Report_{requested}_{datetime.now().strftime('%Y%m%d')}.pdf"
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

@app.get("/api/analyze/stream", dependencies=[Depends(get_api_key)])
async def analyze_stream(ticker: str):
    async def event_generator():
        resolved_ticker = (ticker or "").strip().upper()
        cached, is_stale = prepare_cached_payload(resolved_ticker)
        if cached is not None:
            if is_stale:
                trigger_compute(resolved_ticker)
            yield f"data: {json.dumps({'type': 'progress', 'step': 'cache', 'label': 'Cache hit. Returning instantly.'})}\n\n"
            yield f"data: {json.dumps({'type': 'result', 'payload': cached})}\n\n"
            yield "data: [DONE]\n\n"
            return

        trigger_compute(resolved_ticker)
        yield f"data: {json.dumps({'type': 'error', 'message': 'Analysis cache miss. Background warm triggered; retry shortly.'})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

# ── API Paths & SPA ─────────────────────────────────────────────────────────

potential_paths = [
    os.path.join(os.getcwd(), "frontend-next", "out"),
    "/app/frontend-next/out"
]
print(f"Checking for frontend at: {potential_paths}")
frontend_path = next((p for p in potential_paths if os.path.exists(os.path.join(p, "index.html"))), None)
print(f"Frontend path resolved to: {frontend_path}")

@app.get("/api/history", dependencies=[Depends(get_api_key)])
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
