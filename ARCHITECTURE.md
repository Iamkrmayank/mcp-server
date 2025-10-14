# Architecture - Agno MCP Orchestration System

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACES                                │
├─────────────────┬───────────────────┬──────────────────┬────────────────┤
│   MCP Client    │    CLI Interface   │  Programmatic   │   REST API*    │
│ (Claude, etc)   │   (Terminal)       │   (Python)      │  (Optional)    │
└────────┬────────┴─────────┬──────────┴────────┬─────────┴────────┬──────┘
         │                  │                   │                  │
         └──────────────────┴───────────────────┴──────────────────┘
                                      │
                                      ↓
         ┌──────────────────────────────────────────────────────┐
         │         AGNO ORCHESTRATOR (Core Control)             │
         │  • Request preprocessing & query optimization        │
         │  • Tool coordination & priority management           │
         │  • Fallback mechanism orchestration                  │
         │  • Response formatting (JSON/Markdown/Structured)    │
         │  • Statistics tracking & performance monitoring      │
         └──────────────────┬───────────────────────────────────┘
                            │
                            ↓
         ┌──────────────────────────────────────────────────────┐
         │      MCP TOOLS INTEGRATION FRAMEWORK                 │
         │  • Dynamic tool registry & discovery                 │
         │  • Tool lifecycle management                         │
         │  • Result validation & confidence scoring            │
         │  • Execution history tracking                        │
         │  • Automatic failover handling                       │
         └──────────────────┬───────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ↓                           ↓
    ┌─────────────────┐         ┌─────────────────┐
    │  TAVILY TOOL    │         │   JINA TOOL     │
    │  (Priority: 0)  │         │  (Priority: 1)  │
    │                 │         │                 │
    │  • Primary      │         │  • Fallback     │
    │  • Fast         │         │  • Semantic     │
    │  • Structured   │         │  • Flexible     │
    └────────┬────────┘         └────────┬────────┘
             │                           │
             └───────────┬───────────────┘
                         │
              ┌──────────┴──────────┐
              │                     │
              ↓                     ↓
    ┌──────────────────┐  ┌──────────────────┐
    │  TAVILY API      │  │   JINA API       │
    │  (External)      │  │  (External)      │
    └──────────────────┘  └──────────────────┘
                         │
                         ↓
         ┌──────────────────────────────────────────────┐
         │      COMPREHENSIVE LOGGING SYSTEM             │
         │  • UTC timestamps on all operations           │
         │  • Duration tracking (milliseconds)           │
         │  • Success/failure status                     │
         │  • Data quality metrics                       │
         │  • Fallback event logging                     │
         │  • File & console output                      │
         └───────────────────────────────────────────────┘
```

## Request Flow Diagram

```
User Query: "Tell me about Microsoft 2024 report"
                    │
                    ↓
        ┌───────────────────────┐
        │  Input Preprocessing  │
        │  "microsoft 2024      │
        │   report"             │
        └───────────┬───────────┘
                    │
                    ↓
        ┌───────────────────────┐
        │  Agno Orchestrator    │
        │  Analyzes Query       │
        └───────────┬───────────┘
                    │
                    ↓
        ┌───────────────────────┐
        │  MCP Framework        │
        │  Selects Tools by     │
        │  Priority             │
        └───────────┬───────────┘
                    │
                    ↓
        ┌───────────────────────┐
        │  PRIMARY: Tavily Tool │
        │  Executes Search      │
        └───────────┬───────────┘
                    │
            ┌───────┴────────┐
            │                │
         SUCCESS          FAILURE
            │                │
            ↓                ↓
    ┌──────────────┐  ┌──────────────┐
    │ Validate     │  │  Log Failure │
    │ Result       │  │  Trigger     │
    │ Confidence   │  │  Fallback    │
    └──────┬───────┘  └──────┬───────┘
           │                 │
      HIGH │ LOW             │
           │  │              │
           │  └──────────────┘
           │                 │
           │                 ↓
           │      ┌──────────────────┐
           │      │ FALLBACK: Jina   │
           │      │ Tool Executes    │
           │      └──────┬───────────┘
           │             │
           │             ↓
           │      ┌──────────────────┐
           │      │ Validate Result  │
           │      └──────┬───────────┘
           │             │
           └─────────────┘
                    │
                    ↓
        ┌───────────────────────┐
        │  Format Response      │
        │  • Structured         │
        │  • JSON               │
        │  • Markdown           │
        └───────────┬───────────┘
                    │
                    ↓
        ┌───────────────────────┐
        │  Return to User with  │
        │  • Results            │
        │  • Metadata           │
        │  • Feedback           │
        │  • Execution Log      │
        └───────────────────────┘
