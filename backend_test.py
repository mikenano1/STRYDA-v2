#!/usr/bin/env python3
"""
STRYDA RAG Backend Testing - Pink Batts Insulation Retrieval
Testing Agent: Backend Testing Agent
Date: 2025-01-04
Focus: Pink Batts trade-aware insulation retrieval with 1,320 documentation chunks
"""

import asyncio
import aiohttp
import json
import time
import sys
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://trade-aware-rag.preview.emergentagent.com"

class PinkBattsRAGTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.test_results = []
        self.session = None
        
    async def setup_session(self):
        """Setup HTTP session for testing"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    async def test_chat_endpoint(self, query: str, test_name: str, expected_keywords: list, expected_trade: str = None):
        """Test chat endpoint with Pink Batts specific expectations"""
        print(f"\n🧪 Testing: {test_name}")
        print(f"Query: {query}")
        print(f"Expected Keywords: {expected_keywords}")
        if expected_trade:
            print(f"Expected Trade: {expected_trade}")
        
        start_time = time.time()
        
        try:
            # Make request to chat endpoint
            payload = {
                "message": query,
                "session_id": f"pink-batts-test-{int(time.time())}"
            }
            
            async with self.session.post(
                f"{self.backend_url}/api/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                response_time = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract response details
                    ai_response = data.get("answer", data.get("response", ""))
                    citations = data.get("citations", [])
                    sources_used = data.get("sources_used", [])
                    intent = data.get("intent", "")
                    model = data.get("model", "")
                    
                    # Check for Pink Batts mentions
                    pink_batts_mentioned = any(term.lower() in ai_response.lower() 
                                             for term in ["pink batts", "pink batt", "pinkbatts"])
                    
                    # Check for Pink Batts Deep Dive source
                    deep_dive_source = any("pink batts deep dive" in str(source).lower() 
                                         for source in sources_used)
                    
                    # Check for expected keywords
                    keywords_found = [kw for kw in expected_keywords 
                                    if kw.lower() in ai_response.lower()]
                    
                    # Check for R-values (important for insulation)
                    r_values_found = []
                    r_value_patterns = ["r-value", "r value", "r2.", "r3.", "r4.", "r5.", "r6."]
                    for pattern in r_value_patterns:
                        if pattern in ai_response.lower():
                            r_values_found.append(pattern)
                    
                    # Check for trade detection
                    trade_detected = expected_trade and expected_trade in str(data).lower() if expected_trade else None
                    
                    # Analyze response quality
                    response_length = len(ai_response)
                    
                    # Determine test status
                    status = "PASS"
                    if not pink_batts_mentioned:
                        status = "FAIL"
                    elif len(keywords_found) < 2:
                        status = "PARTIAL"
                    elif response_length < 100:
                        status = "PARTIAL"
                    
                    result = {
                        "test_name": test_name,
                        "query": query,
                        "status": status,
                        "response_time_ms": round(response_time, 1),
                        "response_length": response_length,
                        "pink_batts_mentioned": pink_batts_mentioned,
                        "deep_dive_source": deep_dive_source,
                        "keywords_found": keywords_found,
                        "expected_keywords": expected_keywords,
                        "r_values_found": r_values_found,
                        "trade_detected": trade_detected,
                        "sources_used": sources_used,
                        "citations_count": len(citations),
                        "intent": intent,
                        "model": model,
                        "ai_response": ai_response[:300] + "..." if len(ai_response) > 300 else ai_response,
                        "full_response": ai_response
                    }
                    
                    print(f"✅ Status: {result['status']}")
                    print(f"⏱️  Response Time: {response_time:.1f}ms")
                    print(f"📝 Response Length: {response_length} chars")
                    print(f"🏷️  Pink Batts Mentioned: {pink_batts_mentioned}")
                    print(f"📚 Deep Dive Source: {deep_dive_source}")
                    print(f"🔧 Keywords Found: {len(keywords_found)}/{len(expected_keywords)} ({keywords_found})")
                    print(f"📊 R-values Found: {r_values_found}")
                    print(f"🎯 Intent: {intent}")
                    print(f"🤖 Model: {model}")
                    print(f"📖 Citations: {len(citations)}")
                    
                    if result['status'] in ["FAIL", "PARTIAL"]:
                        print(f"⚠️  ISSUES:")
                        if not pink_batts_mentioned:
                            print(f"   - Pink Batts brand not mentioned in response")
                        if len(keywords_found) < 2:
                            print(f"   - Insufficient relevant keywords ({len(keywords_found)}/{len(expected_keywords)})")
                        if response_length < 100:
                            print(f"   - Response too short ({response_length} chars)")
                        if not deep_dive_source:
                            print(f"   - Pink Batts Deep Dive source not detected")
                    
                    self.test_results.append(result)
                    return result
                    
                else:
                    error_text = await response.text()
                    print(f"❌ HTTP Error {response.status}: {error_text}")
                    
                    result = {
                        "test_name": test_name,
                        "query": query,
                        "status": "ERROR",
                        "error": f"HTTP {response.status}: {error_text}",
                        "response_time_ms": round(response_time, 1)
                    }
                    self.test_results.append(result)
                    return result
                    
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            
            result = {
                "test_name": test_name,
                "query": query,
                "status": "ERROR",
                "error": str(e),
                "response_time_ms": round((time.time() - start_time) * 1000, 1)
            }
            self.test_results.append(result)
            return result
    
    async def run_pink_batts_tests(self):
        """Run all Pink Batts specific tests"""
        print("🎯 STRYDA RAG Backend - Pink Batts Insulation Retrieval Testing")
        print("=" * 80)
        print(f"Backend URL: {self.backend_url}")
        print(f"Test Start Time: {datetime.now().isoformat()}")
        print(f"Context: Testing 1,320 Pink Batts documentation chunks with trade-aware tagging")
        print()
        
        await self.setup_session()
        
        try:
            # Test 1: Ceiling Insulation R-value Query
            await self.test_chat_endpoint(
                query="What R-value Pink Batts do I need for my ceiling in Auckland?",
                test_name="Ceiling Insulation R-value Test",
                expected_keywords=["r-value", "ceiling", "auckland", "r3.2", "r4.0", "r5.0", "insulation"],
                expected_trade="ceiling_insulation"
            )
            
            # Test 2: Underfloor Installation Query
            await self.test_chat_endpoint(
                query="How do I install Pink Batts underfloor insulation?",
                test_name="Underfloor Installation Test", 
                expected_keywords=["install", "underfloor", "installation", "batts", "floor", "joists"],
                expected_trade="underfloor_insulation"
            )
            
            # Test 3: Wall Insulation Specs Query
            await self.test_chat_endpoint(
                query="What are the dimensions of Pink Batts R2.6 wall insulation?",
                test_name="Wall Insulation Specs Test",
                expected_keywords=["dimensions", "r2.6", "wall", "thickness", "width", "specifications"],
                expected_trade="wall_insulation"
            )
            
        finally:
            await self.cleanup_session()
        
        # Generate summary
        self.generate_test_summary()
    
    def generate_test_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 PINK BATTS INSULATION RETRIEVAL TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.get("status") == "PASS"])
        partial_tests = len([r for r in self.test_results if r.get("status") == "PARTIAL"])
        failed_tests = len([r for r in self.test_results if r.get("status") == "FAIL"])
        error_tests = len([r for r in self.test_results if r.get("status") == "ERROR"])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"⚠️ Partial: {partial_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"🚨 Errors: {error_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Detailed results
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "⚠️" if result["status"] == "PARTIAL" else "❌" if result["status"] == "FAIL" else "🚨"
            print(f"{status_icon} {result['test_name']}: {result['status']}")
            
            if result["status"] in ["PASS", "PARTIAL"]:
                print(f"   Pink Batts Mentioned: {result.get('pink_batts_mentioned', False)}")
                print(f"   Deep Dive Source: {result.get('deep_dive_source', False)}")
                print(f"   Keywords Found: {len(result.get('keywords_found', []))}/{len(result.get('expected_keywords', []))}")
                print(f"   R-values Found: {result.get('r_values_found', [])}")
                print(f"   Response Time: {result.get('response_time_ms', 0)}ms")
                print(f"   Response Length: {result.get('response_length', 0)} chars")
            elif result["status"] == "FAIL":
                print(f"   Issues: Pink Batts={result.get('pink_batts_mentioned', False)}, Keywords={len(result.get('keywords_found', []))}")
            else:
                print(f"   Error: {result.get('error', 'Unknown error')}")
            print()
        
        # Pink Batts specific analysis
        print("🔍 PINK BATTS RETRIEVAL ANALYSIS:")
        print("-" * 40)
        
        pink_batts_mention_rate = len([r for r in self.test_results if r.get("pink_batts_mentioned", False)]) / total_tests * 100
        deep_dive_detection_rate = len([r for r in self.test_results if r.get("deep_dive_source", False)]) / total_tests * 100
        avg_keywords_found = sum(len(r.get("keywords_found", [])) for r in self.test_results) / total_tests
        avg_response_time = sum(r.get("response_time_ms", 0) for r in self.test_results) / total_tests
        
        print(f"Pink Batts Brand Mention Rate: {pink_batts_mention_rate:.1f}%")
        print(f"Deep Dive Source Detection Rate: {deep_dive_detection_rate:.1f}%")
        print(f"Average Keywords Found per Response: {avg_keywords_found:.1f}")
        print(f"Average Response Time: {avg_response_time:.1f}ms")
        print()
        
        # Success criteria evaluation
        print("🎯 SUCCESS CRITERIA EVALUATION:")
        print("-" * 40)
        
        criteria_met = 0
        total_criteria = 3
        
        if pink_batts_mention_rate >= 80:
            print("✅ Pink Batts Brand Recognition: PASS (≥80% mention rate)")
            criteria_met += 1
        else:
            print(f"❌ Pink Batts Brand Recognition: FAIL ({pink_batts_mention_rate:.1f}% < 80%)")
        
        if deep_dive_detection_rate >= 50:
            print("✅ Deep Dive Source Detection: PASS (≥50% detection rate)")
            criteria_met += 1
        else:
            print(f"❌ Deep Dive Source Detection: FAIL ({deep_dive_detection_rate:.1f}% < 50%)")
        
        if (passed_tests + partial_tests) >= total_tests * 0.8:
            print("✅ Overall Response Quality: PASS (≥80% pass/partial rate)")
            criteria_met += 1
        else:
            print(f"❌ Overall Response Quality: FAIL ({((passed_tests + partial_tests)/total_tests)*100:.1f}% < 80%)")
        
        print()
        print(f"📈 FINAL VERDICT: {criteria_met}/{total_criteria} criteria met")
        
        if criteria_met == total_criteria:
            print("🎉 PINK BATTS INSULATION RETRIEVAL: ✅ FULLY WORKING")
        elif criteria_met >= 2:
            print("⚠️  PINK BATTS INSULATION RETRIEVAL: 🔶 PARTIALLY WORKING")
        else:
            print("🚨 PINK BATTS INSULATION RETRIEVAL: ❌ NOT WORKING")
        
        print(f"\nTest Completed: {datetime.now().isoformat()}")

async def main():
    """Main test execution"""
    tester = PinkBattsRAGTester()
    await tester.run_pink_batts_tests()

if __name__ == "__main__":
    asyncio.run(main())