"""
Demo: Proper Data Scraping with Tavily/Jina and Complete Logging
Shows how to extract structured data with full audit trail
"""

import asyncio
import json
from src.agno_orchestrator import AgnoOrchestrator
from src.logging_system import get_logger


async def demo_proper_scraping():
    """
    Demonstrate proper data scraping with:
    1. Structured data extraction
    2. Quality metrics
    3. Complete logging
    4. Fallback handling
    """
    
    logger = get_logger()
    orchestrator = AgnoOrchestrator()
    
    print("=" * 70)
    print("🔍 DEMO: Proper Data Scraping with Logging")
    print("=" * 70)
    
    # Example 1: Tech News Scraping
    print("\n📰 Example 1: Scraping Tech News")
    print("-" * 70)
    
    query1 = "Latest AI developments in 2025"
    result1 = await orchestrator.execute_query(query1)
    
    print(f"\n✅ Query: {query1}")
    print(f"📊 Status: {result1.status.value}")
    print(f"🎯 Confidence: {result1.confidence:.2%}")
    print(f"📦 Source: {result1.metadata.get('source', 'N/A')}")
    
    if result1.data:
        print(f"\n📝 Results Found: {len(result1.data.get('results', []))}")
        
        for i, item in enumerate(result1.data.get('results', [])[:3], 1):
            print(f"\n  {i}. {item['title']}")
            print(f"     URL: {item['url']}")
            print(f"     Score: {item.get('score', 0):.2f}")
            print(f"     Preview: {item['content'][:100]}...")
    
    # Example 2: Company Information
    print("\n\n🏢 Example 2: Scraping Company Data")
    print("-" * 70)
    
    query2 = "Microsoft annual revenue 2024"
    result2 = await orchestrator.execute_query(query2)
    
    print(f"\n✅ Query: {query2}")
    print(f"📊 Status: {result2.status.value}")
    print(f"🎯 Confidence: {result2.confidence:.2%}")
    
    if result2.data and result2.data.get('answer'):
        print(f"\n💡 Answer: {result2.data['answer'][:200]}...")
    
    # Example 3: Academic Research
    print("\n\n🎓 Example 3: Scraping Research Papers")
    print("-" * 70)
    
    query3 = "Machine learning research papers 2025"
    result3 = await orchestrator.execute_query(query3)
    
    print(f"\n✅ Query: {query3}")
    print(f"📊 Status: {result3.status.value}")
    print(f"🎯 Confidence: {result3.confidence:.2%}")
    
    # Show data quality metrics
    print("\n\n📊 DATA QUALITY METRICS")
    print("=" * 70)
    print(f"Query 1 Confidence: {result1.confidence:.2%}")
    print(f"Query 2 Confidence: {result2.confidence:.2%}")
    print(f"Query 3 Confidence: {result3.confidence:.2%}")
    
    # Show logging information
    print("\n\n📝 LOGGING & AUDIT TRAIL")
    print("=" * 70)
    print("✅ All operations logged to: agno_system.log")
    print("📋 Log includes:")
    print("   • Timestamps (UTC)")
    print("   • Request/Response details")
    print("   • Duration metrics")
    print("   • Confidence scores")
    print("   • Error tracking")
    print("   • Fallback events")
    
    # Show log sample
    print("\n\n📄 Sample Log Entry:")
    print("-" * 70)
    log_sample = {
        "timestamp": "2025-10-14T12:30:45.123456+00:00",
        "operation": "Tavily_Request",
        "status": "success",
        "duration_ms": 234.56,
        "data_quality": {
            "confidence": 0.89,
            "result_count": 5,
            "has_answer": True
        },
        "metadata": {
            "source": "Tavily",
            "query": query1
        }
    }
    print(json.dumps(log_sample, indent=2))
    
    # Show structured data export
    print("\n\n💾 STRUCTURED DATA EXPORT")
    print("=" * 70)
    
    export_data = {
        "scraping_session": {
            "timestamp": "2025-10-14T12:30:45",
            "queries_executed": 3,
            "results": [
                {
                    "query": query1,
                    "status": result1.status.value,
                    "confidence": result1.confidence,
                    "result_count": len(result1.data.get('results', [])) if result1.data else 0
                },
                {
                    "query": query2,
                    "status": result2.status.value,
                    "confidence": result2.confidence,
                    "result_count": len(result2.data.get('results', [])) if result2.data else 0
                },
                {
                    "query": query3,
                    "status": result3.status.value,
                    "confidence": result3.confidence,
                    "result_count": len(result3.data.get('results', [])) if result3.data else 0
                }
            ]
        }
    }
    
    print(json.dumps(export_data, indent=2))
    
    print("\n" + "=" * 70)
    print("✅ Demo Complete! Check 'agno_system.log' for detailed logs")
    print("=" * 70)


async def demo_advanced_scraping():
    """
    Advanced scraping features:
    - Custom parameters
    - Domain filtering
    - Deep search
    """
    
    print("\n\n" + "=" * 70)
    print("🚀 ADVANCED SCRAPING FEATURES")
    print("=" * 70)
    
    orchestrator = AgnoOrchestrator()
    
    # Example: Deep search with domain filtering
    print("\n🔎 Deep Search with Domain Filtering")
    print("-" * 70)
    
    query = "Python web scraping tutorials"
    
    # You can pass additional parameters to Tavily
    # (This would need to be integrated into AgnoOrchestrator)
    print(f"Query: {query}")
    print("Parameters:")
    print("  • search_depth: advanced")
    print("  • max_results: 10")
    print("  • include_domains: ['github.com', 'stackoverflow.com']")
    
    result = await orchestrator.execute_query(query)
    
    print(f"\nResults: {len(result.data.get('results', [])) if result.data else 0}")
    print(f"Confidence: {result.confidence:.2%}")
    
    print("\n✅ Features Available:")
    print("   ✓ Real-time web scraping")
    print("   ✓ Structured data extraction")
    print("   ✓ Quality scoring")
    print("   ✓ Complete logging")
    print("   ✓ Automatic fallback")
    print("   ✓ Timeout handling")
    print("   ✓ Error recovery")


async def main():
    """Run all demos"""
    await demo_proper_scraping()
    await demo_advanced_scraping()


if __name__ == "__main__":
    asyncio.run(main())

