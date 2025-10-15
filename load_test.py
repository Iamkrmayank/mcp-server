#!/usr/bin/env python3
"""
Load Testing Script for Agno Production Server
Tests the production server under various load conditions.
"""

import asyncio
import aiohttp
import time
import json
import statistics
from typing import List, Dict, Any
import argparse
from dataclasses import dataclass


@dataclass
class TestResult:
    """Test result data."""
    success: bool
    response_time: float
    status_code: int
    error: str = None


class LoadTester:
    """Load testing utility for the Agno production server."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[TestResult] = []
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def single_request(self, query: str, client_id: str = "test_client") -> TestResult:
        """Make a single request to the server."""
        start_time = time.time()
        
        try:
            payload = {
                "query": query,
                "max_results": 5,
                "format": "json",
                "client_id": client_id,
                "use_cache": True
            }
            
            async with self.session.post(
                f"{self.base_url}/api/search",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    if data.get("success", False):
                        return TestResult(
                            success=True,
                            response_time=response_time,
                            status_code=response.status
                        )
                    else:
                        return TestResult(
                            success=False,
                            response_time=response_time,
                            status_code=response.status,
                            error=f"API error: {data.get('error', 'Unknown error')}"
                        )
                else:
                    error_text = await response.text()
                    return TestResult(
                        success=False,
                        response_time=response_time,
                        status_code=response.status,
                        error=f"HTTP {response.status}: {error_text}"
                    )
        
        except asyncio.TimeoutError:
            return TestResult(
                success=False,
                response_time=time.time() - start_time,
                status_code=0,
                error="Request timeout"
            )
        except Exception as e:
            return TestResult(
                success=False,
                response_time=time.time() - start_time,
                status_code=0,
                error=str(e)
            )
    
    async def run_load_test(
        self,
        concurrent_users: int,
        requests_per_user: int,
        ramp_up_seconds: int = 0,
        test_queries: List[str] = None
    ) -> Dict[str, Any]:
        """Run a load test with specified parameters."""
        
        if test_queries is None:
            test_queries = [
                "Tell me about artificial intelligence trends in 2024",
                "What are the latest developments in quantum computing?",
                "How is machine learning being used in healthcare?",
                "What are the benefits of renewable energy?",
                "Tell me about space exploration missions",
                "What is the future of electric vehicles?",
                "How does blockchain technology work?",
                "What are the challenges of climate change?",
                "Tell me about recent advances in biotechnology",
                "What is the impact of 5G technology?"
            ]
        
        print(f"Starting load test:")
        print(f"  Concurrent users: {concurrent_users}")
        print(f"  Requests per user: {requests_per_user}")
        print(f"  Total requests: {concurrent_users * requests_per_user}")
        print(f"  Ramp-up time: {ramp_up_seconds}s")
        print()
        
        self.results = []
        start_time = time.time()
        
        # Create tasks for concurrent users
        tasks = []
        for user_id in range(concurrent_users):
            # Stagger user start times for ramp-up
            delay = (user_id * ramp_up_seconds) / concurrent_users if ramp_up_seconds > 0 else 0
            
            task = asyncio.create_task(
                self._user_simulation(user_id, requests_per_user, test_queries, delay)
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        # Calculate statistics
        stats = self._calculate_statistics(total_time)
        
        return stats
    
    async def _user_simulation(
        self,
        user_id: int,
        requests_per_user: int,
        test_queries: List[str],
        delay: float
    ):
        """Simulate a single user making requests."""
        if delay > 0:
            await asyncio.sleep(delay)
        
        client_id = f"test_user_{user_id}"
        
        for i in range(requests_per_user):
            query = test_queries[i % len(test_queries)]
            result = await self.single_request(query, client_id)
            self.results.append(result)
            
            # Small delay between requests
            await asyncio.sleep(0.1)
    
    def _calculate_statistics(self, total_time: float) -> Dict[str, Any]:
        """Calculate test statistics."""
        if not self.results:
            return {"error": "No results to analyze"}
        
        successful_results = [r for r in self.results if r.success]
        failed_results = [r for r in self.results if not r.success]
        
        response_times = [r.response_time for r in successful_results]
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            p95_response_time = self._percentile(response_times, 95)
            p99_response_time = self._percentile(response_times, 99)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
        else:
            avg_response_time = median_response_time = p95_response_time = p99_response_time = 0
            min_response_time = max_response_time = 0
        
        success_rate = (len(successful_results) / len(self.results)) * 100
        requests_per_second = len(self.results) / total_time if total_time > 0 else 0
        
        # Group errors by type
        error_counts = {}
        for result in failed_results:
            error_type = result.error or f"HTTP {result.status_code}"
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        return {
            "test_summary": {
                "total_requests": len(self.results),
                "successful_requests": len(successful_results),
                "failed_requests": len(failed_results),
                "success_rate": round(success_rate, 2),
                "total_time": round(total_time, 2),
                "requests_per_second": round(requests_per_second, 2)
            },
            "response_times": {
                "average": round(avg_response_time, 3),
                "median": round(median_response_time, 3),
                "p95": round(p95_response_time, 3),
                "p99": round(p99_response_time, 3),
                "min": round(min_response_time, 3),
                "max": round(max_response_time, 3)
            },
            "errors": error_counts
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data."""
        if not data:
            return 0
        
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def print_results(self, stats: Dict[str, Any]):
        """Print formatted test results."""
        print("=" * 80)
        print("LOAD TEST RESULTS")
        print("=" * 80)
        
        summary = stats["test_summary"]
        print(f"\n📊 TEST SUMMARY:")
        print(f"  Total Requests: {summary['total_requests']}")
        print(f"  Successful: {summary['successful_requests']}")
        print(f"  Failed: {summary['failed_requests']}")
        print(f"  Success Rate: {summary['success_rate']}%")
        print(f"  Total Time: {summary['total_time']}s")
        print(f"  Requests/Second: {summary['requests_per_second']}")
        
        response_times = stats["response_times"]
        print(f"\n⏱️  RESPONSE TIMES:")
        print(f"  Average: {response_times['average']}s")
        print(f"  Median: {response_times['median']}s")
        print(f"  P95: {response_times['p95']}s")
        print(f"  P99: {response_times['p99']}s")
        print(f"  Min: {response_times['min']}s")
        print(f"  Max: {response_times['max']}s")
        
        if stats["errors"]:
            print(f"\n❌ ERRORS:")
            for error, count in stats["errors"].items():
                print(f"  {error}: {count}")
        
        print("\n" + "=" * 80)


