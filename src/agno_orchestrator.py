"""
Agno Orchestration Framework
Central control layer managing request flow, coordination, and fallback handling.
"""

import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .mcp_tools_integration import MCPToolsFramework, ToolResult, ToolStatus
from .tools.tavily_tool import TavilyTool
from .tools.jina_tool import JinaTool
from .logging_system import get_logger


@dataclass
class AgnoResponse:
    """Response from the Agno orchestration system."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    execution_log: Optional[List[Dict[str, Any]]] = None
    feedback: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
            "execution_log": self.execution_log,
            "feedback": self.feedback
        }


class AgnoOrchestrator:
    """
    Central orchestration framework for the MCP scraping system.
    
    Responsibilities:
    - Interpret user input
    - Coordinate tool execution
    - Manage fallback mechanisms
    - Provide transparent feedback
    - Format and deliver results
    """
    
    def __init__(
        self,
        tavily_api_key: Optional[str] = None,
        jina_api_key: Optional[str] = None,
        min_confidence: float = 0.5,
        timeout: int = 30
    ):
        """
        Initialize the Agno orchestrator.
        
        Args:
            tavily_api_key: API key for Tavily (optional, reads from env)
            jina_api_key: API key for Jina (optional, reads from env)
            min_confidence: Minimum confidence threshold for results
            timeout: Request timeout in seconds
        """
        self.logger = get_logger()
        self.min_confidence = min_confidence
        self.timeout = timeout
        
        # Initialize MCP Tools Framework
        self.framework = MCPToolsFramework()
        
        # Register tools
        self._register_tools(tavily_api_key, jina_api_key)
        
        # Track orchestration metrics
        self.request_count = 0
        self.success_count = 0
        self.fallback_count = 0
        
        self.logger.info("Agno Orchestrator initialized successfully")
    
    def _register_tools(
        self,
        tavily_api_key: Optional[str],
        jina_api_key: Optional[str]
    ):
        """Register all available scraping tools."""
        # Register Tavily (primary tool)
        tavily = TavilyTool(api_key=tavily_api_key, timeout=self.timeout)
        self.framework.register_tool(tavily)
        
        # Register Jina (fallback tool)
        jina = JinaTool(api_key=jina_api_key, timeout=self.timeout)
        self.framework.register_tool(jina)
        
        # Log available tools
        available = self.framework.registry.get_available_tools()
        self.logger.info(
            f"Registered {len(available)} available tools: "
            f"{', '.join(t.name for t in available)}"
        )
    
    async def process_request(
        self,
        user_input: str,
        **kwargs
    ) -> AgnoResponse:
        """
        Process a user request with full orchestration.
        
        This is the main entry point for the system. It:
        1. Preprocesses the user input
        2. Executes tools with automatic fallback
        3. Formats the response
        4. Provides transparent feedback
        
        Args:
            user_input: Natural language query from the user
            **kwargs: Additional parameters for the tools
            
        Returns:
            AgnoResponse with results and metadata
        """
        start_time = time.time()
        self.request_count += 1
        
        self.logger.info(f"Processing request #{self.request_count}: {user_input}")
        
        # Preprocess input
        query = self._preprocess_input(user_input)
        
        # Execute with fallback mechanism
        result = await self.framework.execute_with_fallback(
            query=query,
            min_confidence=self.min_confidence,
            **kwargs
        )
        
        # Calculate total duration
        total_duration_ms = (time.time() - start_time) * 1000
        
        # Generate feedback message
        feedback = self._generate_feedback(result)
        
        # Get execution history
        execution_log = self.framework.get_execution_history()
        
        # Build response
        if result.is_success():
            self.success_count += 1
            
            response = AgnoResponse(
                success=True,
                data=result.data,
                metadata={
                    "request_number": self.request_count,
                    "duration_ms": total_duration_ms,
                    "confidence": result.confidence,
                    "source": result.metadata.get("source") if result.metadata else None,
                    "tool_duration_ms": result.duration_ms
                },
                execution_log=execution_log[-5:],  # Last 5 executions
                feedback=feedback
            )
            
            self.logger.info(
                f"Request #{self.request_count} completed successfully "
                f"in {total_duration_ms:.2f}ms"
            )
        else:
            response = AgnoResponse(
                success=False,
                error=result.error or "All scraping tools failed",
                metadata={
                    "request_number": self.request_count,
                    "duration_ms": total_duration_ms,
                },
                execution_log=execution_log[-5:],
                feedback=feedback
            )
            
            self.logger.error(
                f"Request #{self.request_count} failed: {result.error}"
            )
        
        return response
    
    def _preprocess_input(self, user_input: str) -> str:
        """
        Preprocess user input to extract search query.
        
        Args:
            user_input: Raw user input
            
        Returns:
            Processed search query
        """
        # Remove common command phrases
        query = user_input.lower()
        
        # Remove phrases like "tell me about", "find information on", etc.
        removal_phrases = [
            "tell me about ",
            "tell me the ",
            "find information on ",
            "search for ",
            "look up ",
            "get me ",
            "what is ",
            "who is ",
        ]
        
        for phrase in removal_phrases:
            if query.startswith(phrase):
                query = query[len(phrase):]
                break
        
        # Clean up
        query = query.strip()
        
        # If the original input is already clean, use it
        if not query or len(query) < 3:
            query = user_input.strip()
        
        self.logger.debug(f"Preprocessed query: '{query}'")
        
        return query
    
    def _generate_feedback(self, result: ToolResult) -> str:
        """
        Generate user-friendly feedback message.
        
        Args:
            result: The tool execution result
            
        Returns:
            Feedback message
        """
        if result.is_success():
            source = result.metadata.get("source", "Unknown") if result.metadata else "Unknown"
            
            # Check if fallback was used
            execution_history = self.framework.get_execution_history()
            if len(execution_history) > 1:
                self.fallback_count += 1
                return (
                    f"[OK] Results retrieved successfully using {source}. "
                    f"Note: Primary source was unavailable, fallback mechanism used."
                )
            else:
                return f"[OK] Results retrieved successfully from {source}."
        
        elif result.status == ToolStatus.TIMEOUT:
            return "[WARN] Request timed out. Please try again or check your connection."
        
        elif result.status == ToolStatus.NOT_FOUND:
            return "[WARN] No scraping tools are available. Please configure API keys."
        
        else:
            return f"[ERROR] Unable to retrieve results. {result.error or 'All sources failed.'}"
    
    def format_response(
        self,
        response: AgnoResponse,
        format_type: str = "structured"
    ) -> str:
        """
        Format the response for presentation.
        
        Args:
            response: The AgnoResponse to format
            format_type: Output format ("structured", "json", "markdown")
            
        Returns:
            Formatted response string
        """
        import json
        
        if format_type == "json":
            return json.dumps(response.to_dict(), indent=2)
        
        elif format_type == "markdown":
            output = "# Agno Search Results\n\n"
            
            if response.feedback:
                output += f"{response.feedback}\n\n"
            
            if response.success and response.data:
                output += "## Answer\n\n"
                answer = response.data.get("answer", "")
                if answer:
                    output += f"{answer}\n\n"
                
                output += "## Sources\n\n"
                results = response.data.get("results", [])
                for i, result in enumerate(results, 1):
                    output += f"### {i}. {result.get('title', 'Untitled')}\n\n"
                    output += f"**URL:** {result.get('url', 'N/A')}\n\n"
                    output += f"{result.get('content', 'No content')}\n\n"
                    output += "---\n\n"
            
            if response.metadata:
                output += "## Metadata\n\n"
                output += f"- **Duration:** {response.metadata.get('duration_ms', 0):.2f}ms\n"
                output += f"- **Confidence:** {response.metadata.get('confidence', 0):.2%}\n"
                output += f"- **Source:** {response.metadata.get('source', 'Unknown')}\n"
            
            return output
        
        else:  # structured
            output = []
            output.append("=" * 80)
            output.append("AGNO ORCHESTRATION SYSTEM - RESULTS")
            output.append("=" * 80)
            
            if response.feedback:
                output.append(f"\n{response.feedback}\n")
            
            if response.success and response.data:
                output.append("\nANSWER:")
                output.append("-" * 80)
                answer = response.data.get("answer", "")
                if answer:
                    output.append(answer)
                else:
                    output.append("No summary available.")
                
                output.append("\n\nSOURCES:")
                output.append("-" * 80)
                results = response.data.get("results", [])
                for i, result in enumerate(results, 1):
                    output.append(f"\n[{i}] {result.get('title', 'Untitled')}")
                    output.append(f"    URL: {result.get('url', 'N/A')}")
                    content = result.get('content', 'No content')
                    if len(content) > 200:
                        content = content[:200] + "..."
                    output.append(f"    {content}")
            
            if response.metadata:
                output.append("\n\nMETADATA:")
                output.append("-" * 80)
                output.append(f"Duration: {response.metadata.get('duration_ms', 0):.2f}ms")
                output.append(f"Confidence: {response.metadata.get('confidence', 0):.2%}")
                output.append(f"Source: {response.metadata.get('source', 'Unknown')}")
            
            output.append("\n" + "=" * 80)
            
            return "\n".join(output)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get orchestration statistics.
        
        Returns:
            Dictionary with system statistics
        """
        success_rate = (
            (self.success_count / self.request_count * 100)
            if self.request_count > 0 else 0.0
        )
        
        fallback_rate = (
            (self.fallback_count / self.request_count * 100)
            if self.request_count > 0 else 0.0
        )
        
        return {
            "total_requests": self.request_count,
            "successful_requests": self.success_count,
            "success_rate": success_rate,
            "fallback_count": self.fallback_count,
            "fallback_rate": fallback_rate,
            "available_tools": len(self.framework.registry.get_available_tools()),
            "registered_tools": len(self.framework.registry.list_tools())
        }

