# Examples - Agno MCP Orchestration System

This document provides practical examples of using the Agno orchestration system.

## Command-Line Examples

### Basic Queries

```bash
# Simple search
python -m src.cli "What is machine learning?"

# Technology news
python -m src.cli "Latest developments in quantum computing"

# Company information
python -m src.cli "Tell me about Microsoft 2024 annual report"

# Scientific topics
python -m src.cli "Recent discoveries in astronomy"
```

### Formatted Output

#### Structured Format (Default)
```bash
python -m src.cli "Python programming basics"
```

Output:
```
================================================================================
AGNO ORCHESTRATION SYSTEM - RESULTS
================================================================================

✓ Results retrieved successfully from Tavily.

ANSWER:
--------------------------------------------------------------------------------
Python is a high-level, interpreted programming language known for its 
simplicity and readability...

SOURCES:
--------------------------------------------------------------------------------

[1] Python Tutorial - Official Documentation
    URL: https://docs.python.org/3/tutorial/
    Python is an easy to learn, powerful programming language. It has 
    efficient high-level data structures...

[2] Learn Python - Beginner's Guide
    URL: https://www.learnpython.org/
    Python is a popular programming language used for web development, 
    data analysis, artificial intelligence...

METADATA:
--------------------------------------------------------------------------------
Duration: 1245.32ms
Confidence: 87.50%
Source: Tavily

================================================================================
```

#### JSON Format
```bash
python -m src.cli "Artificial intelligence trends" --format json
```

Output:
```json
{
  "success": true,
  "data": {
    "query": "artificial intelligence trends",
    "answer": "AI is rapidly evolving with breakthroughs in...",
    "results": [
      {
        "title": "AI Trends 2024",
        "url": "https://example.com/ai-trends",
        "content": "...",
        "score": 0.95
      }
    ]
  },
  "metadata": {
    "duration_ms": 1523.45,
    "confidence": 0.89,
    "source": "Tavily"
  },
  "feedback": "✓ Results retrieved successfully from Tavily."
}
```

#### Markdown Format
```bash
python -m src.cli "Machine learning algorithms" --format markdown
```

Output:
```markdown
# Agno Search Results

✓ Results retrieved successfully from Tavily.

## Answer

Machine learning algorithms are computational methods that enable 
systems to learn from data...

## Sources

### 1. Introduction to Machine Learning Algorithms

**URL:** https://example.com/ml-algorithms

Machine learning encompasses various algorithms including supervised, 
unsupervised, and reinforcement learning...

---

### 2. Popular ML Algorithms Explained

**URL:** https://example.com/ml-explained

Common algorithms include linear regression, decision trees, neural 
networks, and support vector machines...

---

## Metadata

- **Duration:** 1423.67ms
- **Confidence:** 85.00%
- **Source:** Tavily
```

### Advanced Options

#### More Results
```bash
python -m src.cli "Best restaurants in Paris" --max-results 10
```

#### With Statistics
```bash
python -m src.cli "Climate change solutions" --stats
```

Output includes:
```
================================================================================
STATISTICS
================================================================================

Total Requests: 15
Successful Requests: 14
Success Rate: 93.33%
Fallback Count: 2
Fallback Rate: 13.33%

Available Tools: 2
Registered Tools: 2

================================================================================
```

## Programmatic Examples

### Example 1: Simple Query

```python
import asyncio
from src.agno_orchestrator import AgnoOrchestrator

async def simple_search():
    orchestrator = AgnoOrchestrator()
    
    response = await orchestrator.process_request(
        user_input="What is Python?"
    )
    
    if response.success:
        print(f"Answer: {response.data['answer']}")
        print(f"Found {len(response.data['results'])} sources")
    else:
        print(f"Error: {response.error}")

asyncio.run(simple_search())
```

### Example 2: Multiple Queries

