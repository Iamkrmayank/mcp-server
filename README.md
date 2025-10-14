# Agno MCP Orchestration System

A comprehensive web scraping orchestration framework with automatic fallback mechanisms, built on the Model Context Protocol (MCP).

## 🎯 System Overview

The Agno orchestration system provides a robust, production-ready solution for web data extraction with:

- **Multi-source scraping** with intelligent fallback
- **Comprehensive logging** with timestamps and performance metrics
- **MCP integration** for seamless tool coordination
- **Natural language queries** with automatic preprocessing
- **Transparent feedback** on execution status

### Architecture

```
User Input
   ↓
Agno Orchestrator (preprocesses & coordinates)
   ↓
MCP Tools Framework (manages execution)
   ↓
Primary: Tavily API (fast, structured extraction)
   ↓ (on failure)
Fallback: Jina API (semantic understanding)
   ↓
Formatted Response + Execution Logs
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- API keys for:
  - [Tavily](https://tavily.com/) (primary scraping)
  - [Jina](https://jina.ai/) (fallback scraping, optional)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/mcp-server.git
cd mcp-server
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your API keys
# Required:
TAVILY_API_KEY=your_tavily_api_key_here

# Optional:
JINA_API_KEY=your_jina_api_key_here

# Configuration (optional):
LOG_LEVEL=INFO
LOG_FILE=agno_system.log
MAX_RETRIES=3
TIMEOUT_SECONDS=30
```

### Usage

#### As MCP Server

Run as an MCP server (for integration with MCP-compatible clients):

```bash
python -m src.server
```

#### As CLI Tool

Run standalone queries from the command line:

```bash
# Basic usage
python -m src.cli "Tell me about Microsoft 2024 report"

# With custom formatting
python -m src.cli "What happened in AI in 2024?" --format markdown

# With more results
python -m src.cli "Latest climate change news" --max-results 10

# Show statistics
python -m src.cli "Search query" --stats
```

#### Programmatic Usage

```python
import asyncio
from src.agno_orchestrator import AgnoOrchestrator

async def main():
    # Initialize orchestrator
    orchestrator = AgnoOrchestrator()
    
    # Process a request
    response = await orchestrator.process_request(
        user_input="Tell me about Microsoft 2024 report",
        max_results=5
    )
    
    # Format and display
    if response.success:
        formatted = orchestrator.format_response(response, format_type="markdown")
        print(formatted)
    else:
        print(f"Error: {response.error}")

asyncio.run(main())
```

## 📋 Core Components

### 1. Agno Orchestrator (`src/agno_orchestrator.py`)

Central control layer that:
- Preprocesses natural language queries
- Coordinates tool execution with priority-based selection
- Manages automatic fallback mechanisms
- Provides transparent user feedback
- Tracks system statistics

**Key Methods:**
- `process_request(user_input, **kwargs)` - Main entry point for queries
- `format_response(response, format_type)` - Format results as structured/JSON/Markdown
- `get_statistics()` - Retrieve system performance metrics

### 2. MCP Tools Framework (`src/mcp_tools_integration.py`)

Unified interface for tool management:
- Dynamic tool registration and discovery
- Priority-based execution ordering
- Result validation with confidence scoring
- Execution history tracking
- Automatic failover handling

**Key Classes:**
- `BaseTool` - Abstract base for all scraping tools
- `ToolRegistry` - Central registry for tool management
- `MCPToolsFramework` - Main coordination framework
- `ToolResult` - Standardized result container

### 3. Scraping Tools

#### Tavily Tool (`src/tools/tavily_tool.py`)
- **Priority:** 0 (highest)
- **Purpose:** Fast, structured web extraction
- **Features:**
  - Configurable search depth (basic/advanced)
  - Domain filtering (include/exclude)
  - Automatic confidence calculation
  - Rich result metadata

#### Jina Tool (`src/tools/jina_tool.py`)
- **Priority:** 1 (fallback)
- **Purpose:** Semantic web understanding
- **Features:**
  - Search API integration
  - Reader API for content extraction
  - Fallback search mechanisms
  - Works without API key (rate-limited)

### 4. Logging System (`src/logging_system.py`)

Comprehensive logging with:
- UTC timestamps on all events
- Operation-level tracking (start/end)
- Duration measurements (milliseconds)
- Success/failure status
- Data quality metrics (confidence, completeness)
- Fallback event logging

**Log Format:**
```
2024-10-14 15:30:45 UTC - AgnoSystem - INFO - [Tavily_Request] Status: success | Duration: 1250.45ms | Quality: {"confidence": 0.85}
```

### 5. Configuration Management (`src/config.py`)

Centralized configuration:
- Environment variable loading
- Configuration validation
- Default value management
- Secure API key handling

## 🔧 Configuration Options

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `TAVILY_API_KEY` | Tavily API key | - | Yes* |
| `JINA_API_KEY` | Jina API key | - | No |
| `LOG_LEVEL` | Logging level | INFO | No |
| `LOG_FILE` | Log file path | agno_system.log | No |
| `TIMEOUT_SECONDS` | Request timeout | 30 | No |
| `MAX_RETRIES` | Max retry attempts | 3 | No |
| `MIN_CONFIDENCE` | Min confidence threshold | 0.5 | No |

