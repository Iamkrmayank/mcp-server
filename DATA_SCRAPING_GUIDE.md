# Data Scraping Guide - Proper Data Collection kaise karein

## ✅ Haan, Aap Proper Data La Sakte Hain!

Your system **already has** full capabilities for proper data scraping with complete logging.

---

## 🎯 Kya-Kya Kar Sakte Hain

### 1. **Web Scraping** (Real-time)
- ✅ Tavily API se structured data
- ✅ Jina API se semantic content
- ✅ Automatic fallback if one fails
- ✅ Timeout handling
- ✅ Error recovery

### 2. **Data Quality**
- ✅ Confidence scores (0-100%)
- ✅ Result validation
- ✅ Source tracking
- ✅ Quality metrics

### 3. **Complete Logging**
- ✅ Every request logged
- ✅ UTC timestamps
- ✅ Duration metrics (milliseconds)
- ✅ Success/failure status
- ✅ Error messages
- ✅ Fallback events

### 4. **Data Storage**
- ✅ Save to JSON files
- ✅ Export to CSV
- ✅ Structured format
- ✅ Batch processing

---

## 🚀 Quick Start Examples

### Example 1: Simple Scraping
```python
from src.agno_orchestrator import AgnoOrchestrator
import asyncio

async def scrape_data():
    orchestrator = AgnoOrchestrator()
    
    # Scrape data
    result = await orchestrator.execute_query("Python tutorials")
    
    # Check results
    print(f"Status: {result.status}")
    print(f"Confidence: {result.confidence:.2%}")
    print(f"Results: {len(result.data['results'])}")
    
    # Access data
    for item in result.data['results']:
        print(f"- {item['title']}")
        print(f"  URL: {item['url']}")
        print(f"  Content: {item['content'][:100]}...")

asyncio.run(scrape_data())
```

### Example 2: Save Scraped Data
```python
from save_scraped_data import DataScraper
import asyncio

async def save_data():
    scraper = DataScraper(output_dir="my_data")
    
    # Scrape and save
    result = await scraper.scrape_and_save(
        query="AI trends 2025"
    )
    
    print(f"Saved to: {result['file_path']}")
    print(f"Confidence: {result['confidence']:.2%}")

asyncio.run(save_data())
```

### Example 3: Batch Scraping
```python
from save_scraped_data import DataScraper
import asyncio

async def batch_scrape():
    scraper = DataScraper()
    
    queries = [
        "Python web scraping",
        "Machine learning 2025",
        "Cloud computing trends"
    ]
    
    results = await scraper.scrape_multiple(
        queries=queries,
        batch_name="tech_research"
    )
    
    print(f"Completed {len(results)} queries")

asyncio.run(batch_scrape())
```

---

## 📊 Log ka Structure

Every operation is logged like this:

```json
{
  "timestamp": "2025-10-14T12:30:45.123456+00:00",
  "operation": "Tavily_Request",
  "status": "success",
  "duration_ms": 234.56,
  "data_quality": {
    "confidence": 0.89,
    "result_count": 5,
    "has_answer": true
  },
  "metadata": {
    "source": "Tavily",
    "query": "your search query"
  }
}
```

---

## 🔍 Data ka Structure

Scraped data saves in this format:

```json
{
  "metadata": {
    "query": "your query",
    "timestamp": "2025-10-14T12:30:45",
    "status": "success",
    "confidence": 0.85,
    "source": "Tavily"
  },
  "data": {
    "query": "your query",
    "answer": "AI-generated summary...",
    "results": [
      {
        "title": "Article Title",
        "url": "https://example.com/article",
        "content": "Full article content...",
        "score": 0.95
      }
    ]
  },
  "quality_metrics": {
    "confidence_score": 0.85,
    "result_count": 5,
    "has_answer": true
  }
}
```

---

## 🛠️ Kaise Use Karein

### Step 1: Setup (One-time)
```bash
# Install dependencies
pip install -r requirements.txt

# Set API keys (optional - Jina works without key)
export TAVILY_API_KEY="your_key_here"
export JINA_API_KEY="your_key_here"  # Optional
```

