#!/usr/bin/env python3
"""
Review Request Testing - Gemini Response Quality Verification
Testing specific scenarios mentioned in the review request
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

BACKEND_URL = "https://nzconstructai.preview.emergentagent.com"

async def test_review_request_scenarios():
    """Test the specific scenarios from the review request"""
    
    print("🎯 REVIEW REQUEST TESTING - Gemini Response Quality")
    print("=" * 60)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Time: {datetime.now().isoformat()}")
    print()
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Hybrid/Factual Question (Gemini Flash)
        print("🔍 TEST 1: Hybrid/Factual Question (Gemini Flash)")
        print("Question: What is the minimum pitch for corrugated iron?")
        print("Session ID: test-tokens-flash")
        print("Expected: Detailed answer > 100 characters")
        
        test1_payload = {
            "message": "What is the minimum pitch for corrugated iron?",
            "session_id": "test-tokens-flash"
        }
        
        try:
            async with session.post(f"{BACKEND_URL}/api/chat", json=test1_payload) as response:
                if response.status == 200:
                    data = await response.json()
                    response_text = data.get("response", "")
                    response_length = len(response_text)
                    
                    print(f"✅ Response received: {response_length} characters")
                    print(f"📝 Response: {response_text[:300]}...")
                    
                    if response_length > 100:
                        print(f"✅ TEST 1 PASS: Response length {response_length} > 100 characters")
                        test1_result = "PASS"
                    else:
                        print(f"❌ TEST 1 FAIL: Response too short ({response_length} chars)")
                        test1_result = "FAIL"
                        
                    # Check for specific content about 8-degree minimum
                    if "8" in response_text and ("degree" in response_text.lower() or "pitch" in response_text.lower()):
                        print("✅ Contains expected technical details about minimum pitch")
                    else:
                        print("⚠️  May not contain expected 8-degree minimum information")
                        
                else:
                    print(f"❌ TEST 1 ERROR: HTTP {response.status}")
                    test1_result = "ERROR"
                    
        except Exception as e:
            print(f"❌ TEST 1 ERROR: {e}")
            test1_result = "ERROR"
        
        print()
        
        # Follow-up if needed
        print("🔍 TEST 1b: Follow-up Question")
        print("Question: Corrugate, RU24, lap direction")
        print("Session ID: test-tokens-flash (same session)")
        
        test1b_payload = {
            "message": "Corrugate, RU24, lap direction",
            "session_id": "test-tokens-flash"
        }
        
        try:
            async with session.post(f"{BACKEND_URL}/api/chat", json=test1b_payload) as response:
                if response.status == 200:
                    data = await response.json()
                    response_text = data.get("response", "")
                    response_length = len(response_text)
                    
                    print(f"✅ Follow-up response: {response_length} characters")
                    print(f"📝 Response: {response_text[:300]}...")
                    
                    # Check for 8-degree minimum and conditions
                    if "8" in response_text and ("degree" in response_text.lower()):
                        print("✅ Contains 8-degree minimum information")
                    else:
                        print("⚠️  May not contain specific 8-degree information")
                        
                else:
                    print(f"❌ Follow-up ERROR: HTTP {response.status}")
                    
        except Exception as e:
            print(f"❌ Follow-up ERROR: {e}")
        
        print()
        print("=" * 60)
        
        # Test 2: Strict Compliance Question (Gemini Pro)
        print("🔍 TEST 2: Strict Compliance Question (Gemini Pro)")
        print("Question: What is the stud spacing for a 2.4m wall in high wind zone?")
        print("Session ID: test-tokens-pro")
        print("Expected: Detailed answer > 300 characters with citations")
        
        test2_payload = {
            "message": "What is the stud spacing for a 2.4m wall in high wind zone?",
            "session_id": "test-tokens-pro"
        }
        
        try:
            async with session.post(f"{BACKEND_URL}/api/chat", json=test2_payload) as response:
                if response.status == 200:
                    data = await response.json()
                    response_text = data.get("response", "")
                    citations = data.get("citations", [])
                    response_length = len(response_text)
                    
                    print(f"✅ Response received: {response_length} characters")
                    print(f"📚 Citations provided: {len(citations)}")
                    print(f"📝 Response: {response_text[:400]}...")
                    
                    # Check length requirement
                    if response_length > 300:
                        print(f"✅ Length requirement met: {response_length} > 300 characters")
                        length_check = "PASS"
                    else:
                        print(f"❌ Length requirement failed: {response_length} < 300 characters")
                        length_check = "FAIL"
                    
                    # Check citations requirement
                    if len(citations) > 0:
                        print(f"✅ Citations requirement met: {len(citations)} citations")
                        citations_check = "PASS"
                        for i, citation in enumerate(citations[:3]):  # Show first 3
                            print(f"   Citation {i+1}: {citation.get('title', 'Unknown')}")
                    else:
                        print("❌ Citations requirement failed: No citations provided")
                        citations_check = "FAIL"
                    
                    # Overall test 2 result
                    if length_check == "PASS" and citations_check == "PASS":
                        test2_result = "PASS"
                        print("✅ TEST 2 PASS: Both length and citations requirements met")
                    else:
                        test2_result = "FAIL"
                        print("❌ TEST 2 FAIL: Requirements not fully met")
                        
                    # Check for complete sentences
                    if response_text.endswith('.') or response_text.endswith('!') or response_text.endswith('?'):
                        print("✅ Response appears to complete sentences properly")
                    else:
                        print("⚠️  Response may be truncated (doesn't end with proper punctuation)")
                        
                else:
                    print(f"❌ TEST 2 ERROR: HTTP {response.status}")
                    test2_result = "ERROR"
                    
        except Exception as e:
            print(f"❌ TEST 2 ERROR: {e}")
            test2_result = "ERROR"
        
        print()
        print("=" * 60)
        
        # Summary
        print("📊 REVIEW REQUEST TEST SUMMARY")
        print(f"Test 1 (Hybrid/Factual): {test1_result}")
        print(f"Test 2 (Strict Compliance): {test2_result}")
        
        if test1_result == "PASS" and test2_result == "PASS":
            print("🎉 ALL REVIEW REQUEST TESTS PASSED")
            print("✅ Gemini is producing longer, more complete answers")
            overall_result = "SUCCESS"
        else:
            print("❌ SOME REVIEW REQUEST TESTS FAILED")
            print("⚠️  Gemini response quality issues may still exist")
            overall_result = "ISSUES_FOUND"
        
        return overall_result

if __name__ == "__main__":
    result = asyncio.run(test_review_request_scenarios())
    print(f"\nFinal Result: {result}")