```python
import asyncio
from src.agno_orchestrator import AgnoOrchestrator

async def batch_search():
    orchestrator = AgnoOrchestrator()
    
    queries = [
        "What is artificial intelligence?",
        "Latest machine learning trends",
        "Python vs JavaScript"
    ]
    
    for query in queries:
        print(f"\nSearching: {query}")
        response = await orchestrator.process_request(query)
        
        if response.success:
            print(f"✓ {response.data['answer'][:100]}...")
        else:
            print(f"✗ {response.error}")
    
    # Show final statistics
    stats = orchestrator.get_statistics()
    print(f"\n\nSuccess Rate: {stats['success_rate']:.1f}%")
    print(f"Fallback Rate: {stats['fallback_rate']:.1f}%")

asyncio.run(batch_search())
```

### Example 3: Custom Formatting

```python
import asyncio
from src.agno_orchestrator import AgnoOrchestrator

async def custom_format():
    orchestrator = AgnoOrchestrator()
    
    response = await orchestrator.process_request(
        user_input="Machine learning basics"
    )
    
    if response.success:
        # Get markdown output
        md_output = orchestrator.format_response(
            response, 
            format_type="markdown"
        )
        
        # Save to file
        with open("results.md", "w", encoding="utf-8") as f:
            f.write(md_output)
        
        print("Results saved to results.md")

asyncio.run(custom_format())
```

### Example 4: Error Handling

```python
import asyncio
from src.agno_orchestrator import AgnoOrchestrator

async def robust_search():
    orchestrator = AgnoOrchestrator()
    
    try:
        response = await orchestrator.process_request(
            user_input="Complex query here",
            max_results=10
        )
        
        if response.success:
            # Process results
            data = response.data
            confidence = response.metadata.get('confidence', 0)
            
            if confidence > 0.8:
                print("High confidence results!")
            elif confidence > 0.5:
                print("Moderate confidence results")
            else:
                print("Low confidence, consider refining query")
            
            # Display results
            for i, result in enumerate(data['results'], 1):
                print(f"\n{i}. {result['title']}")
                print(f"   {result['url']}")
        
        else:
            print(f"Search failed: {response.error}")
            print(f"Feedback: {response.feedback}")
    
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

asyncio.run(robust_search())
```

### Example 5: Integration with Web App

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.agno_orchestrator import AgnoOrchestrator
import asyncio

app = FastAPI()
orchestrator = AgnoOrchestrator()

class SearchRequest(BaseModel):
    query: str
    max_results: int = 5
    format: str = "json"

class SearchResponse(BaseModel):
    success: bool
    data: dict = None
    error: str = None
    metadata: dict = None

@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Search endpoint using Agno orchestrator."""
    try:
        response = await orchestrator.process_request(
            user_input=request.query,
            max_results=request.max_results
        )
        
        return SearchResponse(
            success=response.success,
            data=response.data,
            error=response.error,
            metadata=response.metadata
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Get system statistics."""
    return orchestrator.get_statistics()

# Run with: uvicorn example_webapp:app --reload
```

### Example 6: Monitoring and Logging

```python
import asyncio
from src.agno_orchestrator import AgnoOrchestrator
from src.logging_system import get_logger

async def monitored_search():
    logger = get_logger()
    orchestrator = AgnoOrchestrator()
    
    logger.info("Starting monitored search session")
    
    queries = [
        "Python tutorials",
        "JavaScript frameworks",
        "Database design patterns"
    ]
    
    results_summary = []
    
    for query in queries:
        logger.info(f"Processing query: {query}")
        
        response = await orchestrator.process_request(query)
        
        results_summary.append({
            "query": query,
            "success": response.success,
            "duration": response.metadata.get('duration_ms', 0),
            "confidence": response.metadata.get('confidence', 0)
        })
        
        logger.info(
            f"Query completed: success={response.success}, "
            f"duration={response.metadata.get('duration_ms', 0):.2f}ms"
        )
    
    # Summary report
    logger.info("Session summary:")
    for summary in results_summary:
        logger.info(
            f"  {summary['query']}: "
            f"success={summary['success']}, "
            f"confidence={summary['confidence']:.2%}"
        )
    
    stats = orchestrator.get_statistics()
    logger.info(f"Overall success rate: {stats['success_rate']:.1f}%")

