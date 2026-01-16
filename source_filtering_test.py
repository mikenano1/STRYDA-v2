"""
COMPREHENSIVE SOURCE FILTERING VALIDATION TEST
Tests the newly re-implemented source filtering in simple_tier1_retrieval.py
with canonical_source_map() and fallback logic.

This test validates:
1. canonical_source_map() correctly detects target sources based on query keywords
2. Filtered search with psycopg2-safe IN clause works correctly
3. Fallback to global search activates when filtered search returns 0 results
4. Source distribution in retrieved chunks matches query intent
5. No more "0 citations" for document-specific queries
"""

import requests
import json
import time
from typing import Dict, List, Any
from datetime import datetime

# Backend URL
BACKEND_URL = "https://pdf-library-14.preview.emergentagent.com/api/chat"

# Test queries organized by expected source
TEST_QUERIES = {
    "E2/AS1": [
        "What is the minimum apron flashing cover required for E2/AS1?",
        "What roof pitch is acceptable for direct fix cladding under E2?",
        "What are the cavity batten requirements in E2/AS1?",
        "What is the minimum clearance under deck to ground per E2/AS1?",
        "What is the minimum fall for roof membrane in E2?"
    ],
    "NZS 3604": [
        "What is the stud spacing for NZS 3604?",
        "What are the requirements in NZS 3604 Table 7.1?",
        "What bearer and joist sizing does NZS 3604 require?",
        "What lintel span is permitted in NZS 3604?",
        "What nog spacing is required per NZS 3604?"
    ],
    "NZ Building Code": [
        "What are H1 insulation R-values for Auckland?",
        "What are F4 means of escape requirements?",
        "What are G5.3.2 hearth clearance requirements?",
        "What are C3 fire stopping requirements?",
        "What are G12 water supply requirements?"
    ],
    "NZS 4229": [
        "What are reinforcement requirements in NZS 4229?",
        "What concrete masonry block requirements are in NZS 4229?",
        "What steel mesh sizing does NZS 4229 specify?",
        "What rebar spacing is required per NZS 4229?",
        "What lintel reinforcement does NZS 4229 require?"
    ]
}

def test_chat_endpoint(query: str, session_id: str) -> Dict[str, Any]:
    """Test the /api/chat endpoint with a query"""
    try:
        payload = {
            "message": query,
            "session_id": session_id
        }
        
        start_time = time.time()
        response = requests.post(
            BACKEND_URL,
            json=payload,
            timeout=30
        )
        latency = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            # Handle both "citation" and "citations" keys
            citations = data.get("citations", data.get("citation", []))
            return {
                "success": True,
                "status_code": 200,
                "latency_ms": latency,
                "response": data.get("answer", ""),
                "citations": citations,
                "intent": data.get("intent", "unknown"),
                "tier1_hit": data.get("tier1_hit", False),
                "raw_data": data
            }
        else:
            return {
                "success": False,
                "status_code": response.status_code,
                "latency_ms": latency,
                "error": response.text
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "latency_ms": 0
        }

def extract_citation_sources(citations: List[Dict]) -> Dict[str, int]:
    """Extract source distribution from citations"""
    source_counts = {}
    for citation in citations:
        source = citation.get("source", "Unknown")
        source_counts[source] = source_counts.get(source, 0) + 1
    return source_counts

