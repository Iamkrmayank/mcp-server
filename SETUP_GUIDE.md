# Setup Guide - Agno MCP Orchestration System

This guide will walk you through setting up and running the Agno orchestration system.

## Step 1: Prerequisites

Ensure you have:
- Python 3.10 or higher installed
- pip package manager
- A Tavily API key (required) - Get one at [https://tavily.com/](https://tavily.com/)
- Optional: Jina API key for fallback

## Step 2: Installation

### 2.1 Clone or Download the Project

```bash
cd D:\mcp-server
```

### 2.2 Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `mcp` - Model Context Protocol SDK
- `httpx` - Async HTTP client
- `pydantic` - Data validation
- `python-dotenv` - Environment variable management
- `aiohttp` - Async HTTP server/client

## Step 3: Configuration

### 3.1 Create Environment File

Create a `.env` file in the project root:

```bash
# On Windows PowerShell
New-Item -Path .env -ItemType File

# Or simply create manually
```

### 3.2 Add Your API Keys

Edit `.env` and add:

```env
# Required: Get from https://tavily.com/
TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxxxxxxx

# Optional: Get from https://jina.ai/
JINA_API_KEY=jina_xxxxxxxxxxxxxxxxxxxxx

# Optional Configuration
LOG_LEVEL=INFO
LOG_FILE=agno_system.log
TIMEOUT_SECONDS=30
MAX_RETRIES=3
MIN_CONFIDENCE=0.5
```

### 3.3 Verify Configuration

Test your setup:

```bash
python -m src.cli "test query" --format json
```

If you see results, configuration is correct!

## Step 4: Running the System

### Option A: MCP Server Mode

For integration with MCP-compatible clients:

```bash
python -m src.server
```

The server will:
- Initialize the Agno orchestrator
- Register available tools (Tavily, Jina)
- Listen for MCP requests on stdin/stdout
- Log all operations to `agno_system.log`

### Option B: CLI Mode

For standalone testing and queries:

```bash
# Basic query
python -m src.cli "Tell me about Microsoft 2024 report"

# With custom formatting
python -m src.cli "Latest AI news" --format markdown

# Show statistics
python -m src.cli "Climate change updates" --stats

# More results
python -m src.cli "Python tutorials" --max-results 10
```

### Option C: Programmatic Usage

Create a Python script:

```python
# my_script.py
import asyncio
from src.agno_orchestrator import AgnoOrchestrator

async def main():
    # Initialize
    orchestrator = AgnoOrchestrator()
    
    # Execute query
    response = await orchestrator.process_request(
        user_input="What's new in AI?",
        max_results=5
    )
    
    # Display results
    if response.success:
        output = orchestrator.format_response(
            response, 
            format_type="structured"
        )
        print(output)
    else:
        print(f"Error: {response.error}")
    
    # Show stats
    stats = orchestrator.get_statistics()
    print(f"\nSuccess rate: {stats['success_rate']:.1f}%")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:

```bash
python my_script.py
```

## Step 5: Verify Everything Works

### Test 1: Basic Query

```bash
python -m src.cli "Tell me about Python programming"
```

Expected output:
- Query preprocessing
- Tool execution (Tavily)
- Results with sources
- Confidence score
- Duration metrics

### Test 2: Fallback Mechanism

To test fallback, temporarily set an invalid Tavily key:

```env
TAVILY_API_KEY=invalid_key
```

Run:
```bash
python -m src.cli "test query"
```

You should see:
- Tavily fails
- Automatic fallback to Jina
- Message: "Primary source unavailable, fallback mechanism used"

### Test 3: Statistics

```bash
python -m src.cli "test query" --stats
```

Should show:
- Total requests
- Success rate
- Fallback usage
- Available tools

## Step 6: Monitor Logs

View real-time logs:

```bash
# On Windows PowerShell
Get-Content agno_system.log -Wait

# Or open in text editor
notepad agno_system.log
```

Log entries include:
- Timestamps (UTC)
- Operation names
- Duration (ms)
- Success/failure status
- Confidence scores
- Fallback events

## Troubleshooting

### Issue: "No module named 'mcp'"

**Solution:**
```bash
pip install mcp
# or
pip install -r requirements.txt
```

### Issue: "Configuration error: At least one API key must be configured"

**Solution:**
1. Verify `.env` file exists in project root
2. Check `TAVILY_API_KEY` is set and valid
3. Ensure no extra spaces around the key

### Issue: "Request timed out"

**Solution:**
1. Increase timeout: `TIMEOUT_SECONDS=60` in `.env`
2. Check internet connection
3. Verify API services are online

### Issue: Import errors

**Solution:**
```bash
# Ensure you're in the project root
cd D:\mcp-server

# Run with module syntax
python -m src.cli "query"

# Not: python src/cli.py "query"
```

## Advanced Configuration

### Custom Tool Priority

Edit `src/tools/tavily_tool.py` and `src/tools/jina_tool.py`:

```python
# Lower number = higher priority
super().__init__(name="Tavily", priority=0)  # Primary
super().__init__(name="Jina", priority=1)    # Fallback
```

### Adjust Confidence Threshold

In `.env`:
```env
MIN_CONFIDENCE=0.7  # Higher = stricter (0.0-1.0)
```

### Custom Log Location

In `.env`:
```env
LOG_FILE=logs/agno.log
```

Create the directory:
```bash
mkdir logs
```

## Integration with MCP Clients

To use with Claude Desktop or other MCP clients:

1. Add to MCP configuration:

```json
{
  "mcpServers": {
    "agno-orchestrator": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "D:\\mcp-server",
      "env": {
        "TAVILY_API_KEY": "your_key_here",
        "JINA_API_KEY": "your_key_here"
      }
    }
  }
}
```

2. Restart the MCP client

3. Available tools:
   - `search_web` - Search with automatic fallback
   - `get_statistics` - View system stats

## Next Steps

- Read `README.md` for detailed architecture
- Explore `src/` directory for code structure
- Add custom tools (see README.md "Adding New Tools")
- Integrate with your applications

## Support

- Check logs: `agno_system.log`
- Review README.md for troubleshooting
- Ensure API keys are valid
- Test with simple queries first

---

**Ready to start?**

```bash
python -m src.cli "Tell me about artificial intelligence"
```

