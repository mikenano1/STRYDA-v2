#!/usr/bin/env python3
"""Quick validation test - 6 queries (1 per category)"""

import requests
import json
import time

BACKEND_URL = "https://techscraper.preview.emergentagent.com"
API_ENDPOINT = f"{BACKEND_URL}/api/chat"

# One query per category
TEST_QUERIES = [
    ("nzs 3604 stud spacing requirements", "NZS 3604", True),
    ("e2as1 minimum apron flashing cover", "E2/AS1", True),
    ("minimum barrier height f4 requirements", "NZ Building Code", True),
    ("nzs 4229 minimum reinforcing for concrete masonry", "NZS 4229", True),
    ("how far can 140x45 joists span", "General Builder", False),
    ("whats the best laser level for framing", "Practical/Tool", False),
]

print("Quick Validation Test - 6 queries")
print("=" * 80)

for query, category, expect_citations in TEST_QUERIES:
    print(f"\nTesting: {query}")
    print(f"Category: {category}")
    
    start = time.time()
    try:
        response = requests.post(
            API_ENDPOINT,
            json={"message": query, "session_id": f"test_{int(time.time())}"},
            timeout=30
        )
        latency = (time.time() - start) * 1000
        
        if response.status_code == 200:
            data = response.json()
            citations = data.get("citation", [])
            intent = data.get("intent", "unknown")
            
            print(f"✅ Status: 200 OK")
            print(f"   Intent: {intent}")
            print(f"   Citations: {len(citations)}")
            if citations:
                sources = [c.get("source", "Unknown") for c in citations]
                print(f"   Sources: {', '.join(set(sources))}")
            print(f"   Latency: {latency:.0f}ms")
            
            # Check if result matches expectation
            if expect_citations and len(citations) > 0:
                print(f"   ✅ PASS - Citations provided as expected")
            elif not expect_citations and len(citations) <= 1:
                print(f"   ✅ PASS - No/minimal citations as expected")
            else:
                print(f"   ❌ FAIL - Citation count mismatch")
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"   Error: {response.text[:200]}")
    
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    time.sleep(1)

print("\n" + "=" * 80)
print("Quick test complete!")
