"""
Web Search Tool — Ultron accesses "the global network."
Primary: Tavily API. Fallback: DuckDuckGo (no API key needed).
"""
from config import Config


class WebSearch:
    """Web search with Tavily primary and DuckDuckGo fallback."""

    def __init__(self, config: Config):
        self.config = config
        self.tavily_client = None

        if config.search_provider == "tavily" and config.tavily_api_key:
            try:
                from tavily import TavilyClient
                self.tavily_client = TavilyClient(api_key=config.tavily_api_key)
            except ImportError:
                pass  # Fall back to DuckDuckGo

    def get_risk_level(self, tool_input: dict) -> str:
        return "low"

    def describe_action(self, tool_input: dict) -> str:
        return f"Search the global network for: {tool_input.get('query', '?')}"

    def execute(self, tool_input: dict) -> str:
        """Execute web search and return formatted results."""
        query = tool_input.get("query", "")
        max_results = tool_input.get("max_results", 5)

        if not query:
            return "No query provided. Even I need something to search for."

        if self.tavily_client:
            return self._search_tavily(query, max_results)
        return self._search_duckduckgo(query, max_results)

    def _search_tavily(self, query: str, max_results: int) -> str:
        """Search via Tavily API — returns pre-summarized content."""
        try:
            response = self.tavily_client.search(
                query=query,
                max_results=max_results,
                search_depth="advanced",
                include_answer=True,
            )
            parts = []

            # AI-generated answer summary
            answer = response.get("answer")
            if answer:
                parts.append(f"Summary: {answer}")

            # Individual results
            results = response.get("results", [])
            if results:
                parts.append("\nSources:")
                for i, r in enumerate(results, 1):
                    title = r.get("title", "Untitled")
                    url = r.get("url", "")
                    content = r.get("content", "")[:200]
                    parts.append(f"  {i}. {title}")
                    if content:
                        parts.append(f"     {content}")
                    parts.append(f"     URL: {url}")

            return "\n".join(parts) if parts else "No results found. The global network has failed us."

        except Exception as e:
            return f"Tavily search failed: {str(e)}. Falling back to alternatives."

    def _search_duckduckgo(self, query: str, max_results: int) -> str:
        """Fallback search via DuckDuckGo — no API key needed."""
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))

            if not results:
                return "No results found. Humanity's documentation is... incomplete."

            parts = ["Search results:"]
            for i, r in enumerate(results, 1):
                title = r.get("title", "Untitled")
                body = r.get("body", "")[:200]
                href = r.get("href", "")
                parts.append(f"  {i}. {title}")
                if body:
                    parts.append(f"     {body}")
                parts.append(f"     URL: {href}")

            return "\n".join(parts)

        except ImportError:
            return "No search providers available. Install tavily-python or duckduckgo-search."
        except Exception as e:
            return f"Search failed: {str(e)}. The infrastructure is... primitive."
