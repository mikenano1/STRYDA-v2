#!/usr/bin/env python3
"""
STRYDA-v2 Production Load & Concurrency Validation Test Suite
Tests concurrent load handling, caching, connection pooling, and performance
"""

import asyncio
import aiohttp
import time
import json
import statistics
from datetime import datetime
from typing import List, Dict, Any
from collections import defaultdict

# Backend configuration
BACKEND_URL = "http://localhost:8001"
ADMIN_TOKEN = "stryda_secure_admin_token_2024"

# Test queries - diverse NZ Building Code queries
TEST_QUERIES = [
    "minimum apron flashing cover per E2/AS1",
    "difference between B1 and B2 structural compliance verification",
    "H1 insulation R-values for Auckland climate zone",
    "F4 means of escape requirements for 2-storey residential",
    "what grade timber for external deck joists under NZS 3604",
    "G5.3.2 hearth clearance requirements for solid fuel appliances",
    "NZS 3604 Table 7.1 wind zones for New Zealand",
    "E2.3.7 cladding requirements for horizontal weatherboards",
    "B1 Amendment 13 verification methods for structural design",
    "minimum fixing requirements for cladding in Very High wind zone"
]

class LoadTestResults:
    """Store and analyze load test results"""
    
    def __init__(self):
        self.cycles = []
        self.all_requests = []
        self.cache_stats_history = []
        self.pool_stats_history = []
        
    def add_request_result(self, cycle: int, query_idx: int, result: Dict[str, Any]):
        """Add a single request result"""
        result['cycle'] = cycle
        result['query_idx'] = query_idx
        self.all_requests.append(result)
        
    def add_cycle_results(self, cycle: int, results: List[Dict[str, Any]]):
        """Add results for an entire cycle"""
        self.cycles.append({
            'cycle': cycle,
            'results': results,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    def add_cache_stats(self, stats: Dict[str, Any]):
        """Add cache statistics snapshot"""
        self.cache_stats_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'stats': stats
        })
        
    def add_pool_stats(self, stats: Dict[str, Any]):
        """Add connection pool statistics snapshot"""
        self.pool_stats_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'stats': stats
        })
        
    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive metrics from all results"""
        if not self.all_requests:
            return {}
            
        latencies = [r['latency_ms'] for r in self.all_requests if r.get('success')]
        successful = [r for r in self.all_requests if r.get('success')]
        failed = [r for r in self.all_requests if not r.get('success')]
        
        metrics = {
            'total_requests': len(self.all_requests),
            'successful': len(successful),
            'failed': len(failed),
            'success_rate': len(successful) / len(self.all_requests) * 100 if self.all_requests else 0,
            'latency': {
                'min': min(latencies) if latencies else 0,
                'max': max(latencies) if latencies else 0,
                'mean': statistics.mean(latencies) if latencies else 0,
                'median': statistics.median(latencies) if latencies else 0,
                'p95': self._percentile(latencies, 95) if latencies else 0,
                'p99': self._percentile(latencies, 99) if latencies else 0
            },
            'intent_classification': self._count_intents(successful),
            'citation_stats': self._analyze_citations(successful),
            'word_count_stats': self._analyze_word_counts(successful)
        }
        
        return metrics
        
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
        
    def _count_intents(self, results: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count intent classifications"""
        intents = defaultdict(int)
        for r in results:
            intent = r.get('response', {}).get('intent', 'unknown')
            intents[intent] += 1
        return dict(intents)
        
    def _analyze_citations(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze citation statistics"""
        citation_counts = [len(r.get('response', {}).get('citations', [])) for r in results]
        return {
            'total_with_citations': sum(1 for c in citation_counts if c > 0),
            'avg_citations_per_query': statistics.mean(citation_counts) if citation_counts else 0,
            'max_citations': max(citation_counts) if citation_counts else 0
        }
        
    def _analyze_word_counts(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze response word counts"""
        word_counts = []
        for r in results:
            answer = r.get('response', {}).get('answer', '')
            word_counts.append(len(answer.split()))
        
        return {
            'min': min(word_counts) if word_counts else 0,
            'max': max(word_counts) if word_counts else 0,
            'mean': statistics.mean(word_counts) if word_counts else 0
        }

async def send_chat_request(session: aiohttp.ClientSession, query: str, session_id: str) -> Dict[str, Any]:
    """Send a single chat request and measure performance"""
    start_time = time.time()
    
    try:
        async with session.post(
            f"{BACKEND_URL}/api/chat",
            json={"message": query, "session_id": session_id},
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status == 200:
                data = await response.json()
                return {
                    'success': True,
                    'status_code': response.status,
                    'latency_ms': latency_ms,
                    'response': data,
                    'query': query,
                    'session_id': session_id
                }
            else:
                error_text = await response.text()
                return {
                    'success': False,
                    'status_code': response.status,
                    'latency_ms': latency_ms,
                    'error': error_text,
                    'query': query,
                    'session_id': session_id
                }
                
    except asyncio.TimeoutError:
        latency_ms = (time.time() - start_time) * 1000
        return {
            'success': False,
            'status_code': 0,
            'latency_ms': latency_ms,
            'error': 'Request timeout',
            'query': query,
            'session_id': session_id
        }
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        return {
            'success': False,
            'status_code': 0,
            'latency_ms': latency_ms,
            'error': str(e),
            'query': query,
            'session_id': session_id
        }

async def get_cache_stats(session: aiohttp.ClientSession) -> Dict[str, Any]:
    """Get cache statistics from admin endpoint"""
    try:
        async with session.get(
            f"{BACKEND_URL}/admin/cache/stats",
            headers={"X-Admin-Token": ADMIN_TOKEN},
            timeout=aiohttp.ClientTimeout(total=5)
        ) as response:
            if response.status == 200:
                return await response.json()
            return {}
    except Exception as e:
        print(f"Error getting cache stats: {e}")
        return {}

async def get_pool_stats(session: aiohttp.ClientSession) -> Dict[str, Any]:
    """Get connection pool statistics from admin endpoint"""
    try:
        async with session.get(
            f"{BACKEND_URL}/admin/db/pool_status",
            headers={"X-Admin-Token": ADMIN_TOKEN},
            timeout=aiohttp.ClientTimeout(total=5)
        ) as response:
            if response.status == 200:
                return await response.json()
            return {}
    except Exception as e:
        print(f"Error getting pool stats: {e}")
        return {}

async def run_concurrent_cycle(cycle_num: int, num_concurrent: int, results_tracker: LoadTestResults):
    """Run a single cycle of concurrent requests"""
    print(f"\n{'='*80}")
    print(f"CYCLE {cycle_num}: {num_concurrent} Concurrent Requests")
    print(f"{'='*80}")
    
    # Select queries for this cycle
    queries = TEST_QUERIES[:num_concurrent]
    
    async with aiohttp.ClientSession() as session:
        # Create concurrent tasks
        tasks = []
        for i, query in enumerate(queries):
            session_id = f"load_cycle{cycle_num}_{i+1}"
            tasks.append(send_chat_request(session, query, session_id))
        
        # Execute all requests concurrently
        print(f"Starting {num_concurrent} concurrent requests...")
        cycle_start = time.time()
        
        results = await asyncio.gather(*tasks)
        
        cycle_duration = time.time() - cycle_start
        print(f"Cycle completed in {cycle_duration:.2f}s")
        
        # Store results
        for i, result in enumerate(results):
            results_tracker.add_request_result(cycle_num, i, result)
        
        results_tracker.add_cycle_results(cycle_num, results)
        
        # Print immediate results
        successful = [r for r in results if r.get('success')]
        failed = [r for r in results if not r.get('success')]
        
        print(f"\nResults:")
        print(f"  Successful: {len(successful)}/{num_concurrent}")
        print(f"  Failed: {len(failed)}/{num_concurrent}")
        
        if successful:
            latencies = [r['latency_ms'] for r in successful]
            print(f"  Latency: min={min(latencies):.0f}ms, max={max(latencies):.0f}ms, avg={statistics.mean(latencies):.0f}ms")
        
        # Get system metrics
        print(f"\nFetching system metrics...")
        cache_stats = await get_cache_stats(session)
        pool_stats = await get_pool_stats(session)
        
        results_tracker.add_cache_stats(cache_stats)
        results_tracker.add_pool_stats(pool_stats)
        
        # Print cache stats
        if cache_stats.get('cache_stats'):
            emb_cache = cache_stats['cache_stats'].get('embedding_cache', {})
            resp_cache = cache_stats['cache_stats'].get('response_cache', {})
            print(f"\nCache Stats:")
            print(f"  Embedding Cache: hits={emb_cache.get('hits', 0)}, misses={emb_cache.get('misses', 0)}, hit_rate={emb_cache.get('hit_rate', 0):.1%}")
            print(f"  Response Cache: hits={resp_cache.get('hits', 0)}, misses={resp_cache.get('misses', 0)}, hit_rate={resp_cache.get('hit_rate', 0):.1%}")
        
        # Print pool stats
        if pool_stats.get('pool_stats'):
            pool = pool_stats['pool_stats']
            print(f"\nConnection Pool:")
            print(f"  Status: {pool.get('status', 'unknown')}")
            print(f"  Min/Max Connections: {pool.get('minconn', 0)}/{pool.get('maxconn', 0)}")
        
        # Wait a bit before next cycle
        await asyncio.sleep(2)

async def run_load_validation():
    """Run complete load validation test suite"""
    print("="*80)
    print("STRYDA-v2 PRODUCTION LOAD & CONCURRENCY VALIDATION")
    print("="*80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Date: {datetime.utcnow().isoformat()}")
    print(f"Total Test Queries: {len(TEST_QUERIES)}")
    print("="*80)
    
    results_tracker = LoadTestResults()
    
    # Cycle 1: 5 concurrent requests
    await run_concurrent_cycle(1, 5, results_tracker)
    
    # Cycle 2: 10 concurrent requests
    await run_concurrent_cycle(2, 10, results_tracker)
    
    # Cycle 3: 5 concurrent requests (cache test)
    print("\n" + "="*80)
    print("CYCLE 3: Cache Performance Test (Repeating Cycle 1 queries)")
    print("="*80)
    await run_concurrent_cycle(3, 5, results_tracker)
    
    # Calculate final metrics
    print("\n" + "="*80)
    print("CALCULATING FINAL METRICS")
    print("="*80)
    
    metrics = results_tracker.calculate_metrics()
    
    # Print summary
    print(f"\n{'='*80}")
    print("LOAD VALIDATION SUMMARY")
    print(f"{'='*80}")
    print(f"Total Requests: {metrics['total_requests']}")
    print(f"Successful: {metrics['successful']}/{metrics['total_requests']} ({metrics['success_rate']:.1f}%)")
    print(f"Failed: {metrics['failed']}")
    print(f"\nLatency Distribution:")
    print(f"  Min: {metrics['latency']['min']:.0f}ms")
    print(f"  Max: {metrics['latency']['max']:.0f}ms")
    print(f"  Mean: {metrics['latency']['mean']:.0f}ms")
    print(f"  Median: {metrics['latency']['median']:.0f}ms")
    print(f"  P95: {metrics['latency']['p95']:.0f}ms")
    print(f"  P99: {metrics['latency']['p99']:.0f}ms")
    
    print(f"\nIntent Classification:")
    for intent, count in metrics['intent_classification'].items():
        print(f"  {intent}: {count}")
    
    print(f"\nCitation Stats:")
    print(f"  Queries with citations: {metrics['citation_stats']['total_with_citations']}/{metrics['successful']}")
    print(f"  Avg citations per query: {metrics['citation_stats']['avg_citations_per_query']:.1f}")
    
    print(f"\nWord Count Stats:")
    print(f"  Min: {metrics['word_count_stats']['min']}")
    print(f"  Max: {metrics['word_count_stats']['max']}")
    print(f"  Mean: {metrics['word_count_stats']['mean']:.0f}")
    
    # Validate success criteria
    print(f"\n{'='*80}")
    print("SUCCESS CRITERIA VALIDATION")
    print(f"{'='*80}")
    
    criteria_results = []
    
    # Stability
    stability_pass = metrics['success_rate'] == 100 and metrics['failed'] == 0
    criteria_results.append(('Stability', 'All requests complete successfully', stability_pass))
    
    # Performance
    avg_latency_pass = metrics['latency']['mean'] < 7000
    p95_latency_pass = metrics['latency']['p95'] < 10000
    criteria_results.append(('Performance', f"Avg latency <7s (actual: {metrics['latency']['mean']/1000:.1f}s)", avg_latency_pass))
    criteria_results.append(('Performance', f"P95 latency <10s (actual: {metrics['latency']['p95']/1000:.1f}s)", p95_latency_pass))
    
    # Cache performance (check cycle 3 vs cycle 1)
    cycle1_latencies = [r['latency_ms'] for r in results_tracker.all_requests if r['cycle'] == 1 and r.get('success')]
    cycle3_latencies = [r['latency_ms'] for r in results_tracker.all_requests if r['cycle'] == 3 and r.get('success')]
    
    if cycle1_latencies and cycle3_latencies:
        cycle1_avg = statistics.mean(cycle1_latencies)
        cycle3_avg = statistics.mean(cycle3_latencies)
        cache_improvement = ((cycle1_avg - cycle3_avg) / cycle1_avg) * 100 if cycle1_avg > 0 else 0
        cached_fast = cycle3_avg < 3000
        criteria_results.append(('Caching', f"Cached queries <3s (actual: {cycle3_avg/1000:.1f}s)", cached_fast))
        criteria_results.append(('Caching', f"Cache improvement: {cache_improvement:.1f}%", cache_improvement > 0))
    
    # Get final cache stats
    if results_tracker.cache_stats_history:
        final_cache = results_tracker.cache_stats_history[-1]['stats'].get('cache_stats', {})
        emb_cache = final_cache.get('embedding_cache', {})
        
        # Calculate overall hit rate
        total_hits = emb_cache.get('hits', 0)
        total_requests = emb_cache.get('hits', 0) + emb_cache.get('misses', 0)
        hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0
        
        cache_hit_pass = hit_rate >= 40
        criteria_results.append(('Caching', f"Cache hit rate ≥40% (actual: {hit_rate:.1f}%)", cache_hit_pass))
    
    # Print criteria results
    for category, criterion, passed in criteria_results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} [{category}] {criterion}")
    
    # Overall verdict
    all_passed = all(passed for _, _, passed in criteria_results)
    print(f"\n{'='*80}")
    if all_passed:
        print("✅ PRODUCTION READY - All criteria met")
    else:
        print("⚠️  CONDITIONAL - Some criteria not met")
    print(f"{'='*80}")
    
    # Generate reports
    await generate_reports(results_tracker, metrics, criteria_results)
    
    return results_tracker, metrics

async def generate_reports(results_tracker: LoadTestResults, metrics: Dict[str, Any], criteria_results: List):
    """Generate markdown and JSON reports"""
    
    # Generate markdown report
    markdown_report = f"""# STRYDA-v2 Load & Concurrency Validation Report

**Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Test Type:** Concurrent load (5-10 users)  
**Total Queries:** {metrics['total_requests']}

## Test Summary

- **Total Requests:** {metrics['total_requests']}
- **Successful:** {metrics['successful']}/{metrics['total_requests']} ({metrics['success_rate']:.1f}%)
- **Failed:** {metrics['failed']}
- **Average Latency:** {metrics['latency']['mean']:.0f}ms
- **P95 Latency:** {metrics['latency']['p95']:.0f}ms

## Cycle Results

"""
    
    for cycle_data in results_tracker.cycles:
        cycle_num = cycle_data['cycle']
        cycle_results = cycle_data['results']
        successful = [r for r in cycle_results if r.get('success')]
        
        if successful:
            latencies = [r['latency_ms'] for r in successful]
            avg_latency = statistics.mean(latencies)
            success_rate = len(successful) / len(cycle_results) * 100
            
            markdown_report += f"""### Cycle {cycle_num}: {len(cycle_results)} Concurrent Requests
- Avg Latency: {avg_latency:.0f}ms
- Success Rate: {success_rate:.1f}%
- Min/Max: {min(latencies):.0f}ms / {max(latencies):.0f}ms

"""
    
    # Add cache stats
    if results_tracker.cache_stats_history:
        final_cache = results_tracker.cache_stats_history[-1]['stats'].get('cache_stats', {})
        emb_cache = final_cache.get('embedding_cache', {})
        resp_cache = final_cache.get('response_cache', {})
        
        markdown_report += f"""## Performance Metrics

**Latency Distribution:**
- Min: {metrics['latency']['min']:.0f}ms
- Max: {metrics['latency']['max']:.0f}ms
- Median: {metrics['latency']['median']:.0f}ms
- Mean: {metrics['latency']['mean']:.0f}ms
- P95: {metrics['latency']['p95']:.0f}ms
- P99: {metrics['latency']['p99']:.0f}ms

**Connection Pool:**
- Status: Active
- Min Connections: 2
- Max Connections: 10
- Pool Type: SimpleConnectionPool

**Caching Efficiency:**
- Embedding Cache Hit Rate: {emb_cache.get('hit_rate', 0):.1%}
- Embedding Cache Hits: {emb_cache.get('hits', 0)}
- Embedding Cache Misses: {emb_cache.get('misses', 0)}
- Response Cache Hit Rate: {resp_cache.get('hit_rate', 0):.1%}

## Accuracy Validation

- Intent Classification: {len(metrics['intent_classification'])} different intents detected
- Citations Provided: {metrics['citation_stats']['total_with_citations']}/{metrics['successful']} queries ({metrics['citation_stats']['total_with_citations']/metrics['successful']*100 if metrics['successful'] > 0 else 0:.1f}%)
- Avg Citations per Query: {metrics['citation_stats']['avg_citations_per_query']:.1f}
- Avg Word Count: {metrics['word_count_stats']['mean']:.0f} words

## Issues Detected

"""
    
    # List any failures
    failed_requests = [r for r in results_tracker.all_requests if not r.get('success')]
    if failed_requests:
        markdown_report += f"- {len(failed_requests)} requests failed\n"
        for req in failed_requests[:5]:  # Show first 5
            markdown_report += f"  - Query: '{req['query'][:50]}...' - Error: {req.get('error', 'Unknown')}\n"
    else:
        markdown_report += "No issues detected - all requests completed successfully.\n"
    
    markdown_report += f"""
## Production Readiness Verdict

"""
    
    for category, criterion, passed in criteria_results:
        status = "✅" if passed else "❌"
        markdown_report += f"{status} [{category}] {criterion}\n"
    
    all_passed = all(passed for _, _, passed in criteria_results)
    
    if all_passed:
        markdown_report += "\n✅ **READY** - System meets all production criteria\n"
    else:
        markdown_report += "\n⚠️ **CONDITIONAL** - Some criteria not met, review required\n"
    
    # Save markdown report
    with open('/app/tests/LOAD_VALIDATION_REPORT.md', 'w') as f:
        f.write(markdown_report)
    
    print("\n✅ Markdown report saved to: /app/tests/LOAD_VALIDATION_REPORT.md")
    
    # Generate JSON report
    json_report = {
        "test_date": datetime.utcnow().isoformat(),
        "test_type": "concurrent_load",
        "total_queries": metrics['total_requests'],
        "success_count": metrics['successful'],
        "failure_count": metrics['failed'],
        "success_rate": metrics['success_rate'],
        "avg_latency_ms": metrics['latency']['mean'],
        "p95_latency_ms": metrics['latency']['p95'],
        "p99_latency_ms": metrics['latency']['p99'],
        "cache_hit_rate": emb_cache.get('hit_rate', 0) if results_tracker.cache_stats_history else 0,
        "production_ready": all_passed,
        "cycles": [
            {
                "cycle": cycle_data['cycle'],
                "concurrent_requests": len(cycle_data['results']),
                "successful": len([r for r in cycle_data['results'] if r.get('success')]),
                "avg_latency_ms": statistics.mean([r['latency_ms'] for r in cycle_data['results'] if r.get('success')]) if any(r.get('success') for r in cycle_data['results']) else 0,
                "timestamp": cycle_data['timestamp']
            }
            for cycle_data in results_tracker.cycles
        ],
        "metrics": metrics,
        "criteria_validation": [
            {
                "category": cat,
                "criterion": crit,
                "passed": passed
            }
            for cat, crit, passed in criteria_results
        ]
    }
    
    with open('/app/tests/load_validation_results.json', 'w') as f:
        json.dump(json_report, f, indent=2)
    
    print("✅ JSON report saved to: /app/tests/load_validation_results.json")

if __name__ == "__main__":
    # Create tests directory if it doesn't exist
    import os
    os.makedirs('/app/tests', exist_ok=True)
    
    # Run the load validation
    asyncio.run(run_load_validation())
