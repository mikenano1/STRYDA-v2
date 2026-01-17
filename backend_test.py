#!/usr/bin/env python3
"""
STRYDA RAG Backend Testing - Protocol V2.0 Infrastructure
Testing Agent: Backend Testing Agent
Date: 2025-01-04
Focus: Protocol V2.0 infrastructure verification
"""

import requests
import json
import time
from typing import Dict, Any, List

# Test Configuration
BASE_URL = "https://strydahub.preview.emergentagent.com"
CHAT_URL = f"{BASE_URL}/api/chat"
SESSION_ID = "test-v2-infra"

class ProtocolV2Tester:
    def __init__(self):
        self.results = []
        self.base_url = BASE_URL
        
    def log_result(self, test_name: str, status: str, details: str, response_time: float = None):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "response_time_ms": int(response_time * 1000) if response_time else None,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
        if response_time:
            print(f"   Response Time: {int(response_time * 1000)}ms")
        print()

    def test_health_check(self):
        """Test 1: Health Check - GET /health"""
        print("🔍 Testing Health Check Endpoint...")
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/health", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("ok") == True:
                        self.log_result("Health Check", "PASS", 
                                      f"Status: 200 OK, Response: {data}", response_time)
                    else:
                        self.log_result("Health Check", "FAIL", 
                                      f"Status: 200 but ok != true, Response: {data}", response_time)
                except json.JSONDecodeError:
                    self.log_result("Health Check", "FAIL", 
                                  f"Status: 200 but invalid JSON: {response.text[:100]}", response_time)
            else:
                self.log_result("Health Check", "FAIL", 
                              f"Status: {response.status_code}, Response: {response.text[:100]}", response_time)
                
        except Exception as e:
            self.log_result("Health Check", "FAIL", f"Exception: {str(e)}")

    def test_feedback_stats(self):
        """Test 2: Feedback API - Stats - GET /api/feedback/stats"""
        print("🔍 Testing Feedback Stats API...")
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/api/feedback/stats", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("ok") == True and "stats" in data and "unresolved_feedback" in data["stats"]:
                        self.log_result("Feedback Stats API", "PASS", 
                                      f"Status: 200 OK, Stats: {data['stats']}", response_time)
                    else:
                        self.log_result("Feedback Stats API", "FAIL", 
                                      f"Status: 200 but missing required fields, Response: {data}", response_time)
                except json.JSONDecodeError:
                    self.log_result("Feedback Stats API", "FAIL", 
                                  f"Status: 200 but invalid JSON: {response.text[:100]}", response_time)
            else:
                self.log_result("Feedback Stats API", "FAIL", 
                              f"Status: {response.status_code}, Response: {response.text[:100]}", response_time)
                
        except Exception as e:
            self.log_result("Feedback Stats API", "FAIL", f"Exception: {str(e)}")

    def test_feedback_flagged(self):
        """Test 3: Feedback API - Flagged Chunks - GET /api/feedback/flagged"""
        print("🔍 Testing Feedback Flagged API...")
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/api/feedback/flagged", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("ok") == True and "flagged_chunks" in data and isinstance(data["flagged_chunks"], list):
                        self.log_result("Feedback Flagged API", "PASS", 
                                      f"Status: 200 OK, Flagged chunks: {len(data['flagged_chunks'])} items", response_time)
                    else:
                        self.log_result("Feedback Flagged API", "FAIL", 
                                      f"Status: 200 but missing required fields, Response: {data}", response_time)
                except json.JSONDecodeError:
                    self.log_result("Feedback Flagged API", "FAIL", 
                                  f"Status: 200 but invalid JSON: {response.text[:100]}", response_time)
            else:
                self.log_result("Feedback Flagged API", "FAIL", 
                              f"Status: {response.status_code}, Response: {response.text[:100]}", response_time)
                
        except Exception as e:
            self.log_result("Feedback Flagged API", "FAIL", f"Exception: {str(e)}")

    def test_feedback_submit(self):
        """Test 4: Feedback API - Submit - POST /api/feedback"""
        print("🔍 Testing Feedback Submit API...")
        try:
            payload = {
                "chunk_id": "00000000-0000-0000-0000-000000000000",
                "feedback_type": "incorrect", 
                "feedback_note": "Test feedback"
            }
            
            start_time = time.time()
            response = requests.post(f"{self.base_url}/api/feedback", 
                                   json=payload, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Expecting success=False since chunk doesn't exist
                    if data.get("success") == False:
                        self.log_result("Feedback Submit API", "PASS", 
                                      f"Status: 200 OK, Expected failure (chunk not found): {data}", response_time)
                    else:
                        self.log_result("Feedback Submit API", "PARTIAL", 
                                      f"Status: 200 but unexpected success, Response: {data}", response_time)
                except json.JSONDecodeError:
                    self.log_result("Feedback Submit API", "FAIL", 
                                  f"Status: 200 but invalid JSON: {response.text[:100]}", response_time)
            else:
                self.log_result("Feedback Submit API", "FAIL", 
                              f"Status: {response.status_code}, Response: {response.text[:100]}", response_time)
                
        except Exception as e:
            self.log_result("Feedback Submit API", "FAIL", f"Exception: {str(e)}")

    def test_chat_endpoint(self):
        """Test 5: Chat Endpoint - POST /api/chat"""
        print("🔍 Testing Chat Endpoint...")
        try:
            payload = {
                "message": "What is the minimum pitch for corrugate roofing?",
                "session_id": SESSION_ID
            }
            
            start_time = time.time()
            response = requests.post(CHAT_URL, json=payload, timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Check for different possible response field names
                    answer_field = None
                    answer_text = ""
                    for field in ["answer", "response", "message", "text"]:
                        if field in data and data[field]:
                            answer_field = field
                            answer_text = data[field]
                            break
                    
                    if answer_field and "citations" in data:
                        answer_length = len(answer_text)
                        citations_count = len(data.get("citations", []))
                        model_used = data.get("model", "unknown")
                        intent = data.get("intent", "unknown")
                        
                        self.log_result("Chat Endpoint", "PASS", 
                                      f"Status: 200 OK, Answer: {answer_length} chars, Citations: {citations_count}, Model: {model_used}, Intent: {intent}", 
                                      response_time)
                    else:
                        missing_fields = []
                        if not answer_field:
                            missing_fields.append("answer/response field")
                        if "citations" not in data:
                            missing_fields.append("citations")
                        
                        self.log_result("Chat Endpoint", "FAIL", 
                                      f"Status: 200 but missing fields: {missing_fields}, Available fields: {list(data.keys())}", response_time)
                except json.JSONDecodeError:
                    self.log_result("Chat Endpoint", "FAIL", 
                                  f"Status: 200 but invalid JSON: {response.text[:100]}", response_time)
            else:
                self.log_result("Chat Endpoint", "FAIL", 
                              f"Status: {response.status_code}, Response: {response.text[:100]}", response_time)
                
        except Exception as e:
            self.log_result("Chat Endpoint", "FAIL", f"Exception: {str(e)}")

    def test_existing_endpoints(self):
        """Test existing endpoints to verify backend is operational"""
        print("🔍 Testing Existing API Endpoints...")
        try:
            # Test root API endpoint
            start_time = time.time()
            response = requests.get(f"{self.base_url}/api/", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.log_result("API Root Endpoint", "PASS", 
                                  f"Status: 200 OK, Message: {data.get('message', 'No message')}", response_time)
                except json.JSONDecodeError:
                    self.log_result("API Root Endpoint", "PASS", 
                                  f"Status: 200 OK, Response: {response.text[:100]}", response_time)
            else:
                self.log_result("API Root Endpoint", "FAIL", 
                              f"Status: {response.status_code}, Response: {response.text[:100]}", response_time)
                
        except Exception as e:
            self.log_result("API Root Endpoint", "FAIL", f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all Protocol V2.0 tests"""
        print("=" * 80)
        print("🚀 STRYDA RAG Backend Testing - Protocol V2.0 Infrastructure")
        print(f"Backend URL: {self.base_url}")
        print(f"Test Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()
        
        # Test existing endpoints first to verify backend is running
        self.test_existing_endpoints()
        
        # Protocol V2.0 specific tests
        self.test_health_check()
        self.test_feedback_stats()
        self.test_feedback_flagged()
        self.test_feedback_submit()
        self.test_chat_endpoint()
        
        # Summary
        print("=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        passed = len([r for r in self.results if r["status"] == "PASS"])
        failed = len([r for r in self.results if r["status"] == "FAIL"])
        partial = len([r for r in self.results if r["status"] == "PARTIAL"])
        total = len(self.results)
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️ Partial: {partial}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        print()
        
        # Detailed results
        print("📋 DETAILED RESULTS:")
        for result in self.results:
            status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            print(f"{status_icon} {result['test']}: {result['status']}")
            if result["details"]:
                print(f"   {result['details']}")
        
        # Protocol V2.0 verdict
        print(f"\n🎯 PROTOCOL V2.0 VERDICT:")
        
        # Check specific Protocol V2.0 endpoints
        v2_tests = [r for r in self.results if "Feedback" in r["test"] or "Chat Endpoint" in r["test"]]
        v2_passed = len([r for r in v2_tests if r["status"] == "PASS"])
        v2_total = len(v2_tests)
        
        if v2_passed == v2_total:
            print("✅ PROTOCOL V2.0 INFRASTRUCTURE WORKING")
        elif v2_passed > 0:
            print("⚠️  PROTOCOL V2.0 PARTIALLY WORKING")
        else:
            print("❌ PROTOCOL V2.0 INFRASTRUCTURE NOT WORKING")
        
        return self.results

def main():
    """Main test execution"""
    tester = ProtocolV2Tester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    failed_tests = [r for r in results if r["status"] == "FAIL"]
    if failed_tests:
        print(f"\n❌ {len(failed_tests)} tests failed")
        return 1
    else:
        print(f"\n✅ All tests passed!")
        return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)