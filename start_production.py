#!/usr/bin/env python3
"""
Production Server Startup Script
Quick start script for the Agno production MCP server.
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path

# Add src directory to path
src_path = str(Path(__file__).parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

try:
    from src.production_server import main, get_production_config
    from src.logging_system import get_logger
except ImportError:
    try:
        from production_server import main, get_production_config
        from logging_system import get_logger
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're running from the project root directory")
        print("   and that all dependencies are installed:")
        print("   pip install -r requirements.production.txt")
        sys.exit(1)


def check_requirements():
    """Check if all required dependencies are installed."""
    required_packages = [
        'mcp', 'httpx', 'pydantic', 'python-dotenv', 
        'asyncio', 'aiohttp', 'redis'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n💡 Install them with:")
        print("   pip install -r requirements.production.txt")
        return False
    
    return True


def check_configuration():
    """Check if configuration is properly set up."""
    config = get_production_config()
    
    # Check for required API keys
    if not config["api"]["tavily_api_key"] and not config["api"]["jina_api_key"]:
        print("❌ No API keys configured!")
        print("   Set TAVILY_API_KEY or JINA_API_KEY in your .env file")
        return False
    
    # Check Redis connection (optional)
    try:
        import redis
        redis_client = redis.from_url(config["caching"]["redis_url"])
        redis_client.ping()
        print("✅ Redis connection successful")
    except Exception as e:
        print(f"⚠️  Redis connection failed: {e}")
        print("   Caching will use memory fallback")
    
    return True


def print_startup_info():
    """Print startup information."""
    config = get_production_config()
    
    print("🚀 Agno Production MCP Server")
    print("=" * 50)
    print(f"Rate Limit: {config['rate_limiting']['max_requests_per_minute']}/min")
    print(f"Max Concurrent: {config['rate_limiting']['max_concurrent_requests']}")
    print(f"Cache TTL: {config['caching']['default_ttl']}s")
    print(f"Memory Limit: {config['memory']['max_execution_history']} entries")
    print("=" * 50)


async def run_server():
    """Run the production server."""
    logger = get_logger()
    
    try:
        await main()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


def main_cli():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description="Start Agno Production MCP Server")
    parser.add_argument("--check-only", action="store_true", help="Only check configuration, don't start server")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        os.environ["LOG_LEVEL"] = "DEBUG"
    
    print("🔍 Checking requirements...")
    if not check_requirements():
        sys.exit(1)
    
    print("✅ Requirements check passed")
    
    print("\n🔍 Checking configuration...")
    if not check_configuration():
        sys.exit(1)
    
    print("✅ Configuration check passed")
    
    if args.check_only:
        print("\n✅ All checks passed! Server is ready to start.")
        return
    
    print_startup_info()
    
    print("\n🚀 Starting production server...")
    print("   Press Ctrl+C to stop")
    print()
    
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main_cli()
