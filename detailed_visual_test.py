#!/usr/bin/env python3
"""
Detailed Visual Content Testing - Verify exact structure and content
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

BACKEND_URL = os.getenv('EXPO_PUBLIC_BACKEND_URL', 'https://builder-assistant.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def test_specific_queries():
    """Test the specific queries mentioned in the review request"""
    session = requests.Session()
    
    test_queries = [
        "What clearances do I need for a fireplace hearth?",
        "Show me insulation R-values for Auckland", 
        "Weathertightness requirements for window installation",
        "Timber framing connection details",
        "Foundation requirements"
    ]
    
    print("🔍 DETAILED VISUAL CONTENT ANALYSIS")
    print("=" * 60)
    
    for i, query in enumerate(test_queries):
        print(f"\n📋 Query {i+1}: {query}")
        
        chat_data = {
            "message": query,
            "enable_compliance_analysis": True,
            "enable_query_processing": True
        }
        
        try:
            response = session.post(f"{API_BASE}/chat/enhanced", json=chat_data)
            
            if response.status_code == 200:
                result = response.json()
                visual_content = result.get('visual_content', [])
                
                print(f"✅ Status: SUCCESS")
                print(f"📊 Visual Content Count: {len(visual_content)}")
                print(f"⏱️  Processing Time: {result.get('processing_time_ms', 0):.1f}ms")
                
                for j, visual in enumerate(visual_content):
                    print(f"\n   📋 Visual {j+1}:")
                    print(f"      🆔 ID: {visual.get('id', 'N/A')}")
                    print(f"      📝 Title: {visual.get('title', 'N/A')}")
                    print(f"      📄 Description: {visual.get('description', 'N/A')[:100]}...")
                    print(f"      🏷️  Content Type: {visual.get('content_type', 'N/A')}")
                    print(f"      📚 Source Document: {visual.get('source_document', 'N/A')}")
                    print(f"      🔑 Keywords: {visual.get('keywords', [])}")
                    print(f"      📋 NZ Building Codes: {visual.get('nz_building_codes', [])}")
                    print(f"      🏗️  Trade Categories: {visual.get('trade_categories', [])}")
                    
                    text_diagram = visual.get('text_diagram', '')
                    if text_diagram:
                        print(f"      📐 Text Diagram: {len(str(text_diagram))} characters")
                        print(f"         Preview: {str(text_diagram)[:150]}...")
                    else:
                        print(f"      📐 Text Diagram: None")
                
                # Check response structure
                print(f"\n   📊 Response Structure:")
                print(f"      Response Length: {len(result.get('response', ''))} characters")
                print(f"      Citations: {len(result.get('citations', []))}")
                print(f"      Confidence Score: {result.get('confidence_score', 0)}")
                print(f"      Sources Used: {result.get('sources_used', [])}")
                
            else:
                print(f"❌ Status: FAILED - HTTP {response.status_code}")
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Status: ERROR - {str(e)}")
        
        print("-" * 60)

if __name__ == "__main__":
    test_specific_queries()