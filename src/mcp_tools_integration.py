"""
MCP Tools Integration Layer
Provides unified interface for managing and executing scraping tools.
"""

from typing import Dict, Any, Optional, Callable, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import time

from .logging_system import get_logger


class ToolStatus(Enum):
    """Status of a tool execution."""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    NOT_FOUND = "not_found"


@dataclass
class ToolResult:
    """Result of a tool execution."""
    status: ToolStatus
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    confidence: float = 0.0
    metadata: Optional[Dict[str, Any]] = None
    
    def is_success(self) -> bool:
        """Check if the execution was successful."""
        return self.status == ToolStatus.SUCCESS


class BaseTool(ABC):
    """Base class for all scraping tools."""
    
    def __init__(self, name: str, priority: int = 0):
        """
        Initialize the tool.
        
        Args:
            name: Name of the tool
            priority: Priority level (lower number = higher priority)
        """
        self.name = name
        self.priority = priority
        self.logger = get_logger()
    
    @abstractmethod
    async def execute(self, query: str, **kwargs) -> ToolResult:
        """
        Execute the tool with the given query.
        
        Args:
            query: The search query
            **kwargs: Additional parameters
            
        Returns:
            ToolResult containing the execution results
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the tool is available and properly configured."""
        pass
    
    def validate_result(self, result: ToolResult, min_confidence: float = 0.5) -> bool:
        """
        Validate if the result meets quality criteria.
        
        Args:
            result: The result to validate
            min_confidence: Minimum confidence threshold
            
        Returns:
            True if the result is valid
        """
        if not result.is_success():
            return False
        
        if result.confidence < min_confidence:
            self.logger.warning(
                f"{self.name}: Low confidence result ({result.confidence:.2f})"
            )
            return False
        
        if not result.data:
            self.logger.warning(f"{self.name}: Empty data in result")
            return False
        
        return True