### Step 2: Run Examples
```bash
# Demo scraping
python demo_scraping.py

# Save scraped data
python save_scraped_data.py

# Or use the CLI
python -m src.cli query "your search query"
```

### Step 3: Check Results
```bash
# View logs
cat agno_system.log

# View scraped data
ls scraped_data/
cat scraped_data/your_file.json
```

---

## 📝 Available Commands

### Using CLI:
```bash
# Simple query
python -m src.cli query "Python tutorials"

# Start MCP server
python -m src.cli start-server

# Test system
python test_system.py
```

### Using Scripts:
```bash
# Demo all features
python demo_scraping.py

# Save data to files
python save_scraped_data.py

# Quick start
python quick_start.py
```

---

## 🎯 Features Summary

| Feature | Status | Details |
|---------|--------|---------|
| **Tavily Scraping** | ✅ | Fast, structured extraction |
| **Jina Scraping** | ✅ | Semantic understanding |
| **Auto Fallback** | ✅ | Tavily → Jina on failure |
| **Logging** | ✅ | Complete audit trail |
| **Timestamps** | ✅ | UTC timezone |
| **Duration Tracking** | ✅ | Millisecond precision |
| **Confidence Scores** | ✅ | 0-100% quality metric |
| **Error Handling** | ✅ | Detailed error messages |
| **Timeout Management** | ✅ | Configurable timeouts |
| **JSON Export** | ✅ | Structured data format |
| **CSV Export** | ✅ | Tabular data format |
| **Batch Processing** | ✅ | Multiple queries |
| **Quality Validation** | ✅ | Automatic quality checks |

---

## 💡 Pro Tips

### 1. **Confidence Scores Samjhein**
- **≥ 70%** = High quality, reliable data
- **50-70%** = Medium quality, verify important facts
- **< 50%** = Low quality, use with caution

### 2. **Logs Regularly Check Karein**
```bash
tail -f agno_system.log  # Real-time log monitoring
```

### 3. **Batch Processing for Multiple Queries**
- Faster than single queries
- Automatic summary generation
- Better for large datasets

### 4. **Data Validation**
- Always check confidence scores
- Verify critical information
- Use multiple sources for important data

### 5. **Error Recovery**
- System automatically retries with Jina if Tavily fails
- Timeouts are handled gracefully
- All errors are logged

---

## 🔧 Troubleshooting

### Issue: "Tavily API key not configured"
**Solution:**
```bash
export TAVILY_API_KEY="your_key_here"
```

### Issue: "No results found"
**Possible Reasons:**
- Query too specific
- Network issues
- API rate limits
**Solution:**
- Try broader query
- Check internet connection
- Check logs for details

### Issue: "Timeout error"
**Solution:**
- Increase timeout in config
- Check network speed
- Try again later

---

## 📁 Output Files

After running examples, you'll see:

```
project/
├── agno_system.log           # Complete operation logs
├── scraped_data/             # All scraped data
│   ├── query1_20251014.json  # Individual results
│   ├── query2_20251014.json
│   ├── batch_summary.json    # Batch summary
│   └── data_export.csv       # CSV export
```

---

## ✅ Summary

**Haan, bilkul proper data scraping kar sakte hain:**

1. ✅ **Real-time web scraping** - Tavily & Jina se
2. ✅ **Structured data** - JSON/CSV format mein
3. ✅ **Complete logging** - Har operation track hota hai
4. ✅ **Quality metrics** - Confidence scores milte hain
5. ✅ **Error handling** - Automatic fallback & recovery
6. ✅ **Batch processing** - Multiple queries ek saath

**Start karne ke liye:**
```bash
python demo_scraping.py
# ya
python save_scraped_data.py
```

**Logs dekhne ke liye:**
```bash
cat agno_system.log
```

---

## 📚 More Resources

- `GETTING_STARTED.md` - Full setup guide
- `EXAMPLES.md` - More code examples
- `ARCHITECTURE.md` - System architecture
- `README.md` - Project overview

---

**Ready to scrape! 🚀**

