#!/usr/bin/env python3
"""
STRYDA-v2 Comprehensive Post-Regeneration Validation
Detailed diagnostics for each query showing:
- Intent detection
- Canonical source mapping
- Source filtering
- Retrieval results
- Citations
"""

import requests
import json
import time
from typing import Dict, List, Any

BACKEND_URL = "http://localhost:8001"
CHAT_ENDPOINT = f"{BACKEND_URL}/api/chat"

# 10 Sample Test Queries
TEST_QUERIES = [
    # NZS 3604 (2 queries)
    {"query": "nzs 3604 stud spacing requirements", "category": "NZS 3604", "expect_citations": True},
    {"query": "nzs 3604 rafter span 4.2m", "category": "NZS 3604", "expect_citations": True},
    
    # E2/AS1 (2 queries)
    {"query": "e2as1 minimum apron flashing cover", "category": "E2/AS1", "expect_citations": True},
    {"query": "e2as1 roof pitch requirements", "category": "E2/AS1", "expect_citations": True},
    
    # NZ Building Code (3 queries - H1, F4, G12)
    {"query": "h1 insulation r-values for walls", "category": "NZ Building Code (H1)", "expect_citations": True},
    {"query": "minimum barrier height f4 requirements", "category": "NZ Building Code (F4)", "expect_citations": True},
    {"query": "g12 hot water system safe temperatures", "category": "NZ Building Code (G12)", "expect_citations": True},
    
    # NZS 4229 (2 queries)
    {"query": "nzs 4229 minimum reinforcing for concrete masonry", "category": "NZS 4229", "expect_citations": True},
    {"query": "nzs 4229 lintel reinforcement schedule", "category": "NZS 4229", "expect_citations": True},
    
    # Practical (1 query)
    {"query": "best screws for treated pine", "category": "Practical", "expect_citations": False},
]

def test_query_with_diagnostics(test_case: Dict[str, Any], query_num: int) -> Dict[str, Any]:
    """Test a single query and return detailed diagnostics"""
    
    query = test_case["query"]
    category = test_case["category"]
    expect_citations = test_case["expect_citations"]
    
    print(f"\n{'='*80}")
    print(f"[{query_num}/10] Testing: {query}")
    print(f"Category: {category}")
    print(f"Expected citations: {'Yes' if expect_citations else 'No'}")
    print(f"{'='*80}")
    
    # Send query
    start_time = time.time()
    try:
        response = requests.post(
            CHAT_ENDPOINT,
            json={"message": query, "session_id": f"validation_{query_num}"},
            timeout=30
        )
        latency_ms = (time.time() - start_time) * 1000
        
        if response.status_code != 200:
            print(f"❌ HTTP Error: {response.status_code}")
            return {
                "query_num": query_num,
                "query": query,
                "category": category,
                "error": f"HTTP {response.status_code}",
                "pass": False
            }
        
        data = response.json()
        
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return {
            "query_num": query_num,
            "query": query,
            "category": category,
            "error": str(e),
            "pass": False
        }
    
    # Extract diagnostics
    intent = data.get("intent", "unknown")
    citations = data.get("citations", [])
    citations_count = len(citations)
    
    # Extract citation sources
    citation_sources = []
    for cite in citations:
        source = cite.get("source", "Unknown")
        page = cite.get("page", 0)
        citation_sources.append(f"{source} p.{page}")
    
    # Determine pass/fail
    if expect_citations:
        passed = intent == "compliance_strict" and citations_count > 0
        if not passed:
            if intent != "compliance_strict":
                reason = f"Wrong intent: {intent}"
            else:
                reason = "No citations returned"
        else:
            reason = "✅ PASS"
    else:
        passed = intent != "compliance_strict" or citations_count <= 1
        if not passed:
            reason = f"Over-classified as compliance with {citations_count} citations"
        else:
            reason = "✅ PASS"
    
    # Print diagnostics
    print(f"\n📊 DIAGNOSTICS:")
    print(f"   Intent detected: {intent}")
    print(f"   Citations returned: {citations_count}")
    if citation_sources:
        print(f"   Citation sources: {', '.join(citation_sources[:3])}")
    print(f"   Latency: {latency_ms:.0f}ms")
    print(f"   Tier-1 hit: {data.get('tier1_hit', False)}")
    
    # Verdict
    verdict = "✅ PASS" if passed else "❌ FAIL"
    print(f"\n{verdict}: {reason}")
    
    return {
        "query_num": query_num,
        "query": query,
        "category": category,
        "intent": intent,
        "citations_count": citations_count,
        "citation_sources": citation_sources[:3],
        "latency_ms": int(latency_ms),
        "tier1_hit": data.get("tier1_hit", False),
        "expect_citations": expect_citations,
        "pass": passed,
        "reason": reason
    }

