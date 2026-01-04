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
            
    async def test_chat_endpoint(self, query: str, expected_trade: str, expected_brand: str, test_name: str):
        """Test chat endpoint with trade-aware retrieval expectations"""
        print(f"\n🧪 Testing: {test_name}")
        print(f"Query: {query}")
        print(f"Expected Trade: {expected_trade}")
        print(f"Expected Brand: {expected_brand}")
        
        start_time = time.time()
        
        try:
            # Make request to chat endpoint
            payload = {
                "message": query,
                "session_id": f"test-trade-aware-{int(time.time())}"
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
                    ai_response = data.get("answer", "")
                    citations = data.get("citations", [])
                    sources_used = data.get("sources_used", [])
                    
                    # Check for brand mention
                    brand_mentioned = expected_brand.lower() in ai_response.lower()
                    
                    # Check for trade-specific keywords
                    trade_keywords = self.get_trade_keywords(expected_trade)
                    trade_keyword_count = sum(1 for keyword in trade_keywords if keyword.lower() in ai_response.lower())
                    
                    # Analyze response quality
                    response_length = len(ai_response)
                    
                    result = {
                        "test_name": test_name,
                        "query": query,
                        "expected_trade": expected_trade,
                        "expected_brand": expected_brand,
                        "status": "PASS" if brand_mentioned and trade_keyword_count > 0 else "FAIL",
                        "response_time_ms": round(response_time, 1),
                        "response_length": response_length,
                        "brand_mentioned": brand_mentioned,
                        "trade_keyword_count": trade_keyword_count,
                        "trade_keywords_found": [kw for kw in trade_keywords if kw.lower() in ai_response.lower()],
                        "sources_used": sources_used,
                        "citations_count": len(citations),
                        "ai_response": ai_response[:200] + "..." if len(ai_response) > 200 else ai_response,
                        "full_response": ai_response
                    }
                    
                    print(f"✅ Status: {result['status']}")
                    print(f"⏱️  Response Time: {response_time:.1f}ms")
                    print(f"📝 Response Length: {response_length} chars")
                    print(f"🏷️  Brand Mentioned: {brand_mentioned}")
                    print(f"🔧 Trade Keywords Found: {trade_keyword_count} ({result['trade_keywords_found']})")
                    print(f"📚 Sources Used: {len(sources_used)}")
                    print(f"📖 Citations: {len(citations)}")
                    
                    if result['status'] == "FAIL":
                        print(f"❌ FAILURE REASONS:")
                        if not brand_mentioned:
                            print(f"   - Brand '{expected_brand}' not mentioned in response")
                        if trade_keyword_count == 0:
                            print(f"   - No trade-specific keywords found for '{expected_trade}'")
                    
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
    
    def get_trade_keywords(self, trade: str) -> list:
        """Get expected keywords for each trade category"""
        trade_keywords = {
            "framing": ["joist", "hangers", "hanger", "beam", "framing", "lvl", "timber", "structural", "face mount", "top mount"],
            "bracing": ["bracing", "brace", "earthquake", "seismic", "hold down", "strap", "speed brace", "wall bracing", "lateral"],
            "anchoring": ["anchor", "anchors", "dynabolt", "concrete", "masonry", "fixing", "bolt", "chemical anchor", "drop-in"],
            "decking": ["deck", "decking", "boards", "joists", "bearers", "posts", "outdoor", "timber deck"],
            "fasteners": ["screws", "nails", "bolts", "fixings", "fasteners", "self-drilling", "hex head"],
            "hardware": ["hinges", "handles", "locks", "door", "window", "cabinet", "furniture"],
            "nailplates": ["nail plate", "nailplate", "truss", "gang nail", "connector plate"],
            "framing_nails": ["framing nail", "nail", "galvanised", "bright", "ring shank"],
            "staples": ["staple", "staples", "pneumatic", "crown", "leg length"]
        }
        return trade_keywords.get(trade, [])
    
    async def run_all_tests(self):
        """Run all multi-category brand trade-aware retrieval tests"""
        print("🎯 STRYDA RAG Backend - Multi-Category Brand Trade-Aware Retrieval Tests")
        print("=" * 80)
        print(f"Backend URL: {self.backend_url}")
        print(f"Test Start Time: {datetime.now().isoformat()}")
        print()
        
        await self.setup_session()
        
        try:
            # Test 1: Simpson Strong-Tie Framing
            await self.test_chat_endpoint(
                query="What Simpson joist hangers should I use for LVL beams?",
                expected_trade="framing",
                expected_brand="Simpson",
                test_name="Simpson Framing Test"
            )
            
            # Test 2: Pryda Bracing
            await self.test_chat_endpoint(
                query="What Pryda bracing options are available for earthquake zones?",
                expected_trade="bracing", 
                expected_brand="Pryda",
                test_name="Pryda Bracing Test"
            )
            
            # Test 3: Zenith Anchoring
            await self.test_chat_endpoint(
                query="What Zenith dynabolt sizes are available for concrete?",
                expected_trade="anchoring",
                expected_brand="Zenith", 
                test_name="Zenith Anchoring Test"
            )
            
            # Additional Test 4: Ecko Decking (bonus test)
            await self.test_chat_endpoint(
                query="What Ecko decking screws should I use for outdoor timber?",
                expected_trade="decking",
                expected_brand="Ecko",
                test_name="Ecko Decking Test"
            )
            
            # Additional Test 5: Zenith Fasteners (different trade for same brand)
            await self.test_chat_endpoint(
                query="What Zenith self-drilling screws are available for steel framing?",
                expected_trade="fasteners",
                expected_brand="Zenith",
                test_name="Zenith Fasteners Test"
            )
            
        finally:
            await self.cleanup_session()
        
        # Generate summary
        self.generate_test_summary()
    
    def generate_test_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 MULTI-CATEGORY BRAND TRADE-AWARE RETRIEVAL TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.get("status") == "PASS"])
        failed_tests = len([r for r in self.test_results if r.get("status") == "FAIL"])
        error_tests = len([r for r in self.test_results if r.get("status") == "ERROR"])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"🚨 Errors: {error_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Detailed results
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "🚨"
            print(f"{status_icon} {result['test_name']}: {result['status']}")
            
            if result["status"] == "PASS":
                print(f"   Brand Mentioned: {result.get('brand_mentioned', False)}")
                print(f"   Trade Keywords: {result.get('trade_keyword_count', 0)} found")
                print(f"   Response Time: {result.get('response_time_ms', 0)}ms")
                print(f"   Response Length: {result.get('response_length', 0)} chars")
            elif result["status"] == "FAIL":
                print(f"   Issues: Brand mentioned={result.get('brand_mentioned', False)}, Trade keywords={result.get('trade_keyword_count', 0)}")
            else:
                print(f"   Error: {result.get('error', 'Unknown error')}")
            print()
        
        # Trade-aware retrieval analysis
        print("🔍 TRADE-AWARE RETRIEVAL ANALYSIS:")
        print("-" * 40)
        
        brand_mention_rate = len([r for r in self.test_results if r.get("brand_mentioned", False)]) / total_tests * 100
        avg_trade_keywords = sum(r.get("trade_keyword_count", 0) for r in self.test_results) / total_tests
        avg_response_time = sum(r.get("response_time_ms", 0) for r in self.test_results) / total_tests
        
        print(f"Brand Mention Rate: {brand_mention_rate:.1f}%")
        print(f"Average Trade Keywords per Response: {avg_trade_keywords:.1f}")
        print(f"Average Response Time: {avg_response_time:.1f}ms")
        print()
        
        # Success criteria evaluation
        print("🎯 SUCCESS CRITERIA EVALUATION:")
        print("-" * 40)
        
        criteria_met = 0
        total_criteria = 3
        
        if brand_mention_rate >= 80:
            print("✅ Brand Detection: PASS (≥80% brand mention rate)")
            criteria_met += 1
        else:
            print(f"❌ Brand Detection: FAIL ({brand_mention_rate:.1f}% < 80%)")
        
        if avg_trade_keywords >= 2:
            print("✅ Trade Detection: PASS (≥2 avg trade keywords)")
            criteria_met += 1
        else:
            print(f"❌ Trade Detection: FAIL ({avg_trade_keywords:.1f} < 2)")
        
        if passed_tests >= total_tests * 0.8:
            print("✅ Overall Success: PASS (≥80% test pass rate)")
            criteria_met += 1
        else:
            print(f"❌ Overall Success: FAIL ({(passed_tests/total_tests)*100:.1f}% < 80%)")
        
        print()
        print(f"📈 FINAL VERDICT: {criteria_met}/{total_criteria} criteria met")
        
        if criteria_met == total_criteria:
            print("🎉 MULTI-CATEGORY BRAND TRADE-AWARE RETRIEVAL: ✅ FULLY WORKING")
        elif criteria_met >= 2:
            print("⚠️  MULTI-CATEGORY BRAND TRADE-AWARE RETRIEVAL: 🔶 PARTIALLY WORKING")
        else:
            print("🚨 MULTI-CATEGORY BRAND TRADE-AWARE RETRIEVAL: ❌ NOT WORKING")
        
        print(f"\nTest Completed: {datetime.now().isoformat()}")

async def main():
    """Main test execution"""
    tester = TradeAwareRetrievalTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())