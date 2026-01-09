#!/usr/bin/env python3
"""
STRYDA RAG Backend Testing - Detailed Final Sweep Verification
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

BACKEND_URL = "https://eng-image-extract.preview.emergentagent.com"

async def test_detailed_final_sweep():
    """Test the Final Sweep queries and capture detailed responses"""
    
    queries = [
        "What is the load capacity of a Pryda bracing anchor?",
        "What SPAX screws should I use for deck framing?", 
        "What masonry anchors does Bremick make?",
        "I'm at Bunnings, what anchors do you recommend?"
    ]
    
    print("🔍 DETAILED FINAL SWEEP VERIFICATION")
    print("="*60)
    
    async with aiohttp.ClientSession() as session:
        for i, query in enumerate(queries, 1):
            print(f"\n🎯 Query {i}: {query}")
            print("-" * 50)
            
            try:
                payload = {"message": query, "session_id": f"test-{int(time.time())}-{i}"}
                
                async with session.post(
                    f"{BACKEND_URL}/api/chat",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract response text
                        response_text = data.get("response", "") or data.get("answer", "")
                        citations = data.get("citations", [])
                        sources = data.get("sources_used", [])
                        
                        print(f"✅ Status: SUCCESS")
                        print(f"📝 Response ({len(response_text)} chars):")
                        print(f"   {response_text}")
                        print(f"📚 Citations: {len(citations)}")
                        print(f"🔗 Sources: {sources}")
                        
                        # Check for brand mentions
                        brands = ["pryda", "spax", "bremick", "zenith", "bunnings"]
                        found_brands = [brand for brand in brands if brand.lower() in response_text.lower()]
                        if found_brands:
                            print(f"🏷️ Brand Mentions: {found_brands}")
                        
                        # Check for Final Sweep indicators
                        if "fasteners full suite" in str(data).lower():
                            print("🎯 FINAL SWEEP SOURCE DETECTED: Fasteners Full Suite")
                        
                    else:
                        print(f"❌ Status: FAILED ({response.status})")
                        error_text = await response.text()
                        print(f"   Error: {error_text}")
                        
            except Exception as e:
                print(f"❌ Status: ERROR")
                print(f"   Exception: {str(e)}")
    
    print("\n" + "="*60)
    print("🏆 FINAL SWEEP VERIFICATION COMPLETE")

if __name__ == "__main__":
    asyncio.run(test_detailed_final_sweep())