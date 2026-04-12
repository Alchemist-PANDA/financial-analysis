"""
state.py — Defines the shared state schema used by the agent graph.

AgentState is passed through every node in the LangGraph graph.
Each field is populated incrementally as the graph executes.
"""

from typing import TypedDict, Optional


class AgentState(TypedDict):
    """Shared mutable state passed between graph nodes."""

    # General company metadata (e.g., name, sector)
    company_data: dict

    # 5-year historical financial dataset (Y-4 through Y0)
    historical_data: Optional[list[dict]]

    # Calculated financial metrics and trends produced by the calculator node
    metrics: Optional[dict]

    # The search query we use to find news
    search_query: str

    # News search results from DuckDuckGo
    search_results: Optional[list[dict]]

    # Final structured analysis returned by the LLM agent node
    analysis_result: Optional[dict]
