#!/usr/bin/env python3
"""
STRYDA-v2 Performance Optimization Benchmark
Tests current implementation to establish baseline before vector search optimization
"""

import requests
import time
import json
from datetime import datetime
from typing import List, Dict, Any

# Backend URL
BACKEND_URL = "https://pdf-library-14.preview.emergentagent.com"

# 20 test queries from CITATION_PRECISION_AUDIT.md
TEST_QUERIES = [
    "E2/AS1 minimum apron flashing cover",
    "B1 Amendment 13 verification methods for structural engineering",
    "G5.3.2 hearth clearance requirements for solid fuel appliances",
    "H1 insulation R-values for Auckland climate zone",
    "F4 means of escape requirements for 2-storey residential buildings",
    "E2.3.7 cladding requirements for horizontal weatherboards",
    "B1.3.3 foundation requirements for standard soil conditions",
    "NZS 3604 clause 5.4.2 bracing requirements",
    "NZS 3604 Table 7.1 wind zones for New Zealand regions",
    "NZS 3604 stud spacing table for standard wind zone",
    "E2/AS1 table for cladding risk scores and weathertightness",
    "NZS 3604 Table 8.3 bearer and joist sizing for decks",
    "difference between B1 and B2 structural compliance verification methods",
    "how does E2 weathertightness relate to H1 thermal performance",
    "NZS 3604 and B1 Amendment 13 requirements for deck joist connections",
    "relationship between F7 warning systems and G5 solid fuel appliances",
    "what underlay is acceptable under corrugate metal roofing per E2/AS1",
    "recommended flashing tape specifications for window installations",
    "what grade timber for external deck joists under NZS 3604",
    "minimum fixing requirements for cladding in Very High wind zone"
]

def check_vector_search_implementation():
    """Check if vector search has been implemented in simple_tier1_retrieval.py"""
    print("\n" + "=" * 80)
    print("CHECKING VECTOR SEARCH IMPLEMENTATION")
    print("=" * 80)
    
    try:
        with open('/app/backend-minimal/simple_tier1_retrieval.py', 'r') as f:
            content = f.read()
            
        # Check for vector search indicators
        has_pgvector = 'pgvector' in content.lower() or 'embedding <=> %s::vector' in content
        has_openai_embedding = 'OpenAI' in content and 'embeddings.create' in content
        has_like_search = 'LIKE %s' in content or "LIKE '%{term}%'" in content
        
        print(f"📁 File: /app/backend-minimal/simple_tier1_retrieval.py")
        print(f"🔍 Vector Search Indicators:")
        print(f"   - pgvector similarity search: {'✅ FOUND' if has_pgvector else '❌ NOT FOUND'}")
        print(f"   - OpenAI embedding generation: {'✅ FOUND' if has_openai_embedding else '❌ NOT FOUND'}")
        print(f"   - LIKE keyword search: {'⚠️ FOUND (should be replaced)' if has_like_search else '✅ NOT FOUND'}")
        
        if has_pgvector and has_openai_embedding and not has_like_search:
            print(f"\n✅ OPTIMIZATION COMPLETE: Vector search implemented")
            return "vector_search"
        elif has_like_search:
            print(f"\n❌ OPTIMIZATION NOT IMPLEMENTED: Still using keyword search")
            return "keyword_search"
        else:
            print(f"\n⚠️ PARTIAL IMPLEMENTATION: Mixed or unclear state")
            return "partial"
            
    except Exception as e:
        print(f"❌ Error checking implementation: {e}")
        return "unknown"

def test_backend_health():
    """Test if backend is accessible"""
    print("\n" + "=" * 80)
    print("TESTING BACKEND HEALTH")
    print("=" * 80)
    
    try:
        # Try the /api/chat endpoint with a simple test
        response = requests.post(
            f"{BACKEND_URL}/api/chat",
            json={"query": "test"},
            timeout=10
        )
        print(f"✅ Backend API check: {response.status_code}")
        if response.status_code == 200:
            print(f"   Backend is accessible and responding")
            return True
        else:
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Backend API check failed: {e}")
        return False

