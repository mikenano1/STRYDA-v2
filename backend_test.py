#!/usr/bin/env python3
"""
STRYDA RAG API Bug Fix Testing
Testing specific bug fixes for source context and response completeness
Testing Agent: Backend Testing Agent
Date: 2025-01-04
Focus: Bug Fix 1 (Window Variation Source) & Bug Fix 2 (Deck Height Source & Completeness)
"""

import requests
import json
import time
from typing import Dict, Any, List

# Test Configuration
BACKEND_URL = "https://eng-image-extract.preview.emergentagent.com/api/chat"
SESSION_ID = "test_session_bug_fixes"
USER_ID = "test_user"

def make_chat_request(message: str) -> Dict[str, Any]:
    """Make a chat request to the STRYDA RAG API"""
    payload = {
        "message": message,
        "session_id": SESSION_ID,
        "user_id": USER_ID
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print(f"🔍 Testing query: {message}")
        start_time = time.time()
        
        response = requests.post(BACKEND_URL, json=payload, headers=headers, timeout=30)
        
        response_time = time.time() - start_time
        print(f"⏱️  Response time: {response_time:.2f}s")
        
        if response.status_code == 200:
            response_json = response.json()
            print(f"🔍 Raw response keys: {list(response_json.keys())}")
            return {
                "success": True,
                "data": response_json,
                "response_time": response_time,
                "status_code": response.status_code
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}",
                "response_time": response_time,
                "status_code": response.status_code
            }
            
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Request timeout (30s)",
            "response_time": 30.0,
            "status_code": None
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Request failed: {str(e)}",
            "response_time": 0,
            "status_code": None
        }