class ToolRegistry:
    """Registry for managing and discovering scraping tools."""
    
    def __init__(self):
        """Initialize the tool registry."""
        self.tools: Dict[str, BaseTool] = {}
        self.logger = get_logger()
    
    def register_tool(self, tool: BaseTool) -> None:
        """
        Register a tool in the registry.
        
        Args:
            tool: The tool to register
        """
        self.tools[tool.name] = tool
        self.logger.info(f"Tool registered: {tool.name} (priority: {tool.priority})")
    
    def unregister_tool(self, tool_name: str) -> None:
        """
        Unregister a tool from the registry.
        
        Args:
            tool_name: Name of the tool to unregister
        """
        if tool_name in self.tools:
            del self.tools[tool_name]
            self.logger.info(f"Tool unregistered: {tool_name}")
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        Get a tool by name.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            The tool instance or None if not found
        """
        return self.tools.get(tool_name)
    
    def get_available_tools(self) -> List[BaseTool]:
        """
        Get all available tools sorted by priority.
        
        Returns:
            List of available tools
        """
        available = [tool for tool in self.tools.values() if tool.is_available()]
        return sorted(available, key=lambda t: t.priority)
    
    def list_tools(self) -> List[str]:
        """
        List all registered tool names.
        
        Returns:
            List of tool names
        """
        return list(self.tools.keys())


class MCPToolsFramework:
    """
    Main framework for coordinating MCP tool execution.
    Handles tool registration, lifecycle, and output formatting.
    """
    
    def __init__(self):
        """Initialize the MCP Tools Framework."""
        self.registry = ToolRegistry()
        self.logger = get_logger()
        self.execution_history: List[Dict[str, Any]] = []
    
    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool with the framework."""
        self.registry.register_tool(tool)
    
    async def execute_tool(
        self,
        tool_name: str,
        query: str,
        **kwargs
    ) -> ToolResult:
        """
        Execute a specific tool by name.
        
        Args:
            tool_name: Name of the tool to execute
            query: The search query
            **kwargs: Additional parameters
            
        Returns:
            ToolResult containing execution results
        """
        start_time = time.time()
        
        tool = self.registry.get_tool(tool_name)
        if not tool:
            error_msg = f"Tool not found: {tool_name}"
            self.logger.error(error_msg)
            return ToolResult(
                status=ToolStatus.NOT_FOUND,
                error=error_msg,
                duration_ms=(time.time() - start_time) * 1000
            )
        
        if not tool.is_available():
            error_msg = f"Tool not available: {tool_name}"
            self.logger.warning(error_msg)
            return ToolResult(
                status=ToolStatus.FAILURE,
                error=error_msg,
                duration_ms=(time.time() - start_time) * 1000
            )
        
        self.logger.log_request_start(tool_name, {"query": query})
        
        try:
            result = await tool.execute(query, **kwargs)
            
            duration_ms = (time.time() - start_time) * 1000
            result.duration_ms = duration_ms
            
            self.logger.log_request_end(
                operation_name=tool_name,
                success=result.is_success(),
                duration_ms=duration_ms,
                error=result.error,
                data_quality={"confidence": result.confidence}
            )
            
            # Record execution history
            self.execution_history.append({
                "tool": tool_name,
                "query": query,
                "status": result.status.value,
                "duration_ms": duration_ms,
                "timestamp": time.time()
            })
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"Tool execution failed: {str(e)}"
            self.logger.error(error_msg)
            
            return ToolResult(
                status=ToolStatus.FAILURE,
                error=error_msg,
                duration_ms=duration_ms
            )
    
    async def execute_with_fallback(
        self,
        query: str,
        min_confidence: float = 0.5,
        **kwargs
    ) -> ToolResult:
        """
        Execute tools with automatic fallback mechanism.
        Tries tools in priority order until one succeeds.
        
        Args:
            query: The search query
            min_confidence: Minimum confidence threshold for results
            **kwargs: Additional parameters
            
        Returns:
            ToolResult from the first successful tool
        """
        available_tools = self.registry.get_available_tools()
        
        if not available_tools:
            error_msg = "No available tools found"
            self.logger.error(error_msg)
            return ToolResult(
                status=ToolStatus.NOT_FOUND,
                error=error_msg
            )
        
        self.logger.info(f"Executing query with {len(available_tools)} available tools")
        
        last_result = None
        for i, tool in enumerate(available_tools):
            self.logger.info(f"Attempting tool: {tool.name} (priority: {tool.priority})")
            
            result = await self.execute_tool(tool.name, query, **kwargs)
            
            if tool.validate_result(result, min_confidence):
                self.logger.info(f"Tool {tool.name} succeeded with confidence {result.confidence:.2f}")
                return result
            
            # Log fallback if not the last tool
            if i < len(available_tools) - 1:
                next_tool = available_tools[i + 1]
                reason = result.error or "Low confidence or invalid result"
                self.logger.log_fallback(
                    from_tool=tool.name,
                    to_tool=next_tool.name,
                    reason=reason
                )
            
            last_result = result
        
        # All tools failed
        self.logger.error("All tools failed or returned invalid results")
        return last_result or ToolResult(
            status=ToolStatus.FAILURE,
            error="All tools failed"
        )
    
    def format_output(self, result: ToolResult, format_type: str = "json") -> str:
        """
        Format tool output for presentation.
        
        Args:
            result: The result to format
            format_type: Output format ("json" or "markdown")
            
        Returns:
            Formatted string
        """
        import json
        
        if format_type == "json":
            return json.dumps({
                "status": result.status.value,
                "data": result.data,
                "error": result.error,
                "duration_ms": result.duration_ms,
                "confidence": result.confidence,
                "metadata": result.metadata
            }, indent=2)
        
        elif format_type == "markdown":
            output = f"# Result\n\n"
            output += f"**Status:** {result.status.value}\n\n"
            
            if result.is_success() and result.data:
                output += "## Data\n\n"
                output += json.dumps(result.data, indent=2)
                output += "\n\n"
            
            if result.error:
                output += f"**Error:** {result.error}\n\n"
            
            output += f"**Duration:** {result.duration_ms:.2f}ms\n"
            output += f"**Confidence:** {result.confidence:.2%}\n"
            
            return output
        
        return str(result)
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get the execution history."""
        return self.execution_history.copy()

