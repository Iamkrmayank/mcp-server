"""
Production MCP Server
Enhanced server with concurrency, rate limiting, caching, and monitoring.
"""

import asyncio
import os
import time
from typing import Any, Dict, Optional
from dotenv import load_dotenv

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

try:
    from .production_orchestrator import ProductionOrchestrator, RateLimitConfig, MemoryConfig
    from .cache_manager import CacheManager, CacheConfig, MemoryCacheManager
    from .logging_system import get_logger
except ImportError:
    from production_orchestrator import ProductionOrchestrator, RateLimitConfig, MemoryConfig
    from cache_manager import CacheManager, CacheConfig, MemoryCacheManager
    from logging_system import get_logger


# Load environment variables
load_dotenv()

# Initialize logger
logger = get_logger()

# Create MCP server instance
app = Server("agno-production-server")

# Initialize production components
production_orchestrator: ProductionOrchestrator = None
cache_manager = None


def get_production_config() -> Dict[str, Any]:
    """Get production configuration from environment variables."""
    return {
        "rate_limiting": {
            "max_requests_per_minute": int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
            "max_requests_per_hour": int(os.getenv("RATE_LIMIT_PER_HOUR", "1000")),
            "max_concurrent_requests": int(os.getenv("MAX_CONCURRENT_REQUESTS", "100")),
            "burst_limit": int(os.getenv("BURST_LIMIT", "10"))
        },
        "memory": {
            "max_execution_history": int(os.getenv("MAX_EXECUTION_HISTORY", "1000")),
            "max_request_size_mb": int(os.getenv("MAX_REQUEST_SIZE_MB", "10")),
            "cleanup_interval_seconds": int(os.getenv("CLEANUP_INTERVAL_SECONDS", "300"))
        },
        "caching": {
            "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
            "default_ttl": int(os.getenv("CACHE_TTL_SECONDS", "3600")),
            "max_cache_size_mb": int(os.getenv("MAX_CACHE_SIZE_MB", "100")),
            "enable_compression": os.getenv("CACHE_COMPRESSION", "true").lower() == "true"
        },
        "api": {
            "tavily_api_key": os.getenv("TAVILY_API_KEY"),
            "jina_api_key": os.getenv("JINA_API_KEY"),
            "timeout_seconds": int(os.getenv("TIMEOUT_SECONDS", "30")),
            "min_confidence": float(os.getenv("MIN_CONFIDENCE", "0.5"))
        }
    }


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools with production enhancements."""
    return [
        Tool(
            name="search_web",
            description=(
                "Search the web for information using multiple scraping tools with automatic fallback. "
                "This tool uses Tavily API as the primary source and Jina API as fallback. "
                "Accepts natural language queries and returns structured, formatted results. "
                "Production version includes rate limiting, caching, and concurrency management."
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
                    },
                    "client_id": {
                        "type": "string",
                        "description": "Client identifier for rate limiting (optional)",
                        "default": "default"
                    },
                    "use_cache": {
                        "type": "boolean",
                        "description": "Whether to use cached results (default: true)",
                        "default": True
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_statistics",
            description=(
                "Get comprehensive system statistics including production metrics, "
                "rate limiting stats, memory usage, and cache performance."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_health_status",
            description=(
                "Get system health status for monitoring and alerting. "
                "Returns detailed health checks for all components."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="clear_cache",
            description=(
                "Clear the cache for specific queries or all cached data. "
                "Useful for testing or when data needs to be refreshed."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query_pattern": {
                        "type": "string",
                        "description": "Pattern to match for cache invalidation (optional, clears all if not provided)"
                    }
                },
                "required": []
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool execution requests with production enhancements."""
    global production_orchestrator, cache_manager
    
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
            client_id = arguments.get("client_id", "default")
            use_cache = arguments.get("use_cache", True)
            
            logger.info(f"Executing search_web tool with query: {query} (client: {client_id})")
            
            # Check cache first if enabled
            if use_cache and cache_manager:
                cached_result = await cache_manager.get_cached_result(
                    query, 
                    max_results=max_results,
                    format=format_type
                )
                if cached_result:
                    logger.info(f"Returning cached result for query: {query[:50]}...")
                    return [TextContent(
                        type="text",
                        text=cached_result["result"]
                    )]
            
            # Process the request through production orchestrator
            response = await production_orchestrator.process_request(
                user_input=query,
                max_results=max_results,
                client_id=client_id
            )
            
            # Format the response
            formatted_output = production_orchestrator.base_orchestrator.format_response(
                response,
                format_type=format_type
            )
            
            # Cache the result if caching is enabled
            if use_cache and cache_manager and response.success:
                await cache_manager.cache_result(
                    query,
                    {"result": formatted_output},
                    max_results=max_results,
                    format=format_type
                )
            
            return [TextContent(
                type="text",
                text=formatted_output
            )]
        
        elif name == "get_statistics":
            logger.info("Executing get_statistics tool")
            
            stats = production_orchestrator.get_system_stats()
            
            # Add cache statistics if available
            if cache_manager:
                cache_stats = await cache_manager.get_cache_stats()
                stats["cache_metrics"] = cache_stats
            
            # Format statistics
            output = []
            output.append("=" * 80)
            output.append("AGNO PRODUCTION SYSTEM - COMPREHENSIVE STATISTICS")
            output.append("=" * 80)
            output.append(f"\n📊 REQUEST METRICS:")
            output.append(f"  Total Requests: {stats['total_requests']}")
            output.append(f"  Successful Requests: {stats['successful_requests']}")
            output.append(f"  Success Rate: {stats['success_rate']:.2f}%")
            output.append(f"  Fallback Count: {stats['fallback_count']}")
            output.append(f"  Fallback Rate: {stats['fallback_rate']:.2f}%")
            
            if "production_metrics" in stats:
                prod_metrics = stats["production_metrics"]
                output.append(f"\n🚀 PRODUCTION METRICS:")
                output.append(f"  Active Requests: {prod_metrics['active_requests']}")
                output.append(f"  Max Concurrent: {prod_metrics['max_concurrent']}")
                output.append(f"  Unique Clients: {prod_metrics['rate_limiter_stats']['unique_clients']}")
                output.append(f"  Requests/Minute: {prod_metrics['rate_limiter_stats']['total_requests_minute']}")
                output.append(f"  Requests/Hour: {prod_metrics['rate_limiter_stats']['total_requests_hour']}")
                output.append(f"  Execution History: {prod_metrics['memory_stats']['execution_history_size']}")
            
            if "cache_metrics" in stats:
                cache_metrics = stats["cache_metrics"]
                output.append(f"\n💾 CACHE METRICS:")
                output.append(f"  Status: {cache_metrics.get('status', 'unknown')}")
                output.append(f"  Total Keys: {cache_metrics.get('total_keys', 0)}")
                if "memory_usage" in cache_metrics:
                    output.append(f"  Memory Usage: {cache_metrics['memory_usage']}")
            
            output.append(f"\n🔧 SYSTEM INFO:")
            output.append(f"  Available Tools: {stats['available_tools']}")
            output.append(f"  Registered Tools: {stats['registered_tools']}")
            output.append("\n" + "=" * 80)
            
            return [TextContent(
                type="text",
                text="\n".join(output)
            )]
        
        elif name == "get_health_status":
            logger.info("Executing get_health_status tool")
            
            health_status = production_orchestrator.get_health_status()
            
            # Add cache health if available
            if cache_manager:
                cache_stats = await cache_manager.get_cache_stats()
                health_status["cache_health"] = cache_stats
            
            # Format health status
            output = []
            output.append("=" * 80)
            output.append("AGNO PRODUCTION SYSTEM - HEALTH STATUS")
            output.append("=" * 80)
            output.append(f"\n🏥 OVERALL STATUS: {health_status['status'].upper()}")
            output.append(f"  Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(health_status['timestamp']))}")
            
            if "checks" in health_status:
                output.append(f"\n🔍 COMPONENT CHECKS:")
                for component, status in health_status["checks"].items():
                    emoji = "✅" if status == "healthy" else "⚠️" if status == "warning" else "❌"
                    output.append(f"  {emoji} {component.replace('_', ' ').title()}: {status}")
            
            if "metrics" in health_status:
                output.append(f"\n📈 CURRENT METRICS:")
                for metric, value in health_status["metrics"].items():
                    output.append(f"  {metric.replace('_', ' ').title()}: {value}")
            
            if "cache_health" in health_status:
                cache_health = health_status["cache_health"]
                output.append(f"\n💾 CACHE HEALTH:")
                output.append(f"  Status: {cache_health.get('status', 'unknown')}")
                if "total_keys" in cache_health:
                    output.append(f"  Total Keys: {cache_health['total_keys']}")
            
            if "error" in health_status:
                output.append(f"\n❌ ERROR: {health_status['error']}")
            
            output.append("\n" + "=" * 80)
            
            return [TextContent(
                type="text",
                text="\n".join(output)
            )]
        
        elif name == "clear_cache":
            logger.info("Executing clear_cache tool")
            
            query_pattern = arguments.get("query_pattern")
            
            if not cache_manager:
                return [TextContent(
                    type="text",
                    text="Error: Cache manager not available"
                )]
            
            deleted_count = await cache_manager.invalidate_cache(query_pattern)
            
            if query_pattern:
                message = f"Cache cleared for pattern '{query_pattern}': {deleted_count} entries removed"
            else:
                message = f"All cache cleared: {deleted_count} entries removed"
            
            return [TextContent(
                type="text",
                text=message
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
    """Main entry point for the production MCP server."""
    global production_orchestrator, cache_manager
    
    # Get production configuration
    config = get_production_config()
    
    # Initialize the production orchestrator
    logger.info("Initializing Agno Production Orchestration System...")
    
    rate_limit_config = RateLimitConfig(**config["rate_limiting"])
    memory_config = MemoryConfig(**config["memory"])
    
    production_orchestrator = ProductionOrchestrator(
        tavily_api_key=config["api"]["tavily_api_key"],
        jina_api_key=config["api"]["jina_api_key"],
        min_confidence=config["api"]["min_confidence"],
        timeout=config["api"]["timeout_seconds"],
        rate_limit_config=rate_limit_config,
        memory_config=memory_config
    )
    
    # Initialize cache manager
    logger.info("Initializing cache manager...")
    try:
        cache_config = CacheConfig(**config["caching"])
        cache_manager = CacheManager(cache_config)
        
        # Test cache connection
        cache_stats = await cache_manager.get_cache_stats()
        if cache_stats.get("status") == "active":
            logger.info("Redis cache connected successfully")
        else:
            logger.warning("Redis cache not available, using memory cache fallback")
            cache_manager = MemoryCacheManager()
            
    except Exception as e:
        logger.warning(f"Cache initialization failed: {str(e)}. Using memory cache fallback.")
        cache_manager = MemoryCacheManager()
    
    logger.info("Agno Production System initialized successfully")
    logger.info("Starting production MCP server...")
    
    # Log configuration summary
    logger.info("Production Configuration:")
    logger.info(f"  Rate Limit: {rate_limit_config.max_requests_per_minute}/min, {rate_limit_config.max_requests_per_hour}/hour")
    logger.info(f"  Max Concurrent: {rate_limit_config.max_concurrent_requests}")
    logger.info(f"  Memory Limit: {memory_config.max_execution_history} history entries")
    logger.info(f"  Cache TTL: {config['caching']['default_ttl']} seconds")
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


def run():
    """Run the production server."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