```

## Component Interaction Matrix

```
┌─────────────────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
│                     │  Agno    │   MCP    │  Tools   │ Logging  │  Config  │
│                     │  Orch.   │  Frame.  │          │ System   │  Mgmt    │
├─────────────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ Agno Orchestrator   │    -     │  Uses    │  Via     │  Uses    │  Uses    │
│                     │          │          │  Frame.  │          │          │
├─────────────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ MCP Framework       │  Used by │    -     │  Manages │  Uses    │    -     │
│                     │          │          │          │          │          │
├─────────────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ Tools (Tavily/Jina) │  Used by │  Reg. in │    -     │  Uses    │    -     │
│                     │          │          │          │          │          │
├─────────────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ Logging System      │  Used by │  Used by │  Used by │    -     │    -     │
│                     │  All     │  All     │  All     │          │          │
├─────────────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ Config Management   │  Used by │    -     │    -     │  Config  │    -     │
│                     │          │          │          │  Logger  │          │
└─────────────────────┴──────────┴──────────┴──────────┴──────────┴──────────┘
```

## Data Flow

### Request Data Flow

```
User Input (String)
    ↓
Query (Preprocessed String)
    ↓
Tool Execution Parameters (Dict)
    ↓
ToolResult (Object)
    ↓
AgnoResponse (Object)
    ↓
Formatted Output (String: JSON/Markdown/Structured)
```

### ToolResult Structure

```python
ToolResult {
    status: ToolStatus           # SUCCESS | FAILURE | TIMEOUT | NOT_FOUND
    data: Dict[str, Any]        # Search results
    error: Optional[str]         # Error message if any
    duration_ms: float           # Execution time
    confidence: float            # 0.0 - 1.0
    metadata: Dict[str, Any]    # Additional info
}
```

### AgnoResponse Structure

```python
AgnoResponse {
    success: bool                # Overall success
    data: Dict[str, Any]        # Results from tools
    error: Optional[str]         # Error if failed
    metadata: Dict[str, Any]    # Performance metrics
    execution_log: List[Dict]    # History of executions
    feedback: str               # User-friendly message
}
```

## Module Dependencies

```
server.py
    ├── agno_orchestrator.py
    │   ├── mcp_tools_integration.py
    │   │   ├── logging_system.py
    │   │   └── tools/
    │   │       ├── tavily_tool.py
    │   │       │   ├── mcp_tools_integration.py (BaseTool)
    │   │       │   └── logging_system.py
    │   │       └── jina_tool.py
    │   │           ├── mcp_tools_integration.py (BaseTool)
    │   │           └── logging_system.py
    │   ├── logging_system.py
    │   └── tools/ (imports)
    ├── logging_system.py
    └── config.py

cli.py
    ├── agno_orchestrator.py (same tree as above)
    ├── logging_system.py
    └── config.py

No circular dependencies ✓
Clean separation of concerns ✓
```

## Class Hierarchy

```
BaseTool (Abstract)
    ├── TavilyTool
    └── JinaTool

ToolResult (Dataclass)
    └── Used by all tools

ToolStatus (Enum)
    ├── SUCCESS
    ├── FAILURE
    ├── TIMEOUT
    └── NOT_FOUND

ToolRegistry
    └── Manages tool instances

MCPToolsFramework
    ├── Has: ToolRegistry
    └── Coordinates: BaseTool instances

AgnoOrchestrator
    ├── Has: MCPToolsFramework
    └── Returns: AgnoResponse

AgnoResponse (Dataclass)
    └── Returned to users

AgnoLogger
    └── Singleton pattern

AgnoConfig (Dataclass)
    └── Singleton pattern
```

## Execution Patterns

### Pattern 1: Successful Primary Tool

```
Request → Agno → Framework → Tavily → Success (confidence > 0.5)
                                           ↓
                                     Format & Return
```

### Pattern 2: Fallback Triggered

```
Request → Agno → Framework → Tavily → Failure/Low Confidence
                                           ↓
                                      Log Fallback
                                           ↓
                                      Jina → Success
                                           ↓
                                     Format & Return
```

### Pattern 3: All Tools Failed

```
Request → Agno → Framework → Tavily → Failure
                                           ↓
                                      Log Fallback
                                           ↓
                                      Jina → Failure
                                           ↓
                                      Return Error Response
```

## Configuration Flow

```
Environment Variables (.env)
    ↓
python-dotenv loads
    ↓
AgnoConfig.from_env()
    ↓
Configuration validation
    ↓
Passed to components during initialization
```

## Logging Flow

```
Any Component Operation
    ↓
get_logger() → Singleton AgnoLogger
    ↓
log_operation() / log_request_start() / log_request_end()
    ↓
Format with UTC timestamp + metadata
    ↓
