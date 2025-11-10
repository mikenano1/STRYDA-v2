#!/usr/bin/env python3
"""
STRYDA-v2 Caching & Performance Optimization Testing
Tests the implementation status of:
1. In-Memory Caching (cache_manager.py)
2. Profiler Timing Accuracy
3. Connection Pooling
4. Benchmark Performance Testing
"""

import requests
import time
import json
import os
import sys
from typing import Dict, List, Any

# Backend URL
BACKEND_URL = "http://localhost:8001"

# Test queries for benchmark
BENCHMARK_QUERIES = [
    "E2/AS1 minimum apron flashing cover",
    "G5.3.2 hearth clearance requirements",
    "H1 insulation R-values for Auckland",
    "F4 means of escape requirements",
    "NZS 3604 Table 7.1 wind zones",
    "B1 Amendment 13 verification methods",
    "NZS 3604 stud spacing for standard wind",
    "E2.3.7 cladding requirements",
    "B1.3.3 foundation requirements",
    "difference between B1 and B2 compliance"
]

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_header(text: str):
    print(f"\n{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*80}{Colors.RESET}\n")

def print_success(text: str):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text: str):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_info(text: str):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")

def test_health_endpoint():
    """Test if backend is accessible"""
    print_header("TEST 1: Backend Health Check")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Backend is running - Version: {data.get('version', 'unknown')}")
            return True
        else:
            print_error(f"Backend returned status code: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Cannot connect to backend: {e}")
        return False

def check_cache_manager_implementation():
    """Check if cache_manager.py exists and is implemented"""
    print_header("TEST 2: Phase 1 - In-Memory Caching Implementation")
    
    cache_manager_path = "/app/backend-minimal/cache_manager.py"
    
    if os.path.exists(cache_manager_path):
        print_success(f"cache_manager.py exists at {cache_manager_path}")
        
        # Check if it has the required components
        with open(cache_manager_path, 'r') as f:
            content = f.read()
            
        required_components = [
            ("LRUCache class", "class LRUCache"),
            ("embedding_cache", "embedding_cache"),
            ("response_cache", "response_cache"),
            ("cache_key function", "def cache_key")
        ]
        
        all_found = True
        for component_name, search_string in required_components:
            if search_string in content:
                print_success(f"  {component_name} found")
            else:
                print_error(f"  {component_name} NOT found")
                all_found = False
        
        return all_found
    else:
        print_error(f"cache_manager.py NOT found at {cache_manager_path}")
        print_warning("Phase 1 (In-Memory Caching) has NOT been implemented")
        return False

def check_caching_integration():
    """Check if caching is integrated into simple_tier1_retrieval.py"""
    print_header("TEST 3: Caching Integration in Retrieval")
    
    retrieval_path = "/app/backend-minimal/simple_tier1_retrieval.py"
    
    with open(retrieval_path, 'r') as f:
        content = f.read()
    
    integration_checks = [
        ("cache_manager import", "from cache_manager import"),
        ("embedding cache check", "embedding_cache.get"),
        ("embedding cache set", "embedding_cache.set"),
        ("cache_key usage", "cache_key(")
    ]
    
    all_integrated = True
    for check_name, search_string in integration_checks:
        if search_string in content:
            print_success(f"  {check_name} found")
        else:
            print_error(f"  {check_name} NOT found")
            all_integrated = False
    
    if not all_integrated:
        print_warning("Caching is NOT integrated into retrieval system")
    
    return all_integrated

def check_connection_pooling():
    """Check if connection pooling is implemented"""
    print_header("TEST 4: Phase 3 - Connection Pooling Implementation")
    
    retrieval_path = "/app/backend-minimal/simple_tier1_retrieval.py"
    
    with open(retrieval_path, 'r') as f:
        content = f.read()
    
    pooling_checks = [
        ("psycopg2.pool import", "from psycopg2 import pool"),
        ("connection_pool variable", "connection_pool"),
        ("get_db_connection function", "def get_db_connection"),
        ("return_db_connection function", "def return_db_connection"),
        ("SimpleConnectionPool", "SimpleConnectionPool")
    ]
    
    all_found = True
    for check_name, search_string in pooling_checks:
        if search_string in content:
            print_success(f"  {check_name} found")
        else:
            print_error(f"  {check_name} NOT found")
            all_found = False
    
    if not all_found:
        print_warning("Connection pooling is NOT implemented")
        print_info("Current implementation creates new connection for each request")
    
    return all_found

def check_profiler_timing():
    """Check profiler implementation"""
    print_header("TEST 5: Phase 2 - Profiler Timing Check")
    
    profiler_path = "/app/backend-minimal/profiler.py"
    
    with open(profiler_path, 'r') as f:
        content = f.read()
    
    print_info("Profiler exists with the following timers:")
    
    timers = [
        "t_parse",
        "t_embed_query",
        "t_vector_search",
        "t_hybrid_keyword",
        "t_merge_relevance",
        "t_generate",
        "t_total"
    ]
    
    for timer in timers:
        if timer in content:
            print_success(f"  {timer} timer defined")
        else:
            print_warning(f"  {timer} timer NOT found")
    
    print_info("Profiler uses context manager for precise timing")
    return True

def run_single_query_test(query: str, run_number: int = 1) -> Dict[str, Any]:
    """Run a single query and measure performance"""
    try:
        start_time = time.time()
        
        response = requests.post(
            f"{BACKEND_URL}/api/chat",
            json={
                "message": query,
                "session_id": f"benchmark_test_{run_number}"
            },
            timeout=30
        )
        
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            
            return {
                "success": True,
                "query": query,
                "latency_ms": latency_ms,
                "answer_length": len(data.get("answer", "")),
                "citations_count": len(data.get("citations", [])),
                "intent": data.get("intent", "unknown"),
                "model": data.get("model", "unknown"),
                "tier1_hit": data.get("tier1_hit", False),
                "backend_latency_ms": data.get("latency_ms", 0)
            }
        else:
            return {
                "success": False,
                "query": query,
                "latency_ms": latency_ms,
                "error": f"HTTP {response.status_code}"
            }
    except Exception as e:
        return {
            "success": False,
            "query": query,
            "error": str(e)
        }

