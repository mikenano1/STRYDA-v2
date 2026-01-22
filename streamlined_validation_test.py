#!/usr/bin/env python3
"""
Streamlined 30-query validation - runs all queries and saves results
"""

import requests
import json
import time
from datetime import datetime
import os

BACKEND_URL = "https://inteldoc-agent.preview.emergentagent.com"
API_ENDPOINT = f"{BACKEND_URL}/api/chat"
TIMEOUT = 30

# All 30 test queries
ALL_QUERIES = [
    # NZS 3604 (5)
    ("nzs 3604 stud spacing requirements", "NZS 3604", True),
    ("nzs 3604 rafter span 4.2m", "NZS 3604", True),
    ("nzs 3604 brace fixing pattern", "NZS 3604", True),
    ("nzs 3604 pile embedment depth", "NZS 3604", True),
    ("nzs 3604 verandah beam sizing", "NZS 3604", True),
    # E2/AS1 (5)
    ("e2as1 minimum apron flashing cover", "E2/AS1", True),
    ("e2as1 roof pitch requirements", "E2/AS1", True),
    ("e2as1 cavity batten treatment levels", "E2/AS1", True),
    ("e2as1 deck to cladding clearance", "E2/AS1", True),
    ("e2as1 membrane fall requirements", "E2/AS1", True),
    # NZ Building Code (5)
    ("minimum barrier height f4 requirements", "NZ Building Code", True),
    ("b1 as1 footing depth for standard residential", "NZ Building Code", True),
    ("fire stopping between floors c3 rules", "NZ Building Code", True),
    ("h1 insulation r-values for walls", "NZ Building Code", True),
    ("g12 hot water system safe temperatures", "NZ Building Code", True),
    # NZS 4229 (5)
    ("nzs 4229 minimum reinforcing for concrete masonry", "NZS 4229", True),
    ("nzs 4229 lintel reinforcement schedule", "NZS 4229", True),
    ("nzs 4229 grout fill requirements", "NZS 4229", True),
    ("nzs 4229 bond beam spacing rules", "NZS 4229", True),
    ("nzs 4229 foundation block requirements", "NZS 4229", True),
    # General Builder (5)
    ("how far can 140x45 joists span", "General Builder", False),
    ("best fixings for exterior pergola", "General Builder", False),
    ("how to prevent decking cupping", "General Builder", False),
    ("how much clearance under cladding", "General Builder", False),
    ("what size posts for 3m veranda", "General Builder", False),
    # Practical/Tool (5)
    ("whats the best laser level for framing", "Practical/Tool", False),
    ("how to stop doors sticking in winter", "Practical/Tool", False),
    ("why is my deck moving when i walk on it", "Practical/Tool", False),
    ("what is the best timber for outdoor steps", "Practical/Tool", False),
    ("best screws for treated pine", "Practical/Tool", False),
]

results = []
start_time = time.time()

print("=" * 80)
print("STRYDA-v2 POST-REGENERATION VALIDATION - 30 QUERIES")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

for i, (query, category, expect_cit) in enumerate(ALL_QUERIES, 1):
    print(f"[{i}/30] {category}: {query[:50]}...")
    
    try:
        req_start = time.time()
        resp = requests.post(
            API_ENDPOINT,
            json={"message": query, "session_id": f"val_{int(time.time())}"},
            timeout=TIMEOUT
        )
        latency = (time.time() - req_start) * 1000
        
        if resp.status_code == 200:
            data = resp.json()
            intent = data.get("intent", "unknown")
            citations = data.get("citations", [])
            cit_count = len(citations)
            sources = list(set([c.get("source", "Unknown") for c in citations]))
            tier1 = data.get("tier1_hit", False)
            
            # Determine pass/fail
            if expect_cit:
                passed = 1 <= cit_count <= 3 and latency < 20000
            else:
                passed = cit_count <= 1 and latency < 20000
            
            status = "✅" if passed else "❌"
            print(f"    {status} Intent:{intent} Cit:{cit_count} Lat:{latency:.0f}ms")
            
            results.append({
                "query": query,
                "category": category,
                "intent": intent,
                "citations_count": cit_count,
                "citations_sources": sources,
                "tier1_hit": tier1,
                "latency_ms": round(latency, 1),
                "pass": passed
            })
        else:
            print(f"    ❌ HTTP {resp.status_code}")
            results.append({
                "query": query,
                "category": category,
                "error": f"HTTP {resp.status_code}",
                "pass": False
            })
    
    except Exception as e:
        print(f"    ❌ Error: {str(e)[:50]}")
        results.append({
            "query": query,
            "category": category,
            "error": str(e),
            "pass": False
        })
    
    time.sleep(0.5)  # Small delay between requests