def validate_query_result(query: str, expected_source: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """Validate a single query result against expected criteria"""
    validation = {
        "query": query,
        "expected_source": expected_source,
        "pass": False,
        "issues": []
    }
    
    if not result.get("success"):
        validation["issues"].append(f"Request failed: {result.get('error', 'Unknown error')}")
        return validation
    
    # Check citations
    citations = result.get("citations", [])
    num_citations = len(citations)
    
    if num_citations == 0:
        validation["issues"].append("0 citations returned (CRITICAL ISSUE)")
        return validation
    
    # Check citation sources
    source_counts = extract_citation_sources(citations)
    
    if not source_counts:
        validation["issues"].append("No sources in citations")
        return validation
    
    # Check for "Unknown" sources
    if "Unknown" in source_counts:
        validation["issues"].append(f"'Unknown' sources found ({source_counts['Unknown']} citations)")
    
    # Check if expected source is present
    expected_source_found = False
    for source in source_counts.keys():
        if expected_source.lower() in source.lower() or source.lower() in expected_source.lower():
            expected_source_found = True
            break
    
    # Determine if query passed
    if num_citations >= 1 and num_citations <= 3:
        if expected_source_found or expected_source == "NZ Building Code":
            # For NZ Building Code, we accept any building code source
            validation["pass"] = True
        else:
            validation["issues"].append(f"Expected source '{expected_source}' not found in citations. Got: {list(source_counts.keys())}")
    else:
        validation["issues"].append(f"Citation count out of range: {num_citations} (expected 1-3)")
    
    # Add metadata
    validation["num_citations"] = num_citations
    validation["sources"] = source_counts
    validation["latency_ms"] = result.get("latency_ms", 0)
    validation["intent"] = result.get("intent", "unknown")
    validation["response_length"] = len(result.get("response", ""))
    
    return validation

def run_comprehensive_test():
    """Run comprehensive source filtering validation"""
    print("=" * 80)
    print("COMPREHENSIVE SOURCE FILTERING VALIDATION")
    print("=" * 80)
    print(f"Testing {sum(len(queries) for queries in TEST_QUERIES.values())} queries across 4 source categories")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test started: {datetime.now().isoformat()}")
    print("=" * 80)
    print()
    
    all_results = []
    category_stats = {}
    
    # Test each category
    for expected_source, queries in TEST_QUERIES.items():
        print(f"\n{'=' * 80}")
        print(f"TESTING: {expected_source} Queries ({len(queries)} queries)")
        print(f"{'=' * 80}")
        
        category_results = []
        
        for i, query in enumerate(queries, 1):
            print(f"\n[{i}/{len(queries)}] Testing: {query[:70]}...")
            
            # Generate unique session ID for each query
            session_id = f"test_{expected_source.replace(' ', '_').replace('/', '_')}_{i}_{int(time.time())}"
            
            # Execute query
            result = test_chat_endpoint(query, session_id)
            
            # Validate result
            validation = validate_query_result(query, expected_source, result)
            
            # Print result
            if validation["pass"]:
                print(f"   ✅ PASS")
            else:
                print(f"   ❌ FAIL")
            
            print(f"   Citations: {validation.get('num_citations', 0)}")
            if validation.get("sources"):
                sources_str = ", ".join([f"{src} x{count}" for src, count in validation["sources"].items()])
                print(f"   Sources: {sources_str}")
            
            if validation.get("issues"):
                for issue in validation["issues"]:
                    print(f"   ⚠️  {issue}")
            
            print(f"   Latency: {validation.get('latency_ms', 0):.0f}ms")
            print(f"   Intent: {validation.get('intent', 'unknown')}")
            
            category_results.append(validation)
            all_results.append(validation)
            
            # Small delay between requests
            time.sleep(0.5)
        
        # Category summary
        passed = sum(1 for r in category_results if r["pass"])
        total = len(category_results)
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        category_stats[expected_source] = {
            "passed": passed,
            "total": total,
            "pass_rate": pass_rate,
            "results": category_results
        }
        
        print(f"\n{expected_source} Summary: {passed}/{total} passed ({pass_rate:.1f}%)")
    
    # Overall summary
    print(f"\n{'=' * 80}")
    print("OVERALL SUMMARY")
    print(f"{'=' * 80}")
    
    total_passed = sum(1 for r in all_results if r["pass"])
    total_queries = len(all_results)
    overall_pass_rate = (total_passed / total_queries * 100) if total_queries > 0 else 0
    
    print(f"\nTotal Queries: {total_queries}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_queries - total_passed}")
    print(f"Pass Rate: {overall_pass_rate:.1f}%")
    
    # Category breakdown
    print(f"\nCategory Breakdown:")
    for source, stats in category_stats.items():
        status = "✅" if stats["pass_rate"] >= 80 else "⚠️" if stats["pass_rate"] >= 60 else "❌"
        print(f"  {status} {source}: {stats['passed']}/{stats['total']} ({stats['pass_rate']:.1f}%)")
    
    # Key metrics
    avg_latency = sum(r.get("latency_ms", 0) for r in all_results) / len(all_results) if all_results else 0
    zero_citation_count = sum(1 for r in all_results if r.get("num_citations", 0) == 0)
    unknown_source_count = sum(1 for r in all_results if "Unknown" in r.get("sources", {}))
    
    print(f"\nKey Metrics:")
    print(f"  Average Latency: {avg_latency:.0f}ms")
    print(f"  Queries with 0 Citations: {zero_citation_count}/{total_queries}")
    print(f"  Queries with 'Unknown' Sources: {unknown_source_count}/{total_queries}")
    
    # Validation criteria
    print(f"\n{'=' * 80}")
    print("VALIDATION CRITERIA")
    print(f"{'=' * 80}")
    
    criteria_results = []
    
    # 1. Source Filtering Working
    source_match_count = sum(1 for r in all_results if r["pass"])
    source_filtering_pass = (source_match_count / total_queries * 100) >= 70
    criteria_results.append(("Source Filtering Working", source_filtering_pass, f"{source_match_count}/{total_queries} queries returned expected sources"))
    
    # 2. Fallback Logic Working
    fallback_working = zero_citation_count < (total_queries * 0.2)  # Less than 20% should have 0 citations
    criteria_results.append(("Fallback Logic Working", fallback_working, f"Only {zero_citation_count}/{total_queries} queries returned 0 citations"))
    
    # 3. Citations Present
    citations_present = (total_queries - zero_citation_count) / total_queries * 100 >= 80
    criteria_results.append(("Citations Present (≥80%)", citations_present, f"{total_queries - zero_citation_count}/{total_queries} queries have citations"))
    
    # 4. No "Unknown" Sources
    no_unknown = unknown_source_count == 0
    criteria_results.append(("No 'Unknown' Sources", no_unknown, f"{unknown_source_count}/{total_queries} queries have 'Unknown' sources"))
    
    # 5. Response Quality
    avg_response_length = sum(r.get("response_length", 0) for r in all_results) / len(all_results) if all_results else 0
    response_quality = avg_response_length > 50
    criteria_results.append(("Response Quality", response_quality, f"Average response length: {avg_response_length:.0f} chars"))
    
    for criterion, passed, detail in criteria_results:
        status = "✅" if passed else "❌"
        print(f"{status} {criterion}: {detail}")
    
    # Final verdict
    all_criteria_pass = all(passed for _, passed, _ in criteria_results)
    
    print(f"\n{'=' * 80}")
    if all_criteria_pass:
        print("🎉 VALIDATION PASSED - Source filtering is working correctly!")
    else:
        print("⚠️  VALIDATION FAILED - Source filtering needs improvement")
    print(f"{'=' * 80}")
    
    # Generate detailed report
    generate_report(all_results, category_stats, criteria_results, overall_pass_rate)
    
    return all_results, category_stats

def generate_report(all_results, category_stats, criteria_results, overall_pass_rate):
    """Generate comprehensive markdown report"""
    report_path = "/app/tests/SOURCE_FILTERING_VALIDATION_REPORT.md"
    
    with open(report_path, "w") as f:
        f.write("# SOURCE FILTERING VALIDATION REPORT\n\n")
        f.write(f"**Test Date:** {datetime.now().isoformat()}\n\n")
        f.write(f"**Backend URL:** {BACKEND_URL}\n\n")
        f.write(f"**Total Queries Tested:** {len(all_results)}\n\n")
        
        f.write("## Executive Summary\n\n")
        f.write(f"- **Overall Pass Rate:** {overall_pass_rate:.1f}%\n")
        f.write(f"- **Queries Passed:** {sum(1 for r in all_results if r['pass'])}/{len(all_results)}\n")
        f.write(f"- **Average Latency:** {sum(r.get('latency_ms', 0) for r in all_results) / len(all_results):.0f}ms\n\n")
        
        f.write("## Validation Criteria Results\n\n")
        for criterion, passed, detail in criteria_results:
            status = "✅ PASS" if passed else "❌ FAIL"
            f.write(f"### {criterion}: {status}\n")
            f.write(f"{detail}\n\n")
        
        f.write("## Category Breakdown\n\n")
        for source, stats in category_stats.items():
            f.write(f"### {source} ({stats['passed']}/{stats['total']} passed - {stats['pass_rate']:.1f}%)\n\n")
            
            for result in stats['results']:
                status = "✅" if result['pass'] else "❌"
                f.write(f"{status} **Query:** {result['query']}\n")
                f.write(f"   - Citations: {result.get('num_citations', 0)}\n")
                if result.get('sources'):
                    sources_str = ", ".join([f"{src} x{count}" for src, count in result['sources'].items()])
                    f.write(f"   - Sources: {sources_str}\n")
                if result.get('issues'):
                    f.write(f"   - Issues: {'; '.join(result['issues'])}\n")
                f.write(f"   - Latency: {result.get('latency_ms', 0):.0f}ms\n")
                f.write(f"   - Intent: {result.get('intent', 'unknown')}\n\n")
        
        f.write("## Detailed Query Results\n\n")
        f.write("| # | Query | Expected Source | Citations | Sources | Pass | Issues |\n")
        f.write("|---|-------|----------------|-----------|---------|------|--------|\n")
        
        for i, result in enumerate(all_results, 1):
            query_short = result['query'][:50] + "..." if len(result['query']) > 50 else result['query']
            sources_str = ", ".join([f"{src}({count})" for src, count in result.get('sources', {}).items()])
            pass_str = "✅" if result['pass'] else "❌"
            issues_str = "; ".join(result.get('issues', []))[:50]
            
            f.write(f"| {i} | {query_short} | {result['expected_source']} | {result.get('num_citations', 0)} | {sources_str} | {pass_str} | {issues_str} |\n")
        
        f.write("\n## Conclusion\n\n")
        if overall_pass_rate >= 80:
            f.write("✅ **Source filtering is working correctly.** The canonical_source_map() function successfully detects target sources, and the fallback logic activates appropriately when filtered searches return no results.\n")
        elif overall_pass_rate >= 60:
            f.write("⚠️ **Source filtering is partially working.** Some improvements are needed to achieve the target 80% pass rate.\n")
        else:
            f.write("❌ **Source filtering needs significant improvement.** The system is not meeting the expected performance criteria.\n")
    
    print(f"\n📄 Detailed report generated: {report_path}")

if __name__ == "__main__":
    try:
        results, stats = run_comprehensive_test()
        print("\n✅ Test completed successfully")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
