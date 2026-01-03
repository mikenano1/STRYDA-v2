#!/usr/bin/env python3
"""
Debug Test - Check actual response structure
"""

import asyncio
import aiohttp
import json

BACKEND_URL = "https://trade-aware-rag.preview.emergentagent.com"

async def debug_response_structure():
    """Debug the actual response structure"""
    
    print("🔍 DEBUGGING RESPONSE STRUCTURE")
    print("=" * 40)
    
    async with aiohttp.ClientSession() as session:
        
        payload = {
            "message": "What is the minimum pitch for corrugated iron?",
            "session_id": "debug-test"
        }
        
        try:
            async with session.post(f"{BACKEND_URL}/api/chat", json=payload) as response:
                print(f"Status Code: {response.status}")
                print(f"Headers: {dict(response.headers)}")
                
                if response.status == 200:
                    data = await response.json()
                    print("\n📄 FULL RESPONSE DATA:")
                    print(json.dumps(data, indent=2))
                    
                    print("\n🔍 RESPONSE FIELD ANALYSIS:")
                    for key, value in data.items():
                        print(f"  {key}: {type(value)} = {str(value)[:100]}...")
                        
                else:
                    text = await response.text()
                    print(f"Error Response: {text}")
                    
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_response_structure())