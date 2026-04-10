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


def get_company_news(company_name: str, max_results: int = 2) -> list[dict]:
    """
    Search DuckDuckGo for recent news about a given company.
    Runs with a strict 1-second timeout to prevent hanging.
    """
    import concurrent.futures

    def _fetch():
        query = f"{company_name} company news"
        results = []
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=RuntimeWarning)
                original_simplefilter = warnings.simplefilter
                try:
                    warnings.simplefilter = lambda *args, **kwargs: None
                    with DDGS() as ddgs:
                        ddgs_gen = ddgs.text(query, max_results=max_results)
                        for r in ddgs_gen:
                            results.append({
                                "title": r.get("title", "No Title"),
                                "snippet": r.get("body", "No Snippet"),
                                "link": r.get("href", "#")
                            })
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
        except Exception:
            pass
        return results

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_fetch)
        try:
            return future.result(timeout=1.5)  # Strict 1.5s timeout
        except concurrent.futures.TimeoutError:
            print(f"[SEARCH TIMEOUT] Failed to fetch news for {company_name} in 1.5s.")
            return []
