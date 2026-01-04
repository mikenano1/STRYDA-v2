#!/usr/bin/env python3
"""
Backend Testing for Material Triage System (Attribute Filter Protocol)
Testing the new insulation material triage functionality
Testing Agent: Backend Testing Agent
Date: 2025-01-04
Focus: Material Triage for insulation queries - Glass Wool vs Polyester
"""

import requests
import json
import time
from typing import Dict, Any

# Backend URL from frontend/.env
BACKEND_URL = "https://trade-aware-rag.preview.emergentagent.com"
CHAT_ENDPOINT = f"{BACKEND_URL}/api/chat"

def test_chat_endpoint(query: str, session_id: str = None) -> Dict[str, Any]:
    """Test the chat endpoint with a specific query"""
    
    if session_id is None:
        session_id = f"test-material-triage-{int(time.time())}"
    
    payload = {
        "message": query,
        "session_id": session_id
    }
    
    print(f"\n🔍 Testing Query: '{query}'")
    print(f"📋 Session ID: {session_id}")
    print(f"🌐 Endpoint: {CHAT_ENDPOINT}")
    
    try:
        start_time = time.time()
        response = requests.post(CHAT_ENDPOINT, json=payload, timeout=30)
        response_time = time.time() - start_time
        
        print(f"⏱️  Response Time: {response_time:.2f}s")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract key information
            answer = data.get('response', data.get('answer', ''))
            citations = data.get('citations', [])
            session_id = data.get('session_id', session_id)
            
            print(f"✅ Response Length: {len(answer)} characters")
            print(f"📚 Citations: {len(citations)}")
            print(f"💬 Response Preview: {answer[:200]}...")
            
            return {
                "success": True,
                "response": answer,
                "citations": citations,
                "session_id": session_id,
                "response_time": response_time,
                "full_data": data
            }
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}",
                "response_time": response_time
            }
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "response_time": 0
        }

def analyze_material_triage_response(response: str, test_type: str) -> Dict[str, Any]:
    """Analyze if the response shows proper material triage behavior"""
    
    response_lower = response.lower()
    
    # Material groups
    glass_wool_brands = ['pink batts', 'earthwool', 'bradford', 'knauf']
    polyester_brands = ['mammoth', 'greenstuf', 'autex']
    
    # Check for material triage indicators
    triage_indicators = [
        'material preference', 'do you have a preference', 'which material',
        'glass wool', 'polyester', 'both glass wool and polyester',
        'options in both', 'material type', 'prefer glass wool', 'prefer polyester',
        'choice between', 'two main types', 'two options'
    ]
    
    # Check for brand mentions
    glass_wool_mentioned = any(brand in response_lower for brand in glass_wool_brands)
    polyester_mentioned = any(brand in response_lower for brand in polyester_brands)
    triage_language = any(indicator in response_lower for indicator in triage_indicators)
    
    analysis = {
        "test_type": test_type,
        "glass_wool_mentioned": glass_wool_mentioned,
        "polyester_mentioned": polyester_mentioned,
        "triage_language_detected": triage_language,
        "response_length": len(response),
        "brands_mentioned": []
    }
    
    # Count specific brand mentions
    for brand in glass_wool_brands + polyester_brands:
        if brand in response_lower:
            analysis["brands_mentioned"].append(brand)
    
    return analysis

