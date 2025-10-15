#!/usr/bin/env python3
"""
HTTP API Server Runner
Starts the HTTP API server for load testing and production use.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up environment
os.environ.setdefault('PYTHONPATH', str(project_root))

if __name__ == "__main__":
    # Import and run the HTTP API server
    from http_api import run_server
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Agno Production HTTP API")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    
    args = parser.parse_args()
    
    print("🚀 Starting Agno Production HTTP API Server...")
    print(f"   Host: {args.host}")
    print(f"   Port: {args.port}")
    print(f"   Workers: {args.workers}")
    print("   Press Ctrl+C to stop")
    print()
    
    try:
        run_server(host=args.host, port=args.port, workers=args.workers)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)
