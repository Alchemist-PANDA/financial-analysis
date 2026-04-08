"""
__init__.py — Public API for the `app` package.

NOTE: These imports use relative paths (dot notation).
      They work when `app` is imported as a package from outside.
      When running main.py directly from inside app/, Python uses
      absolute imports instead — that is the normal behaviour.
"""

# Only expose symbols when app is imported as a package (e.g. from tests)
# Running main.py directly inside app/ does NOT use this file.
try:
    from .graph import graph
    from .state import AgentState
    from .sample_data import SAMPLE_COMPANY
    from .calculator import calculate_metrics
    from .agent import run_snapshot_agent
    from .search import get_company_news

    __all__ = [
        "graph",
        "AgentState",
        "SAMPLE_COMPANY",
        "calculate_metrics",
        "run_snapshot_agent",
        "get_company_news",
    ]
except ImportError:
    # Silently skip when running scripts directly inside the app/ folder
    pass
