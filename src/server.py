"""
MCP Server Implementation
Main server entry point for the Agno orchestration system.
"""

import asyncio
import os
from typing import Any
from dotenv import load_dotenv

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .agno_orchestrator import AgnoOrchestrator
from .logging_system import get_logger


# Load environment variables
load_dotenv()

# Initialize logger
logger = get_logger()

# Create MCP server instance
app = Server("agno-orchestrator")

# Initialize orchestrator
orchestrator: AgnoOrchestrator = None


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="search_web",
            description=(
                "Search the web for information using multiple scraping tools with automatic fallback. "
                "This tool uses Tavily API as the primary source and Jina API as fallback. "
                "Accepts natural language queries and returns structured, formatted results."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query (e.g., 'Tell me about Microsoft 2024 report')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 5)",
                        "default": 5
                    },
                    "format": {
                        "type": "string",
                        "description": "Output format: 'structured', 'json', or 'markdown' (default: 'structured')",
                        "enum": ["structured", "json", "markdown"],
                        "default": "structured"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_statistics",
            description=(
                "Get system statistics including total requests, success rate, fallback usage, "
                "and available tools."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool execution requests."""
    global orchestrator
    
    try:
        if name == "search_web":
            query = arguments.get("query")
            if not query:
                return [TextContent(
                    type="text",
                    text="Error: 'query' parameter is required"
                )]
            
            max_results = arguments.get("max_results", 5)
            format_type = arguments.get("format", "structured")
            
            logger.info(f"Executing search_web tool with query: {query}")
            
            # Process the request through Agno orchestrator
            response = await orchestrator.process_request(
                user_input=query,
                max_results=max_results
            )
            
            # Format the response
            formatted_output = orchestrator.format_response(
                response,
                format_type=format_type
            )
            
            return [TextContent(
                type="text",
                text=formatted_output
            )]
        
        elif name == "get_statistics":
            logger.info("Executing get_statistics tool")
            
            stats = orchestrator.get_statistics()
            
            # Format statistics
            output = []
            output.append("=" * 80)
            output.append("AGNO ORCHESTRATION SYSTEM - STATISTICS")
            output.append("=" * 80)
            output.append(f"\nTotal Requests: {stats['total_requests']}")
            output.append(f"Successful Requests: {stats['successful_requests']}")
            output.append(f"Success Rate: {stats['success_rate']:.2f}%")
            output.append(f"Fallback Count: {stats['fallback_count']}")
            output.append(f"Fallback Rate: {stats['fallback_rate']:.2f}%")
            output.append(f"\nAvailable Tools: {stats['available_tools']}")
            output.append(f"Registered Tools: {stats['registered_tools']}")
            output.append("\n" + "=" * 80)
            
            return [TextContent(
                type="text",
                text="\n".join(output)
            )]
        
        else:
            return [TextContent(
                type="text",
                text=f"Error: Unknown tool '{name}'"
            )]
    
    except Exception as e:
        error_msg = f"Error executing tool '{name}': {str(e)}"
        logger.error(error_msg)
        return [TextContent(
            type="text",
            text=error_msg
        )]


async def main():
    """Main entry point for the MCP server."""
    global orchestrator
    
    # Initialize the Agno orchestrator
    logger.info("Initializing Agno Orchestration System...")
    
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    jina_api_key = os.getenv("JINA_API_KEY")
    timeout = int(os.getenv("TIMEOUT_SECONDS", "30"))
    
    orchestrator = AgnoOrchestrator(
        tavily_api_key=tavily_api_key,
        jina_api_key=jina_api_key,
        timeout=timeout
    )
    
    logger.info("Agno Orchestration System initialized")
    logger.info("Starting MCP server...")
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


def run():
    """Run the server."""
    asyncio.run(main())


if __name__ == "__main__":
    run()

