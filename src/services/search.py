from duckduckgo_search import DDGS
from typing import Optional
import asyncio
from src.utils import get_logger

logger = get_logger("search_service")


class SearchService:
    def __init__(self):
        pass
    
    async def search_web(self, query: str, max_results: int = 5) -> list[dict]:
        try:
            def _search():
                with DDGS() as ddgs:
                    return list(ddgs.text(query, max_results=max_results))
            
            results = await asyncio.to_thread(_search)
            
            logger.info_ctx(
                f"Web search completed: {query}",
                action="web_search",
                extra_data={"query": query, "results_count": len(results)}
            )
            
            return results
            
        except Exception as e:
            logger.error_ctx(f"Search error: {str(e)}", action="search_error")
            return []
    
    async def search_news(self, query: str, max_results: int = 5) -> list[dict]:
        try:
            def _search_news():
                with DDGS() as ddgs:
                    return list(ddgs.news(query, max_results=max_results))
            
            results = await asyncio.to_thread(_search_news)
            
            logger.info_ctx(
                f"News search completed: {query}",
                action="news_search",
                extra_data={"query": query, "results_count": len(results)}
            )
            
            return results
            
        except Exception as e:
            logger.error_ctx(f"News search error: {str(e)}", action="news_search_error")
            return []
    
    async def search_with_ai_context(self, query: str) -> Optional[str]:
        results = await self.search_web(query, max_results=5)
        
        if not results:
            return None
        
        context_parts = []
        for i, result in enumerate(results, 1):
            title = result.get("title", "")
            body = result.get("body", "")
            url = result.get("href", "")
            context_parts.append(f"[{i}] {title}\n{body}\nURL: {url}")
        
        return "\n\n".join(context_parts)
