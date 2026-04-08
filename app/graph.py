"""
graph.py — Builds and compiles the LangGraph execution graph.

Graph flow:
    START → calculate_metrics_node → run_agent_node → END

Each node receives the shared AgentState, performs its work,
and returns a partial state update that is merged back.
"""

import sys
import os

# Ensure app/ is on the path for sibling imports
sys.path.insert(0, os.path.dirname(__file__))

from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph

from state import AgentState
from calculator import calculate_metrics
from agent import run_snapshot_agent
from search import get_company_news


# ── Node definitions ──────────────────────────────────────────────────────────

def calculate_metrics_node(state: AgentState) -> dict:
    """Node 1: Compute financial metrics from raw 5-year inputs."""
    metrics = calculate_metrics(state["historical_data"])
    query   = f"{state['company_data']['company_name']} news 2024"
    return {"metrics": metrics, "search_query": query}


def search_web_node(state: AgentState) -> dict:
    """Node 2: Search for news about the company."""
    results = get_company_news(state["company_data"]["company_name"])
    return {"search_results": results}


def run_agent_node(state: AgentState) -> dict:
    """Node 3: Call the OpenAI agent to generate a financial analysis."""
    result = run_snapshot_agent(
        state["company_data"], 
        state["metrics"], 
        state["search_results"]
    )
    return {"analysis_result": result}


# ── Graph assembly ────────────────────────────────────────────────────────────

def build_graph() -> CompiledStateGraph:
    """Construct and compile the agent graph. Returns a compiled runnable graph."""
    builder = StateGraph(AgentState)

    # Register nodes
    builder.add_node("calculate_metrics", calculate_metrics_node)
    builder.add_node("search_web", search_web_node)
    builder.add_node("run_agent", run_agent_node)

    # Parallel Execution: Start both nodes at once
    builder.add_edge(START, "calculate_metrics")
    builder.add_edge(START, "search_web")

    # Join: Both must finish before the AI starts
    builder.add_edge("calculate_metrics", "run_agent")
    builder.add_edge("search_web", "run_agent")
    builder.add_edge("run_agent", END)

    return builder.compile()


# Compiled graph — importable directly as `from graph import graph`
graph = build_graph()
