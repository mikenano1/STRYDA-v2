#!/usr/bin/env python3
"""
Final comprehensive test for review request
"""

import asyncio
import aiohttp
import json

BACKEND_URL = "https://integrity-hub-5.preview.emergentagent.com"

async def final_comprehensive_test():
    """Run comprehensive test to confirm issues"""
    
    print("🔍 FINAL COMPREHENSIVE TEST")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        
        # Test multiple scenarios to confirm pattern
        test_cases = [
            {
                "name": "Corrugated Iron Pitch (Review Request Test 1)",
                "message": "What is the minimum pitch for corrugated iron?",
                "session_id": "test-tokens-flash",
                "expected_length": 100
            },
            {
                "name": "Stud Spacing (Review Request Test 2)", 
                "message": "What is the stud spacing for a 2.4m wall in high wind zone?",
                "session_id": "test-tokens-pro",
                "expected_length": 300
            },
            {
                "name": "General Building Question",
                "message": "What are the requirements for bathroom waterproofing?",
                "session_id": "test-general",
                "expected_length": 200
            }
        ]
        
        results = []
        
        for test_case in test_cases:
            print(f"\n🧪 Testing: {test_case['name']}")
            
            payload = {
                "message": test_case["message"],
                "session_id": test_case["session_id"]
            }
            
            try:
                async with session.post(f"{BACKEND_URL}/api/chat", json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        answer = data.get("answer", "")
                        length = len(answer)
                        intent = data.get("intent", "")
                        model = data.get("model", "")
                        citations = data.get("citations", [])
                        
                        print(f"  📏 Length: {length} chars (expected: >{test_case['expected_length']})")
                        print(f"  🎯 Intent: {intent}")
                        print(f"  🤖 Model: {model}")
                        print(f"  📚 Citations: {len(citations)}")
                        print(f"  📝 Preview: {answer[:150]}...")
                        
                        # Check if response is truncated
                        is_truncated = length < test_case['expected_length']
                        ends_properly = answer.endswith('.') or answer.endswith('!') or answer.endswith('?')
                        
                        result = {
                            "test_name": test_case['name'],
                            "length": length,
                            "expected_length": test_case['expected_length'],
                            "is_truncated": is_truncated,
                            "ends_properly": ends_properly,
                            "intent": intent,
                            "model": model,
                            "citations_count": len(citations),
                            "answer": answer
                        }
                        
                        if is_truncated:
                            print(f"  ❌ TRUNCATED: {length} < {test_case['expected_length']}")
                        else:
                            print(f"  ✅ LENGTH OK: {length} >= {test_case['expected_length']}")
                            
                        if not ends_properly and length > 50:
                            print(f"  ⚠️  May be cut off (doesn't end with punctuation)")
                            
                        results.append(result)
                        
                    else:
                        print(f"  ❌ HTTP Error: {response.status}")
                        
            except Exception as e:
                print(f"  ❌ Error: {e}")
        
        # Summary
        print("\n📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 40)
        
        truncated_count = len([r for r in results if r['is_truncated']])
        total_tests = len(results)
        
        print(f"Total tests: {total_tests}")
        print(f"Truncated responses: {truncated_count}")
        print(f"Citation issues: {len([r for r in results if r['citations_count'] == 0])}")
        
        if truncated_count > 0:
            print(f"\n❌ GEMINI TRUNCATION ISSUE CONFIRMED")
            print(f"   {truncated_count}/{total_tests} responses are shorter than expected")
            print(f"   This matches the issue reported in test_result.md")
        else:
            print(f"\n✅ NO TRUNCATION ISSUES FOUND")
            
        return results

if __name__ == "__main__":
    asyncio.run(final_comprehensive_test())