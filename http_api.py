"""
HTTP API Wrapper for MCP Server
Converts the MCP server to HTTP API for load testing and production use.
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# Add src to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from production_server import get_production_config
    from production_orchestrator import ProductionOrchestrator, RateLimitConfig, MemoryConfig
    from cache_manager import CacheManager, CacheConfig, MemoryCacheManager
    from logging_system import get_logger
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you're running from the project root directory")
    sys.exit(1)


# Initialize FastAPI app
app = FastAPI(
    title="Agno Production API",
    description="Production-ready web scraping API with MCP orchestration",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
production_orchestrator: Optional[ProductionOrchestrator] = None
cache_manager: Optional[CacheManager] = None
logger = get_logger()


# Pydantic models
class SearchRequest(BaseModel):
    query: str
    max_results: Optional[int] = 5
    format: Optional[str] = "json"
    client_id: Optional[str] = "default"
    use_cache: Optional[bool] = True


class SearchResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    execution_log: Optional[list] = None
    feedback: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    timestamp: float
    checks: Optional[Dict[str, str]] = None
    metrics: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class StatsResponse(BaseModel):
    total_requests: int
    successful_requests: int
    success_rate: float
    fallback_count: int
    fallback_rate: float
    available_tools: int
    registered_tools: int
    production_metrics: Optional[Dict[str, Any]] = None
    cache_metrics: Optional[Dict[str, Any]] = None


@app.on_event("startup")
async def startup_event():
    """Initialize the production system on startup."""
    global production_orchestrator, cache_manager
    
    logger.info("🚀 Starting Agno Production HTTP API...")
    
    # Get production configuration
    config = get_production_config()
    
    # Initialize the production orchestrator
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
    try:
        cache_config = CacheConfig(**config["caching"])
        cache_manager = CacheManager(cache_config)
        
        # Test cache connection
        cache_stats = await cache_manager.get_cache_stats()
        if cache_stats.get("status") == "active":
            logger.info("✅ Redis cache connected successfully")
        else:
            logger.warning("⚠️ Redis cache not available, using memory cache fallback")
            cache_manager = MemoryCacheManager()
            
    except Exception as e:
        logger.warning(f"⚠️ Cache initialization failed: {str(e)}. Using memory cache fallback.")
        cache_manager = MemoryCacheManager()
    
    logger.info("✅ Agno Production HTTP API initialized successfully")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Agno Production API",
        "version": "1.0.0",
        "description": "Production-ready web scraping API with MCP orchestration",
        "endpoints": {
            "search": "/api/search",
            "health": "/health",
            "stats": "/stats",
            "docs": "/docs"
        }
    }


@app.post("/api/search", response_model=SearchResponse)
async def search_web(request: SearchRequest):
    """Search the web using the production orchestrator."""
    global production_orchestrator, cache_manager
    
    if not production_orchestrator:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        # Check cache first if enabled
        if request.use_cache and cache_manager:
            cached_result = await cache_manager.get_cached_result(
                request.query,
                max_results=request.max_results,
                format=request.format
            )
            if cached_result:
                logger.info(f"Returning cached result for query: {request.query[:50]}...")
                return SearchResponse(
                    success=True,
                    data=cached_result["result"],
                    metadata={"cached": True, "cache_hit": True}
                )
        
        # Process the request through production orchestrator
        response = await production_orchestrator.process_request(
            user_input=request.query,
            max_results=request.max_results,
            client_id=request.client_id
        )
        
        # Format the response
        if request.format == "json":
            formatted_output = response.to_dict()
        else:
            formatted_output = production_orchestrator.base_orchestrator.format_response(
                response,
                format_type=request.format
            )
        
        # Cache the result if caching is enabled
        if request.use_cache and cache_manager and response.success:
            await cache_manager.cache_result(
                request.query,
                {"result": formatted_output},
                max_results=request.max_results,
                format=request.format
            )
        
        return SearchResponse(
            success=response.success,
            data=formatted_output if response.success else None,
            error=response.error,
            metadata=response.metadata,
            execution_log=response.execution_log,
            feedback=response.feedback
        )
        
    except Exception as e:
        logger.error(f"Error in search endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Get system health status."""
    global production_orchestrator, cache_manager
    
    if not production_orchestrator:
        return HealthResponse(
            status="unhealthy",
            timestamp=time.time(),
            error="Service not initialized"
        )
    
    try:
        health_status = production_orchestrator.get_health_status()
        
        # Add cache health if available
        if cache_manager:
            cache_stats = await cache_manager.get_cache_stats()
            health_status["cache_health"] = cache_stats
        
        return HealthResponse(**health_status)
        
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            timestamp=time.time(),
            error=str(e)
        )


@app.get("/stats", response_model=StatsResponse)
async def get_statistics():
    """Get comprehensive system statistics."""
    global production_orchestrator, cache_manager
    
    if not production_orchestrator:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        stats = production_orchestrator.get_system_stats()
        
        # Add cache statistics if available
        if cache_manager:
            cache_stats = await cache_manager.get_cache_stats()
            stats["cache_metrics"] = cache_stats
        
        return StatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.delete("/api/cache")
async def clear_cache(query_pattern: Optional[str] = None):
    """Clear the cache."""
    global cache_manager
    
    if not cache_manager:
        raise HTTPException(status_code=503, detail="Cache manager not available")
    
    try:
        deleted_count = await cache_manager.invalidate_cache(query_pattern)
        
        return {
            "message": f"Cache cleared: {deleted_count} entries removed",
            "deleted_count": deleted_count,
            "pattern": query_pattern
        }
        
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe endpoint."""
    global production_orchestrator
    
    if not production_orchestrator:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    # Check if orchestrator is healthy
    health = production_orchestrator.get_health_status()
    
    if health["status"] == "healthy":
        return {"status": "ready"}
    else:
        raise HTTPException(status_code=503, detail="Service not ready")


@app.get("/live")
async def liveness_check():
    """Kubernetes liveness probe endpoint."""
    return {"status": "alive", "timestamp": time.time()}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


def run_server(host: str = "0.0.0.0", port: int = 8000, workers: int = 1):
    """Run the HTTP server."""
    logger.info(f"🚀 Starting HTTP server on {host}:{port}")
    uvicorn.run(
        "http_api:app",
        host=host,
        port=port,
        workers=workers,
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Agno Production HTTP API")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    
    args = parser.parse_args()
    
    run_server(host=args.host, port=args.port, workers=args.workers)
