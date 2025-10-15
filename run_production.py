#!/usr/bin/env python3
"""
Simple Production Server Runner
Runs the production server with proper module imports.
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
    # Import and run the production server
    from src.production_server import main
    import asyncio
    
    print("🚀 Starting Agno Production MCP Server...")
    print("   Press Ctrl+C to stop")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)