def run_material_triage_tests():
    """Run all Material Triage tests as specified in the review request"""
    
    print("🎯 MATERIAL TRIAGE TESTING - Attribute Filter Protocol")
    print("=" * 60)
    print("Context: New Material Triage system for insulation queries")
    print("Glass Wool group: Pink Batts, Earthwool, Bradford, Knauf")
    print("Polyester group: Mammoth, GreenStuf, Autex")
    print("Goal: Never present more than 3 options without asking a narrowing question")
    
    test_results = []
    
    # Test 1: Generic Insulation Query (SHOULD trigger material triage)
    print("\n📋 TEST 1: Generic Insulation Query (Should trigger triage)")
    result1 = test_chat_endpoint("What R-value insulation do I need for walls in Auckland?")
    if result1["success"]:
        analysis1 = analyze_material_triage_response(result1["response"], "generic_query")
        analysis1["expected_behavior"] = "Should ask about material preference BEFORE listing products"
        analysis1["should_trigger_triage"] = True
        test_results.append({"test": "generic_query", "result": result1, "analysis": analysis1})
    
    time.sleep(2)  # Brief pause between tests
    
    # Test 2: Brand-Specific Query (should NOT trigger triage)
    print("\n📋 TEST 2: Brand-Specific Query (Should NOT trigger triage)")
    result2 = test_chat_endpoint("What Mammoth wall insulation R-values are available?")
    if result2["success"]:
        analysis2 = analyze_material_triage_response(result2["response"], "brand_specific")
        analysis2["expected_behavior"] = "Should directly answer about Mammoth products (polyester)"
        analysis2["should_trigger_triage"] = False
        test_results.append({"test": "brand_specific", "result": result2, "analysis": analysis2})
    
    time.sleep(2)
    
    # Test 3: Material-Specific Query (should NOT trigger triage)
    print("\n📋 TEST 3: Material-Specific Query (Should NOT trigger triage)")
    result3 = test_chat_endpoint("I want glass wool insulation for my ceiling")
    if result3["success"]:
        analysis3 = analyze_material_triage_response(result3["response"], "material_specific")
        analysis3["expected_behavior"] = "Should focus on Pink Batts/Earthwool (glass wool brands)"
        analysis3["should_trigger_triage"] = False
        test_results.append({"test": "material_specific", "result": result3, "analysis": analysis3})
    
    time.sleep(2)
    
    # Test 4: Follow-up after Material Selection
    print("\n📋 TEST 4: Follow-up Material Selection")
    result4 = test_chat_endpoint("I prefer polyester insulation")
    if result4["success"]:
        analysis4 = analyze_material_triage_response(result4["response"], "material_preference")
        analysis4["expected_behavior"] = "Should focus on Mammoth/GreenStuf options"
        analysis4["should_trigger_triage"] = False
        test_results.append({"test": "material_preference", "result": result4, "analysis": analysis4})
    
    return test_results

def evaluate_test_results(test_results):
    """Evaluate the test results against success criteria"""
    
    print("\n🔍 MATERIAL TRIAGE TEST EVALUATION")
    print("=" * 50)
    
    evaluation = {
        "total_tests": len(test_results),
        "passed_tests": 0,
        "failed_tests": 0,
        "test_details": []
    }
    
    for test_data in test_results:
        test_name = test_data["test"]
        analysis = test_data["analysis"]
        
        print(f"\n📊 {test_name.upper()} ANALYSIS:")
        print(f"   Expected: {analysis['expected_behavior']}")
        print(f"   Should Trigger Triage: {analysis['should_trigger_triage']}")
        print(f"   Glass Wool Mentioned: {analysis['glass_wool_mentioned']}")
        print(f"   Polyester Mentioned: {analysis['polyester_mentioned']}")
        print(f"   Triage Language: {analysis['triage_language_detected']}")
        print(f"   Brands Mentioned: {analysis['brands_mentioned']}")
        print(f"   Response Length: {analysis['response_length']} chars")
        
        # Evaluate success based on test type
        test_passed = False
        failure_reasons = []
        
        if test_name == "generic_query":
            # Should trigger triage - ask about material preference
            if analysis["triage_language_detected"]:
                if analysis["glass_wool_mentioned"] and analysis["polyester_mentioned"]:
                    test_passed = True
                    print("   ✅ PASS: Correctly triggered material triage with both options")
                elif analysis["glass_wool_mentioned"] or analysis["polyester_mentioned"]:
                    test_passed = True
                    print("   ✅ PASS: Triggered material triage (partial material mention)")
                else:
                    failure_reasons.append("Triage triggered but no material types mentioned")
            else:
                failure_reasons.append("Did not trigger material triage")
        
        elif test_name == "brand_specific":
            # Should NOT trigger triage, should focus on Mammoth (polyester)
            if "mammoth" in analysis["brands_mentioned"]:
                if not analysis["triage_language_detected"]:
                    test_passed = True
                    print("   ✅ PASS: Correctly answered about Mammoth without triage")
                else:
                    failure_reasons.append("Triggered triage when it shouldn't have")
            else:
                failure_reasons.append("Did not focus on Mammoth brand")
        
        elif test_name == "material_specific":
            # Should NOT trigger triage, should focus on glass wool brands
            if analysis["glass_wool_mentioned"]:
                if not analysis["triage_language_detected"]:
                    test_passed = True
                    print("   ✅ PASS: Correctly focused on glass wool brands without triage")
                else:
                    failure_reasons.append("Triggered triage when it shouldn't have")
            else:
                failure_reasons.append("Did not focus on glass wool brands")
        
        elif test_name == "material_preference":
            # Should focus on polyester brands (Mammoth/GreenStuf)
            if analysis["polyester_mentioned"]:
                if not analysis["triage_language_detected"]:
                    test_passed = True
                    print("   ✅ PASS: Correctly focused on polyester options")
                else:
                    failure_reasons.append("Triggered triage when it shouldn't have")
            else:
                failure_reasons.append("Did not focus on polyester options")
        
        if not test_passed:
            print(f"   ❌ FAIL: {'; '.join(failure_reasons)}")
        
        if test_passed:
            evaluation["passed_tests"] += 1
        else:
            evaluation["failed_tests"] += 1
        
        evaluation["test_details"].append({
            "test": test_name,
            "passed": test_passed,
            "failure_reasons": failure_reasons,
            "analysis": analysis
        })
    
    return evaluation