asyncio.run(monitored_search())
```

## Real-World Use Cases

### Use Case 1: Research Assistant

```python
async def research_assistant(topic: str):
    """Gather comprehensive information on a topic."""
    orchestrator = AgnoOrchestrator()
    
    # Search for general information
    overview = await orchestrator.process_request(
        f"Overview of {topic}"
    )
    
    # Search for recent developments
    recent = await orchestrator.process_request(
        f"Recent developments in {topic}",
        max_results=10
    )
    
    # Search for applications
    applications = await orchestrator.process_request(
        f"Applications of {topic}"
    )
    
    # Compile report
    report = {
        "topic": topic,
        "overview": overview.data if overview.success else None,
        "recent_developments": recent.data if recent.success else None,
        "applications": applications.data if applications.success else None
    }
    
    return report

# Usage
report = asyncio.run(research_assistant("artificial intelligence"))
```

### Use Case 2: News Aggregator

```python
async def news_aggregator(keywords: list[str], max_per_keyword: int = 5):
    """Aggregate news on multiple topics."""
    orchestrator = AgnoOrchestrator()
    
    all_news = {}
    
    for keyword in keywords:
        response = await orchestrator.process_request(
            f"Latest news about {keyword}",
            max_results=max_per_keyword
        )
        
        if response.success:
            all_news[keyword] = response.data['results']
    
    return all_news

# Usage
keywords = ["technology", "AI", "climate change", "space exploration"]
news = asyncio.run(news_aggregator(keywords))
```

### Use Case 3: Competitive Analysis

```python
async def competitive_analysis(companies: list[str]):
    """Analyze multiple companies."""
    orchestrator = AgnoOrchestrator()
    
    analysis = {}
    
    for company in companies:
        # Get company info
        info = await orchestrator.process_request(
            f"Information about {company} company"
        )
        
        # Get recent news
        news = await orchestrator.process_request(
            f"Recent news about {company}"
        )
        
        # Get financial info
        financials = await orchestrator.process_request(
            f"{company} financial performance 2024"
        )
        
        analysis[company] = {
            "info": info.data if info.success else None,
            "news": news.data if news.success else None,
            "financials": financials.data if financials.success else None
        }
    
    return analysis

# Usage
companies = ["Microsoft", "Google", "Amazon"]
analysis = asyncio.run(competitive_analysis(companies))
```

## Tips and Best Practices

### 1. Query Optimization

**Good queries:**
- "Python machine learning libraries"
- "Climate change impact on agriculture"
- "Latest developments in quantum computing"

**Less optimal queries:**
- "Tell me stuff" (too vague)
- "asdfghjkl" (not meaningful)
- "a b c d e f g" (no context)

### 2. Result Handling

```python
response = await orchestrator.process_request(query)

# Always check success
if response.success:
    # Check confidence
    confidence = response.metadata.get('confidence', 0)
    
    if confidence > 0.7:
        # High confidence - use directly
        pass
    else:
        # Low confidence - may need refinement
        pass
else:
    # Handle error
    print(f"Error: {response.error}")
    print(f"Feedback: {response.feedback}")
```

### 3. Performance Monitoring

```python
# Get execution log
if response.execution_log:
    for entry in response.execution_log:
        print(f"{entry['tool']}: {entry['duration_ms']:.2f}ms")
```

### 4. Batch Processing

```python
# Process queries concurrently (careful with rate limits)
tasks = [
    orchestrator.process_request(query)
    for query in queries
]
responses = await asyncio.gather(*tasks)
```

---

For more examples and documentation, see `README.md` and `SETUP_GUIDE.md`.

