"""
graph.py — Builds and compiles the LangGraph execution graph.
Optimized for speed: Parallel fetching and hardened nodes.
"""

import sys
import os
import asyncio

# Ensure app/ is on the path for sibling imports
sys.path.insert(0, os.path.dirname(__file__))

from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph

from state import AgentState
from calculator import calculate_metrics
from agent import run_snapshot_agent
from search import get_company_news
from dynamic_fetcher import fetch_historical_data


# ── Node definitions ──────────────────────────────────────────────────────────

async def fetch_data_node(state: AgentState) -> dict:
    """Node 0: Fetch historical data if not present (Parallel Candidate)."""
    if state.get("historical_data"):
        return {}
    
    ticker = state["company_data"].get("ticker")
    if not ticker or ticker == "CUSTOM":
        return {}

    try:
        # Run sync yfinance in a thread to keep graph async
        res = await fetch_historical_data(ticker)
        if res:
            name, data = res
            return {
                "historical_data": data, 
                "company_data": {**state["company_data"], "company_name": name}
            }
    except Exception as e:
        print(f"Fetch error: {e}")
    
    return {"historical_data": []}


def calculate_metrics_node(state: AgentState) -> dict:
    """Node 1: Compute financial metrics. Depends on historical_data."""
    hist = state.get("historical_data")
    if not hist:
        return {"metrics": {}}
    
    try:
        metrics = calculate_metrics(hist)
        return {"metrics": metrics}
    except Exception as e:
        print(f"Metrics calculation error: {e}")
        return {"metrics": {}}


async def search_web_node(state: AgentState) -> dict:
    """Node 2: Search for news (Parallel Candidate)."""
    name = state["company_data"].get("company_name") or state["company_data"].get("ticker")
    # Wrap in try/except to ensure graph doesn't die on search failure
    try:
        results = get_company_news(name)
        return {"search_results": results}
    except Exception:
        return {"search_results": []}


def run_agent_node(state: AgentState) -> dict:
    """Node 3: AI Analysis. Hardened against missing metrics."""
    result = run_snapshot_agent(
        state["company_data"], 
        state.get("metrics") or {}, 
        state.get("search_results") or []
    )
    return {"analysis_result": result}


# ── Graph assembly ────────────────────────────────────────────────────────────

def build_graph() -> CompiledStateGraph:
    """
    Parallel Optimized Graph:
    START -> [fetch_data, search_web] -> calculate_metrics -> run_agent -> END
    """
    builder = StateGraph(AgentState)

    builder.add_node("fetch_data", fetch_data_node)
    builder.add_node("search_web", search_web_node)
    builder.add_node("calculate_metrics", calculate_metrics_node)
    builder.add_node("run_agent", run_agent_node)

    # 1. Start parallel tasks
    builder.add_edge(START, "fetch_data")
    builder.add_edge(START, "search_web")

    # 2. Both must flow into metrics (metrics needs data from fetch_data)
    builder.add_edge("fetch_data", "calculate_metrics")
    builder.add_edge("search_web", "calculate_metrics")

    # 3. Final steps
    builder.add_edge("calculate_metrics", "run_agent")
    builder.add_edge("run_agent", END)

    return builder.compile()


# Compiled graph
graph = build_graph()
