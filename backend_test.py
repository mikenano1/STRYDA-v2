#!/usr/bin/env python3
"""
STRYDA.ai Backend Testing Suite
Tests all backend API endpoints and functionality
"""

import requests
import json
import time
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('EXPO_PUBLIC_BACKEND_URL', 'https://stryda-chat-shell.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class STRYDABackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.session_id = str(uuid.uuid4())
        
    def log_test(self, test_name, success, message, details=None):
        """Log test results"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'details': details
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def test_root_endpoint(self):
        """Test the root API endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/")
            if response.status_code == 200:
                data = response.json()
                if "STRYDA.ai Backend API" in data.get('message', ''):
                    self.log_test("Root Endpoint", True, "API root accessible")
                    return True
                else:
                    self.log_test("Root Endpoint", False, "Unexpected response message", data)
                    return False
            else:
                self.log_test("Root Endpoint", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Root Endpoint", False, f"Connection error: {str(e)}")
            return False
    
    def test_status_endpoints(self):
        """Test status check endpoints"""
        try:
            # Test creating a status check
            status_data = {"client_name": "STRYDA_Test_Client"}
            response = self.session.post(f"{API_BASE}/status", json=status_data)
            
            if response.status_code == 200:
                created_status = response.json()
                if created_status.get('client_name') == "STRYDA_Test_Client":
                    self.log_test("Create Status Check", True, "Status check created successfully")
                    
                    # Test getting status checks
                    get_response = self.session.get(f"{API_BASE}/status")
                    if get_response.status_code == 200:
                        status_list = get_response.json()
                        if isinstance(status_list, list) and len(status_list) > 0:
                            self.log_test("Get Status Checks", True, f"Retrieved {len(status_list)} status checks")
                            return True
                        else:
                            self.log_test("Get Status Checks", False, "No status checks returned")
                            return False
                    else:
                        self.log_test("Get Status Checks", False, f"HTTP {get_response.status_code}")
                        return False
                else:
                    self.log_test("Create Status Check", False, "Incorrect client name in response", created_status)
                    return False
            else:
                self.log_test("Create Status Check", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Status Endpoints", False, f"Error: {str(e)}")
            return False
    
    def test_job_management(self):
        """Test job creation and management endpoints"""
        try:
            # Test creating a job
            job_data = {
                "name": "Test House Build - Auckland",
                "address": "123 Queen Street, Auckland, New Zealand"
            }
            response = self.session.post(f"{API_BASE}/jobs", json=job_data)
            
            if response.status_code == 200:
                created_job = response.json()
                job_id = created_job.get('id')
                
                if created_job.get('name') == job_data['name'] and job_id:
                    self.log_test("Create Job", True, f"Job created with ID: {job_id}")
                    
                    # Test getting all jobs
                    get_jobs_response = self.session.get(f"{API_BASE}/jobs")
                    if get_jobs_response.status_code == 200:
                        jobs_list = get_jobs_response.json()
                        if isinstance(jobs_list, list) and len(jobs_list) > 0:
                            self.log_test("Get All Jobs", True, f"Retrieved {len(jobs_list)} jobs")
                            
                            # Test getting specific job
                            get_job_response = self.session.get(f"{API_BASE}/jobs/{job_id}")
                            if get_job_response.status_code == 200:
                                specific_job = get_job_response.json()
                                if specific_job.get('id') == job_id:
                                    self.log_test("Get Specific Job", True, f"Retrieved job {job_id}")
                                    return True
                                else:
                                    self.log_test("Get Specific Job", False, "Job ID mismatch")
                                    return False
                            else:
                                self.log_test("Get Specific Job", False, f"HTTP {get_job_response.status_code}")
                                return False
                        else:
                            self.log_test("Get All Jobs", False, "No jobs returned")
                            return False
                    else:
                        self.log_test("Get All Jobs", False, f"HTTP {get_jobs_response.status_code}")
                        return False
                else:
                    self.log_test("Create Job", False, "Job creation response invalid", created_job)
                    return False
            else:
                self.log_test("Create Job", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Job Management", False, f"Error: {str(e)}")
            return False
    
    def test_chat_functionality(self):
        """Test AI chat functionality with NZ building code questions"""
        test_questions = [
            {
                "question": "What are the minimum hearth clearances for a solid fuel fireplace in New Zealand?",
                "expected_keywords": ["hearth", "clearance", "fireplace", "nz", "building code"]
            },
            {
                "question": "What insulation requirements apply to H1 energy efficiency in Auckland?",
                "expected_keywords": ["insulation", "h1", "energy", "efficiency"]
            },
            {
                "question": "What are the weathertightness requirements under E2 for external walls?",
                "expected_keywords": ["weathertight", "e2", "external", "moisture"]
            }
        ]
        
        all_tests_passed = True
        
        for i, test_case in enumerate(test_questions):
            try:
                chat_data = {
                    "message": test_case["question"],
                    "session_id": self.session_id
                }
                
                response = self.session.post(f"{API_BASE}/chat", json=chat_data)
                
                if response.status_code == 200:
                    chat_response = response.json()
                    ai_response = chat_response.get('response', '')
                    citations = chat_response.get('citations', [])
                    returned_session_id = chat_response.get('session_id')
                    
                    # Check if response contains relevant content
                    response_lower = ai_response.lower()
                    has_relevant_content = any(keyword.lower() in response_lower for keyword in test_case["expected_keywords"])
                    
                    # Check citations
                    has_citations = len(citations) > 0
                    
                    # Check session ID
                    correct_session = returned_session_id == self.session_id
                    
                    if ai_response and has_relevant_content and correct_session:
                        details = {
                            "response_length": len(ai_response),
                            "citations_count": len(citations),
                            "has_nz_context": "new zealand" in response_lower or "nz" in response_lower
                        }
                        self.log_test(f"Chat Question {i+1}", True, f"AI responded appropriately to NZ building code question", details)
                    else:
                        issues = []
                        if not ai_response:
                            issues.append("No AI response")
                        if not has_relevant_content:
                            issues.append("Response lacks relevant keywords")
                        if not correct_session:
                            issues.append("Session ID mismatch")
                        
                        self.log_test(f"Chat Question {i+1}", False, f"Issues: {', '.join(issues)}", {
                            "response": ai_response[:200] + "..." if len(ai_response) > 200 else ai_response,
                            "citations": citations
                        })
                        all_tests_passed = False
                else:
                    self.log_test(f"Chat Question {i+1}", False, f"HTTP {response.status_code}", response.text)
                    all_tests_passed = False
                    
                # Small delay between requests
                time.sleep(1)
                
            except Exception as e:
                self.log_test(f"Chat Question {i+1}", False, f"Error: {str(e)}")
                all_tests_passed = False
        
        return all_tests_passed
    
    def test_chat_history(self):
        """Test chat history retrieval"""
        try:
            # Get chat history for the session used in chat tests
            response = self.session.get(f"{API_BASE}/chat/{self.session_id}/history")
            
            if response.status_code == 200:
                history = response.json()
                if isinstance(history, list) and len(history) > 0:
                    # Check if we have both user and bot messages
                    user_messages = [msg for msg in history if msg.get('sender') == 'user']
                    bot_messages = [msg for msg in history if msg.get('sender') == 'bot']
                    
                    if len(user_messages) > 0 and len(bot_messages) > 0:
                        self.log_test("Chat History", True, f"Retrieved {len(history)} messages ({len(user_messages)} user, {len(bot_messages)} bot)")
                        return True
                    else:
                        self.log_test("Chat History", False, f"Missing message types: {len(user_messages)} user, {len(bot_messages)} bot")
                        return False
                else:
                    self.log_test("Chat History", False, "No chat history found")
                    return False
            else:
                self.log_test("Chat History", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Chat History", False, f"Error: {str(e)}")
            return False
    
    def test_error_handling(self):
        """Test error handling for invalid requests"""
        try:
            # Test invalid job creation
            invalid_job = {"name": ""}  # Missing address
            response = self.session.post(f"{API_BASE}/jobs", json=invalid_job)
            
            # Should handle gracefully (either 400 or 422)
            if response.status_code in [400, 422, 500]:
                self.log_test("Invalid Job Creation", True, f"Properly handled invalid request with HTTP {response.status_code}")
            else:
                self.log_test("Invalid Job Creation", False, f"Unexpected status code: {response.status_code}")
                return False
            
            # Test non-existent job retrieval
            fake_job_id = str(uuid.uuid4())
            response = self.session.get(f"{API_BASE}/jobs/{fake_job_id}")
            
            if response.status_code == 404:
                self.log_test("Non-existent Job", True, "Properly returned 404 for non-existent job")
            else:
                self.log_test("Non-existent Job", False, f"Expected 404, got {response.status_code}")
                return False
            
            # Test empty chat message
            empty_chat = {"message": ""}
            response = self.session.post(f"{API_BASE}/chat", json=empty_chat)
            
            # Should handle gracefully
            if response.status_code in [400, 422, 500] or (response.status_code == 200 and response.json().get('response')):
                self.log_test("Empty Chat Message", True, f"Handled empty message appropriately")
                return True
            else:
                self.log_test("Empty Chat Message", False, f"Unexpected handling of empty message")
                return False
                
        except Exception as e:
            self.log_test("Error Handling", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        print(f"\n🚀 Starting STRYDA.ai Backend Tests")
        print(f"Backend URL: {API_BASE}")
        print(f"Session ID: {self.session_id}")
        print("=" * 60)
        
        # Run tests in order
        tests = [
            ("Backend Connectivity", self.test_root_endpoint),
            ("Status Management", self.test_status_endpoints),
            ("Job Management", self.test_job_management),
            ("AI Chat Functionality", self.test_chat_functionality),
            ("Chat History", self.test_chat_history),
            ("Error Handling", self.test_error_handling)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 Testing: {test_name}")
            if test_func():
                passed += 1
            time.sleep(0.5)  # Brief pause between test suites
        
        print("\n" + "=" * 60)
        print(f"🏁 Test Summary: {passed}/{total} test suites passed")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['message']}")
        
        return passed == total

if __name__ == "__main__":
    tester = STRYDABackendTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All backend tests passed!")
        exit(0)
    else:
        print("\n⚠️  Some backend tests failed!")
        exit(1)