total_time = time.time() - start_time

# Calculate stats
passed = sum(1 for r in results if r.get("pass", False))
pass_rate = (passed / 30) * 100

# Category stats
cat_stats = {}
for cat in ["NZS 3604", "E2/AS1", "NZ Building Code", "NZS 4229", "General Builder", "Practical/Tool"]:
    cat_results = [r for r in results if r.get("category") == cat]
    cat_passed = sum(1 for r in cat_results if r.get("pass", False))
    cat_stats[cat] = {
        "passed": cat_passed,
        "total": len(cat_results),
        "pass_rate": (cat_passed / len(cat_results) * 100) if cat_results else 0
    }

# Print summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total: {passed}/30 ({pass_rate:.1f}%)")
print(f"Time: {total_time:.1f}s")
print()
for cat, stats in cat_stats.items():
    status = "✅" if stats["pass_rate"] >= 80 else "❌"
    print(f"{status} {cat}: {stats['passed']}/{stats['total']} ({stats['pass_rate']:.1f}%)")

# Save results
os.makedirs("/app/tests", exist_ok=True)

# Save JSON
json_data = {
    "test_date": datetime.now().isoformat(),
    "backend_url": BACKEND_URL,
    "total_queries": 30,
    "passed": passed,
    "pass_rate": round(pass_rate, 1),
    "total_time_seconds": round(total_time, 1),
    "category_stats": cat_stats,
    "results": results
}

with open("/app/tests/post_regen_validation_results.json", "w") as f:
    json.dump(json_data, f, indent=2)

print(f"\n✅ Results saved to /app/tests/post_regen_validation_results.json")

# Generate simple markdown report
md = f"""# POST-REGENERATION VALIDATION RESULTS

**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Backend:** {BACKEND_URL}  
**Total Queries:** 30  
**Pass Rate:** {passed}/30 ({pass_rate:.1f}%)  
**Total Time:** {total_time:.1f}s

## Category Breakdown

| Category | Pass Rate | Status |
|----------|-----------|--------|
"""

for cat, stats in cat_stats.items():
    status = "✅ PASS" if stats["pass_rate"] >= 80 else "❌ FAIL"
    md += f"| {cat} | {stats['passed']}/{stats['total']} ({stats['pass_rate']:.1f}%) | {status} |\n"

md += f"""

## Production Readiness

{'✅ **READY** - System meets ≥90% pass rate' if pass_rate >= 90 else '❌ **NOT READY** - System below 90% pass rate'}

## Detailed Results

| # | Query | Category | Intent | Citations | Pass |
|---|-------|----------|--------|-----------|------|
"""

for i, r in enumerate(results, 1):
    status = "✅" if r.get("pass") else "❌"
    md += f"| {i} | {r['query'][:40]}... | {r.get('category', 'N/A')} | {r.get('intent', 'N/A')} | {r.get('citations_count', 0)} | {status} |\n"

with open("/app/tests/POST_REGEN_VALIDATION_REPORT.md", "w") as f:
    f.write(md)

print(f"✅ Report saved to /app/tests/POST_REGEN_VALIDATION_REPORT.md")
print("\n" + "=" * 80)