def test_query_performance(query: str, query_num: int) -> Dict[str, Any]:
    """Test a single query and measure performance"""
    print(f"\n{'='*80}")
    print(f"Query #{query_num}: {query}")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/ask",
            json={"query": query},
            timeout=30
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get('answer', '')
            citations = data.get('citation', [])
            notes = data.get('notes', [])
            
            # Check if it's a fallback response
            is_fallback = 'fallback' in notes or len(answer) < 50
            
            word_count = len(answer.split())
            citation_count = len(citations) if isinstance(citations, list) else 0
            
            # Determine verdict
            if is_fallback or citation_count == 0:
                verdict = "❌ FAIL"
                reason = "Fallback response" if is_fallback else "No citations"
            elif word_count < 80:
                verdict = "⚠️ PARTIAL"
                reason = f"Word count too low ({word_count})"
            elif citation_count > 3:
                verdict = "⚠️ PARTIAL"
                reason = f"Too many citations ({citation_count})"
            else:
                verdict = "✅ PASS"
                reason = "All criteria met"
            
            print(f"⏱️  Latency: {latency_ms:.0f}ms ({latency_ms/1000:.1f}s)")
            print(f"📝 Word count: {word_count}")
            print(f"📚 Citations: {citation_count}")
            print(f"🔍 Notes: {notes}")
            print(f"📊 Verdict: {verdict} - {reason}")
            
            if citation_count > 0:
                print(f"📖 Citation sources:")
                for i, cite in enumerate(citations[:3], 1):
                    source = cite.get('source', 'Unknown')
                    page = cite.get('page', 'N/A')
                    print(f"   {i}. {source} (page {page})")
            
            return {
                'query': query,
                'query_num': query_num,
                'latency_ms': latency_ms,
                'word_count': word_count,
                'citation_count': citation_count,
                'verdict': verdict,
                'reason': reason,
                'is_fallback': is_fallback,
                'answer_preview': answer[:200] if answer else '',
                'citations': citations[:3] if citations else [],
                'notes': notes
            }
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return {
                'query': query,
                'query_num': query_num,
                'latency_ms': latency_ms,
                'error': f"HTTP {response.status_code}",
                'verdict': "❌ FAIL"
            }
            
    except requests.Timeout:
        latency_ms = (time.time() - start_time) * 1000
        print(f"⏱️  Timeout after {latency_ms:.0f}ms")
        return {
            'query': query,
            'query_num': query_num,
            'latency_ms': latency_ms,
            'error': 'Timeout',
            'verdict': "❌ FAIL"
        }
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        print(f"❌ Error: {e}")
        return {
            'query': query,
            'query_num': query_num,
            'latency_ms': latency_ms,
            'error': str(e),
            'verdict': "❌ FAIL"
        }

