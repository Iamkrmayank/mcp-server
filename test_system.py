#!/usr/bin/env python3
"""
System Test Script
Tests core functionality of the Agno MCP orchestration system.
"""

import asyncio
import os
from dotenv import load_dotenv


async def test_imports():
    """Test that all modules can be imported."""
    print("[*] Testing imports...")
    
    try:
        from src.logging_system import get_logger
        from src.config import get_config
        from src.mcp_tools_integration import MCPToolsFramework, BaseTool, ToolResult
        from src.tools.tavily_tool import TavilyTool
        from src.tools.jina_tool import JinaTool
        from src.agno_orchestrator import AgnoOrchestrator
        print("[OK] All imports successful")
        return True
    except Exception as e:
        print(f"[FAIL] Import failed: {str(e)}")
        return False


async def test_logger():
    """Test the logging system."""
    print("\n[*] Testing logging system...")
    
    try:
        from src.logging_system import get_logger
        
        logger = get_logger()
        logger.info("Test log message")
        logger.log_operation(
            operation_name="Test_Operation",
            status="success",
            duration_ms=100.5
        )
        print("[OK] Logging system working")
        return True
    except Exception as e:
        print(f"[FAIL] Logger test failed: {str(e)}")
        return False


async def test_config():
    """Test configuration management."""
    print("\n[*] Testing configuration...")
    
    try:
        from src.config import get_config
        
        config = get_config()
        is_valid, error = config.validate()
        
        if is_valid:
            print("[OK] Configuration valid")
            return True
        else:
            print(f"[WARN] Configuration issue: {error}")
            return False
    except Exception as e:
        print(f"[FAIL] Config test failed: {str(e)}")
        return False


async def test_tools():
    """Test tool initialization."""
    print("\n[*] Testing tools...")
    
    try:
        from src.tools.tavily_tool import TavilyTool
        from src.tools.jina_tool import JinaTool
        
        tavily = TavilyTool()
        jina = JinaTool()
        
        tavily_available = tavily.is_available()
        jina_available = jina.is_available()
        
        print(f"   Tavily available: {tavily_available}")
        print(f"   Jina available: {jina_available}")
        
        if tavily_available or jina_available:
            print("[OK] At least one tool available")
            return True
        else:
            print("[WARN] No tools available - check API keys")
            return False
    except Exception as e:
        print(f"[FAIL] Tool test failed: {str(e)}")
        return False


async def test_framework():
    """Test MCP Tools Framework."""
    print("\n[*] Testing MCP Tools Framework...")
    
    try:
        from src.mcp_tools_integration import MCPToolsFramework
        from src.tools.tavily_tool import TavilyTool
        from src.tools.jina_tool import JinaTool
        
        framework = MCPToolsFramework()
        
        # Register tools
        framework.register_tool(TavilyTool())
        framework.register_tool(JinaTool())
        
        # Check registry
        available_tools = framework.registry.get_available_tools()
        
        print(f"   Registered tools: {len(framework.registry.list_tools())}")
        print(f"   Available tools: {len(available_tools)}")
        
        if available_tools:
            print("[OK] Framework working")
            return True
        else:
            print("[WARN] No available tools in framework")
            return False
    except Exception as e:
        print(f"[FAIL] Framework test failed: {str(e)}")
        return False


async def test_orchestrator():
    """Test the Agno orchestrator."""
    print("\n[*] Testing Agno orchestrator...")
    
    try:
        from src.agno_orchestrator import AgnoOrchestrator
        
        orchestrator = AgnoOrchestrator()
        
        # Get statistics (should be zero initially)
        stats = orchestrator.get_statistics()
        
        print(f"   Registered tools: {stats['registered_tools']}")
        print(f"   Available tools: {stats['available_tools']}")
        
        if stats['available_tools'] > 0:
            print("[OK] Orchestrator initialized")
            return True
        else:
            print("[WARN] Orchestrator has no available tools")
            return False
    except Exception as e:
        print(f"[FAIL] Orchestrator test failed: {str(e)}")
        return False


async def test_end_to_end():
    """Test end-to-end query execution."""
    print("\n[*] Testing end-to-end query...")
    
    try:
        from src.agno_orchestrator import AgnoOrchestrator
        
        orchestrator = AgnoOrchestrator()
        
        # Simple test query
        print("   Running test query: 'Python programming'")
        response = await orchestrator.process_request(
            user_input="Python programming",
            max_results=3
        )
        
        if response.success:
            print(f"[OK] Query successful!")
            print(f"   Confidence: {response.metadata.get('confidence', 0):.1%}")
            print(f"   Duration: {response.metadata.get('duration_ms', 0):.0f}ms")
            print(f"   Source: {response.metadata.get('source', 'Unknown')}")
            print(f"   Results: {len(response.data.get('results', []))}")
            return True
        else:
            print(f"[FAIL] Query failed: {response.error}")
            print(f"   Feedback: {response.feedback}")
            return False
    except Exception as e:
        print(f"[FAIL] End-to-end test failed: {str(e)}")
        return False


async def main():
    """Run all tests."""
    print("=" * 80)
    print("AGNO MCP ORCHESTRATION SYSTEM - TEST SUITE")
    print("=" * 80)
    
    # Load environment
    load_dotenv()
    
    # Run tests
    tests = [
        ("Imports", test_imports),
        ("Logger", test_logger),
        ("Config", test_config),
        ("Tools", test_tools),
        ("Framework", test_framework),
        ("Orchestrator", test_orchestrator),
        ("End-to-End", test_end_to_end)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"[FAIL] {test_name} test crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed! System is ready to use.")
    elif passed >= total * 0.7:
        print("\n[WARNING] Most tests passed. Some features may have issues.")
    else:
        print("\n[ERROR] Multiple tests failed. Please check configuration and dependencies.")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[WARN] Tests interrupted by user.")
    except Exception as e:
        print(f"\n[ERROR] Test suite failed: {str(e)}")

