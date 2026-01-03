#!/usr/bin/env python3
"""
STRYDA RAG Backend Testing - Operation Final Sweep Verification
Testing specific brand queries to verify Final Sweep document integration
"""

import asyncio
import aiohttp
import json
import time
import re
from datetime import datetime
import sys
import os

# Get backend URL from environment
BACKEND_URL = "https://trade-aware-rag.preview.emergentagent.com/api"

class STRYDABackendTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.session = None
        self.test_results = []
        
    async def setup(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup(self):
        """Clean up HTTP session"""
        if self.session:
            await self.session.close()
    
    def _extract_inline_citations(self, text: str) -> list:
        """Extract inline citations from response text"""
        # Look for patterns like [[Source: Final Sweep - SPAX | Page: 64]]
        pattern = r'\[\[Source: ([^|]+)(?:\|[^\]]+)?\]\]'
        matches = re.findall(pattern, text)
        return matches
    
    def _check_brand_mention(self, query: str, response: str) -> bool:
        """Check if the expected brand from the query is mentioned in the response"""
        query_lower = query.lower()
        response_lower = response.lower()
        
        # Extract brand from query
        brands = {
            "pryda": "pryda",
            "zenith": "zenith", 
            "macsim": "macsim",
            "spax": "spax",
            "bremick": "bremick",
            "bunnings": ["bunnings", "zenith", "pryda", "bremick"]  # Bunnings should mention these brands
        }
        
        for brand, expected in brands.items():
            if brand in query_lower:
                if isinstance(expected, list):
                    return any(exp in response_lower for exp in expected)
                else:
                    return expected in response_lower
        
        return False
    
    def _check_brand_in_sources(self, query: str, sources_used: list) -> bool:
        """Check if the expected brand appears in the sources used"""
        query_lower = query.lower()
        sources_str = " ".join(str(source) for source in sources_used).lower()
        
        brands = ["pryda", "zenith", "macsim", "spax", "bremick"]
        
        for brand in brands:
            if brand in query_lower:
                return brand in sources_str
        
        return False
    
    def _check_brand_in_inline_citations(self, query: str, inline_citations: list) -> bool:
        """Check if the expected brand appears in inline citations"""
        query_lower = query.lower()
        citations_str = " ".join(str(citation) for citation in inline_citations).lower()
        
        brands = ["pryda", "zenith", "macsim", "spax", "bremick"]
        
        for brand in brands:
            if brand in query_lower:
                return brand in citations_str
        
        return False
            
    async def test_chat_endpoint(self, message: str, session_id: str, test_name: str):
        """Test the /api/chat endpoint with a specific message"""
        try:
            start_time = time.time()
            
            payload = {
                "message": message,
                "session_id": session_id
            }
            
            print(f"\n🧪 Testing: {test_name}")
            print(f"📝 Query: {message}")
            print(f"🔗 Session: {session_id}")
            
            async with self.session.post(
                f"{self.backend_url}/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                response_time = (time.time() - start_time) * 1000
                status_code = response.status
                
                if status_code == 200:
                    data = await response.json()
                    
                    # Extract key information
                    answer = data.get("answer", "")
                    citations = data.get("citations", [])
                    sources_used = data.get("sources_used", [])
                    confidence_score = data.get("confidence_score", 0)
                    
                    # Check for inline source citations in the answer
                    inline_citations = self._extract_inline_citations(answer)
                    
                    # Check for brand mentions
                    brand_mentioned = self._check_brand_mention(message, answer)
                    
                    # Check for Final Sweep source
                    final_sweep_source = any("Final Sweep" in str(source) or "Fasteners Full Suite" in str(source) 
                                           for source in sources_used) or "Final Sweep" in answer
                    
                    # Check for specific brand in sources or inline citations
                    brand_in_sources = self._check_brand_in_sources(message, sources_used) or \
                                     self._check_brand_in_inline_citations(message, inline_citations)
                    
                    result = {
                        "test_name": test_name,
                        "query": message,
                        "session_id": session_id,
                        "status": "PASS",
                        "status_code": status_code,
                        "response_time_ms": round(response_time, 1),
                        "response_length": len(answer),
                        "answer": answer[:300] + "..." if len(answer) > 300 else answer,
                        "citations_count": len(citations),
                        "inline_citations": inline_citations,
                        "sources_used": sources_used,
                        "confidence_score": confidence_score,
                        "brand_mentioned": brand_mentioned,
                        "brand_in_sources": brand_in_sources,
                        "final_sweep_source": final_sweep_source,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    print(f"✅ Status: {status_code} OK")
                    print(f"⏱️  Response Time: {response_time:.1f}ms")
                    print(f"📏 Response Length: {len(answer)} characters")
                    print(f"🎯 Brand Mentioned: {brand_mentioned}")
                    print(f"🏷️  Brand in Sources: {brand_in_sources}")
                    print(f"📚 Final Sweep Source: {final_sweep_source}")
                    print(f"📖 Citations: {len(citations)}")
                    print(f"🔗 Inline Citations: {inline_citations}")
                    print(f"🔍 Sources: {sources_used}")
                    print(f"💯 Confidence: {confidence_score}")
                    print(f"📝 Response Preview: {answer[:200]}...")
                    
                else:
                    error_text = await response.text()
                    result = {
                        "test_name": test_name,
                        "query": message,
                        "session_id": session_id,
                        "status": "FAIL",
                        "status_code": status_code,
                        "response_time_ms": round(response_time, 1),
                        "error": error_text,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    print(f"❌ Status: {status_code}")
                    print(f"⚠️  Error: {error_text}")
                
                self.test_results.append(result)
                return result
                
        except Exception as e:
            result = {
                "test_name": test_name,
                "query": message,
                "session_id": session_id,
                "status": "ERROR",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"💥 Exception: {str(e)}")
            self.test_results.append(result)
            return result
    
    async def run_operation_final_sweep_tests(self):
        """Run all Operation Final Sweep brand tests"""
        
        print("🚀 STRYDA RAG Backend Testing - Operation Final Sweep Verification")
        print("=" * 80)
        print(f"🎯 Backend URL: {self.backend_url}")
        print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Test cases from the review request
        test_cases = [
            {
                "message": "What Pryda bracing anchors and connectors are available?",
                "session_id": "test-pryda-final-sweep",
                "test_name": "Pryda Bracing Query",
                "expected": "Should return Pryda product info with load capacities"
            },
            {
                "message": "What Zenith butt hinges are in the catalogue?", 
                "session_id": "test-zenith-final-sweep",
                "test_name": "Zenith Hardware Query",
                "expected": "Should return Zenith hardware catalogue data with sizes"
            },
            {
                "message": "What MacSim drop-in anchors are available?",
                "session_id": "test-macsim-final-sweep", 
                "test_name": "MacSim Anchor Query",
                "expected": "Should return MacSim anchor specifications"
            },
            {
                "message": "What SPAX screws should I use for decking?",
                "session_id": "test-spax-final-sweep",
                "test_name": "SPAX Decking Query", 
                "expected": "Should return SPAX product info"
            },
            {
                "message": "What Bremick masonry anchors are available?",
                "session_id": "test-bremick-final-sweep",
                "test_name": "Bremick Masonry Query",
                "expected": "Should return Bremick masonry anchor data"
            },
            {
                "message": "I'm at Bunnings, what brackets should I use for deck posts?",
                "session_id": "test-bunnings-bias-final-sweep",
                "test_name": "Retailer Bias Test",
                "expected": "Response should mention Bunnings brands like Zenith, Pryda, or Bremick"
            }
        ]
        
        # Run all tests
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'='*20} TEST {i}/{len(test_cases)} {'='*20}")
            print(f"Expected: {test_case['expected']}")
            
            await self.test_chat_endpoint(
                test_case["message"],
                test_case["session_id"], 
                test_case["test_name"]
            )
            
            # Small delay between tests
            await asyncio.sleep(2)
        
        # Generate summary
        return self.generate_test_summary()
    
    def generate_test_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "="*80)
        print("📊 OPERATION FINAL SWEEP TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] in ["FAIL", "ERROR"]])
        
        print(f"📈 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📊 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Brand detection analysis
        brand_detection_results = []
        brand_in_sources_results = []
        final_sweep_usage = []
        
        for result in self.test_results:
            if result["status"] == "PASS":
                brand_detection_results.append(result.get("brand_mentioned", False))
                brand_in_sources_results.append(result.get("brand_in_sources", False))
                final_sweep_usage.append(result.get("final_sweep_source", False))
        
        brand_detection_rate = (sum(brand_detection_results) / len(brand_detection_results)) * 100 if brand_detection_results else 0
        brand_sources_rate = (sum(brand_in_sources_results) / len(brand_in_sources_results)) * 100 if brand_in_sources_results else 0
        final_sweep_rate = (sum(final_sweep_usage) / len(final_sweep_usage)) * 100 if final_sweep_usage else 0
        
        print(f"\n🎯 BRAND DETECTION ANALYSIS:")
        print(f"   Brand Mention Rate: {brand_detection_rate:.1f}%")
        print(f"   Brand in Sources Rate: {brand_sources_rate:.1f}%")
        print(f"   Final Sweep Usage Rate: {final_sweep_rate:.1f}%")
        
        print(f"\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            brand_icon = "🎯" if result.get("brand_mentioned", False) else "⚪"
            source_icon = "🏷️" if result.get("brand_in_sources", False) else "⚪"
            sweep_icon = "📚" if result.get("final_sweep_source", False) else "⚪"
            
            print(f"   {status_icon} {result['test_name']}")
            print(f"      {brand_icon} Brand Mentioned: {result.get('brand_mentioned', 'N/A')}")
            print(f"      {source_icon} Brand in Sources: {result.get('brand_in_sources', 'N/A')}")
            print(f"      {sweep_icon} Final Sweep Source: {result.get('final_sweep_source', 'N/A')}")
            if result["status"] == "PASS":
                print(f"      📏 Response: {result.get('response_length', 0)} chars")
                print(f"      ⏱️  Time: {result.get('response_time_ms', 0)}ms")
                print(f"      🔗 Inline Citations: {result.get('inline_citations', [])}")
            else:
                print(f"      ⚠️  Error: {result.get('error', 'Unknown error')}")
        
        # Final assessment
        print(f"\n🔍 OPERATION FINAL SWEEP ASSESSMENT:")
        
        if passed_tests == total_tests:
            if brand_detection_rate >= 80 and final_sweep_rate >= 80:
                print("   🎉 EXCELLENT: All tests passed with high brand detection and Final Sweep usage")
                verdict = "FULLY WORKING"
            elif brand_sources_rate >= 80:
                print("   ✅ GOOD: All tests passed with brands found in sources")
                verdict = "MOSTLY WORKING"
            elif final_sweep_rate >= 80:
                print("   ⚠️  PARTIAL: Tests pass with Final Sweep usage but low brand detection")
                verdict = "PARTIALLY WORKING"
            else:
                print("   ⚠️  ISSUES: Tests pass but brand detection and Final Sweep usage are low")
                verdict = "PARTIALLY WORKING"
        else:
            print("   ❌ CRITICAL: Some tests failed")
            verdict = "NOT WORKING"
        
        print(f"\n🏆 FINAL VERDICT: {verdict}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if brand_detection_rate < 50:
            print("   • Expected brands (Pryda, Zenith, MacSim, SPAX, Bremick) may be missing from Final Sweep")
            print("   • Verify Final Sweep document contains the expected NZ brand catalogs")
        if brand_sources_rate < 50:
            print("   • Brand-specific sources not being retrieved effectively")
            print("   • Check if brand documents are properly indexed and prioritized")
        if final_sweep_rate < 80:
            print("   • Final Sweep document may not be properly integrated or prioritized")
            print("   • Check document ingestion and retrieval configuration")
        if failed_tests > 0:
            print("   • Investigate API endpoint failures and error handling")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests, 
            "failed_tests": failed_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "brand_detection_rate": brand_detection_rate,
            "brand_sources_rate": brand_sources_rate,
            "final_sweep_usage_rate": final_sweep_rate,
            "verdict": verdict,
            "test_results": self.test_results
        }

async def main():
    """Main test execution"""
    tester = STRYDABackendTester()
    
    try:
        await tester.setup()
        summary = await tester.run_operation_final_sweep_tests()
        return summary
    except Exception as e:
        print(f"💥 Test execution failed: {e}")
        return None
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    # Run the tests
    result = asyncio.run(main())
    
    # Exit with appropriate code
    if result and result.get("failed_tests", 1) == 0:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure