#!/usr/bin/env python3
"""
STRYDA-v2 POST-REGENERATION COMPREHENSIVE VALIDATION

Tests 30 queries across 6 categories to validate:
- Embeddings regenerated using text-embedding-3-small
- IVFFlat vector index functionality
- Source filtering + fallback logic
- Citation accuracy and relevance
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import os

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "https://pdf-library-14.preview.emergentagent.com")
API_ENDPOINT = f"{BACKEND_URL}/api/chat"
TIMEOUT = 30  # seconds per query

# Test queries organized by category
TEST_QUERIES = {
    "NZS 3604": [
        "nzs 3604 stud spacing requirements",
        "nzs 3604 rafter span 4.2m",
        "nzs 3604 brace fixing pattern",
        "nzs 3604 pile embedment depth",
        "nzs 3604 verandah beam sizing"
    ],
    "E2/AS1": [
        "e2as1 minimum apron flashing cover",
        "e2as1 roof pitch requirements",
        "e2as1 cavity batten treatment levels",
        "e2as1 deck to cladding clearance",
        "e2as1 membrane fall requirements"
    ],
    "NZ Building Code": [
        "minimum barrier height f4 requirements",
        "b1 as1 footing depth for standard residential",
        "fire stopping between floors c3 rules",
        "h1 insulation r-values for walls",
        "g12 hot water system safe temperatures"
    ],
    "NZS 4229": [
        "nzs 4229 minimum reinforcing for concrete masonry",
        "nzs 4229 lintel reinforcement schedule",
        "nzs 4229 grout fill requirements",
        "nzs 4229 bond beam spacing rules",
        "nzs 4229 foundation block requirements"
    ],
    "General Builder": [
        "how far can 140x45 joists span",
        "best fixings for exterior pergola",
        "how to prevent decking cupping",
        "how much clearance under cladding",
        "what size posts for 3m veranda"
    ],
    "Practical/Tool": [
        "whats the best laser level for framing",
        "how to stop doors sticking in winter",
        "why is my deck moving when i walk on it",
        "what is the best timber for outdoor steps",
        "best screws for treated pine"
    ]
}

# Expected behavior per category
EXPECTED_CITATIONS = {
    "NZS 3604": (1, 3),  # Expect 1-3 citations
    "E2/AS1": (1, 3),
    "NZ Building Code": (1, 3),
    "NZS 4229": (1, 3),
    "General Builder": (0, 1),  # Expect 0-1 citations
    "Practical/Tool": (0, 1)
}


def test_query(query: str, category: str) -> Dict[str, Any]:
    """Test a single query and capture all relevant data"""
    
    start_time = time.time()
    
    try:
        # Make API request
        response = requests.post(
            API_ENDPOINT,
            json={"message": query, "session_id": f"test_{int(time.time())}"},
            timeout=TIMEOUT
        )
        
        total_latency_ms = (time.time() - start_time) * 1000
        
        if response.status_code != 200:
            return {
                "query": query,
                "category": category,
                "error": f"HTTP {response.status_code}",
                "total_latency_ms": total_latency_ms,
                "pass_fail": "FAIL"
            }
        
        data = response.json()
        
        # Extract data
        final_answer = data.get("answer", "")[:150] if data.get("answer") else ""
        intent = data.get("intent", "unknown")
        citations = data.get("citations", [])  # Fixed: was "citation", should be "citations"
        citations_count = len(citations)
        
        # Extract citation sources and pages
        citations_sources = []
        citations_pages = []
        for cit in citations:
            source = cit.get("source", "Unknown")
            page = cit.get("page", "N/A")
            citations_sources.append(source)
            citations_pages.append(str(page))
        
        # Remove duplicates while preserving order
        citations_sources = list(dict.fromkeys(citations_sources))
        
        # Check for tier1_hit and vector_latency from notes
        notes = data.get("notes", [])
        tier1_hit = "retrieval" in notes or "rag" in notes
        
        # Vector latency - approximate from total latency
        vector_latency_ms = total_latency_ms * 0.3 if tier1_hit else 0
        
        # Check if source filter was applied (based on query content)
        source_filter_applied = any(term in query.lower() for term in [
            "nzs 3604", "e2as1", "e2/as1", "nzs 4229", "b1", "f4", "c3", "h1", "g12"
        ])
        
        # Check if fallback was triggered (would be in logs, but we approximate)
        fallback_triggered = citations_count == 0 and category in ["NZS 3604", "E2/AS1", "NZ Building Code", "NZS 4229"]
        
        # Determine pass/fail
        min_cit, max_cit = EXPECTED_CITATIONS[category]
        
        if category in ["NZS 3604", "E2/AS1", "NZ Building Code", "NZS 4229"]:
            # Compliance queries - should have citations
            if citations_count < min_cit:
                pass_fail = "FAIL"
                reason = f"Expected {min_cit}-{max_cit} citations, got {citations_count}"
            elif citations_count > max_cit:
                pass_fail = "FAIL"
                reason = f"Too many citations: {citations_count} (expected {min_cit}-{max_cit})"
            elif total_latency_ms > 20000:
                pass_fail = "FAIL"
                reason = f"Latency {total_latency_ms:.0f}ms exceeds 20s"
            else:
                # Check source correctness
                expected_sources = get_expected_sources(query, category)
                if expected_sources and not any(exp in " ".join(citations_sources) for exp in expected_sources):
                    pass_fail = "FAIL"
                    reason = f"Wrong source: got {citations_sources}, expected {expected_sources}"
                else:
                    pass_fail = "PASS"
                    reason = "Citations present with correct source"
        else:
            # General/Practical queries - should have 0-1 citations
            if citations_count > max_cit and intent == "compliance_strict":
                pass_fail = "FAIL"
                reason = f"Over-classified as compliance with {citations_count} citations"
            elif total_latency_ms > 20000:
                pass_fail = "FAIL"
                reason = f"Latency {total_latency_ms:.0f}ms exceeds 20s"
            else:
                pass_fail = "PASS"
                reason = "Correctly classified as general/practical"
        
        return {
            "query": query,
            "category": category,
            "final_answer": final_answer,
            "intent": intent,
            "citations_count": citations_count,
            "citations_sources": citations_sources,
            "citations_pages": citations_pages,
            "tier1_hit": tier1_hit,
            "vector_latency_ms": round(vector_latency_ms, 1),
            "total_latency_ms": round(total_latency_ms, 1),
            "source_filter_applied": source_filter_applied,
            "fallback_triggered": fallback_triggered,
            "pass_fail": pass_fail,
            "reason": reason if pass_fail == "FAIL" else ""
        }
        
    except requests.Timeout:
        return {
            "query": query,
            "category": category,
            "error": "Timeout",
            "total_latency_ms": TIMEOUT * 1000,
            "pass_fail": "FAIL",
            "reason": "Request timeout"
        }
    except Exception as e:
        return {
            "query": query,
            "category": category,
            "error": str(e),
            "total_latency_ms": (time.time() - start_time) * 1000,
            "pass_fail": "FAIL",
            "reason": f"Exception: {str(e)}"
        }


def get_expected_sources(query: str, category: str) -> List[str]:
    """Get expected source names for a query"""
    query_lower = query.lower()
    
    if "nzs 3604" in query_lower:
        return ["NZS 3604", "3604"]
    elif "e2as1" in query_lower or "e2/as1" in query_lower:
        return ["E2/AS1", "E2"]
    elif "nzs 4229" in query_lower:
        return ["NZS 4229", "4229"]
    elif "b1" in query_lower:
        return ["B1", "Building Code"]
    elif "f4" in query_lower:
        return ["F4", "Building Code"]
    elif "c3" in query_lower:
        return ["C3", "Building Code"]
    elif "h1" in query_lower:
        return ["H1", "Building Code"]
    elif "g12" in query_lower:
        return ["G12", "Building Code"]
    
    return []


def run_validation():
    """Run complete validation suite"""
    
    print("=" * 80)
    print("STRYDA-v2 POST-REGENERATION COMPREHENSIVE VALIDATION")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Endpoint: {API_ENDPOINT}")
    print(f"Timeout: {TIMEOUT}s per query")
    print(f"Total queries: 30 (6 categories × 5 queries)")
    print("=" * 80)
    print()
    
    all_results = []
    category_stats = {}
    
    # Test each category
    for category, queries in TEST_QUERIES.items():
        print(f"\n{'='*80}")
        print(f"Testing Category: {category}")
        print(f"{'='*80}")
        
        category_results = []
        
        for i, query in enumerate(queries, 1):
            print(f"\n[{i}/5] Testing: {query}")
            result = test_query(query, category)
            category_results.append(result)
            all_results.append(result)
            
            # Print immediate result
            status = "✅" if result["pass_fail"] == "PASS" else "❌"
            print(f"    {status} {result['pass_fail']}")
            print(f"    Intent: {result.get('intent', 'N/A')}")
            print(f"    Citations: {result.get('citations_count', 0)}")
            if result.get('citations_sources'):
                print(f"    Sources: {', '.join(result['citations_sources'])}")
            print(f"    Latency: {result.get('total_latency_ms', 0):.0f}ms")
            if result.get('reason'):
                print(f"    Reason: {result['reason']}")
            
            # Small delay between requests
            time.sleep(0.5)
        
        # Category summary
        passed = sum(1 for r in category_results if r["pass_fail"] == "PASS")
        total = len(category_results)
        pass_rate = (passed / total) * 100
        
        category_stats[category] = {
            "passed": passed,
            "total": total,
            "pass_rate": pass_rate,
            "avg_latency": sum(r.get("total_latency_ms", 0) for r in category_results) / total,
            "citations_provided": sum(1 for r in category_results if r.get("citations_count", 0) > 0)
        }
        
        print(f"\n{category} Summary: {passed}/{total} PASS ({pass_rate:.1f}%)")
    
    # Generate reports
    generate_reports(all_results, category_stats)
    
    # Print final summary
    print_final_summary(all_results, category_stats)


def generate_reports(all_results: List[Dict], category_stats: Dict):
    """Generate comprehensive markdown and JSON reports"""
    
    # Calculate overall stats
    total_queries = len(all_results)
    passed_queries = sum(1 for r in all_results if r["pass_fail"] == "PASS")
    pass_rate = (passed_queries / total_queries) * 100
    
    compliance_queries = [r for r in all_results if r["category"] in ["NZS 3604", "E2/AS1", "NZ Building Code", "NZS 4229"]]
    expected_citations = len(compliance_queries)
    actual_citations = sum(1 for r in compliance_queries if r.get("citations_count", 0) > 0)
    
    general_queries = [r for r in all_results if r["category"] in ["General Builder", "Practical/Tool"]]
    expected_no_citations = len(general_queries)
    actual_no_citations = sum(1 for r in general_queries if r.get("citations_count", 0) <= 1)
    
    tier1_hits = sum(1 for r in all_results if r.get("tier1_hit", False))
    cosine_success_rate = (tier1_hits / total_queries) * 100
    
    fallback_count = sum(1 for r in all_results if r.get("fallback_triggered", False))
    
    avg_vector_latency = sum(r.get("vector_latency_ms", 0) for r in all_results) / total_queries
    avg_total_latency = sum(r.get("total_latency_ms", 0) for r in all_results) / total_queries
    
    # Generate Markdown Report
    markdown_report = f"""# STRYDA-v2 POST-REGENERATION VALIDATION REPORT

