"""
search.py — Contains the web search logic for the agent.

Uses the `duckduckgo_search` library (free, no API key needed) 
to find recent news about the analyzed company.
"""

from duckduckgo_search import DDGS


def get_company_news(company_name: str, max_results: int = 5) -> list[dict]:
    """
    Search DuckDuckGo for recent news about a given company.
    """
    from duckduckgo_search import DDGS
    query = f"{company_name} company news"
    
    results = []
    try:
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
    except Exception as e:
        print(f"DEBUG: Search failed for '{company_name}': {e}")
        # Return an empty list if search fails so the pipeline doesn't crash
        return []
        
    return results
