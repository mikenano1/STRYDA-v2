#!/usr/bin/env python3
"""
STRYDA Backend Testing Suite - Gemini Migration & Regulation Compliance
Tests the backend API endpoints for proper functionality after Gemini migration.
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, List
import sys
import os

# Backend URL from environment
BACKEND_URL = "https://nzconstructai.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class STRYDABackendTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'Content-Type': 'application/json'}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, status: str, details: str = "", response_data: Any = None):
        """Log test results"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "response_data": response_data
        }
        self.test_results.append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
        print()
    
    async def test_health_check(self):
        """Test 1: Health Check - GET /health"""
        try:
            async with self.session.get(f"{BACKEND_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test("Health Check", "PASS", f"Status: {response.status}", data)
                    return True
                else:
                    self.log_test("Health Check", "FAIL", f"Expected 200, got {response.status}")
                    return False
        except Exception as e:
            # Try alternative health endpoints
            try:
                async with self.session.get(f"{API_BASE}/") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log_test("Health Check (Alternative)", "PASS", f"Root endpoint working: {response.status}", data)
                        return True
                    else:
                        self.log_test("Health Check", "FAIL", f"Root endpoint failed: {response.status}")
                        return False
            except Exception as e2:
                self.log_test("Health Check", "FAIL", f"Connection error: {str(e2)}")
                return False
    
    async def test_admin_config(self):
        """Test 2: Admin Config - GET /admin/config"""
        try:
            async with self.session.get(f"{BACKEND_URL}/admin/config") as response:
                if response.status == 200:
                    data = await response.json()
                    # Check for Gemini models
                    models = data.get('models', {})
                    if 'gemini-2.5-flash' in str(models) and 'gemini-2.5-pro' in str(models):
                        self.log_test("Admin Config", "PASS", "Gemini models configured correctly", data)
                        return True
                    else:
                        self.log_test("Admin Config", "FAIL", f"Gemini models not found in config: {models}")
                        return False
                else:
                    self.log_test("Admin Config", "FAIL", f"Expected 200, got {response.status}")
                    return False
        except Exception as e:
            self.log_test("Admin Config", "FAIL", f"Endpoint not found or error: {str(e)}")
            return False
    
    async def test_gate_logic_multi_turn(self):
        """Test 3: Gate Logic (Multi-turn conversation)"""
        session_id = "test-gate-gemini"
        
        # First question - should trigger gate
        try:
            payload = {
                "message": "What is the minimum pitch for corrugated iron?",
                "session_id": session_id
            }
            
            async with self.session.post(f"{API_BASE}/chat", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    response_text = data.get('response', '').lower()
                    
                    # Check if response asks for more details (gate trigger)
                    gate_keywords = ['roof profile', 'underlay', 'lap direction', 'more information', 'details']
                    if any(keyword in response_text for keyword in gate_keywords):
                        self.log_test("Gate Logic - First Question", "PASS", "Gate triggered correctly", data)
                        
                        # Second question - provide details
                        payload2 = {
                            "message": "It is corrugate, RU24 underlay, lap direction.",
                            "session_id": session_id
                        }
                        
                        async with self.session.post(f"{API_BASE}/chat", json=payload2) as response2:
                            if response2.status == 200:
                                data2 = await response2.json()
                                response_text2 = data2.get('response', '').lower()
                                
                                # Check for specific answer (likely 8 degrees)
                                if '8' in response_text2 and ('degree' in response_text2 or 'pitch' in response_text2):
                                    self.log_test("Gate Logic - Second Question", "PASS", "Final answer provided correctly", data2)
                                    return True
                                else:
                                    self.log_test("Gate Logic - Second Question", "FAIL", f"Expected pitch answer, got: {response_text2[:200]}")
                                    return False
                            else:
                                self.log_test("Gate Logic - Second Question", "FAIL", f"Status: {response2.status}")
                                return False
                    else:
                        self.log_test("Gate Logic - First Question", "FAIL", f"Gate not triggered. Response: {response_text[:200]}")
                        return False
                else:
                    self.log_test("Gate Logic - First Question", "FAIL", f"Status: {response.status}")
                    return False
        except Exception as e:
            self.log_test("Gate Logic", "FAIL", f"Error: {str(e)}")
            return False
    
    async def test_regulatory_check_h1_schedule(self):
        """Test 4: Regulatory Check (H1 Schedule Method)"""
        try:
            payload = {
                "message": "Can I use the schedule method for H1 compliance?",
                "session_id": "test-reg-gemini"
            }
            
            async with self.session.post(f"{API_BASE}/chat", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    response_text = data.get('response', '').lower()
                    
                    # Check for warning about schedule method
                    warning_keywords = ['not permitted', 'no longer valid', 'not allowed', 'deprecated', 'warning', 'nov 2025']
                    if any(keyword in response_text for keyword in warning_keywords):
                        self.log_test("Regulatory Check - H1 Schedule", "PASS", "Warning about schedule method provided", data)
                        return True
                    else:
                        self.log_test("Regulatory Check - H1 Schedule", "FAIL", f"No warning about schedule method. Response: {response_text[:200]}")
                        return False
                else:
                    self.log_test("Regulatory Check - H1 Schedule", "FAIL", f"Status: {response.status}")
                    return False
        except Exception as e:
            self.log_test("Regulatory Check - H1 Schedule", "FAIL", f"Error: {str(e)}")
            return False
    
    async def test_strict_compliance_gemini_pro(self):
        """Test 5: Strict Compliance (Gemini Pro with citations)"""
        try:
            payload = {
                "message": "What is the stud spacing for a 2.4m wall in high wind zone?",
                "session_id": "test-strict-gemini"
            }
            
            async with self.session.post(f"{API_BASE}/chat", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    response_text = data.get('response', '')
                    citations = data.get('citations', [])
                    
                    # Check for detailed answer with citations
                    if citations and len(citations) > 0:
                        self.log_test("Strict Compliance - Citations", "PASS", f"Citations provided: {len(citations)}", data)
                        
                        # Check for technical details in response
                        if 'stud' in response_text.lower() and ('spacing' in response_text.lower() or 'mm' in response_text.lower()):
                            self.log_test("Strict Compliance - Technical Answer", "PASS", "Detailed technical answer provided", data)
                            return True
                        else:
                            self.log_test("Strict Compliance - Technical Answer", "FAIL", f"Insufficient technical detail: {response_text[:200]}")
                            return False
                    else:
                        self.log_test("Strict Compliance - Citations", "FAIL", "No citations provided")
                        return False
                else:
                    self.log_test("Strict Compliance", "FAIL", f"Status: {response.status}")
                    return False
        except Exception as e:
            self.log_test("Strict Compliance", "FAIL", f"Error: {str(e)}")
            return False
    
    async def test_basic_chat_functionality(self):
        """Test basic chat functionality"""
        try:
            payload = {
                "message": "Hello, can you help me with building questions?",
                "session_id": "test-basic"
            }
            
            async with self.session.post(f"{API_BASE}/chat", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    response_text = data.get('response', '')
                    
                    if response_text and len(response_text) > 10:
                        self.log_test("Basic Chat Functionality", "PASS", "Chat endpoint responding", data)
                        return True
                    else:
                        self.log_test("Basic Chat Functionality", "FAIL", "Empty or minimal response")
                        return False
                else:
                    self.log_test("Basic Chat Functionality", "FAIL", f"Status: {response.status}")
                    return False
        except Exception as e:
            self.log_test("Basic Chat Functionality", "FAIL", f"Error: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting STRYDA Backend Testing Suite - Gemini Migration & Regulation Compliance")
        print("=" * 80)
        print()
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Admin Config", self.test_admin_config),
            ("Basic Chat", self.test_basic_chat_functionality),
            ("Gate Logic (Multi-turn)", self.test_gate_logic_multi_turn),
            ("Regulatory Check (H1 Schedule)", self.test_regulatory_check_h1_schedule),
            ("Strict Compliance (Gemini Pro)", self.test_strict_compliance_gemini_pro),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"Running: {test_name}")
            try:
                result = await test_func()
                if result:
                    passed += 1
            except Exception as e:
                self.log_test(test_name, "FAIL", f"Unexpected error: {str(e)}")
            
            # Small delay between tests
            await asyncio.sleep(1)
        
        print("=" * 80)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed!")
        elif passed >= total * 0.7:
            print("⚠️  Most tests passed, some issues found")
        else:
            print("❌ Multiple test failures detected")
        
        return passed, total, self.test_results

async def main():
    """Main test runner"""
    async with STRYDABackendTester() as tester:
        passed, total, results = await tester.run_all_tests()
        
        # Save detailed results
        with open('/app/test_results_detailed.json', 'w') as f:
            json.dump({
                'summary': {
                    'passed': passed,
                    'total': total,
                    'success_rate': passed / total if total > 0 else 0
                },
                'tests': results
            }, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: /app/test_results_detailed.json")
        
        return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)