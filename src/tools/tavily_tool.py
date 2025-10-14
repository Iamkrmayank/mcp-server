"""
Tavily API Tool
Fast, structured web extraction tool (primary scraping method).
"""

import os
import httpx
from typing import Dict, Any, Optional

from ..mcp_tools_integration import BaseTool, ToolResult, ToolStatus
from ..logging_system import get_logger


class TavilyTool(BaseTool):
    """
    Tavily API integration for fast web scraping and data extraction.
    This is the primary tool with highest priority.
    """
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        """
        Initialize the Tavily tool.
        
        Args:
            api_key: Tavily API key (defaults to TAVILY_API_KEY env var)
            timeout: Request timeout in seconds
        """
        super().__init__(name="Tavily", priority=0)  # Highest priority
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self.timeout = timeout
        self.base_url = "https://api.tavily.com"
        self.logger = get_logger()
    
    def is_available(self) -> bool:
        """Check if Tavily API is configured and available."""
        return bool(self.api_key)
    
    async def execute(self, query: str, **kwargs) -> ToolResult:
        """
        Execute a Tavily search request.
        
        Args:
            query: The search query
            **kwargs: Additional parameters:
                - search_depth: "basic" or "advanced" (default: "basic")
                - max_results: Maximum number of results (default: 5)
                - include_domains: List of domains to include
                - exclude_domains: List of domains to exclude
                
        Returns:
            ToolResult containing search results
        """
        if not self.is_available():
            return ToolResult(
                status=ToolStatus.FAILURE,
                error="Tavily API key not configured"
            )
        
        # Prepare request
        search_depth = kwargs.get("search_depth", "basic")
        max_results = kwargs.get("max_results", 5)
        include_domains = kwargs.get("include_domains", [])
        exclude_domains = kwargs.get("exclude_domains", [])
        
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": search_depth,
            "max_results": max_results,
            "include_answer": True,
            "include_raw_content": False,
            "include_images": False
        }
        
        if include_domains:
            payload["include_domains"] = include_domains
        if exclude_domains:
            payload["exclude_domains"] = exclude_domains
        
        try:
            self.logger.info(f"Tavily: Executing search for query: {query}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/search",
                    json=payload
                )
                
                if response.status_code != 200:
                    error_msg = f"Tavily API error: {response.status_code} - {response.text}"
                    self.logger.error(error_msg)
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error=error_msg
                    )
                
                data = response.json()
                
                # Extract and format results
                results = {
                    "query": query,
                    "answer": data.get("answer", ""),
                    "results": []
                }
                
                for result in data.get("results", []):
                    results["results"].append({
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "content": result.get("content", ""),
                        "score": result.get("score", 0.0)
                    })
                
                # Calculate confidence based on number of results and scores
                confidence = self._calculate_confidence(results)
                
                self.logger.info(
                    f"Tavily: Retrieved {len(results['results'])} results "
                    f"with confidence {confidence:.2f}"
                )
                
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=results,
                    confidence=confidence,
                    metadata={
                        "source": "Tavily",
                        "search_depth": search_depth,
                        "result_count": len(results["results"])
                    }
                )
        
        except httpx.TimeoutException:
            error_msg = f"Tavily request timeout after {self.timeout}s"
            self.logger.error(error_msg)
            return ToolResult(
                status=ToolStatus.TIMEOUT,
                error=error_msg
            )
        
        except Exception as e:
            error_msg = f"Tavily execution failed: {str(e)}"
            self.logger.error(error_msg)
            return ToolResult(
                status=ToolStatus.FAILURE,
                error=error_msg
            )
    
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
        
        # Base confidence on:
        # 1. Number of results (more is better)
        # 2. Average score of results
        # 3. Presence of answer
        
        result_list = results["results"]
        num_results = len(result_list)
        
        # Number of results factor (0.0 - 0.4)
        num_factor = min(num_results / 5.0, 1.0) * 0.4
        
        # Average score factor (0.0 - 0.4)
        avg_score = sum(r.get("score", 0.0) for r in result_list) / num_results
        score_factor = avg_score * 0.4
        
        # Answer presence factor (0.0 - 0.2)
        answer_factor = 0.2 if results.get("answer") else 0.0
        
        total_confidence = num_factor + score_factor + answer_factor
        
        return min(total_confidence, 1.0)

