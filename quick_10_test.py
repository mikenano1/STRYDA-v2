#!/usr/bin/env python3
"""Quick 10-query test - 2 from each category"""

import requests
import json
import time
from datetime import datetime

BACKEND_URL = "https://nzconstructai.preview.emergentagent.com"
API_ENDPOINT = f"{BACKEND_URL}/api/chat"

# 2 queries per category (10 total)
QUERIES = [
    ("nzs 3604 stud spacing requirements", "NZS 3604", True),
    ("nzs 3604 rafter span 4.2m", "NZS 3604", True),
    ("e2as1 minimum apron flashing cover", "E2/AS1", True),
    ("e2as1 roof pitch requirements", "E2/AS1", True),
    ("minimum barrier height f4 requirements", "NZ Building Code", True),
    ("b1 as1 footing depth for standard residential", "NZ Building Code", True),
    ("nzs 4229 minimum reinforcing for concrete masonry", "NZS 4229", True),
    ("nzs 4229 lintel reinforcement schedule", "NZS 4229", True),
    ("how far can 140x45 joists span", "General Builder", False),
    ("whats the best laser level for framing", "Practical/Tool", False),
]

results = []
print("Quick 10-Query Validation Test")
print("=" * 80)

for i, (query, category, expect_cit) in enumerate(QUERIES, 1):
    print(f"\n[{i}/10] {category}: {query}")
    
    try:
        start = time.time()
        resp = requests.post(
            API_ENDPOINT,
            json={"message": query, "session_id": f"quick_{int(time.time())}"},
            timeout=30
        )
        latency = (time.time() - start) * 1000
        
        if resp.status_code == 200:
            data = resp.json()
            intent = data.get("intent", "unknown")
            citations = data.get("citations", [])
            cit_count = len(citations)
            sources = list(set([c.get("source", "Unknown") for c in citations]))
            
            # Check pass/fail
            if expect_cit:
                passed = 1 <= cit_count <= 3 and latency < 20000
            else:
                passed = cit_count <= 1 and latency < 20000
            
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {status}")
            print(f"   Intent: {intent}")
            print(f"   Citations: {cit_count}")
            if sources:
                print(f"   Sources: {', '.join(sources)}")
            print(f"   Latency: {latency:.0f}ms")
            
            results.append({
                "query": query,
                "category": category,
                "intent": intent,
                "citations_count": cit_count,
                "citations_sources": sources,
                "latency_ms": round(latency, 1),
                "pass": passed
            })
        else:
            print(f"   ❌ FAIL - HTTP {resp.status_code}")
            results.append({"query": query, "category": category, "error": f"HTTP {resp.status_code}", "pass": False})
    
    except Exception as e:
        print(f"   ❌ FAIL - {str(e)[:50]}")
        results.append({"query": query, "category": category, "error": str(e), "pass": False})
    
    time.sleep(0.5)

# Summary
passed = sum(1 for r in results if r.get("pass", False))
print("\n" + "=" * 80)
print(f"SUMMARY: {passed}/10 PASS ({(passed/10)*100:.1f}%)")
print("=" * 80)

# Save results
import os
os.makedirs("/app/tests", exist_ok=True)
with open("/app/tests/quick_10_results.json", "w") as f:
    json.dump({"results": results, "passed": passed, "total": 10}, f, indent=2)

print("\n✅ Results saved to /app/tests/quick_10_results.json")
