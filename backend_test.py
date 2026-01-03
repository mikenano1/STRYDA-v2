#!/usr/bin/env python3
"""
STRYDA RAG Backend Testing - Product Function/Trade-Aware Retrieval
Testing the new trade-aware retrieval feature that distinguishes between product lines within brands.
Focus: Firth brand with granular trade metadata (paving, masonry, foundations)
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

class TradeAwareRetrievalTester:
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
    
    def _extract_trade_keywords(self, text: str, expected_trade: str) -> dict:
        """Extract trade-specific keywords from response text"""
        text_lower = text.lower()
        
        # Define trade-specific keywords
        trade_keywords = {
            "paving": [
                "paver", "pavers", "paving", "pathway", "pathways", "driveway", "driveways",
                "laying pattern", "laying patterns", "holland", "ecopave", "bedding sand",
                "joint sand", "compaction", "base course", "sub-base"
            ],
            "masonry": [
                "block", "blocks", "masonry", "steel spacing", "reinforcement", "grout",
                "20 series", "25 series", "mortar", "concrete block", "block wall",
                "steel reinforcement", "vertical reinforcement", "horizontal reinforcement"
            ],
            "foundations": [
                "ribraft", "foundation", "foundations", "edge detail", "edge beam", "x-pod",
                "slab", "concrete slab", "beam", "footing", "footings", "reinforcement",
                "starter bars", "foundation system"
            ]
        }
        
        # Get keywords for expected trade
        expected_keywords = trade_keywords.get(expected_trade.lower(), [])
        found_keywords = [kw for kw in expected_keywords if kw in text_lower]
        
        # Check for wrong trade keywords
        wrong_trade_keywords = []
        for trade, keywords in trade_keywords.items():
            if trade != expected_trade.lower():
                wrong_keywords = [kw for kw in keywords if kw in text_lower]
                if wrong_keywords:
                    wrong_trade_keywords.extend([(trade, kw) for kw in wrong_keywords])
        
        return {
            "found_keywords": found_keywords,
            "wrong_trade_keywords": wrong_trade_keywords,
            "keyword_count": len(found_keywords),
            "wrong_keyword_count": len(wrong_trade_keywords)
        }
    
    def _check_firth_brand_mention(self, response: str) -> bool:
        """Check if Firth brand is mentioned in the response"""
        return "firth" in response.lower()
    
    def _extract_backend_logs_info(self, response_data: dict) -> dict:
        """Extract any backend log information from response metadata"""
        # Look for any debug or log information in the response
        log_info = {
            "trade_detected": None,
            "brand_filter": None,
            "vector_search_info": None
        }
        
        # Check if there's any metadata about trade detection
        # This would typically be in response headers or debug info
        # For now, we'll infer from the response content
        
        return log_info
    async def test_trade_aware_chat(self, message: str, session_id: str, test_name: str, expected_trade: str):
        """Test the /api/chat endpoint for trade-aware retrieval"""
        try:
            start_time = time.time()
            
            payload = {
                "message": message,
                "session_id": session_id
            }
            
            print(f"\n🧪 Testing: {test_name}")
            print(f"📝 Query: {message}")
            print(f"🎯 Expected Trade: {expected_trade}")
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
                    answer = data.get("response", data.get("answer", ""))
                    citations = data.get("citations", [])
                    sources_used = data.get("sources_used", [])
                    confidence_score = data.get("confidence_score", 0)
                    
                    # Analyze trade-specific content
                    trade_analysis = self._extract_trade_keywords(answer, expected_trade)
                    
                    # Check for Firth brand mention
                    firth_mentioned = self._check_firth_brand_mention(answer)
                    
                    # Check for trade-specific sources
                    trade_sources = [source for source in sources_used if "firth" in str(source).lower()]
                    
                    # Determine test result based on trade relevance
                    if trade_analysis["keyword_count"] >= 2 and trade_analysis["wrong_keyword_count"] == 0:
                        test_status = "PASS"
                        status_detail = f"Strong trade relevance: {trade_analysis['keyword_count']} relevant keywords"
                    elif trade_analysis["keyword_count"] >= 1 and trade_analysis["wrong_keyword_count"] <= 1:
                        test_status = "PARTIAL"
                        status_detail = f"Moderate trade relevance: {trade_analysis['keyword_count']} relevant, {trade_analysis['wrong_keyword_count']} wrong"
                    elif trade_analysis["keyword_count"] == 0 and trade_analysis["wrong_keyword_count"] == 0:
                        test_status = "UNCLEAR"
                        status_detail = "No clear trade-specific content detected"
                    else:
                        test_status = "FAIL"
                        status_detail = f"Wrong trade content: {trade_analysis['wrong_keyword_count']} wrong keywords"
                    
                    result = {
                        "test_name": test_name,
                        "query": message,
                        "expected_trade": expected_trade,
                        "session_id": session_id,
                        "status": test_status,
                        "status_detail": status_detail,
                        "status_code": status_code,
                        "response_time_ms": round(response_time, 1),
                        "response_length": len(answer),
                        "answer": answer[:400] + "..." if len(answer) > 400 else answer,
                        "citations_count": len(citations),
                        "sources_used": sources_used,
                        "trade_sources": trade_sources,
                        "confidence_score": confidence_score,
                        "firth_mentioned": firth_mentioned,
                        "trade_analysis": trade_analysis,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    print(f"✅ Status: {status_code} OK")
                    print(f"⏱️  Response Time: {response_time:.1f}ms")
                    print(f"📏 Response Length: {len(answer)} characters")
                    print(f"🏷️  Firth Mentioned: {firth_mentioned}")
                    print(f"🎯 Trade Keywords Found: {trade_analysis['found_keywords']}")
                    print(f"❌ Wrong Trade Keywords: {[f'{t}:{k}' for t,k in trade_analysis['wrong_trade_keywords']]}")
                    print(f"📚 Trade Sources: {trade_sources}")
                    print(f"📖 Citations: {len(citations)}")
                    print(f"🔍 All Sources: {sources_used}")
                    print(f"💯 Confidence: {confidence_score}")
                    print(f"🏆 Test Result: {test_status} - {status_detail}")
                    print(f"📝 Response Preview: {answer[:300]}...")
                    
                else:
                    error_text = await response.text()
                    result = {
                        "test_name": test_name,
                        "query": message,
                        "expected_trade": expected_trade,
                        "session_id": session_id,
                        "status": "FAIL",
                        "status_detail": f"HTTP Error {status_code}",
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
                "expected_trade": expected_trade,
                "session_id": session_id,
                "status": "ERROR",
                "status_detail": f"Exception: {str(e)}",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"💥 Exception: {str(e)}")
            self.test_results.append(result)
            return result
    
    async def run_trade_aware_retrieval_tests(self):
        """Run all trade-aware retrieval tests for Firth brand"""
        
        print("🚀 STRYDA RAG Backend Testing - Product Function/Trade-Aware Retrieval")
        print("=" * 80)
        print(f"🎯 Backend URL: {self.backend_url}")
        print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🏷️  Focus: Firth brand trade-aware retrieval (paving, masonry, foundations)")
        print("=" * 80)
        
        # Test cases from the review request
        test_cases = [
            {
                "message": "How do I install Firth Holland Pavers?",
                "session_id": "test-firth-paving-trade",
                "test_name": "Paving Trade Detection",
                "expected_trade": "paving",
                "expected": "Should focus on PAVING topics (pavers, pathways, driveways, laying patterns)"
            },
            {
                "message": "What is the steel spacing for a Firth 20 Series block wall?", 
                "session_id": "test-firth-masonry-trade",
                "test_name": "Masonry Trade Detection",
                "expected_trade": "masonry",
                "expected": "Should focus on MASONRY topics (block walls, steel reinforcement, grout)"
            },
            {
                "message": "RibRaft edge detail reinforcement",
                "session_id": "test-firth-foundations-trade",
                "test_name": "Foundations Trade Detection",
                "expected_trade": "foundations",
                "expected": "Should focus on FOUNDATIONS topics (RibRaft, edge beams, reinforcement)"
            }
        ]
        
        # Run all tests
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'='*20} TEST {i}/{len(test_cases)} {'='*20}")
            print(f"Expected: {test_case['expected']}")
            
            await self.test_trade_aware_chat(
                test_case["message"],
                test_case["session_id"], 
                test_case["test_name"],
                test_case["expected_trade"]
            )
            
            # Small delay between tests
            await asyncio.sleep(2)
        
        # Generate summary
        return self.generate_test_summary()
    
    def generate_test_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "="*80)
        print("📊 TRADE-AWARE RETRIEVAL TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        partial_tests = len([r for r in self.test_results if r["status"] == "PARTIAL"])
        failed_tests = len([r for r in self.test_results if r["status"] in ["FAIL", "ERROR", "UNCLEAR"]])
        
        print(f"📈 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"⚠️  Partial: {partial_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📊 Success Rate: {((passed_tests + partial_tests)/total_tests)*100:.1f}%")
        
        # Trade detection analysis
        trade_relevance_scores = []
        firth_mentions = []
        
        for result in self.test_results:
            if result["status"] in ["PASS", "PARTIAL"]:
                trade_analysis = result.get("trade_analysis", {})
                trade_relevance_scores.append(trade_analysis.get("keyword_count", 0))
                firth_mentions.append(result.get("firth_mentioned", False))
        
        avg_trade_relevance = sum(trade_relevance_scores) / len(trade_relevance_scores) if trade_relevance_scores else 0
        firth_mention_rate = (sum(firth_mentions) / len(firth_mentions)) * 100 if firth_mentions else 0
        
        print(f"\n🎯 TRADE-AWARE ANALYSIS:")
        print(f"   Average Trade Keywords per Response: {avg_trade_relevance:.1f}")
        print(f"   Firth Brand Mention Rate: {firth_mention_rate:.1f}%")
        
        print(f"\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "⚠️" if result["status"] == "PARTIAL" else "❌"
            trade_icon = "🎯" if result.get("firth_mentioned", False) else "⚪"
            
            print(f"   {status_icon} {result['test_name']} ({result.get('expected_trade', 'unknown').upper()})")
            print(f"      {trade_icon} Firth Mentioned: {result.get('firth_mentioned', 'N/A')}")
            
            if result["status"] in ["PASS", "PARTIAL"]:
                trade_analysis = result.get("trade_analysis", {})
                print(f"      🔍 Trade Keywords: {trade_analysis.get('found_keywords', [])}")
                print(f"      ❌ Wrong Keywords: {[f'{t}:{k}' for t,k in trade_analysis.get('wrong_trade_keywords', [])]}")
                print(f"      📏 Response: {result.get('response_length', 0)} chars")
                print(f"      ⏱️  Time: {result.get('response_time_ms', 0)}ms")
                print(f"      📚 Trade Sources: {result.get('trade_sources', [])}")
            else:
                print(f"      ⚠️  Error: {result.get('error', result.get('status_detail', 'Unknown error'))}")
        
        # Final assessment
        print(f"\n🔍 TRADE-AWARE RETRIEVAL ASSESSMENT:")
        
        if passed_tests == total_tests:
            print("   🎉 EXCELLENT: All tests passed with strong trade-specific responses")
            verdict = "FULLY WORKING"
        elif passed_tests + partial_tests == total_tests:
            print("   ✅ GOOD: All tests show trade relevance (some partial)")
            verdict = "MOSTLY WORKING"
        elif passed_tests + partial_tests >= total_tests * 0.67:
            print("   ⚠️  PARTIAL: Most tests show trade relevance")
            verdict = "PARTIALLY WORKING"
        else:
            print("   ❌ CRITICAL: Trade-aware retrieval not working effectively")
            verdict = "NOT WORKING"
        
        print(f"\n🏆 FINAL VERDICT: {verdict}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if firth_mention_rate < 50:
            print("   • Firth brand documents may not be properly indexed or prioritized")
            print("   • Verify Firth document ingestion and brand detection")
        if avg_trade_relevance < 2:
            print("   • Trade-specific keyword detection is low")
            print("   • Check if trade metadata is properly applied to Firth documents")
        if failed_tests > 0:
            print("   • Investigate API endpoint failures and trade filtering logic")
            print("   • Check backend logs for trade detection messages")
        if passed_tests < total_tests:
            print("   • Review trade-aware retrieval implementation")
            print("   • Verify granular product function detection is working")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "partial_tests": partial_tests, 
            "failed_tests": failed_tests,
            "success_rate": ((passed_tests + partial_tests)/total_tests)*100,
            "avg_trade_relevance": avg_trade_relevance,
            "firth_mention_rate": firth_mention_rate,
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