#!/usr/bin/env python3
"""
Quick Start Script for Agno MCP Orchestration System

This script provides an interactive introduction to the system.
Run with: python quick_start.py
"""

import asyncio
import os
from pathlib import Path


def check_setup():
    """Check if the system is properly set up."""
    print("🔍 Checking setup...")
    
    issues = []
    
    # Check for .env file
    if not Path(".env").exists():
        issues.append("❌ .env file not found. Copy .env.template to .env")
    
    # Check for API keys
    from dotenv import load_dotenv
    load_dotenv()
    
    tavily_key = os.getenv("TAVILY_API_KEY")
    jina_key = os.getenv("JINA_API_KEY")
    
    if not tavily_key and not jina_key:
        issues.append("❌ No API keys configured. Add at least TAVILY_API_KEY to .env")
    elif tavily_key:
        issues.append("✅ Tavily API key configured")
    
    if jina_key:
        issues.append("✅ Jina API key configured (fallback available)")
    
    # Check dependencies
    try:
        import mcp
        issues.append("✅ MCP library installed")
    except ImportError:
        issues.append("❌ MCP library not installed. Run: pip install -r requirements.txt")
    
    try:
        import httpx
        issues.append("✅ HTTP client library installed")
    except ImportError:
        issues.append("❌ httpx not installed. Run: pip install -r requirements.txt")
    
    return issues


def print_banner():
    """Print welcome banner."""
    print("\n" + "=" * 80)
    print("🚀 AGNO MCP ORCHESTRATION SYSTEM - QUICK START")
    print("=" * 80)
    print("\nWelcome to the Agno orchestration system!")
    print("This interactive guide will help you get started.\n")


async def run_demo():
    """Run demonstration queries."""
    from src.agno_orchestrator import AgnoOrchestrator
    
    print("\n" + "=" * 80)
    print("📊 DEMO: Running Sample Queries")
    print("=" * 80)
    
    orchestrator = AgnoOrchestrator()
    
    demo_queries = [
        ("Simple query", "What is Python programming?"),
        ("Technology query", "Latest AI developments 2024"),
        ("Information query", "Benefits of renewable energy")
    ]
    
    for title, query in demo_queries:
        print(f"\n\n🔎 {title}: '{query}'")
        print("-" * 80)
        
        try:
            response = await orchestrator.process_request(
                user_input=query,
                max_results=3
            )
            
            if response.success:
                print(f"\n✅ Success! {response.feedback}")
                print(f"   Confidence: {response.metadata.get('confidence', 0):.1%}")
                print(f"   Duration: {response.metadata.get('duration_ms', 0):.0f}ms")
                print(f"   Source: {response.metadata.get('source', 'Unknown')}")
                
                # Show first result
                if response.data and response.data.get('results'):
                    first = response.data['results'][0]
                    print(f"\n   First result: {first.get('title', 'N/A')}")
                    content = first.get('content', '')
                    if len(content) > 150:
                        content = content[:150] + "..."
                    print(f"   {content}")
            else:
                print(f"\n❌ Failed: {response.error}")
                print(f"   Feedback: {response.feedback}")
        
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
        
        # Small delay between queries
        await asyncio.sleep(1)
    
    # Show statistics
    print("\n\n" + "=" * 80)
    print("📈 STATISTICS")
    print("=" * 80)
    
    stats = orchestrator.get_statistics()
    print(f"\nTotal Requests: {stats['total_requests']}")
    print(f"Successful Requests: {stats['successful_requests']}")
    print(f"Success Rate: {stats['success_rate']:.1f}%")
    print(f"Fallback Usage: {stats['fallback_rate']:.1f}%")
    print(f"Available Tools: {stats['available_tools']}")


def show_next_steps():
    """Show next steps for the user."""
    print("\n\n" + "=" * 80)
    print("📚 NEXT STEPS")
    print("=" * 80)
    print("""
1. Try the CLI:
   python -m src.cli "Your query here"

2. Run as MCP server:
   python -m src.server

3. Use programmatically:
   from src.agno_orchestrator import AgnoOrchestrator
   orchestrator = AgnoOrchestrator()
   response = await orchestrator.process_request("query")

4. Read the documentation:
   - README.md - Full documentation
   - SETUP_GUIDE.md - Detailed setup instructions
   - EXAMPLES.md - Code examples and use cases

5. Check logs:
   View agno_system.log for detailed execution logs

6. Get help:
   python -m src.cli --help
""")


async def main():
    """Main entry point."""
    print_banner()
    
    # Check setup
    issues = check_setup()
    
    print("\n📋 Setup Status:")
    for issue in issues:
        print(f"  {issue}")
    
    # Check if there are blocking issues
    blocking_issues = [i for i in issues if i.startswith("❌")]
    
    if blocking_issues:
        print("\n⚠️  Please fix the issues above before continuing.")
        print("\nQuick fixes:")
        print("  1. Copy template: cp .env.template .env")
        print("  2. Add your Tavily API key to .env")
        print("  3. Install dependencies: pip install -r requirements.txt")
        return
    
    print("\n✅ Setup looks good! Ready to run demo.\n")
    
    # Ask user if they want to run demo
    response = input("Would you like to run a demo with sample queries? (y/n): ")
    
    if response.lower() in ['y', 'yes']:
        try:
            await run_demo()
        except Exception as e:
            print(f"\n❌ Demo failed: {str(e)}")
            print("\nTroubleshooting:")
            print("  - Check your API keys in .env")
            print("  - Verify internet connection")
            print("  - Review logs in agno_system.log")
    
    show_next_steps()
    
    print("\n" + "=" * 80)
    print("🎉 Quick start complete! Happy searching!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nFor help, see SETUP_GUIDE.md or README.md")

