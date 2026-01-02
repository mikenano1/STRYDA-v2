#!/usr/bin/env python3
"""
Test the enhanced chat endpoint directly to see if citations work there
"""

import requests
import json

BACKEND_URL = "https://gemini-stryda.preview.emergentagent.com"

def test_enhanced_chat_endpoint():
    """Test the enhanced chat endpoint directly"""
    
    print("🔍 Testing Enhanced Chat Endpoint Directly")
    print("=" * 50)
    
    test_data = {
        "message": "What is the stud spacing for a 2.4m wall in high wind zone?",
        "session_id": "test-enhanced-direct",
        "enable_compliance_analysis": True,
        "enable_query_processing": True
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/chat/enhanced",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"Response: {data.get('response', '')}")
            print(f"Citations Count: {len(data.get('citations', []))}")
            print(f"Session ID: {data.get('session_id', 'N/A')}")
            print(f"Confidence Score: {data.get('confidence_score', 'N/A')}")
            print(f"Sources Used: {data.get('sources_used', [])}")
            print(f"Processing Time: {data.get('processing_time_ms', 'N/A')}ms")
            
            citations = data.get("citations", [])
            if citations:
                print("\n📚 Citations found:")
                for i, citation in enumerate(citations, 1):
                    print(f"  {i}. {citation}")
            else:
                print("\n❌ No citations in enhanced endpoint either")
                
            return len(citations) > 0
                
        else:
            print(f"❌ Failed: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_health_and_admin():
    """Test health and admin endpoints to verify basic connectivity"""
    
    print("\n🔍 Testing Basic Endpoints")
    print("=" * 30)
    
    # Test health
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        print(f"Health: {response.status_code} - {response.text if response.status_code != 200 else 'OK'}")
    except Exception as e:
        print(f"Health Error: {e}")
    
    # Test admin config
    try:
        response = requests.get(f"{BACKEND_URL}/admin/config", timeout=10)
        print(f"Admin Config: {response.status_code} - {response.text if response.status_code != 200 else 'OK'}")
    except Exception as e:
        print(f"Admin Config Error: {e}")

if __name__ == "__main__":
    test_health_and_admin()
    test_enhanced_chat_endpoint()