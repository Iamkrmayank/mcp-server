"""
Production-Ready Orchestrator
Enhanced version with concurrency management, rate limiting, and memory management.
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from collections import defaultdict, deque
from asyncio import Semaphore
import hashlib
import json

try:
    from .agno_orchestrator import AgnoOrchestrator, AgnoResponse
    from .logging_system import get_logger
except ImportError:
    from agno_orchestrator import AgnoOrchestrator, AgnoResponse
    from logging_system import get_logger


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    max_requests_per_minute: int = 60
    max_requests_per_hour: int = 1000
    max_concurrent_requests: int = 100
    burst_limit: int = 10


@dataclass
class MemoryConfig:
    """Memory management configuration."""
    max_execution_history: int = 1000
    max_request_size_mb: int = 10
    cleanup_interval_seconds: int = 300  # 5 minutes


class RateLimiter:
    """Rate limiting implementation with multiple time windows."""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.requests_per_minute = defaultdict(list)
        self.requests_per_hour = defaultdict(list)
        self.burst_requests = defaultdict(list)
        self.logger = get_logger()
    
    async def is_allowed(self, client_id: str = "default") -> tuple[bool, str]:
        """
        Check if request is allowed based on rate limits.
        
        Returns:
            Tuple of (is_allowed, reason)
        """
        now = time.time()
        
        # Clean old requests
        self._cleanup_old_requests(client_id, now)
        
        # Check burst limit (last 10 seconds)
        recent_requests = [
            req_time for req_time in self.burst_requests[client_id]
            if now - req_time < 10
        ]
        if len(recent_requests) >= self.config.burst_limit:
            return False, f"Burst limit exceeded: {len(recent_requests)} requests in last 10 seconds"
        
        # Check per-minute limit
        if len(self.requests_per_minute[client_id]) >= self.config.max_requests_per_minute:
            return False, f"Rate limit exceeded: {len(self.requests_per_minute[client_id])} requests per minute"
        
        # Check per-hour limit
        if len(self.requests_per_hour[client_id]) >= self.config.max_requests_per_hour:
            return False, f"Rate limit exceeded: {len(self.requests_per_hour[client_id])} requests per hour"
        
        # Record the request
        self.requests_per_minute[client_id].append(now)
        self.requests_per_hour[client_id].append(now)
        self.burst_requests[client_id].append(now)
        
        return True, "Request allowed"
    
    def _cleanup_old_requests(self, client_id: str, now: float):
        """Clean up old request timestamps."""
        # Keep only requests from last minute
        self.requests_per_minute[client_id] = [
            req_time for req_time in self.requests_per_minute[client_id]
            if now - req_time < 60
        ]
        
        # Keep only requests from last hour
        self.requests_per_hour[client_id] = [
            req_time for req_time in self.requests_per_hour[client_id]
            if now - req_time < 3600
        ]
        
        # Keep only burst requests from last 10 seconds
        self.burst_requests[client_id] = [
            req_time for req_time in self.burst_requests[client_id]
            if now - req_time < 10
        ]


class MemoryManager:
    """Memory management for production use."""
    
    def __init__(self, config: MemoryConfig):
        self.config = config
        self.logger = get_logger()
        self.last_cleanup = time.time()
    
    def validate_request_size(self, request_data: Any) -> tuple[bool, str]:
        """Validate request size."""
        try:
            request_size = len(json.dumps(request_data).encode('utf-8'))
            size_mb = request_size / (1024 * 1024)
            
            if size_mb > self.config.max_request_size_mb:
                return False, f"Request too large: {size_mb:.2f}MB > {self.config.max_request_size_mb}MB"
            
            return True, "Request size OK"
        except Exception as e:
            return False, f"Error validating request size: {str(e)}"
    
    def cleanup_history(self, history_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean up execution history to prevent memory leaks."""
        if len(history_list) <= self.config.max_execution_history:
            return history_list
        
        # Keep only recent entries
        cleaned = history_list[-self.config.max_execution_history:]
        self.logger.info(f"Cleaned execution history: {len(history_list)} -> {len(cleaned)} entries")
        return cleaned
    
    def should_cleanup(self) -> bool:
        """Check if it's time for cleanup."""
        return time.time() - self.last_cleanup > self.config.cleanup_interval_seconds
    
    def mark_cleanup_done(self):
        """Mark cleanup as completed."""
        self.last_cleanup = time.time()


