"""
Standalone HTTP API for Load Testing
A simplified HTTP API wrapper for testing the production system.
"""

import asyncio
import json
import time
import os
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import httpx

# Initialize FastAPI app
app = FastAPI(
    title="Agno Production API",
    description="Production-ready web scraping API for load testing",
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
request_count = 0
success_count = 0
cache_hits = 0
response_times = []

# Simple in-memory cache
cache = {}

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
    cached: Optional[bool] = False


class HealthResponse(BaseModel):
    status: str
    timestamp: float
    metrics: Optional[Dict[str, Any]] = None


class StatsResponse(BaseModel):
    total_requests: int
    successful_requests: int
    success_rate: float
    cache_hits: int
    cache_hit_rate: float
    average_response_time: float


def get_cache_key(query: str, **kwargs) -> str:
    """Generate cache key."""
    import hashlib
    cache_data = {
        "query": query,
        "params": sorted(kwargs.items()) if kwargs else {}
    }
    cache_string = json.dumps(cache_data, sort_keys=True)
    return hashlib.md5(cache_string.encode()).hexdigest()


async def simulate_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    """Simulate a search request with realistic timing."""
    # Simulate processing time
    await asyncio.sleep(0.1 + (len(query) * 0.001))  # 100ms + query length factor
    
    # Simulate success/failure based on query content
    if "error" in query.lower() or "fail" in query.lower():
        raise Exception("Simulated search error")
    
    # Generate mock results
    results = []
    for i in range(min(max_results, 3)):
        results.append({
            "title": f"Result {i+1} for '{query}'",
            "url": f"https://example.com/result-{i+1}",
            "content": f"This is mock content for query: {query}. Result {i+1}.",
            "score": 0.9 - (i * 0.1)
        })
    
    return {
        "query": query,
        "answer": f"Mock answer for query: {query}",
        "results": results,
        "metadata": {
            "source": "mock",
            "result_count": len(results),
            "processing_time_ms": 100 + len(query)
        }
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Agno Production API (Mock)",
        "version": "1.0.0",
        "description": "Mock API for load testing the production system",
        "endpoints": {
            "search": "/api/search",
            "health": "/health",
            "stats": "/stats",
            "docs": "/docs"
        }
    }


@app.post("/api/search", response_model=SearchResponse)
async def search_web(request: SearchRequest):
    """Search the web using mock data for load testing."""
    global request_count, success_count, cache_hits, response_times
    
    start_time = time.time()
    request_count += 1
    
    try:
        # Check cache first if enabled
        if request.use_cache:
            cache_key = get_cache_key(request.query, max_results=request.max_results)
            if cache_key in cache:
                cache_hits += 1
                response_time = time.time() - start_time
                response_times.append(response_time)
                
                return SearchResponse(
                    success=True,
                    data=cache[cache_key],
                    metadata={"cached": True, "cache_hit": True, "response_time": response_time}
                )
        
        # Simulate the search
        search_result = await simulate_search(request.query, request.max_results)
        
        # Cache the result if caching is enabled
        if request.use_cache:
            cache_key = get_cache_key(request.query, max_results=request.max_results)
            cache[cache_key] = search_result
        
        success_count += 1
        response_time = time.time() - start_time
        response_times.append(response_time)
        
        return SearchResponse(
            success=True,
            data=search_result,
            metadata={
                "cached": False,
                "cache_hit": False,
                "response_time": response_time,
                "request_id": request_count
            }
        )
        
    except Exception as e:
        response_time = time.time() - start_time
        response_times.append(response_time)
        
        return SearchResponse(
            success=False,
            error=str(e),
            metadata={
                "response_time": response_time,
                "request_id": request_count
            }
        )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Get system health status."""
    global request_count, success_count, response_times
    
    # Calculate health metrics
    success_rate = (success_count / request_count * 100) if request_count > 0 else 100
    avg_response_time = sum(response_times[-100:]) / len(response_times[-100:]) if response_times else 0
    
    # Determine health status
    if success_rate > 95 and avg_response_time < 2.0:
        status = "healthy"
    elif success_rate > 80 and avg_response_time < 5.0:
        status = "degraded"
    else:
        status = "unhealthy"
    
    return HealthResponse(
        status=status,
        timestamp=time.time(),
        metrics={
            "total_requests": request_count,
            "success_rate": success_rate,
            "average_response_time": avg_response_time,
            "cache_size": len(cache)
        }
    )


@app.get("/stats", response_model=StatsResponse)
async def get_statistics():
    """Get comprehensive system statistics."""
    global request_count, success_count, cache_hits, response_times
    
    success_rate = (success_count / request_count * 100) if request_count > 0 else 0
    cache_hit_rate = (cache_hits / request_count * 100) if request_count > 0 else 0
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    
    return StatsResponse(
        total_requests=request_count,
        successful_requests=success_count,
        success_rate=success_rate,
        cache_hits=cache_hits,
        cache_hit_rate=cache_hit_rate,
        average_response_time=avg_response_time
    )


@app.delete("/api/cache")
async def clear_cache():
    """Clear the cache."""
    global cache
    cache_size = len(cache)
    cache.clear()
    
    return {
        "message": f"Cache cleared: {cache_size} entries removed",
        "deleted_count": cache_size
    }


@app.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe endpoint."""
    return {"status": "ready"}


@app.get("/live")
async def liveness_check():
    """Kubernetes liveness probe endpoint."""
    return {"status": "alive", "timestamp": time.time()}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


def run_server(host: str = "0.0.0.0", port: int = 8000, workers: int = 1):
    """Run the HTTP server."""
    print(f"🚀 Starting Mock HTTP API Server on {host}:{port}")
    uvicorn.run(
        "mock_http_api:app",
        host=host,
        port=port,
        workers=workers,
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Agno Mock HTTP API")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    
    args = parser.parse_args()
    
    run_server(host=args.host, port=args.port, workers=args.workers)