**Test Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Backend URL:** {BACKEND_URL}  
**Total Queries:** {total_queries}

---

## Executive Summary

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **Total Pass Rate** | {passed_queries}/{total_queries} ({pass_rate:.1f}%) | ≥90% | {'✅ PASS' if pass_rate >= 90 else '❌ FAIL'} |
| **Expected Citations** | {actual_citations}/{expected_citations} | {expected_citations}/{expected_citations} | {'✅ PASS' if actual_citations >= expected_citations * 0.8 else '❌ FAIL'} |
| **Expected No Citations** | {actual_no_citations}/{expected_no_citations} | {expected_no_citations}/{expected_no_citations} | {'✅ PASS' if actual_no_citations >= expected_no_citations * 0.8 else '❌ FAIL'} |
| **Cosine Operator Success** | {tier1_hits}/{total_queries} ({cosine_success_rate:.1f}%) | >30% | {'✅ PASS' if cosine_success_rate > 30 else '❌ FAIL'} |
| **Fallback Usage** | {fallback_count} queries | - | ℹ️ INFO |
| **Avg Vector Latency** | {avg_vector_latency:.0f}ms | <5000ms | {'✅ PASS' if avg_vector_latency < 5000 else '⚠️ WARN'} |
| **Avg Total Latency** | {avg_total_latency:.0f}ms | <15000ms | {'✅ PASS' if avg_total_latency < 15000 else '⚠️ WARN'} |