*At least one API key (Tavily or Jina) must be configured.

## 📊 System Features

### Priority-Based Execution

Tools are executed in priority order:
1. **Tavily** (priority 0) - Primary fast extraction
2. **Jina** (priority 1) - Semantic fallback

On failure or low confidence, the system automatically tries the next tool.

### Automatic Fallback

```python
# Fallback triggers when:
1. Primary tool fails (error, timeout)
2. Result confidence below threshold
3. Empty or invalid data returned

# Fallback is logged:
{
  "timestamp": "2024-10-14T15:30:45.123Z",
  "operation": "Fallback_Triggered",
  "from": "Tavily",
  "to": "Jina",
  "reason": "Tavily request timeout"
}
```

### Confidence Scoring

Each result includes a confidence score (0.0-1.0) based on:
- Number of results found
- Quality scores from source
- Presence of summary answer
- Content completeness

### Transparent Feedback

Users receive clear status messages:
- ✓ **Success:** "Results retrieved successfully from Tavily."
- ✓ **Fallback Used:** "Primary source unavailable, fallback mechanism used."
- ⚠ **Timeout:** "Request timed out. Please try again."
- ✗ **Failure:** "Unable to retrieve results. All sources failed."

## 📝 Logging Standards

Every operation logs:
1. **Timestamp** - UTC ISO format
2. **Operation Name** - e.g., "Tavily_Request"
3. **Duration** - Execution time in milliseconds
4. **Status** - success/failure/timeout/in_progress
5. **Error Message** - If applicable
6. **Data Quality** - Confidence and completeness metrics
7. **Metadata** - Additional context

Example log entry:
```json
{
  "timestamp": "2024-10-14T15:30:45.123456Z",
  "operation": "Tavily_Request_End",
  "status": "success",
  "duration_ms": 1250.45,
  "error": null,
  "data_quality": {
    "confidence": 0.85
  },
  "metadata": {
    "result_count": 5,
    "search_depth": "basic"
  }
}
```

## 🛠️ Development

### Project Structure

```
mcp-server/
├── src/
│   ├── __init__.py
│   ├── server.py              # MCP server entry point
│   ├── cli.py                 # Command-line interface
│   ├── config.py              # Configuration management
│   ├── logging_system.py      # Comprehensive logging
│   ├── agno_orchestrator.py   # Main orchestration logic
│   ├── mcp_tools_integration.py  # Tool framework
│   └── tools/
│       ├── __init__.py
│       ├── tavily_tool.py     # Tavily integration
│       └── jina_tool.py       # Jina integration
├── requirements.txt           # Python dependencies
├── .env.example              # Example environment file
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```

### Adding New Tools

1. Create a new tool class inheriting from `BaseTool`:

```python
from src.mcp_tools_integration import BaseTool, ToolResult, ToolStatus

class MyCustomTool(BaseTool):
    def __init__(self, api_key=None):
        super().__init__(name="MyTool", priority=2)  # Lower priority = fallback
        self.api_key = api_key
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def execute(self, query: str, **kwargs) -> ToolResult:
        # Implement your scraping logic
        try:
            # ... scraping code ...
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={"results": []},
                confidence=0.8
            )
        except Exception as e:
            return ToolResult(
                status=ToolStatus.FAILURE,
                error=str(e)
            )
```

2. Register the tool in the orchestrator:

```python
from src.tools.my_custom_tool import MyCustomTool

# In AgnoOrchestrator._register_tools()
custom_tool = MyCustomTool(api_key=custom_api_key)
self.framework.register_tool(custom_tool)
```

### Running Tests

```bash
# Test CLI
python -m src.cli "test query" --format json

# Test specific queries
python -m src.cli "Microsoft 2024 report" --stats
python -m src.cli "Latest AI news" --max-results 10 --format markdown
```

## 📈 System Statistics

Track system performance:

```python
stats = orchestrator.get_statistics()
# Returns:
{
  "total_requests": 100,
  "successful_requests": 95,
  "success_rate": 95.0,
  "fallback_count": 12,
  "fallback_rate": 12.0,
  "available_tools": 2,
  "registered_tools": 2
}
```

## 🔒 Security

- API keys stored in environment variables
- Keys never logged or exposed in output
- HTTPS for all API communications
- No sensitive data stored in logs

## 🐛 Troubleshooting

### "No scraping tools are available"
- Check that at least one API key is configured in `.env`
- Verify API keys are valid

### "Request timed out"
- Increase `TIMEOUT_SECONDS` in `.env`
- Check internet connection
- Verify API services are operational

### "All tools failed"
- Check API key validity
- Review logs in `agno_system.log`
- Ensure query is well-formed
- Try with different queries

### Low confidence results
- Adjust `MIN_CONFIDENCE` threshold
- Use more specific queries
- Try with `search_depth=advanced` for Tavily

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues, questions, or feature requests:
- Open an issue on GitHub
- Check existing issues for solutions
- Review logs for debugging information

## 🎉 Acknowledgments

Built with:
- [MCP (Model Context Protocol)](https://modelcontextprotocol.io/)
- [Tavily API](https://tavily.com/)
- [Jina AI](https://jina.ai/)
- Python asyncio and httpx

---

**Version:** 1.0.0  
**Last Updated:** October 2025

