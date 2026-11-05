"""
Search Retrieval Module.
Executes targeted searches using Tavily with seamless DuckDuckGo fallback.
"""
from typing import Dict, List, Optional
from urllib.parse import urlparse, urlunparse
import logging
import time

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

from tavily import TavilyClient

from src.models import SearchResult, ResolvedEntity

logger = logging.getLogger(__name__)


def clean_url(url: str) -> str:
    """Normalizes URL by stripping query tracking params and fragments."""
    try:
        parsed = urlparse(url)
        clean_path = parsed.path.rstrip("/")
        return urlunparse((parsed.scheme, parsed.netloc.lower(), clean_path, "", "", ""))
    except Exception:
        return url.strip()


class SearchRetriever:
    """Manages search queries across Tavily and DuckDuckGo."""

    def __init__(self, tavily_api_key: Optional[str] = None):
        self.tavily_api_key = tavily_api_key.strip() if tavily_api_key else None
        self.tavily_client = None
        if self.tavily_api_key:
            try:
                self.tavily_client = TavilyClient(api_key=self.tavily_api_key)
            except Exception as e:
                logger.warning(f"Could not initialize Tavily client: {e}")
                self.tavily_client = None

    def search_category_tavily(self, category: str, query: str) -> List[SearchResult]:
        """Runs a category search via Tavily."""
        if not self.tavily_client:
            return []

        results: List[SearchResult] = []
        try:
            if category == "snapshot":
                res = self.tavily_client.search(
                    query=query,
                    topic="general",
                    max_results=3,
                    search_depth="basic"
                )
            else:
                res = self.tavily_client.search(
                    query=query,
                    topic="news",
                    time_range="month",
                    days=30,
                    max_results=5,
                    search_depth="basic"
                )

            for item in res.get("results", []):
                results.append(
                    SearchResult(
                        title=item.get("title", "Untitled"),
                        url=item.get("url", ""),
                        snippet=item.get("content", ""),
                        published_date=item.get("published_date"),
                        engine="tavily",
                        query_category=category
                    )
                )
        except Exception as e:
            logger.warning(f"Tavily search failed for '{query}': {e}. Falling back to DuckDuckGo.")
            return []

        return results

    def search_category_ddg(self, category: str, query: str) -> List[SearchResult]:
        """Runs a category search via DuckDuckGo with gentle pacing and fallback."""
        results: List[SearchResult] = []
        ddgs = DDGS()

        # Simplify query to most effective keywords
        simplified_query = query.replace(" OR ", " ")

        try:
            if category == "snapshot":
                raw = list(ddgs.text(simplified_query, max_results=3))
                for item in raw:
                    results.append(
                        SearchResult(
                            title=item.get("title", "Untitled"),
                            url=item.get("href", ""),
                            snippet=item.get("body", ""),
                            published_date=None,
                            engine="duckduckgo",
                            query_category=category
                        )
                    )
            else:
                try:
                    # Attempt news endpoint with 30-day scope (timelimit='m')
                    raw_news = list(ddgs.news(simplified_query, max_results=4, timelimit="m"))
                    for item in raw_news:
                        results.append(
                            SearchResult(
                                title=item.get("title", "Untitled"),
                                url=item.get("url", ""),
                                snippet=item.get("body", ""),
                                published_date=item.get("date"),
                                engine="duckduckgo",
                                query_category=category
                            )
                        )
                except Exception as news_err:
                    logger.debug(f"DDG news endpoint notice: {news_err}, falling back to web text search")

                # If news returned fewer than 2 items, try text search
                if len(results) < 2:
                    time.sleep(0.5)
                    raw_text = list(ddgs.text(simplified_query, max_results=3, timelimit="m"))
                    for item in raw_text:
                        results.append(
                            SearchResult(
                                title=item.get("title", "Untitled"),
                                url=item.get("href", ""),
                                snippet=item.get("body", ""),
                                published_date=None,
                                engine="duckduckgo",
                                query_category=category
                            )
                        )
        except Exception as e:
            logger.warning(f"DuckDuckGo search error for '{query}': {e}")

        return results

    def retrieve_all(
        self,
        queries: Dict[str, str],
        on_progress=None
    ) -> List[SearchResult]:
        """
        Executes searches for all 4 blueprint categories, deduplicating by URL.
        """
        all_results: List[SearchResult] = []
        seen_urls = set()

        categories = ["snapshot", "news", "hires_departures", "launches_funding"]

        for idx, cat in enumerate(categories):
            query = queries.get(cat, "")
            if not query:
                continue

            if on_progress:
                on_progress(f"Searching ({cat.replace('_', ' ').title()})...", (idx + 1) / len(categories))

            cat_results: List[SearchResult] = []

            # 1. Try Tavily if available
            if self.tavily_client:
                cat_results = self.search_category_tavily(cat, query)

            # 2. Fall back to DuckDuckGo if Tavily returned nothing or was not provided
            if not cat_results:
                if idx > 0:
                    time.sleep(0.8)
                cat_results = self.search_category_ddg(cat, query)

            for r in cat_results:
                if not r.url or not r.snippet:
                    continue
                norm_url = clean_url(r.url)
                if norm_url not in seen_urls:
                    seen_urls.add(norm_url)
                    all_results.append(r)

        return all_results