class ProductionOrchestrator:
    """
    Production-ready orchestrator with concurrency management, rate limiting,
    and memory management.
    """
    
    def __init__(
        self,
        tavily_api_key: Optional[str] = None,
        jina_api_key: Optional[str] = None,
        min_confidence: float = 0.5,
        timeout: int = 30,
        rate_limit_config: Optional[RateLimitConfig] = None,
        memory_config: Optional[MemoryConfig] = None
    ):
        """Initialize the production orchestrator."""
        self.logger = get_logger()
        
        # Initialize base orchestrator
        self.base_orchestrator = AgnoOrchestrator(
            tavily_api_key=tavily_api_key,
            jina_api_key=jina_api_key,
            min_confidence=min_confidence,
            timeout=timeout
        )
        
        # Initialize production components
        self.rate_limiter = RateLimiter(rate_limit_config or RateLimitConfig())
        self.memory_manager = MemoryManager(memory_config or MemoryConfig())
        
        # Concurrency control
        self.semaphore = Semaphore(rate_limit_config.max_concurrent_requests if rate_limit_config else 100)
        
        # Request tracking
        self.active_requests = {}
        self.request_counter = 0
        
        self.logger.info("Production Orchestrator initialized with concurrency and rate limiting")
    
    async def process_request(
        self,
        user_input: str,
        client_id: str = "default",
        **kwargs
    ) -> AgnoResponse:
        """
        Process a request with production safeguards.
        
        Args:
            user_input: Natural language query
            client_id: Client identifier for rate limiting
            **kwargs: Additional parameters
            
        Returns:
            AgnoResponse with results or error
        """
        request_id = f"req_{self.request_counter}_{int(time.time())}"
        self.request_counter += 1
        
        # Check rate limits
        is_allowed, rate_limit_reason = await self.rate_limiter.is_allowed(client_id)
        if not is_allowed:
            self.logger.warning(f"Rate limit exceeded for client {client_id}: {rate_limit_reason}")
            return AgnoResponse(
                success=False,
                error=f"Rate limit exceeded: {rate_limit_reason}",
                metadata={
                    "request_id": request_id,
                    "client_id": client_id,
                    "rate_limited": True
                }
            )
        
        # Validate request size
        request_data = {"user_input": user_input, **kwargs}
        is_valid_size, size_reason = self.memory_manager.validate_request_size(request_data)
        if not is_valid_size:
            self.logger.warning(f"Request too large: {size_reason}")
            return AgnoResponse(
                success=False,
                error=f"Request too large: {size_reason}",
                metadata={
                    "request_id": request_id,
                    "client_id": client_id,
                    "size_exceeded": True
                }
            )
        
        # Process with concurrency control
        async with self.semaphore:
            try:
                self.active_requests[request_id] = {
                    "client_id": client_id,
                    "start_time": time.time(),
                    "user_input": user_input
                }
                
                self.logger.info(f"Processing request {request_id} for client {client_id}")
                
                # Process through base orchestrator
                response = await self.base_orchestrator.process_request(
                    user_input=user_input,
                    **kwargs
                )
                
                # Add production metadata
                response.metadata = response.metadata or {}
                response.metadata.update({
                    "request_id": request_id,
                    "client_id": client_id,
                    "processed_at": time.time()
                })
                
                # Cleanup memory if needed
                if self.memory_manager.should_cleanup():
                    self._cleanup_memory()
                
                return response
                
            except Exception as e:
                self.logger.error(f"Error processing request {request_id}: {str(e)}")
                return AgnoResponse(
                    success=False,
                    error=f"Internal error: {str(e)}",
                    metadata={
                        "request_id": request_id,
                        "client_id": client_id,
                        "error": True
                    }
                )
            finally:
                # Clean up active request
                if request_id in self.active_requests:
                    del self.active_requests[request_id]
    
    def _cleanup_memory(self):
        """Clean up memory and execution history."""
        try:
            # Clean up execution history
            if hasattr(self.base_orchestrator.framework, 'execution_history'):
                self.base_orchestrator.framework.execution_history = self.memory_manager.cleanup_history(
                    self.base_orchestrator.framework.execution_history
                )
            
            self.memory_manager.mark_cleanup_done()
            self.logger.info("Memory cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during memory cleanup: {str(e)}")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics including production metrics."""
        base_stats = self.base_orchestrator.get_statistics()
        
        # Add production metrics
        production_stats = {
            "active_requests": len(self.active_requests),
            "max_concurrent": self.semaphore._value + len(self.active_requests),
            "rate_limiter_stats": {
                "unique_clients": len(self.rate_limiter.requests_per_minute),
                "total_requests_minute": sum(len(requests) for requests in self.rate_limiter.requests_per_minute.values()),
                "total_requests_hour": sum(len(requests) for requests in self.rate_limiter.requests_per_hour.values())
            },
            "memory_stats": {
                "execution_history_size": len(getattr(self.base_orchestrator.framework, 'execution_history', [])),
                "max_history_allowed": self.memory_manager.config.max_execution_history,
                "last_cleanup": self.memory_manager.last_cleanup
            }
        }
        
        return {**base_stats, "production_metrics": production_stats}
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status for monitoring."""
        try:
            # Check if base orchestrator is healthy
            base_stats = self.base_orchestrator.get_statistics()
            
            # Check memory usage
            history_size = len(getattr(self.base_orchestrator.framework, 'execution_history', []))
            memory_healthy = history_size < self.memory_manager.config.max_execution_history * 0.9
            
            # Check active requests
            active_requests = len(self.active_requests)
            concurrency_healthy = active_requests < self.semaphore._value * 0.9
            
            overall_healthy = memory_healthy and concurrency_healthy and base_stats['success_rate'] > 80
            
            return {
                "status": "healthy" if overall_healthy else "degraded",
                "timestamp": time.time(),
                "checks": {
                    "memory": "healthy" if memory_healthy else "warning",
                    "concurrency": "healthy" if concurrency_healthy else "warning",
                    "base_orchestrator": "healthy" if base_stats['success_rate'] > 80 else "warning"
                },
                "metrics": {
                    "active_requests": active_requests,
                    "execution_history_size": history_size,
                    "success_rate": base_stats['success_rate']
                }
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": time.time(),
                "error": str(e)
            }