def analyze_citations(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze citations in the response"""
    citations = response_data.get("citations", [])
    sources_used = response_data.get("sources_used", [])
    
    # Try different possible response field names
    response_text = (response_data.get("response", "") or 
                    response_data.get("answer", "") or 
                    response_data.get("message", "") or
                    response_data.get("text", ""))
    
    print(f"🔍 Response text extracted: '{response_text[:100]}...' (length: {len(response_text)})")
    
    # Extract source information
    cited_sources = []
    for citation in citations:
        if isinstance(citation, dict):
            source = citation.get("source", "")
            title = citation.get("title", "")
            cited_sources.append({"source": source, "title": title})
    
    # Check for specific problematic sources
    has_metal_roofing = any("metal" in str(source).lower() and "roof" in str(source).lower() 
                           for source in cited_sources + sources_used)
    has_pryda = any("pryda" in str(source).lower() 
                   for source in cited_sources + sources_used)
    has_building_code = any("building" in str(source).lower() and "code" in str(source).lower() 
                           for source in cited_sources + sources_used)
    has_f4_as1 = any("f4" in str(source).lower() and "as1" in str(source).lower() 
                     for source in cited_sources + sources_used)
    
    # Check response content
    response_lower = response_text.lower()
    mentions_metal_roofing = "metal roof" in response_lower or "roofing" in response_lower
    mentions_pryda = "pryda" in response_lower
    mentions_building_consent = "consent" in response_lower or "building consent" in response_lower
    mentions_one_metre = "1 metre" in response_lower or "1m" in response_lower or "one metre" in response_lower
    
    return {
        "total_citations": len(citations),
        "total_sources_used": len(sources_used),
        "cited_sources": cited_sources,
        "sources_used": sources_used,
        "has_metal_roofing_source": has_metal_roofing,
        "has_pryda_source": has_pryda,
        "has_building_code_source": has_building_code,
        "has_f4_as1_source": has_f4_as1,
        "mentions_metal_roofing": mentions_metal_roofing,
        "mentions_pryda": mentions_pryda,
        "mentions_building_consent": mentions_building_consent,
        "mentions_one_metre": mentions_one_metre,
        "response_length": len(response_text),
        "response_complete": not response_text.endswith("...") and len(response_text) > 100
    }

def test_window_variation_bug_fix():
    """Test Bug Fix 1: Wrong Source Context (Window Variation Question)"""
    print("\n" + "="*80)
    print("🔧 BUG FIX 1: Window Variation Source Context Test")
    print("="*80)
    
    query = "Can I change a window layout from my approved plans? Is this a minor variation or amendment?"
    
    result = make_chat_request(query)
    
    if not result["success"]:
        print(f"❌ API Request Failed: {result['error']}")
        return {
            "test_name": "Window Variation Bug Fix",
            "passed": False,
            "error": result["error"],
            "details": {}
        }
    
    response_data = result["data"]
    analysis = analyze_citations(response_data)
    
    print(f"📝 Response Length: {analysis['response_length']} characters")
    print(f"📚 Citations: {analysis['total_citations']}")
    print(f"🔗 Sources Used: {analysis['total_sources_used']}")
    
    # Test criteria
    criteria_passed = []
    criteria_failed = []
    
    # Should cite building-code as authority (NOT nz_metal_roofing)
    if analysis["has_building_code_source"] and not analysis["has_metal_roofing_source"]:
        criteria_passed.append("✅ Cites building-code authority (not metal roofing)")
    else:
        criteria_failed.append("❌ Should cite building-code, not metal roofing sources")
    
    # Should NOT reference "metal roofing" or "Pryda"
    if not analysis["mentions_metal_roofing"] and not analysis["mentions_pryda"]:
        criteria_passed.append("✅ No inappropriate metal roofing/Pryda references")
    else:
        criteria_failed.append("❌ Contains inappropriate metal roofing/Pryda references")
    
    # Answer should be about building consent process
    if analysis["mentions_building_consent"]:
        criteria_passed.append("✅ Discusses building consent process")
    else:
        criteria_failed.append("❌ Should discuss building consent process")
    
    # Response should be complete
    if analysis["response_complete"]:
        criteria_passed.append("✅ Response appears complete")
    else:
        criteria_failed.append("❌ Response appears incomplete or truncated")
    
    print("\n📊 Test Results:")
    for criterion in criteria_passed:
        print(f"  {criterion}")
    for criterion in criteria_failed:
        print(f"  {criterion}")
    
    print(f"\n📄 Response Preview:")
    response_text = (response_data.get("response", "") or 
                    response_data.get("answer", "") or 
                    response_data.get("message", "") or
                    response_data.get("text", ""))
    print(f"  {response_text[:200]}{'...' if len(response_text) > 200 else ''}")
    
    print(f"\n🔍 Sources Analysis:")
    print(f"  Sources Used: {analysis['sources_used']}")
    print(f"  Has Building Code Source: {analysis['has_building_code_source']}")
    print(f"  Has Metal Roofing Source: {analysis['has_metal_roofing_source']}")
    print(f"  Has Pryda Source: {analysis['has_pryda_source']}")
    
    test_passed = len(criteria_failed) == 0
    
    return {
        "test_name": "Window Variation Bug Fix",
        "passed": test_passed,
        "criteria_passed": len(criteria_passed),
        "criteria_failed": len(criteria_failed),
        "details": analysis,
        "response_data": response_data
    }

def test_deck_height_bug_fix():
    """Test Bug Fix 2: Deck Height Question - Correct Source"""
    print("\n" + "="*80)
    print("🔧 BUG FIX 2: Deck Height Source & Completeness Test")
    print("="*80)
    
    query = "What is the maximum height a deck can be without requiring a balustrade?"
    
    result = make_chat_request(query)
    
    if not result["success"]:
        print(f"❌ API Request Failed: {result['error']}")
        return {
            "test_name": "Deck Height Bug Fix",
            "passed": False,
            "error": result["error"],
            "details": {}
        }
    
    response_data = result["data"]
    analysis = analyze_citations(response_data)
    
    print(f"📝 Response Length: {analysis['response_length']} characters")
    print(f"📚 Citations: {analysis['total_citations']}")
    print(f"🔗 Sources Used: {analysis['total_sources_used']}")
    
    # Test criteria
    criteria_passed = []
    criteria_failed = []
    
    # Should cite F4-AS1 (Safety from Falling) as authority
    if analysis["has_f4_as1_source"]:
        criteria_passed.append("✅ Cites F4-AS1 (Safety from Falling) authority")
    else:
        criteria_failed.append("❌ Should cite F4-AS1 (Safety from Falling) as authority")
    
    # Should mention "1 metre" as height threshold
    if analysis["mentions_one_metre"]:
        criteria_passed.append("✅ Mentions 1 metre height threshold")
    else:
        criteria_failed.append("❌ Should mention 1 metre height threshold")
    
    # Response should NOT be cut off mid-sentence (max_tokens increased)
    if analysis["response_complete"] and analysis["response_length"] > 150:
        criteria_passed.append("✅ Response is complete and substantial")
    else:
        criteria_failed.append("❌ Response appears incomplete or too short")
    
    print("\n📊 Test Results:")
    for criterion in criteria_passed:
        print(f"  {criterion}")
    for criterion in criteria_failed:
        print(f"  {criterion}")
    
    print(f"\n📄 Response Preview:")
    response_text = (response_data.get("response", "") or 
                    response_data.get("answer", "") or 
                    response_data.get("message", "") or
                    response_data.get("text", ""))
    print(f"  {response_text[:300]}{'...' if len(response_text) > 300 else ''}")
    
    print(f"\n🔍 Sources Analysis:")
    print(f"  Sources Used: {analysis['sources_used']}")
    print(f"  Has F4-AS1 Source: {analysis['has_f4_as1_source']}")
    print(f"  Mentions 1 Metre: {analysis['mentions_one_metre']}")
    print(f"  Response Length: {analysis['response_length']} chars")
    
    test_passed = len(criteria_failed) == 0
    
    return {
        "test_name": "Deck Height Bug Fix",
        "passed": test_passed,
        "criteria_passed": len(criteria_passed),
        "criteria_failed": len(criteria_failed),
        "details": analysis,
        "response_data": response_data
    }

def run_bug_fix_tests():
    """Run all bug fix tests"""
    print("🚀 STRYDA RAG API Bug Fix Testing")
    print("="*80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Session ID: {SESSION_ID}")
    print(f"User ID: {USER_ID}")
    
    # Run tests
    test_results = []
    
    # Test 1: Window Variation Bug Fix
    test1_result = test_window_variation_bug_fix()
    test_results.append(test1_result)
    
    # Wait between tests
    time.sleep(2)
    
    # Test 2: Deck Height Bug Fix
    test2_result = test_deck_height_bug_fix()
    test_results.append(test2_result)
    
    # Summary
    print("\n" + "="*80)
    print("📊 BUG FIX TESTING SUMMARY")
    print("="*80)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results if result.get("passed", False))
    failed_tests = total_tests - passed_tests
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\n📋 Individual Test Results:")
    for i, result in enumerate(test_results, 1):
        status = "✅ PASS" if result.get("passed", False) else "❌ FAIL"
        test_name = result.get("test_name", f"Test {i}")
        print(f"  {i}. {test_name}: {status}")
        
        if "error" in result:
            print(f"     Error: {result['error']}")
        elif not result.get("passed", False):
            criteria_failed = result.get("criteria_failed", 0)
            print(f"     Failed Criteria: {criteria_failed}")
    
    # Overall verdict
    print(f"\n🎯 OVERALL VERDICT:")
    if passed_tests == total_tests:
        print("✅ ALL BUG FIXES WORKING CORRECTLY")
    elif passed_tests > 0:
        print("⚠️  PARTIAL SUCCESS - Some bug fixes working")
    else:
        print("❌ BUG FIXES NOT WORKING - All tests failed")
    
    return {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": failed_tests,
        "success_rate": (passed_tests/total_tests)*100,
        "test_results": test_results
    }

if __name__ == "__main__":
    results = run_bug_fix_tests()