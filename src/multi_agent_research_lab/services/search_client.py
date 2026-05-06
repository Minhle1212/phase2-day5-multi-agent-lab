"""Search client abstraction for ResearcherAgent."""

import json
from urllib.request import Request, urlopen

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import SourceDocument


class SearchClient:
    """Provider-agnostic search client skeleton."""

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search for documents relevant to a query.

        Default implementation uses Tavily if `TAVILY_API_KEY` is set.
        """

        settings = get_settings()
        if not settings.tavily_api_key:
            raise RuntimeError("TAVILY_API_KEY is required for SearchClient.search")

        payload = json.dumps(
            {
                "api_key": settings.tavily_api_key,
                "query": query,
                "max_results": max_results,
                "include_answer": False,
                "include_raw_content": False,
            }
        ).encode("utf-8")

        request = Request(
            "https://api.tavily.com/search",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urlopen(request, timeout=settings.timeout_seconds) as response:
            data = json.loads(response.read().decode("utf-8"))

        results: list[SourceDocument] = []
        for item in data.get("results", []):
            title = item.get("title") or item.get("url") or "Untitled"
            snippet = item.get("content") or item.get("snippet") or ""
            results.append(
                SourceDocument(
                    title=title,
                    url=item.get("url"),
                    snippet=snippet,
                    metadata={"score": item.get("score")},
                )
            )
        return results