def run_benchmark_tests(num_queries: int = 10):
    """Run benchmark tests to measure current performance"""
    print_header(f"TEST 6: Benchmark Performance Testing ({num_queries} queries)")
    
    results = []
    
    print_info(f"Running {num_queries} queries to measure baseline performance...")
    print_info("This will take a few minutes...\n")
    
    for i, query in enumerate(BENCHMARK_QUERIES[:num_queries], 1):
        print(f"Query {i}/{num_queries}: {query[:60]}...")
        
        # First run (cache miss expected)
        result = run_single_query_test(query, run_number=i)
        results.append(result)
        
        if result["success"]:
            print(f"  Latency: {result['latency_ms']:.0f}ms | Citations: {result['citations_count']} | Intent: {result['intent']}")
        else:
            print_error(f"  Failed: {result.get('error', 'unknown error')}")
        
        time.sleep(0.5)  # Small delay between requests
    
    # Calculate statistics
    successful_results = [r for r in results if r["success"]]
    
    if successful_results:
        latencies = [r["latency_ms"] for r in successful_results]
        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        
        citations_counts = [r["citations_count"] for r in successful_results]
        avg_citations = sum(citations_counts) / len(citations_counts) if citations_counts else 0
        
        print(f"\n{Colors.BLUE}{'='*80}{Colors.RESET}")
        print(f"{Colors.BLUE}BENCHMARK RESULTS{Colors.RESET}")
        print(f"{Colors.BLUE}{'='*80}{Colors.RESET}")
        print(f"Total Queries: {len(results)}")
        print(f"Successful: {len(successful_results)}")
        print(f"Failed: {len(results) - len(successful_results)}")
        print(f"\nLatency Statistics:")
        print(f"  Average: {avg_latency:.0f}ms")
        print(f"  Min: {min_latency:.0f}ms")
        print(f"  Max: {max_latency:.0f}ms")
        print(f"\nCitations:")
        print(f"  Average per query: {avg_citations:.1f}")
        
        # Check against target
        target_latency = 7000  # 7 seconds
        if avg_latency < target_latency:
            print_success(f"\n✅ Average latency ({avg_latency:.0f}ms) is UNDER target ({target_latency}ms)")
        else:
            print_error(f"\n❌ Average latency ({avg_latency:.0f}ms) EXCEEDS target ({target_latency}ms)")
            print_warning(f"   Latency is {((avg_latency - target_latency) / target_latency * 100):.1f}% over target")
        
        return {
            "total_queries": len(results),
            "successful": len(successful_results),
            "failed": len(results) - len(successful_results),
            "avg_latency_ms": avg_latency,
            "min_latency_ms": min_latency,
            "max_latency_ms": max_latency,
            "avg_citations": avg_citations,
            "target_met": avg_latency < target_latency
        }
    else:
        print_error("All queries failed - cannot calculate statistics")
        return None

def main():
    print(f"\n{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BLUE}STRYDA-v2 Caching & Performance Optimization Test Suite{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*80}{Colors.RESET}\n")
    
    # Test 1: Health check
    if not test_health_endpoint():
        print_error("Backend is not accessible. Exiting.")
        sys.exit(1)
    
    # Test 2: Check cache_manager.py implementation
    cache_manager_exists = check_cache_manager_implementation()
    
    # Test 3: Check caching integration
    caching_integrated = check_caching_integration()
    
    # Test 4: Check connection pooling
    pooling_implemented = check_connection_pooling()
    
    # Test 5: Check profiler
    check_profiler_timing()
    
    # Test 6: Run benchmark tests
    benchmark_results = run_benchmark_tests(num_queries=10)
    
    # Final Summary
    print_header("FINAL SUMMARY")
    
    print("Implementation Status:")
    print(f"  Phase 1 - In-Memory Caching: {'✅ IMPLEMENTED' if cache_manager_exists and caching_integrated else '❌ NOT IMPLEMENTED'}")
    print(f"  Phase 2 - Profiler Timing: ✅ EXISTS (accuracy needs verification)")
    print(f"  Phase 3 - Connection Pooling: {'✅ IMPLEMENTED' if pooling_implemented else '❌ NOT IMPLEMENTED'}")
    
    if benchmark_results:
        print(f"\nPerformance:")
        print(f"  Average Latency: {benchmark_results['avg_latency_ms']:.0f}ms")
        print(f"  Target (<7000ms): {'✅ MET' if benchmark_results['target_met'] else '❌ NOT MET'}")
    
    print("\nRecommendations:")
    if not cache_manager_exists:
        print_error("  1. Implement cache_manager.py as specified in review request")
    if not caching_integrated:
        print_error("  2. Integrate caching into simple_tier1_retrieval.py")
    if not pooling_implemented:
        print_error("  3. Implement connection pooling in simple_tier1_retrieval.py")
    if benchmark_results and not benchmark_results['target_met']:
        print_error(f"  4. Optimize performance to meet <7s target (currently {benchmark_results['avg_latency_ms']/1000:.1f}s)")
    
    if cache_manager_exists and caching_integrated and pooling_implemented and benchmark_results and benchmark_results['target_met']:
        print_success("\n🎉 All optimizations implemented and target met!")
    else:
        print_warning("\n⚠️  Some optimizations are missing or target not met")

if __name__ == "__main__":
    main()
