"""
Practical Example: Save Scraped Data to Files with Complete Logging
Demonstrates proper data collection, validation, and storage
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from src.agno_orchestrator import AgnoOrchestrator
from src.logging_system import get_logger


class DataScraper:
    """
    Proper data scraping with validation and storage.
    """
    
    def __init__(self, output_dir: str = "scraped_data"):
        self.orchestrator = AgnoOrchestrator()
        self.logger = get_logger()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    async def scrape_and_save(
        self,
        query: str,
        output_filename: str = None
    ) -> Dict[str, Any]:
        """
        Scrape data for a query and save to file.
        
        Args:
            query: Search query
            output_filename: Optional custom filename
            
        Returns:
            Dict with scraping results and metadata
        """
        self.logger.info(f"Starting scrape for query: {query}")
        
        # Execute query
        result = await self.orchestrator.execute_query(query)
        
        # Prepare structured data
        scraped_data = {
            "metadata": {
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "status": result.status.value,
                "confidence": result.confidence,
                "source": result.metadata.get("source", "Unknown")
            },
            "data": result.data,
            "quality_metrics": {
                "confidence_score": result.confidence,
                "result_count": len(result.data.get("results", [])) if result.data else 0,
                "has_answer": bool(result.data.get("answer")) if result.data else False
            }
        }
        
        # Generate filename
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_query = "".join(c if c.isalnum() else "_" for c in query[:30])
            output_filename = f"{safe_query}_{timestamp}.json"
        
        # Save to file
        output_path = self.output_dir / output_filename
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(scraped_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Data saved to: {output_path}")
        
        return {
            "file_path": str(output_path),
            "query": query,
            "result_count": scraped_data["quality_metrics"]["result_count"],
            "confidence": result.confidence
        }
    
    async def scrape_multiple(
        self,
        queries: List[str],
        batch_name: str = "batch"
    ) -> List[Dict[str, Any]]:
        """
        Scrape multiple queries and save to separate files.
        
        Args:
            queries: List of search queries
            batch_name: Name for this batch of queries
            
        Returns:
            List of results for each query
        """
        self.logger.info(f"Starting batch scrape: {batch_name} ({len(queries)} queries)")
        
        results = []
        
        for i, query in enumerate(queries, 1):
            print(f"\n[{i}/{len(queries)}] Processing: {query}")
            
            try:
                result = await self.scrape_and_save(
                    query=query,
                    output_filename=f"{batch_name}_{i:02d}.json"
                )
                results.append(result)
                
                print(f"  ✅ Saved | Results: {result['result_count']} | "
                      f"Confidence: {result['confidence']:.2%}")
                
            except Exception as e:
                self.logger.error(f"Failed to scrape '{query}': {str(e)}")
                print(f"  ❌ Failed: {str(e)}")
                results.append({
                    "query": query,
                    "error": str(e),
                    "file_path": None
                })
        
        # Save batch summary
        summary_path = self.output_dir / f"{batch_name}_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump({
                "batch_name": batch_name,
                "timestamp": datetime.now().isoformat(),
                "total_queries": len(queries),
                "successful": sum(1 for r in results if r.get("file_path")),
                "failed": sum(1 for r in results if r.get("error")),
                "results": results
            }, f, indent=2)
        
        self.logger.info(f"Batch summary saved to: {summary_path}")
        
        return results
    
    def export_to_csv(self, json_files: List[str], csv_filename: str):
        """
        Export scraped JSON data to CSV format.
        
        Args:
            json_files: List of JSON file paths
            csv_filename: Output CSV filename
        """
        import csv
        
        csv_path = self.output_dir / csv_filename
        
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                "Query", "Title", "URL", "Content Preview",
                "Score", "Timestamp", "Source"
            ])
            
            # Rows
            for json_file in json_files:
                with open(json_file, "r", encoding="utf-8") as jf:
                    data = json.load(jf)
                    
                    query = data["metadata"]["query"]
                    timestamp = data["metadata"]["timestamp"]
                    source = data["metadata"]["source"]
                    
                    for result in data.get("data", {}).get("results", []):
                        writer.writerow([
                            query,
                            result.get("title", ""),
                            result.get("url", ""),
                            result.get("content", "")[:100],
                            result.get("score", 0),
                            timestamp,
                            source
                        ])
        
        self.logger.info(f"CSV exported to: {csv_path}")
        print(f"✅ CSV exported: {csv_path}")


async def example_1_single_query():
    """Example 1: Scrape single query and save"""
    print("=" * 70)
    print("Example 1: Single Query Scraping")
    print("=" * 70)
    
    scraper = DataScraper(output_dir="scraped_data")
    
    result = await scraper.scrape_and_save(
        query="Python async programming best practices 2025"
    )
    
    print(f"\n✅ Scraping Complete!")
    print(f"📁 File: {result['file_path']}")
    print(f"📊 Results: {result['result_count']}")
    print(f"🎯 Confidence: {result['confidence']:.2%}")


async def example_2_batch_scraping():
    """Example 2: Batch scraping with multiple queries"""
    print("\n\n" + "=" * 70)
    print("Example 2: Batch Scraping")
    print("=" * 70)
    
    scraper = DataScraper(output_dir="scraped_data")
    
    queries = [
        "AI trends 2025",
        "Web scraping best practices",
        "Python data science tools",
        "Machine learning frameworks comparison",
        "Cloud computing platforms 2025"
    ]
    
    results = await scraper.scrape_multiple(
        queries=queries,
        batch_name="tech_trends_2025"
    )
    
    print(f"\n✅ Batch Complete!")
    print(f"📦 Total: {len(results)}")
    print(f"✅ Success: {sum(1 for r in results if r.get('file_path'))}")
    print(f"❌ Failed: {sum(1 for r in results if r.get('error'))}")


async def example_3_data_validation():
    """Example 3: Scraping with data validation"""
    print("\n\n" + "=" * 70)
    print("Example 3: Data Validation & Quality Checks")
    print("=" * 70)
    
    scraper = DataScraper(output_dir="scraped_data")
    
    query = "Latest cybersecurity threats 2025"
    result = await scraper.scrape_and_save(query)
    
    # Validate data quality
    print(f"\n📊 Quality Validation:")
    print(f"   Query: {query}")
    print(f"   Confidence: {result['confidence']:.2%}")
    
    if result['confidence'] >= 0.7:
        print(f"   ✅ HIGH QUALITY - Confidence ≥ 70%")
    elif result['confidence'] >= 0.5:
        print(f"   ⚠️  MEDIUM QUALITY - Confidence 50-70%")
    else:
        print(f"   ❌ LOW QUALITY - Confidence < 50%")
    
    print(f"   Results Found: {result['result_count']}")
    
    # Read and display sample
    with open(result['file_path'], 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n📄 Sample Result:")
    if data['data'] and data['data'].get('results'):
        first_result = data['data']['results'][0]
        print(f"   Title: {first_result.get('title', 'N/A')[:60]}...")
        print(f"   URL: {first_result.get('url', 'N/A')}")
        print(f"   Content: {first_result.get('content', 'N/A')[:100]}...")


async def example_4_export_formats():
    """Example 4: Export to different formats"""
    print("\n\n" + "=" * 70)
    print("Example 4: Export to CSV")
    print("=" * 70)
    
    scraper = DataScraper(output_dir="scraped_data")
    
    # Scrape some data
    queries = ["Python tutorials", "JavaScript frameworks"]
    results = await scraper.scrape_multiple(queries, batch_name="programming")
    
    # Export to CSV
    json_files = [r['file_path'] for r in results if r.get('file_path')]
    
    if json_files:
        scraper.export_to_csv(json_files, "programming_data.csv")


async def main():
    """Run all examples"""
    print("\n🔍 PROPER DATA SCRAPING WITH LOGGING - EXAMPLES\n")
    
    await example_1_single_query()
    await example_2_batch_scraping()
    await example_3_data_validation()
    await example_4_export_formats()
    
    print("\n\n" + "=" * 70)
    print("✅ All Examples Complete!")
    print("=" * 70)
    print("\n📂 Check these locations:")
    print("   • scraped_data/ - All scraped data files")
    print("   • agno_system.log - Complete operation logs")
    print("\n💡 All operations are fully logged with timestamps and metrics!")


if __name__ == "__main__":
    asyncio.run(main())

