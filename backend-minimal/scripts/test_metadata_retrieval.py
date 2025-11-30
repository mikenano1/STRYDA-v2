#!/usr/bin/env python3
"""
Test metadata-aware retrieval with 5 real queries
"""

import requests
import json

test_queries = [
    {"id": "a", "q": "What does E2/AS1 4th edition require for cladding over an 18mm drained cavity in Extra High wind zone?"},
    {"id": "b", "q": "For a building designed under C/AS3 before 2017, what were the fire rating requirements on escape routes?"},
    {"id": "c", "q": "What fall should I use on a longrun roof in Extra High wind according to NZ Metal Roofing / WGANZ?"},
    {"id": "d", "q": "What does H1/AS1 say about R-values for ceilings in climate zone 2?"},
    {"id": "e", "q": "How should I waterproof a tiled shower over timber according to E3/AS1 and the internal wet area code of practice?"}
]

print("="*80)
print("METADATA-AWARE RETRIEVAL TESTING")
print("="*80)

for test in test_queries:
    print(f"\n{'='*80}")
    print(f"Query {test['id'].upper()}: {test['q']}")
    print(f"{'='*80}")
    
    try:
        response = requests.post(
            "http://localhost:8001/api/chat",
            json={"message": test['q'], "session_id": f"meta_test_{test['id']}"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            intent = data.get('intent', 'N/A')
            citations = data.get('citations', [])
            
            print(f"\nDetected Intent: {intent}")
            print(f"Citations: {len(citations)}")
            
            if citations:
                print("\nCitation Sources:")
                for cite in citations[:5]:
                    print(f"  - {cite.get('source')} (p.{cite.get('page')})")
        else:
            print(f"❌ HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

print(f"\n{'='*80}")
print("Check backend logs for [retrieval] debug output with doc_type, priority, scores")
print(f"{'='*80}")