def run_comprehensive_validation():
    """Run all 10 test queries with detailed diagnostics"""
    
    print("=" * 80)
    print("STRYDA-v2 COMPREHENSIVE POST-REGENERATION VALIDATION")
    print("=" * 80)
    print(f"Backend: {BACKEND_URL}")
    print(f"Test queries: {len(TEST_QUERIES)}")
    print()
    
    all_results = []
    
    for i, test_case in enumerate(TEST_QUERIES, 1):
        result = test_query_with_diagnostics(test_case, i)
        all_results.append(result)
        time.sleep(0.5)  # Small delay between queries
    
    # Generate summary
    print(f"\n{'='*80}")
    print("VALIDATION SUMMARY")
    print(f"{'='*80}\n")
    
    passed = sum(1 for r in all_results if r.get("pass", False))
    total = len(all_results)
    pass_rate = (passed / total) * 100 if total > 0 else 0
    
    print(f"Overall: {passed}/{total} PASS ({pass_rate:.1f}%)")
    print()
    
    # Category breakdown
    categories = {}
    for result in all_results:
        cat = result["category"]
        if cat not in categories:
            categories[cat] = {"pass": 0, "total": 0}
        categories[cat]["total"] += 1
        if result.get("pass", False):
            categories[cat]["pass"] += 1
    
    print("Category Breakdown:")
    for cat, stats in categories.items():
        pct = (stats["pass"] / stats["total"]) * 100 if stats["total"] > 0 else 0
        symbol = "✅" if pct == 100 else "⚠️" if pct >= 50 else "❌"
        print(f"  {symbol} {cat}: {stats['pass']}/{stats['total']} ({pct:.0f}%)")
    
    # Failed queries
    failed = [r for r in all_results if not r.get("pass", False)]
    if failed:
        print(f"\nFailed Queries ({len(failed)}):")
        for r in failed:
            print(f"  ❌ {r['query']}")
            print(f"     Reason: {r.get('reason', 'Unknown')}")
    
    # Generate validation table
    print(f"\n{'='*80}")
    print("VALIDATION TABLE")
    print(f"{'='*80}\n")
    
    print(f"{'Query':<50} {'Intent':<18} {'Cites':<6} {'Pass':<6}")
    print("-" * 80)
    
    for r in all_results:
        query_short = r["query"][:48]
        intent_short = r["intent"][:16]
        cites = str(r["citations_count"])
        pass_str = "✅ PASS" if r.get("pass", False) else "❌ FAIL"
        
        print(f"{query_short:<50} {intent_short:<18} {cites:<6} {pass_str:<6}")
    
    print()
    
    # Save results
    with open("/app/tests/comprehensive_validation_results.json", "w") as f:
        json.dump({
            "summary": {
                "total": total,
                "passed": passed,
                "failed": total - passed,
                "pass_rate": pass_rate
            },
            "category_breakdown": categories,
            "detailed_results": all_results
        }, f, indent=2)
    
    print(f"✅ Results saved to /app/tests/comprehensive_validation_results.json")

if __name__ == "__main__":
    run_comprehensive_validation()
