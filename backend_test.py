#!/usr/bin/env python3
"""
STRYDA RAG Backend Testing - Operation Final Sweep Verification
Testing the specific queries mentioned in the review request to verify
the "Operation Final Sweep" ingestion was successful.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Backend URL from frontend .env
BACKEND_URL = "https://stryda-brain.preview.emergentagent.com"

class STRYDABackendTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, status: str, details: Dict[str, Any]):
        """Log test results"""
        result = {
            "test_name": test_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        self.test_results.append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"\n{status_emoji} {test_name}: {status}")
        
        if details.get("error"):
            print(f"   Error: {details['error']}")
        if details.get("response_length"):
            print(f"   Response Length: {details['response_length']} chars")
        if details.get("citations_count") is not None:
            print(f"   Citations: {details['citations_count']}")
        if details.get("final_sweep_sources"):
            print(f"   Final Sweep Sources: {details['final_sweep_sources']}")
        if details.get("brand_mentions"):
            print(f"   Brand Mentions: {details['brand_mentions']}")
    
    async def test_health_check(self) -> bool:
        """Test basic health check endpoint"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test("Health Check", "PASS", {
                        "status_code": response.status,
                        "response": data
                    })
                    return True
                else:
                    self.log_test("Health Check", "FAIL", {
                        "status_code": response.status,
                        "error": f"Expected 200, got {response.status}"
                    })
                    return False
        except Exception as e:
            self.log_test("Health Check", "FAIL", {
                "error": str(e)
            })
            return False
    
    async def create_thread(self) -> Optional[str]:
        """Create a new thread for testing"""
        try:
            payload = {"name": "Final Sweep Test"}
            async with self.session.post(
                f"{self.base_url}/api/threads",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    thread_id = data.get("id")
                    self.log_test("Create Thread", "PASS", {
                        "status_code": response.status,
                        "thread_id": thread_id
                    })
                    return thread_id
                else:
                    error_text = await response.text()
                    self.log_test("Create Thread", "FAIL", {
                        "status_code": response.status,
                        "error": error_text
                    })
                    return None
        except Exception as e:
            self.log_test("Create Thread", "FAIL", {
                "error": str(e)
            })
            return None
    
    async def send_chat_message(self, thread_id: str, message: str) -> Optional[Dict[str, Any]]:
        """Send a chat message and return the response"""
        try:
            payload = {"content": message}
            async with self.session.post(
                f"{self.base_url}/api/messages/{thread_id}",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=60)  # 60 second timeout
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    error_text = await response.text()
                    print(f"Chat API Error: {response.status} - {error_text}")
                    return None
        except Exception as e:
            print(f"Chat API Exception: {str(e)}")
            return None
    
    def analyze_response_for_final_sweep(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze response for Final Sweep indicators"""
        analysis = {
            "response_length": 0,
            "citations_count": 0,
            "final_sweep_sources": [],
            "brand_mentions": [],
            "has_product_info": False,
            "retailer_bias_detected": False
        }
        
        if not response_data:
            return analysis
        
        # Get response text
        response_text = response_data.get("content", "") or response_data.get("response", "") or response_data.get("answer", "")
        analysis["response_length"] = len(response_text)
        
        # Check citations
        citations = response_data.get("citations", [])
        analysis["citations_count"] = len(citations)
        
        # Look for Final Sweep sources in citations
        for citation in citations:
            source = citation.get("source", "") or citation.get("title", "")
            if "final sweep" in source.lower():
                analysis["final_sweep_sources"].append(source)
        
        # Check for brand mentions in response
        brands_to_check = ["pryda", "spax", "bremick", "zenith", "bunnings"]
        response_lower = response_text.lower()
        
        for brand in brands_to_check:
            if brand in response_lower:
                analysis["brand_mentions"].append(brand)
        
        # Check for product-specific information
        product_indicators = ["load capacity", "screws", "anchors", "specifications", "installation"]
        analysis["has_product_info"] = any(indicator in response_lower for indicator in product_indicators)
        
        # Check for retailer bias (Bunnings preference)
        if "bunnings" in response_lower and any(brand in response_lower for brand in ["zenith", "pryda", "bremick"]):
            analysis["retailer_bias_detected"] = True
        
        return analysis
    
    async def test_pryda_bracing_query(self, thread_id: str):
        """Test Pryda bracing load capacity query"""
        query = "What is the load capacity of a Pryda bracing anchor?"
        
        print(f"\n🔍 Testing Pryda Query: {query}")
        response = await self.send_chat_message(thread_id, query)
        
        if response:
            analysis = self.analyze_response_for_final_sweep(response)
            
            # Determine test status
            status = "PASS" if (
                analysis["response_length"] > 50 and
                ("pryda" in analysis["brand_mentions"] or analysis["has_product_info"])
            ) else "FAIL"
            
            self.log_test("Pryda Bracing Query", status, {
                **analysis,
                "query": query,
                "response_preview": (response.get("content", "") or response.get("response", ""))[:200] + "..."
            })
        else:
            self.log_test("Pryda Bracing Query", "FAIL", {
                "query": query,
                "error": "No response received"
            })
    
    async def test_spax_timber_query(self, thread_id: str):
        """Test SPAX timber screws query"""
        query = "What SPAX screws should I use for deck framing?"
        
        print(f"\n🔍 Testing SPAX Query: {query}")
        response = await self.send_chat_message(thread_id, query)
        
        if response:
            analysis = self.analyze_response_for_final_sweep(response)
            
            # Determine test status
            status = "PASS" if (
                analysis["response_length"] > 50 and
                ("spax" in analysis["brand_mentions"] or analysis["has_product_info"])
            ) else "FAIL"
            
            self.log_test("SPAX Timber Query", status, {
                **analysis,
                "query": query,
                "response_preview": (response.get("content", "") or response.get("response", ""))[:200] + "..."
            })
        else:
            self.log_test("SPAX Timber Query", "FAIL", {
                "query": query,
                "error": "No response received"
            })
    
    async def test_bremick_anchor_query(self, thread_id: str):
        """Test Bremick masonry anchors query"""
        query = "What masonry anchors does Bremick make?"
        
        print(f"\n🔍 Testing Bremick Query: {query}")
        response = await self.send_chat_message(thread_id, query)
        
        if response:
            analysis = self.analyze_response_for_final_sweep(response)
            
            # Determine test status
            status = "PASS" if (
                analysis["response_length"] > 50 and
                ("bremick" in analysis["brand_mentions"] or analysis["has_product_info"])
            ) else "FAIL"
            
            self.log_test("Bremick Anchor Query", status, {
                **analysis,
                "query": query,
                "response_preview": (response.get("content", "") or response.get("response", ""))[:200] + "..."
            })
        else:
            self.log_test("Bremick Anchor Query", "FAIL", {
                "query": query,
                "error": "No response received"
            })
    
    async def test_retailer_bias(self, thread_id: str):
        """Test retailer bias for Bunnings"""
        query = "I'm at Bunnings, what anchors do you recommend?"
        
        print(f"\n🔍 Testing Retailer Bias: {query}")
        response = await self.send_chat_message(thread_id, query)
        
        if response:
            analysis = self.analyze_response_for_final_sweep(response)
            
            # Check for Bunnings brand preference
            bunnings_brands = ["zenith", "pryda", "bremick"]
            bunnings_brand_mentions = [brand for brand in bunnings_brands if brand in analysis["brand_mentions"]]
            
            # Determine test status
            status = "PASS" if (
                analysis["response_length"] > 50 and
                ("bunnings" in analysis["brand_mentions"] or len(bunnings_brand_mentions) > 0)
            ) else "FAIL"
            
            self.log_test("Retailer Bias Test", status, {
                **analysis,
                "query": query,
                "bunnings_brands_mentioned": bunnings_brand_mentions,
                "response_preview": (response.get("content", "") or response.get("response", ""))[:200] + "..."
            })
        else:
            self.log_test("Retailer Bias Test", "FAIL", {
                "query": query,
                "error": "No response received"
            })
    
    async def test_alternative_chat_endpoint(self):
        """Test the alternative /api/chat endpoint"""
        query = "What is the load capacity of a Pryda bracing anchor?"
        
        print(f"\n🔍 Testing Alternative Chat Endpoint: {query}")
        
        try:
            payload = {"message": query, "session_id": "test-final-sweep"}
            async with self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    analysis = self.analyze_response_for_final_sweep(data)
                    
                    status = "PASS" if analysis["response_length"] > 50 else "FAIL"
                    
                    self.log_test("Alternative Chat Endpoint", status, {
                        **analysis,
                        "query": query,
                        "endpoint": "/api/chat",
                        "response_preview": (data.get("response", "") or data.get("answer", ""))[:200] + "..."
                    })
                else:
                    error_text = await response.text()
                    self.log_test("Alternative Chat Endpoint", "FAIL", {
                        "status_code": response.status,
                        "error": error_text
                    })
        except Exception as e:
            self.log_test("Alternative Chat Endpoint", "FAIL", {
                "error": str(e)
            })
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("🎯 STRYDA RAG BACKEND TEST SUMMARY - Operation Final Sweep Verification")
        print("="*80)
        
        passed = len([r for r in self.test_results if r["status"] == "PASS"])
        failed = len([r for r in self.test_results if r["status"] == "FAIL"])
        total = len(self.test_results)
        
        print(f"\n📊 Overall Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        print(f"\n✅ PASSED TESTS ({passed}):")
        for result in self.test_results:
            if result["status"] == "PASS":
                print(f"   • {result['test_name']}")
        
        if failed > 0:
            print(f"\n❌ FAILED TESTS ({failed}):")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"   • {result['test_name']}")
                    if result["details"].get("error"):
                        print(f"     Error: {result['details']['error']}")
        
        # Final Sweep specific analysis
        print(f"\n🔍 FINAL SWEEP ANALYSIS:")
        final_sweep_sources = []
        brand_mentions = set()
        
        for result in self.test_results:
            details = result["details"]
            if details.get("final_sweep_sources"):
                final_sweep_sources.extend(details["final_sweep_sources"])
            if details.get("brand_mentions"):
                brand_mentions.update(details["brand_mentions"])
        
        print(f"   • Final Sweep Sources Found: {len(set(final_sweep_sources))}")
        print(f"   • Brand Mentions: {list(brand_mentions)}")
        
        # Verdict
        critical_tests = ["Pryda Bracing Query", "SPAX Timber Query", "Bremick Anchor Query", "Retailer Bias Test"]
        critical_passed = len([r for r in self.test_results if r["test_name"] in critical_tests and r["status"] == "PASS"])
        
        print(f"\n🏆 FINAL VERDICT:")
        if critical_passed >= 3:
            print("   ✅ OPERATION FINAL SWEEP: SUCCESS")
            print("   The RAG system is successfully retrieving brand-specific information.")
        elif critical_passed >= 2:
            print("   ⚠️ OPERATION FINAL SWEEP: PARTIAL SUCCESS")
            print("   Some brand queries working, but improvements needed.")
        else:
            print("   ❌ OPERATION FINAL SWEEP: FAILED")
            print("   RAG system not retrieving expected brand-specific information.")

async def main():
    """Main test execution"""
    print("🚀 Starting STRYDA RAG Backend Testing - Operation Final Sweep Verification")
    print(f"🎯 Backend URL: {BACKEND_URL}")
    print(f"⏰ Test Started: {datetime.now().isoformat()}")
    
    async with STRYDABackendTester() as tester:
        # Test 1: Health check (if available)
        await tester.test_health_check()
        
        # Test 2: Try alternative chat endpoint first
        await tester.test_alternative_chat_endpoint()
        
        # Test 3: Create thread for message-based testing
        thread_id = await tester.create_thread()
        
        if thread_id:
            # Test 4-7: The four specific queries from review request
            await tester.test_pryda_bracing_query(thread_id)
            await tester.test_spax_timber_query(thread_id)
            await tester.test_bremick_anchor_query(thread_id)
            await tester.test_retailer_bias(thread_id)
        else:
            print("⚠️ Could not create thread, skipping message-based tests")
        
        # Print final summary
        tester.print_summary()

if __name__ == "__main__":
    asyncio.run(main())