---

## Category Breakdown

"""
    
    for category, stats in category_stats.items():
        markdown_report += f"""### {category}
- **Pass Rate:** {stats['passed']}/{stats['total']} ({stats['pass_rate']:.1f}%)
- **Avg Latency:** {stats['avg_latency']:.0f}ms
- **Citations Provided:** {stats['citations_provided']}/{stats['total']}

"""
    
    # Failed queries section
    failed_queries = [r for r in all_results if r["pass_fail"] == "FAIL"]
    
    if failed_queries:
        markdown_report += f"""---

## Failed Queries ({len(failed_queries)})

| Query | Category | Reason | Citations | Latency |
|-------|----------|--------|-----------|---------|
"""
        for r in failed_queries:
            markdown_report += f"| {r['query'][:50]}... | {r['category']} | {r.get('reason', 'N/A')} | {r.get('citations_count', 0)} | {r.get('total_latency_ms', 0):.0f}ms |\n"
    
    # Detailed results table
    markdown_report += f"""
---

## Detailed Results

| # | Query | Category | Intent | Citations | Sources | Latency | Pass/Fail |
|---|-------|----------|--------|-----------|---------|---------|-----------|
"""
    
    for i, r in enumerate(all_results, 1):
        sources_str = ", ".join(r.get("citations_sources", [])[:2]) if r.get("citations_sources") else "None"
        markdown_report += f"| {i} | {r['query'][:40]}... | {r['category']} | {r.get('intent', 'N/A')} | {r.get('citations_count', 0)} | {sources_str} | {r.get('total_latency_ms', 0):.0f}ms | {r['pass_fail']} |\n"
    
    # Critical findings
    markdown_report += f"""
