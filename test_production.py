#!/usr/bin/env python3
"""
Production System Test Script
Tests all components of the production MCP server.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        from src.production_orchestrator import ProductionOrchestrator, RateLimitConfig, MemoryConfig
        print("  ✅ ProductionOrchestrator")
    except Exception as e:
        print(f"  ❌ ProductionOrchestrator: {e}")
        return False
    
    try:
        from src.cache_manager import CacheManager, CacheConfig, MemoryCacheManager
        print("  ✅ CacheManager")
    except Exception as e:
        print(f"  ❌ CacheManager: {e}")
        return False
    
    try:
        from src.production_server import get_production_config
        print("  ✅ ProductionServer")
    except Exception as e:
        print(f"  ❌ ProductionServer: {e}")
        return False
    
    try:
        from src.agno_orchestrator import AgnoOrchestrator
        print("  ✅ AgnoOrchestrator")
    except Exception as e:
        print(f"  ❌ AgnoOrchestrator: {e}")
        return False
    
    try:
        from src.logging_system import get_logger
        print("  ✅ LoggingSystem")
    except Exception as e:
        print(f"  ❌ LoggingSystem: {e}")
        return False
    
    return True

def test_configuration():
    """Test configuration loading."""
    print("\n🔍 Testing configuration...")
    
    try:
        from src.production_server import get_production_config
        config = get_production_config()
        
        print(f"  ✅ Rate limit per minute: {config['rate_limiting']['max_requests_per_minute']}")
        print(f"  ✅ Max concurrent requests: {config['rate_limiting']['max_concurrent_requests']}")
        print(f"  ✅ Cache TTL: {config['caching']['default_ttl']}s")
        print(f"  ✅ Memory limit: {config['memory']['max_execution_history']} entries")
        
        return True
    except Exception as e:
        print(f"  ❌ Configuration error: {e}")
        return False

async def test_orchestrator():
    """Test the production orchestrator."""
    print("\n🔍 Testing production orchestrator...")
    
    try:
        from src.production_orchestrator import ProductionOrchestrator, RateLimitConfig, MemoryConfig
        
        # Create test configuration
        rate_config = RateLimitConfig(max_requests_per_minute=10, max_concurrent_requests=5)
        memory_config = MemoryConfig(max_execution_history=100)
        
        # Initialize orchestrator (without API keys for testing)
        orchestrator = ProductionOrchestrator(
            rate_limit_config=rate_config,
            memory_config=memory_config
        )
        
        print("  ✅ Orchestrator initialized")
        
        # Test rate limiting
        is_allowed, reason = await orchestrator.rate_limiter.is_allowed("test_client")
        print(f"  ✅ Rate limiting test: {is_allowed} - {reason}")
        
        # Test memory management
        test_data = {"query": "test", "results": ["a", "b", "c"]}
        is_valid, reason = orchestrator.memory_manager.validate_request_size(test_data)
        print(f"  ✅ Memory validation test: {is_valid} - {reason}")
        
        # Test statistics
        stats = orchestrator.get_system_stats()
        print(f"  ✅ Statistics: {len(stats)} metrics available")
        
        # Test health status
        health = orchestrator.get_health_status()
        print(f"  ✅ Health status: {health['status']}")
        
        return True
    except Exception as e:
        print(f"  ❌ Orchestrator error: {e}")
        return False

async def test_cache_manager():
    """Test the cache manager."""
    print("\n🔍 Testing cache manager...")
    
    try:
        from src.cache_manager import MemoryCacheManager
        
        # Test memory cache (no Redis required)
        cache = MemoryCacheManager(max_size=10, default_ttl=60)
        
        # Test caching
        test_data = {"result": "test_data", "timestamp": "2024-01-01"}
        success = cache.cache_result("test_query", test_data)
        print(f"  ✅ Cache store: {success}")
        
        # Test retrieval
        cached = cache.get_cached_result("test_query")
        print(f"  ✅ Cache retrieve: {cached is not None}")
        
        # Test statistics
        stats = cache.get_cache_stats()
        print(f"  ✅ Cache stats: {stats['total_keys']} keys")
        
        return True
    except Exception as e:
        print(f"  ❌ Cache manager error: {e}")
        return False

def test_dependencies():
    """Test required dependencies."""
    print("\n🔍 Testing dependencies...")
    
    required_packages = [
        'mcp', 'httpx', 'pydantic', 'dotenv', 
        'asyncio', 'aiohttp'
    ]
    
    optional_packages = [
        'redis', 'prometheus_client', 'psutil'
    ]
    
    all_good = True
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} (required)")
            all_good = False
    
    for package in optional_packages:
        try:
            __import__(package)
            print(f"  ✅ {package} (optional)")
        except ImportError:
            print(f"  ⚠️  {package} (optional, not installed)")
    
    return all_good

async def main():
    """Run all tests."""
    print("🧪 Agno Production System Test Suite")
    print("=" * 50)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Imports", test_imports),
        ("Configuration", test_configuration),
        ("Orchestrator", test_orchestrator),
        ("Cache Manager", test_cache_manager),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Production system is ready.")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
