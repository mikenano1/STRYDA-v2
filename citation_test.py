#!/usr/bin/env python3
"""
Additional testing to understand citation system behavior
"""

import requests
import json

BACKEND_URL = "https://rag-scraper.preview.emergentagent.com"

def test_citation_scenarios():
    """Test various scenarios to understand when citations are provided"""
    
    test_cases = [
        {
            "name": "Building Code Question",
            "message": "What are the requirements for bathroom waterproofing?",
            "session_id": "test-citations-1"
        },
        {
            "name": "NZS 3604 Question", 
            "message": "What is the maximum span for 90x45 H1.2 timber framing?",
            "session_id": "test-citations-2"
        },
        {
            "name": "Fire Safety Question",
            "message": "What are the fire clearance requirements for a wood burner?",
            "session_id": "test-citations-3"
        },
        {
            "name": "Structural Question (Original)",
            "message": "What is the stud spacing for a 2.4m wall in high wind zone?",
            "session_id": "test-citations-4"
        }
    ]
    
    print("🔍 Testing Citation System Behavior")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"Question: {test_case['message']}")
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/chat",
                json=test_case,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "")
                citations = data.get("citations", [])
                intent = data.get("intent", "")
                model = data.get("model", "")
                
                print(f"Status: ✅ Success")
                print(f"Intent: {intent}")
                print(f"Model: {model}")
                print(f"Citations: {len(citations)} found")
                print(f"Answer Length: {len(answer)} chars")
                print(f"Answer Preview: {answer[:100]}...")
                
                if citations:
                    print("📚 Citations found:")
                    for j, citation in enumerate(citations[:2], 1):
                        print(f"  {j}. {citation.get('title', 'Unknown')}")
                else:
                    print("❌ No citations provided")
                    
            else:
                print(f"❌ Failed: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 40)

if __name__ == "__main__":
    test_citation_scenarios()