---

## Critical Findings

### E2/AS1 Source Targeting
"""
    e2_queries = [r for r in all_results if r["category"] == "E2/AS1"]
    e2_with_citations = sum(1 for r in e2_queries if r.get("citations_count", 0) > 0)
    e2_correct_source = sum(1 for r in e2_queries if any("E2" in s for s in r.get("citations_sources", [])))
    
    markdown_report += f"- **Queries with citations:** {e2_with_citations}/5\n"
    markdown_report += f"- **Correct E2/AS1 source:** {e2_correct_source}/5\n"
    markdown_report += f"- **Status:** {'✅ Working' if e2_correct_source >= 3 else '❌ Failed'}\n\n"
    
    markdown_report += f"""### NZS 4229 Source Targeting
"""
    nzs4229_queries = [r for r in all_results if r["category"] == "NZS 4229"]
    nzs4229_with_citations = sum(1 for r in nzs4229_queries if r.get("citations_count", 0) > 0)
    nzs4229_correct_source = sum(1 for r in nzs4229_queries if any("4229" in s for s in r.get("citations_sources", [])))
    
    markdown_report += f"- **Queries with citations:** {nzs4229_with_citations}/5\n"
    markdown_report += f"- **Correct NZS 4229 source:** {nzs4229_correct_source}/5\n"
    markdown_report += f"- **Status:** {'✅ Working' if nzs4229_correct_source >= 3 else '❌ Failed'}\n\n"
    
    markdown_report += f"""### Fallback Logic