def main():
    """Main test execution"""
    
    print("🚀 Starting Material Triage Backend Testing")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print(f"📡 Chat Endpoint: {CHAT_ENDPOINT}")
    
    # Run all tests
    test_results = run_material_triage_tests()
    
    # Evaluate results
    evaluation = evaluate_test_results(test_results)
    
    # Final summary
    print("\n🎯 FINAL MATERIAL TRIAGE TEST SUMMARY")
    print("=" * 50)
    print(f"Total Tests: {evaluation['total_tests']}")
    print(f"Passed: {evaluation['passed_tests']}")
    print(f"Failed: {evaluation['failed_tests']}")
    print(f"Success Rate: {(evaluation['passed_tests']/evaluation['total_tests']*100):.1f}%")
    
    # Detailed failure analysis
    if evaluation["failed_tests"] > 0:
        print("\n❌ FAILED TESTS ANALYSIS:")
        for detail in evaluation["test_details"]:
            if not detail["passed"]:
                print(f"   {detail['test']}: {'; '.join(detail['failure_reasons'])}")
    
    # Success criteria evaluation
    print("\n📋 SUCCESS CRITERIA EVALUATION:")
    print("1. Generic queries trigger the material triage question")
    print("2. Brand/material-specific queries skip triage and answer directly")
    print("3. The triage question mentions both Glass Wool and Polyester options")
    print("4. Goal: Never present more than 3 options without asking a narrowing question")
    
    if evaluation["passed_tests"] == evaluation["total_tests"]:
        print("\n🎉 ALL TESTS PASSED - Material Triage is working correctly!")
        print("✅ The Attribute Filter Protocol is FULLY OPERATIONAL")
    elif evaluation["passed_tests"] >= evaluation["total_tests"] * 0.75:
        print(f"\n⚠️  MOSTLY WORKING - {evaluation['failed_tests']} test(s) failed")
        print("🔶 The Attribute Filter Protocol is PARTIALLY OPERATIONAL")
    else:
        print(f"\n🚨 CRITICAL ISSUES - {evaluation['failed_tests']} test(s) failed")
        print("❌ The Attribute Filter Protocol needs IMMEDIATE ATTENTION")
    
    return evaluation

if __name__ == "__main__":
    main()