async def run_test_scenarios():
    """Run multiple test scenarios."""
    
    scenarios = [
        {
            "name": "Light Load",
            "concurrent_users": 5,
            "requests_per_user": 10,
            "ramp_up_seconds": 5
        },
        {
            "name": "Medium Load",
            "concurrent_users": 20,
            "requests_per_user": 20,
            "ramp_up_seconds": 10
        },
        {
            "name": "Heavy Load",
            "concurrent_users": 50,
            "requests_per_user": 30,
            "ramp_up_seconds": 15
        },
        {
            "name": "Stress Test",
            "concurrent_users": 100,
            "requests_per_user": 50,
            "ramp_up_seconds": 30
        }
    ]
    
    async with LoadTester() as tester:
        for scenario in scenarios:
            print(f"\n🧪 Running {scenario['name']} Test...")
            print("-" * 50)
            
            stats = await tester.run_load_test(
                concurrent_users=scenario["concurrent_users"],
                requests_per_user=scenario["requests_per_user"],
                ramp_up_seconds=scenario["ramp_up_seconds"]
            )
            
            tester.print_results(stats)
            
            # Wait between tests
            print("\n⏳ Waiting 30 seconds before next test...")
            await asyncio.sleep(30)


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Load test the Agno production server")
    parser.add_argument("--url", default="http://localhost:8000", help="Server URL")
    parser.add_argument("--users", type=int, default=10, help="Number of concurrent users")
    parser.add_argument("--requests", type=int, default=20, help="Requests per user")
    parser.add_argument("--ramp-up", type=int, default=5, help="Ramp-up time in seconds")
    parser.add_argument("--scenarios", action="store_true", help="Run all test scenarios")
    
    args = parser.parse_args()
    
    if args.scenarios:
        await run_test_scenarios()
    else:
        async with LoadTester(args.url) as tester:
            stats = await tester.run_load_test(
                concurrent_users=args.users,
                requests_per_user=args.requests,
                ramp_up_seconds=args.ramp_up
            )
            tester.print_results(stats)


if __name__ == "__main__":
    asyncio.run(main())