def run_performance_benchmark():
    """Run full performance benchmark on all 20 queries"""
    print("\n" + "=" * 80)
    print("STRYDA-v2 PERFORMANCE OPTIMIZATION BENCHMARK")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Date: {datetime.utcnow().isoformat()}")
    print(f"Total Queries: {len(TEST_QUERIES)}")
    print("=" * 80)
    
    # Check implementation status
    implementation_status = check_vector_search_implementation()
    
    # Check backend health
    if not test_backend_health():
        print("\n❌ Backend is not accessible. Aborting tests.")
        return
    
    results = []
    
    # Test each query
    for i, query in enumerate(TEST_QUERIES, 1):
        result = test_query_performance(query, i)
        results.append(result)
        
        # Small delay between requests
        time.sleep(0.5)
    
    # Calculate statistics
    print("\n" + "=" * 80)
    print("BENCHMARK RESULTS SUMMARY")
    print("=" * 80)
    
    successful_results = [r for r in results if 'error' not in r]
    
    if successful_results:
        latencies = [r['latency_ms'] for r in successful_results]
        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        
        pass_count = sum(1 for r in results if r['verdict'] == "✅ PASS")
        partial_count = sum(1 for r in results if r['verdict'] == "⚠️ PARTIAL")
        fail_count = sum(1 for r in results if r['verdict'] == "❌ FAIL")
        
        total_citations = sum(r.get('citation_count', 0) for r in successful_results)
        avg_citations = total_citations / len(successful_results) if successful_results else 0
        
        fallback_count = sum(1 for r in successful_results if r.get('is_fallback', False))
        
        print(f"\n📊 Performance Metrics:")
        print(f"   Average Latency: {avg_latency:.0f}ms ({avg_latency/1000:.1f}s)")
        print(f"   Min Latency: {min_latency:.0f}ms ({min_latency/1000:.1f}s)")
        print(f"   Max Latency: {max_latency:.0f}ms ({max_latency/1000:.1f}s)")
        print(f"   Target: <7000ms (7s)")
        print(f"   Status: {'✅ MEETS TARGET' if avg_latency < 7000 else '❌ EXCEEDS TARGET'}")
        
        print(f"\n📈 Quality Metrics:")
        print(f"   Pass: {pass_count}/{len(results)} ({pass_count/len(results)*100:.1f}%)")
        print(f"   Partial: {partial_count}/{len(results)} ({partial_count/len(results)*100:.1f}%)")
        print(f"   Fail: {fail_count}/{len(results)} ({fail_count/len(results)*100:.1f}%)")
        print(f"   Fallback Responses: {fallback_count}/{len(successful_results)}")
        print(f"   Average Citations: {avg_citations:.1f}")
        
        # Implementation status
        print(f"\n🔍 Implementation Status:")
        if implementation_status == "vector_search":
            print(f"   ✅ Vector search optimization IMPLEMENTED")
        elif implementation_status == "keyword_search":
            print(f"   ❌ Vector search optimization NOT IMPLEMENTED")
            print(f"   ⚠️  Still using LIKE '%term%' keyword search")
        else:
            print(f"   ⚠️  Implementation status unclear")
        
        # Save results to JSON
        output_data = {
            'test_date': datetime.utcnow().isoformat(),
            'backend_url': BACKEND_URL,
            'implementation_status': implementation_status,
            'optimization_completed': implementation_status == "vector_search",
            'summary': {
                'total_queries': len(results),
                'avg_latency_ms': avg_latency,
                'min_latency_ms': min_latency,
                'max_latency_ms': max_latency,
                'target_latency_ms': 7000,
                'meets_target': avg_latency < 7000,
                'pass_count': pass_count,
                'partial_count': partial_count,
                'fail_count': fail_count,
                'pass_rate': pass_count / len(results) * 100,
                'fallback_count': fallback_count,
                'avg_citations': avg_citations
            },
            'results': results
        }
        
        with open('/app/tests/performance_baseline_results.json', 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"\n💾 Results saved to: /app/tests/performance_baseline_results.json")
        
        # Generate markdown report
        generate_performance_report(output_data)
        
    else:
        print("\n❌ No successful results to analyze")
    
    return results