Write to:
    ├── File (agno_system.log)
    └── Console (stdout)
```

## Error Handling Strategy

```
Level 1: Tool Level
    ├── Try/Except blocks
    ├── Return ToolResult with error
    └── Log error details

Level 2: Framework Level
    ├── Catch tool errors
    ├── Trigger fallback
    └── Track execution history

Level 3: Orchestrator Level
    ├── Handle all failures
    ├── Generate user feedback
    └── Return AgnoResponse

Level 4: Interface Level (Server/CLI)
    ├── Catch unexpected errors
    ├── Format error messages
    └── Return to user
```

## Performance Characteristics

### Typical Response Times

```
Tavily (Primary):     1,000 - 2,000ms
Jina (Fallback):      1,500 - 3,000ms
Preprocessing:            1 - 10ms
Formatting:              5 - 20ms
Logging overhead:        1 - 5ms

Total (Success):     ~1,000 - 2,000ms
Total (Fallback):    ~2,500 - 5,000ms
```

### Memory Usage

```
Base System:          ~50MB
Per Request:          ~1-5MB
With Results:         ~10-20MB (depends on result size)
Logging Buffer:       ~1MB
```

### Scalability

```
Concurrent Requests:  Limited by API rate limits
Tool Registration:    O(1) lookup
Result Validation:    O(n) where n = number of results
Fallback Chain:       O(t) where t = number of tools
```

## Extension Points

### Adding New Tools

```python
# 1. Create tool class
class MyTool(BaseTool):
    def __init__(self):
        super().__init__(name="MyTool", priority=2)
    
    def is_available(self) -> bool:
        return True
    
    async def execute(self, query: str, **kwargs) -> ToolResult:
        # Implementation
        pass

# 2. Register in orchestrator
def _register_tools(self):
    self.framework.register_tool(MyTool())
```

### Adding New Output Formats

```python
# In AgnoOrchestrator.format_response()
elif format_type == "xml":
    # Add XML formatting logic
    pass
```

### Adding New MCP Tools

```python
# In server.py
@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        # Existing tools...
        Tool(
            name="my_new_tool",
            description="...",
            inputSchema={...}
        )
    ]
```

## Security Architecture

```
API Keys
    ├── Stored in .env (git-ignored)
    ├── Never logged
    ├── Passed via environment
    └── Masked in config display

HTTP Communications
    ├── HTTPS only
    ├── Timeout protection
    └── Error sanitization

Input Validation
    ├── Query sanitization
    ├── Parameter validation
    └── Type checking

Output Sanitization
    ├── Error message filtering
    ├── No sensitive data exposure
    └── Safe formatting
```

## Deployment Architectures

### Architecture 1: Standalone MCP Server

```
┌─────────────────┐
│  MCP Client     │
│  (Claude, etc)  │
└────────┬────────┘
         │ stdio
         ↓
┌─────────────────┐
│  Agno Server    │
│  (This System)  │
└────────┬────────┘
         │ HTTPS
         ↓
┌─────────────────┐
│  External APIs  │
│  (Tavily, Jina) │
└─────────────────┘
```

### Architecture 2: Web Service

```
┌─────────────────┐
│  Web Clients    │
└────────┬────────┘
         │ HTTP/REST
         ↓
┌─────────────────┐
│  Web Framework  │
│  (FastAPI, etc) │
└────────┬────────┘
         │ Python
         ↓
┌─────────────────┐
│  Agno Orch.     │
│  (Library Mode) │
└────────┬────────┘
         │ HTTPS
         ↓
┌─────────────────┐
│  External APIs  │
└─────────────────┘
```

### Architecture 3: Microservice

```
┌─────────────────┐
│  API Gateway    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ↓         ↓
┌────────┐ ┌────────┐
│ Agno   │ │ Other  │
│ Service│ │ Services│
└───┬────┘ └────────┘
    │
    ↓
┌────────┐
│ Cache  │
└────────┘
```

## Monitoring Points

```
Key Metrics to Track:
    ├── Request rate (requests/second)
    ├── Success rate (%)
    ├── Fallback rate (%)
    ├── Average response time (ms)
    ├── P95/P99 response times
    ├── Error rate by type
    ├── Tool availability
    └── Confidence score distribution

Log Analysis:
    ├── Search for "ERROR" for failures
    ├── Track "Fallback_Triggered" events
    ├── Monitor duration_ms trends
    ├── Analyze confidence scores
    └── Check timeout occurrences
```

---

This architecture supports the system requirements of:
- ✅ Priority-based tool execution
- ✅ Automatic fallback mechanisms
- ✅ Comprehensive logging
- ✅ MCP tools integration
- ✅ Flexible output formats
- ✅ Transparent user feedback
- ✅ Extensibility and maintainability

