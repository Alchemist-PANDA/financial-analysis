"""
search.py — Contains the web search logic for the agent.

Uses the `duckduckgo_search` library (free, no API key needed) 
to find recent news about the analyzed company.
"""

import warnings

from duckduckgo_search import DDGS

# Suppress upstream deprecation noise; functionality remains unchanged.
warnings.filterwarnings(
    "ignore",
    category=RuntimeWarning,
)


def get_company_news(company_name: str, max_results: int = 5) -> list[dict]:
    """
    Search DuckDuckGo for recent news about a given company.
    """
    from duckduckgo_search import DDGS
    query = f"{company_name} company news"
    
    results = []
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            original_simplefilter = warnings.simplefilter
            try:
                # The package forcibly sets "always" before warning; neutralize that call.
                warnings.simplefilter = lambda *args, **kwargs: None
                with DDGS() as ddgs:
                    # Try general text search first
                    ddgs_gen = ddgs.text(query, max_results=max_results)
                    for r in ddgs_gen:
                        results.append({
                            "title": r.get("title", "No Title"),
                            "snippet": r.get("body", "No Snippet"),
                            "link": r.get("href", "#")
                        })
                    
                    # If still empty, try specifically news search
                    if not results:
                        ddgs_news = ddgs.news(query, max_results=max_results)
                        for r in ddgs_news:
                            results.append({
                                "title": r.get("title", "No Title"),
                                "snippet": r.get("body", "No Snippet"),
                                "link": r.get("url", "#")
                            })
            finally:
                warnings.simplefilter = original_simplefilter
    except Exception as e:
        print(f"DEBUG: Search failed for '{company_name}': {e}")
        # Return an empty list if search fails so the pipeline doesn't crash
        return []
        
    return results
