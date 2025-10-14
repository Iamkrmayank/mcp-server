"""
Jina API Tool
Semantic web understanding and retrieval tool (fallback scraping method).
"""

import os
import httpx
from typing import Dict, Any, Optional

from ..mcp_tools_integration import BaseTool, ToolResult, ToolStatus
from ..logging_system import get_logger


class JinaTool(BaseTool):
    """
    Jina API integration for semantic web scraping and understanding.
    This is the fallback tool with lower priority than Tavily.
    """
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        """
        Initialize the Jina tool.
        
        Args:
            api_key: Jina API key (defaults to JINA_API_KEY env var)
            timeout: Request timeout in seconds
        """
        super().__init__(name="Jina", priority=1)  # Lower priority than Tavily
        self.api_key = api_key or os.getenv("JINA_API_KEY")
        self.timeout = timeout
        self.search_url = "https://s.jina.ai/"
        self.reader_url = "https://r.jina.ai/"
        self.logger = get_logger()
    
    def is_available(self) -> bool:
        """Check if Jina API is configured and available."""
        # Jina API can work without API key but with rate limits
        # Return True if we have an API key, or True for basic functionality
        return True  # Jina's reader API works without auth
    
    async def execute(self, query: str, **kwargs) -> ToolResult:
        """
        Execute a Jina search and content extraction request.
        
        Args:
            query: The search query
            **kwargs: Additional parameters:
                - max_results: Maximum number of results (default: 5)
                - use_reader: Whether to use the reader API for content extraction
                
        Returns:
            ToolResult containing search results
        """
        try:
            self.logger.info(f"Jina: Executing search for query: {query}")
            
            # Use Jina Search API to find relevant URLs
            search_results = await self._search(query, **kwargs)
            
            if not search_results:
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    error="Jina search returned no results"
                )
            
            # Format results
            results = {
                "query": query,
                "answer": self._generate_answer(search_results),
                "results": search_results
            }
            
            # Calculate confidence
            confidence = self._calculate_confidence(results)
            
            self.logger.info(
                f"Jina: Retrieved {len(results['results'])} results "
                f"with confidence {confidence:.2f}"
            )
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=results,
                confidence=confidence,
                metadata={
                    "source": "Jina",
                    "result_count": len(results["results"])
                }
            )
        
        except httpx.TimeoutException:
            error_msg = f"Jina request timeout after {self.timeout}s"
            self.logger.error(error_msg)
            return ToolResult(
                status=ToolStatus.TIMEOUT,
                error=error_msg
            )
        
        except Exception as e:
            error_msg = f"Jina execution failed: {str(e)}"
            self.logger.error(error_msg)
            return ToolResult(
                status=ToolStatus.FAILURE,
                error=error_msg
            )
    
    async def _search(self, query: str, **kwargs) -> list:
        """
        Perform a Jina search.
        
        Args:
            query: Search query
            **kwargs: Additional parameters
            
        Returns:
            List of search results
        """
        max_results = kwargs.get("max_results", 5)
        
        # Prepare headers
        headers = {
            "Accept": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        # For Jina, we'll use their search endpoint
        # The query format is: https://s.jina.ai/{query}
        search_query = query.replace(" ", "+")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.search_url}{search_query}",
                headers=headers,
                params={"n": max_results}
            )
            
            if response.status_code != 200:
                self.logger.warning(
                    f"Jina search returned status {response.status_code}, "
                    f"falling back to alternative method"
                )
                # Fallback: use reader API with a general search
                return await self._fallback_search(query, max_results)
            
            data = response.json()
            
            # Parse Jina search results
            results = []
            for item in data.get("data", [])[:max_results]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", item.get("description", "")),
                    "score": item.get("score", 0.8)  # Default score for Jina
                })
            
            return results
    
    async def _fallback_search(self, query: str, max_results: int = 5) -> list:
        """
        Fallback search method using simulated results.
        
        In a production environment, this could:
        - Use Google/Bing search APIs
        - Query a local index
        - Use cached results
        
        Args:
            query: Search query
            max_results: Maximum results
            
        Returns:
            List of search results
        """
        self.logger.info("Jina: Using fallback search method")
        
        # For demo purposes, we'll construct a search URL and use the reader
        # In production, integrate with actual search APIs
        
        # Simulate search results for common queries
        results = []
        
        # Try to extract meaningful URLs from the query
        if "microsoft" in query.lower():
            urls = [
                "https://www.microsoft.com/investor",
                "https://www.microsoft.com/en-us/Investor/annual-reports.aspx",
            ]
        elif "report" in query.lower() or "annual" in query.lower():
            urls = []  # Would need actual search implementation
        else:
            urls = []
        
        # Use reader API to extract content from URLs
        for url in urls[:max_results]:
            content = await self._read_url(url)
            if content:
                results.append({
                    "title": f"Report from {url}",
                    "url": url,
                    "content": content[:500],  # Truncate for summary
                    "score": 0.7
                })
        
        return results
    
    async def _read_url(self, url: str) -> Optional[str]:
        """
        Use Jina Reader API to extract content from a URL.
        
        Args:
            url: URL to read
            
        Returns:
            Extracted content or None
        """
        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.reader_url}{url}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    return response.text
        except Exception as e:
            self.logger.warning(f"Jina reader failed for {url}: {str(e)}")
        
        return None
    
    def _generate_answer(self, search_results: list) -> str:
        """
        Generate a summary answer from search results.
        
        Args:
            search_results: List of search results
            
        Returns:
            Summary answer
        """
        if not search_results:
            return ""
        
        # Combine top results into a summary
        top_contents = [r.get("content", "") for r in search_results[:3]]
        answer = " ".join(top_contents)
        
        # Truncate if too long
        max_length = 500
        if len(answer) > max_length:
            answer = answer[:max_length] + "..."
        
        return answer
    
    def _calculate_confidence(self, results: Dict[str, Any]) -> float:
        """
        Calculate confidence score based on result quality.
        
        Args:
            results: The search results
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not results.get("results"):
            return 0.0
        
        result_list = results["results"]
        num_results = len(result_list)
        
        # Number of results factor (0.0 - 0.4)
        num_factor = min(num_results / 5.0, 1.0) * 0.4
        
        # Average score factor (0.0 - 0.4)
        avg_score = sum(r.get("score", 0.0) for r in result_list) / num_results
        score_factor = avg_score * 0.4
        
        # Answer presence factor (0.0 - 0.2)
        answer_factor = 0.2 if results.get("answer") else 0.0
        
        # Jina typically has slightly lower confidence than Tavily
        total_confidence = (num_factor + score_factor + answer_factor) * 0.9
        
        return min(total_confidence, 1.0)