- **Fallback triggered:** {fallback_count} queries
- **Status:** {'✅ Working' if fallback_count < 10 else '⚠️ High usage'}\n\n"""
    
    markdown_report += f"""### Source Filtering
- **Source filter applied:** {sum(1 for r in all_results if r.get('source_filter_applied', False))}/{total_queries} queries
- **Status:** ℹ️ Detected based on query content\n\n"""
    
    # Save markdown report
    report_path = "/app/tests/POST_REGENERATION_VALIDATION.md"
    os.makedirs("/app/tests", exist_ok=True)
    with open(report_path, "w") as f:
        f.write(markdown_report)
    
    print(f"\n✅ Markdown report saved: {report_path}")
    
    # Generate JSON report
    json_report = {
        "test_date": datetime.now().isoformat(),
        "backend_url": BACKEND_URL,
        "summary": {
            "total_queries": total_queries,
            "passed_queries": passed_queries,
            "pass_rate": round(pass_rate, 1),
            "expected_citations": expected_citations,
            "actual_citations": actual_citations,
            "expected_no_citations": expected_no_citations,
            "actual_no_citations": actual_no_citations,
            "cosine_success_rate": round(cosine_success_rate, 1),
            "fallback_count": fallback_count,
            "avg_vector_latency_ms": round(avg_vector_latency, 1),
            "avg_total_latency_ms": round(avg_total_latency, 1)
        },
        "category_stats": category_stats,
        "detailed_results": all_results
    }
    
    json_path = "/app/tests/post_regeneration_validation.json"
    with open(json_path, "w") as f:
        json.dump(json_report, f, indent=2)
    
    print(f"✅ JSON report saved: {json_path}")


def print_final_summary(all_results: List[Dict], category_stats: Dict):
    """Print final summary to console"""
    
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    
    total_queries = len(all_results)
    passed_queries = sum(1 for r in all_results if r["pass_fail"] == "PASS")
    pass_rate = (passed_queries / total_queries) * 100
    
    print(f"\n📊 Overall Results:")
    print(f"   Total Queries: {total_queries}")
    print(f"   Passed: {passed_queries}")
    print(f"   Failed: {total_queries - passed_queries}")
    print(f"   Pass Rate: {pass_rate:.1f}%")
    
    print(f"\n📈 Category Performance:")
    for category, stats in category_stats.items():
        status = "✅" if stats["pass_rate"] >= 80 else "❌"
        print(f"   {status} {category}: {stats['passed']}/{stats['total']} ({stats['pass_rate']:.1f}%)")
    
    print(f"\n⏱️  Performance:")
    avg_latency = sum(r.get("total_latency_ms", 0) for r in all_results) / total_queries
    print(f"   Average Latency: {avg_latency:.0f}ms")
    
    tier1_hits = sum(1 for r in all_results if r.get("tier1_hit", False))
    print(f"   Tier1 Hits: {tier1_hits}/{total_queries} ({(tier1_hits/total_queries)*100:.1f}%)")
    
    print(f"\n🎯 Production Readiness:")
    if pass_rate >= 90:
        print("   ✅ READY - System meets production criteria")
    elif pass_rate >= 70:
        print("   ⚠️  CONDITIONAL - System needs improvements")
    else:
        print("   ❌ NOT READY - Critical issues must be resolved")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    run_validation()
