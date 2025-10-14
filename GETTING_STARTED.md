# Getting Started - Agno MCP Orchestration System

## ✅ Pre-Flight Checklist

Before you begin, make sure you have:

- [ ] Python 3.10 or higher installed
- [ ] pip package manager available
- [ ] A Tavily API key (get one at [https://tavily.com/](https://tavily.com/))
- [ ] (Optional) A Jina API key for fallback
- [ ] Internet connection
- [ ] Text editor for configuration

## 🚀 5-Minute Quick Start

### Step 1: Verify Python Installation (30 seconds)

```bash
python --version
# Should show Python 3.10 or higher

pip --version
# Should show pip is installed
```

**Troubleshooting:**
- Windows: If Python not found, install from [python.org](https://python.org)
- Mac: `brew install python3`
- Linux: `sudo apt install python3 python3-pip`

### Step 2: Install Dependencies (1 minute)

```bash
# Navigate to project directory
cd D:\mcp-server

# Install required packages
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed mcp-x.x.x httpx-x.x.x pydantic-x.x.x ...
```

**Troubleshooting:**
- If permission error: `pip install --user -r requirements.txt`
- If conflict: Create virtual environment first (see Advanced Setup below)

### Step 3: Configure API Keys (1 minute)

```bash
# Copy template
cp .env.template .env

# Edit .env file (use any text editor)
notepad .env  # Windows
nano .env     # Mac/Linux
```

Add your API key:
```env
TAVILY_API_KEY=tvly-your-actual-key-here
```

**Get your Tavily API key:**
1. Visit [https://tavily.com/](https://tavily.com/)
2. Sign up for free
3. Copy your API key
4. Paste into .env file

### Step 4: Test Installation (1 minute)

```bash
python test_system.py
```

**Expected output:**
```
🧪 AGNO MCP ORCHESTRATION SYSTEM - TEST SUITE
===============================================

✅ PASS - Imports
✅ PASS - Logger
✅ PASS - Config
✅ PASS - Tools
✅ PASS - Framework
✅ PASS - Orchestrator
✅ PASS - End-to-End

Total: 7/7 tests passed (100%)
🎉 All tests passed! System is ready to use.
```

**If tests fail:**
- Check your API key is correct
- Verify internet connection
- Review error messages
- See Troubleshooting section below

### Step 5: Run Your First Query (1 minute)

```bash
python -m src.cli "What is artificial intelligence?"
```

**Expected output:**
```
================================================================================
AGNO ORCHESTRATION SYSTEM - RESULTS
================================================================================

✓ Results retrieved successfully from Tavily.

ANSWER:
--------------------------------------------------------------------------------
Artificial intelligence (AI) refers to the simulation of human intelligence...

SOURCES:
--------------------------------------------------------------------------------
[1] Introduction to AI
    URL: https://example.com/ai-intro
    AI is a branch of computer science...

METADATA:
--------------------------------------------------------------------------------
Duration: 1245.32ms
Confidence: 87.50%
Source: Tavily
================================================================================
```

**🎉 Congratulations! Your system is working!**

## 📚 What's Next?

### Try Different Queries

```bash
# Technology
python -m src.cli "Latest developments in quantum computing"

# Business
python -m src.cli "Microsoft 2024 annual report summary"

# Science
python -m src.cli "Recent discoveries in astronomy"

# With different formats
python -m src.cli "Python programming basics" --format markdown
python -m src.cli "Machine learning overview" --format json

# More results
python -m src.cli "Best practices for web development" --max-results 10

# With statistics
python -m src.cli "Any query" --stats
```

### Interactive Quick Start

```bash
python quick_start.py
```

This will:
- Check your setup
- Run demo queries
- Show system capabilities
- Provide next steps

### Run as MCP Server

```bash
python -m src.server
```

The server will start and wait for MCP client connections.

To use with Claude Desktop, add to your MCP configuration:

```json
{
  "mcpServers": {
    "agno-orchestrator": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "D:\\mcp-server",
      "env": {
        "TAVILY_API_KEY": "your_key_here"
      }
    }
  }
}
```

### Use Programmatically

Create a Python script:

```python
# my_search.py
import asyncio
from src.agno_orchestrator import AgnoOrchestrator

async def main():
    orchestrator = AgnoOrchestrator()
    
    response = await orchestrator.process_request(
        "What are the benefits of renewable energy?"
    )
    
    if response.success:
        print(orchestrator.format_response(response))
        print(f"\nConfidence: {response.metadata['confidence']:.1%}")
    else:
        print(f"Error: {response.error}")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python my_search.py
```

## 🔧 Advanced Setup

### Using Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Now proceed with configuration
```

### Custom Configuration

Edit `.env` for advanced settings:

```env
# Required
TAVILY_API_KEY=your_key_here

# Optional: Fallback
JINA_API_KEY=your_jina_key_here

# Logging
LOG_LEVEL=INFO               # DEBUG for more detail
LOG_FILE=logs/agno.log       # Custom log location

# Performance
TIMEOUT_SECONDS=60           # Longer timeout
MIN_CONFIDENCE=0.7           # Higher confidence threshold

# Results
MAX_RESULTS=10               # More results per query
SEARCH_DEPTH=advanced        # More thorough searches (uses more API credits)
```

Create custom log directory:
```bash
mkdir logs
```

### System Requirements

**Minimum:**
- CPU: 1 core
- RAM: 512 MB
- Disk: 100 MB
- Network: Basic internet

**Recommended:**
- CPU: 2+ cores
- RAM: 1 GB
- Disk: 1 GB (for logs)
- Network: Stable broadband

## 📖 Learning Path

### Day 1: Basics
1. ✅ Complete Quick Start (above)
2. Read: `README.md` - Overview section
3. Practice: Run 10 different queries
4. Experiment: Try different output formats

### Day 2: Understanding
1. Read: `ARCHITECTURE.md` - System design
2. Read: `EXAMPLES.md` - Code examples
3. Experiment: Modify output formats
4. Practice: Use statistics feature

### Day 3: Integration
1. Read: `SETUP_GUIDE.md` - Integration section
2. Create: Simple Python script using the system
3. Try: Run as MCP server
4. Explore: Check logs in `agno_system.log`

### Day 4: Advanced
1. Read: Source code in `src/` directory
2. Experiment: Add custom preprocessing
3. Try: Integrate with your application
4. Explore: Add custom tools

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'mcp'"

**Solution:**
```bash
pip install mcp
# or
pip install -r requirements.txt
```

### Issue: "Configuration error: At least one API key must be configured"

**Solution:**
1. Check `.env` file exists in project root
2. Verify `TAVILY_API_KEY=your_actual_key` (no quotes, no spaces)
3. Make sure key is valid (test at tavily.com)
4. Restart terminal/IDE to reload environment

### Issue: "Request timed out"

**Solutions:**
1. Check internet connection
2. Increase timeout in `.env`: `TIMEOUT_SECONDS=60`
3. Try a simpler query first
4. Check if API services are online

### Issue: Import errors when running scripts

**Solution:**
```bash
# Always run from project root
cd D:\mcp-server

# Use module syntax
python -m src.cli "query"

# NOT: python src/cli.py "query"
```

### Issue: All tests pass but queries fail

**Solution:**
1. Check your API key is valid
2. Verify you have API credits/quota remaining
3. Check Tavily service status
4. Try with JINA_API_KEY as fallback
5. Review logs: `type agno_system.log` (Windows) or `cat agno_system.log` (Mac/Linux)

### Issue: Low confidence results

**Solutions:**
1. Make queries more specific
2. Lower threshold: `MIN_CONFIDENCE=0.3` in `.env`
3. Try `search_depth=advanced` for Tavily
4. Check logs for actual confidence scores

### Issue: "Permission denied" when creating .env

**Solution:**
```bash
# Windows (PowerShell as Administrator)
New-Item -Path .env -ItemType File

# Or simply create manually in file explorer
```

## 📊 Verify Installation

Run this checklist after setup:

```bash
# 1. Dependencies installed?
pip list | grep mcp
# Should show: mcp x.x.x

# 2. Configuration valid?
python -c "from src.config import get_config; c = get_config(); print(c.validate())"
# Should show: (True, None)

# 3. Logger working?
python -c "from src.logging_system import get_logger; get_logger().info('Test')"
# Should log to console and file

# 4. Tools available?
python test_system.py
# Should pass all tests

# 5. Can run queries?
python -m src.cli "test" --format json
# Should return JSON results
```

If all five pass: ✅ **Ready for production!**

## 🎓 Best Practices

### For CLI Usage

```bash
# Good queries (specific)
python -m src.cli "Python machine learning libraries comparison"
python -m src.cli "Latest climate change research 2024"

# Less optimal (too vague)
python -m src.cli "stuff about things"
python -m src.cli "news"
```

### For Programmatic Usage

```python
# Always use try-except
try:
    response = await orchestrator.process_request(query)
    if response.success:
        # Process results
        pass
    else:
        # Handle error
        print(response.error)
except Exception as e:
    # Handle unexpected errors
    print(f"Unexpected error: {e}")
```

### For Production

1. **Use virtual environment**
2. **Monitor logs regularly**: `tail -f agno_system.log`
3. **Set appropriate timeouts**: Consider your use case
4. **Handle errors gracefully**: Never expose raw errors to users
5. **Track statistics**: Use `get_statistics()` for monitoring
6. **Rotate logs**: Set up log rotation for production

## 🆘 Getting Help

### Check Documentation
1. `README.md` - Complete reference
2. `SETUP_GUIDE.md` - Detailed setup
3. `EXAMPLES.md` - Code examples
4. `ARCHITECTURE.md` - System design
5. `PROJECT_SUMMARY.md` - Overview

### Check Logs
```bash
# View recent logs
tail -n 50 agno_system.log

# Search for errors
grep ERROR agno_system.log

# Find fallback events
grep Fallback agno_system.log
```

### Debug Mode
```bash
# Enable debug logging in .env
LOG_LEVEL=DEBUG

# Run with debug output
python -m src.cli "query"

# Check detailed logs
cat agno_system.log
```

### Common Solutions
- ✅ Restart terminal/IDE after .env changes
- ✅ Run from project root directory
- ✅ Use module syntax: `python -m src.cli`
- ✅ Check API key validity
- ✅ Verify internet connection

## ✨ Pro Tips

1. **Start Simple**: Begin with basic queries before complex ones
2. **Use Statistics**: `--stats` flag shows system performance
3. **Try Formats**: Markdown is great for documentation
4. **Monitor Confidence**: Low confidence may indicate need to refine query
5. **Check Logs**: Logs show exactly what happened
6. **Fallback is OK**: Using Jina fallback doesn't mean failure
7. **Experiment**: The system is robust - try different things!

## 🎯 Success Indicators

You know the system is working correctly when:

✅ Tests pass (7/7)  
✅ Queries return results in 1-3 seconds  
✅ Confidence scores are typically 0.6-0.9  
✅ Logs show clear operation flow  
✅ Fallback triggers only occasionally  
✅ Error messages are clear and actionable  
✅ Statistics show high success rate  

## 🚀 You're Ready!

Your Agno MCP Orchestration System is now:
- ✅ Installed
- ✅ Configured  
- ✅ Tested
- ✅ Ready to use

**Start exploring:**
```bash
python -m src.cli "Tell me about something interesting"
```

**Happy searching! 🎉**

---

*Need more help? Check the comprehensive documentation in README.md*