def generate_performance_report(data: Dict[str, Any]):
    """Generate performance optimization report"""
    
    summary = data['summary']
    implementation_status = data['implementation_status']
    
    report = f"""# STRYDA-v2 Performance Optimization Report

## Test Information

- **Test Date**: {data['test_date']}
- **Backend URL**: {data['backend_url']}
- **Total Queries**: {summary['total_queries']}
- **Implementation Status**: {implementation_status.upper().replace('_', ' ')}

## Implementation Check

"""
    
    if implementation_status == "vector_search":
        report += "✅ **Vector Search IMPLEMENTED**: pgvector similarity search is active\n\n"
    elif implementation_status == "keyword_search":
        report += "❌ **Vector Search NOT IMPLEMENTED**: Still using LIKE '%term%' keyword search\n\n"
        report += "**Current Method**: Keyword search with LIKE queries\n"
        report += "**Expected Method**: pgvector similarity search with OpenAI embeddings\n\n"
    else:
        report += "⚠️ **Implementation Status UNCLEAR**: Unable to determine search method\n\n"
    
    report += f"""## Performance Results

### Latency Metrics

- **Average Latency**: {summary['avg_latency_ms']:.0f}ms ({summary['avg_latency_ms']/1000:.1f}s)
- **Min Latency**: {summary['min_latency_ms']:.0f}ms ({summary['min_latency_ms']/1000:.1f}s)
- **Max Latency**: {summary['max_latency_ms']:.0f}ms ({summary['max_latency_ms']/1000:.1f}s)
- **Target**: <7000ms (7s)
- **Status**: {'✅ MEETS TARGET' if summary['meets_target'] else '❌ EXCEEDS TARGET'}

### Quality Metrics

- **Pass Rate**: {summary['pass_count']}/{summary['total_queries']} ({summary['pass_rate']:.1f}%)
- **Partial Pass**: {summary['partial_count']}/{summary['total_queries']}
- **Failures**: {summary['fail_count']}/{summary['total_queries']}
- **Fallback Responses**: {summary['fallback_count']}
- **Average Citations**: {summary['avg_citations']:.1f}

## Benchmark Results (20 Queries)

| # | Query | Latency (ms) | Citations | Verdict |
|---|-------|--------------|-----------|---------|
"""
    
    for result in data['results']:
        query_short = result['query'][:50] + "..." if len(result['query']) > 50 else result['query']
        latency = result.get('latency_ms', 0)
        citations = result.get('citation_count', 0)
        verdict = result.get('verdict', '❌ FAIL')
        
        report += f"| {result['query_num']} | {query_short} | {latency:.0f} | {citations} | {verdict} |\n"
    
    report += f"""
## Optimization Status

"""
    
    if implementation_status == "keyword_search":
        report += """### ❌ OPTIMIZATION NOT COMPLETED

The vector search optimization has **NOT been implemented** yet. The system is still using the inefficient keyword search method with LIKE queries.

**Required Actions**:
1. Replace keyword search in `/app/backend-minimal/simple_tier1_retrieval.py`
2. Implement pgvector similarity search with OpenAI embeddings
3. Add query embedding generation
4. Use vector distance operator (<=>)  for similarity matching
5. Maintain existing ranking bias logic
6. Re-run benchmark to measure improvement

**Expected Improvements**:
- Latency reduction: Target <7s average (currently {summary['avg_latency_ms']/1000:.1f}s)
- Better semantic matching
- Improved citation accuracy
- Faster retrieval times

"""
    elif implementation_status == "vector_search":
        report += f"""### ✅ OPTIMIZATION COMPLETED

Vector search has been successfully implemented using pgvector similarity search.

**Performance Improvement**:
- Current Average Latency: {summary['avg_latency_ms']:.0f}ms
- Target: <7000ms
- Status: {'✅ Target achieved' if summary['meets_target'] else '⚠️ Further optimization needed'}

**Quality Metrics**:
- Pass Rate: {summary['pass_rate']:.1f}%
- Citation Accuracy: Maintained at {summary['avg_citations']:.1f} citations per query

"""
    
    report += """## Conclusion

"""
    
    if implementation_status == "keyword_search":
        report += "❌ **OPTIMIZATION PENDING**: Vector search implementation required to meet performance targets.\n"
    elif summary['meets_target'] and summary['pass_rate'] >= 80:
        report += "✅ **EXCELLENT**: System meets both latency and quality targets.\n"
    elif summary['meets_target']:
        report += "⚠️ **GOOD**: Latency target met but quality needs improvement.\n"
    elif summary['pass_rate'] >= 80:
        report += "⚠️ **GOOD**: Quality target met but latency needs optimization.\n"
    else:
        report += "❌ **NEEDS WORK**: Both latency and quality require further optimization.\n"
    
    # Save report
    with open('/app/tests/PERFORMANCE_OPTIMIZATION_REPORT.md', 'w') as f:
        f.write(report)
    
    print(f"📄 Performance report saved to: /app/tests/PERFORMANCE_OPTIMIZATION_REPORT.md")

if __name__ == "__main__":
    run_performance_benchmark()
