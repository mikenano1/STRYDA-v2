#!/usr/bin/env python3
"""
STRYDA.ai User Experience Test
Simulates the exact user experience to identify why STRYDA might not be responding
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
BACKEND_URL = os.getenv('EXPO_PUBLIC_BACKEND_URL', 'https://techscraper.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class UserExperienceTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        
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
        if details:
            if success:
                print(f"   📊 Details: {details}")
            else:
                print(f"   🔍 Error Details: {details}")
    
    def test_frontend_backend_integration(self):
        """Test the exact integration that frontend would use"""
        try:
            print("\n🔗 Testing Frontend-Backend Integration...")
            
            # This simulates exactly what the frontend does
            session_id = f"mobile_session_{uuid.uuid4()}"
            
            # Test the exact endpoint and payload structure the frontend uses
            frontend_payload = {
                "message": "What clearances do I need for a fireplace?",
                "session_id": session_id,
                "enable_compliance_analysis": True,
                "enable_query_processing": True
            }
            
            # Add headers that frontend might send
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'STRYDA-Mobile-App/1.0'
            }
            
            start_time = time.time()
            response = self.session.post(
                f"{API_BASE}/chat/enhanced", 
                json=frontend_payload, 
                headers=headers,
                timeout=45  # Longer timeout for mobile scenarios
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # Check all the fields frontend expects
                expected_fields = ['response', 'citations', 'session_id', 'confidence_score', 'sources_used', 'processing_time_ms']
                missing_fields = [field for field in expected_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Frontend Integration", False, f"Missing expected fields: {missing_fields}")
                    return False
                
                ai_response = data.get('response', '')
                citations = data.get('citations', [])
                returned_session = data.get('session_id', '')
                
                # Validate response quality (what user would expect)
                if (ai_response and 
                    len(ai_response) > 200 and  # Substantial response
                    returned_session == session_id and  # Session consistency
                    ('fireplace' in ai_response.lower() or 'hearth' in ai_response.lower()) and  # Relevant content
                    ('clearance' in ai_response.lower() or 'distance' in ai_response.lower())):  # Answers the question
                    
                    details = {
                        "response_length": len(ai_response),
                        "citations_count": len(citations),
                        "response_time_ms": response_time,
                        "session_consistency": returned_session == session_id,
                        "has_nz_context": any(term in ai_response.lower() for term in ['new zealand', 'nz', 'building code']),
                        "confidence_score": data.get('confidence_score', 0),
                        "sources_count": len(data.get('sources_used', []))
                    }
                    
                    self.log_test("Frontend Integration", True, "Perfect integration - user would get comprehensive response", details)
                    return True
                else:
                    issues = []
                    if not ai_response or len(ai_response) < 200:
                        issues.append("Response too short or empty")
                    if returned_session != session_id:
                        issues.append("Session ID mismatch")
                    if not any(term in ai_response.lower() for term in ['fireplace', 'hearth']):
                        issues.append("Response not relevant to fireplace")
                    if not any(term in ai_response.lower() for term in ['clearance', 'distance']):
                        issues.append("Response doesn't answer clearance question")
                    
                    self.log_test("Frontend Integration", False, f"Response quality issues: {', '.join(issues)}", {
                        "response_preview": ai_response[:300] + "..." if len(ai_response) > 300 else ai_response,
                        "session_sent": session_id,
                        "session_received": returned_session
                    })
                    return False
            else:
                self.log_test("Frontend Integration", False, f"HTTP {response.status_code}", {
                    "error_response": response.text[:500],
                    "response_time_ms": response_time
                })
                return False
                
        except requests.exceptions.Timeout:
            self.log_test("Frontend Integration", False, "Request timed out - user would see no response")
            return False
        except Exception as e:
            self.log_test("Frontend Integration", False, f"Connection error: {str(e)}")
            return False
    
    def test_mobile_app_scenarios(self):
        """Test scenarios specific to mobile app usage"""
        try:
            print("\n📱 Testing Mobile App Scenarios...")
            
            # Scenario 1: Quick question from home screen
            quick_questions = [
                "Hearth clearances",
                "H1 insulation requirements", 
                "E2 weathertightness",
                "Building consent process"
            ]
            
            all_passed = True
            
            for i, question in enumerate(quick_questions):
                session_id = f"quick_question_{i}_{uuid.uuid4()}"
                
                payload = {
                    "message": question,
                    "session_id": session_id
                }
                
                try:
                    start_time = time.time()
                    response = self.session.post(f"{API_BASE}/chat/enhanced", json=payload, timeout=30)
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status_code == 200:
                        data = response.json()
                        ai_response = data.get('response', '')
                        
                        if ai_response and len(ai_response) > 100:
                            self.log_test(f"Quick Question: {question}", True, f"Got response ({len(ai_response)} chars in {response_time:.0f}ms)")
                        else:
                            self.log_test(f"Quick Question: {question}", False, f"Poor response: '{ai_response[:100]}...'")
                            all_passed = False
                    else:
                        self.log_test(f"Quick Question: {question}", False, f"HTTP {response.status_code}")
                        all_passed = False
                        
                except requests.exceptions.Timeout:
                    self.log_test(f"Quick Question: {question}", False, "Timeout - mobile user would give up")
                    all_passed = False
                except Exception as e:
                    self.log_test(f"Quick Question: {question}", False, f"Error: {str(e)}")
                    all_passed = False
                
                time.sleep(1)  # Simulate user pause between questions
            
            return all_passed
            
        except Exception as e:
            self.log_test("Mobile App Scenarios", False, f"Error: {str(e)}")
            return False
    
    def test_network_conditions(self):
        """Test under various network conditions that mobile users might experience"""
        try:
            print("\n🌐 Testing Network Conditions...")
            
            # Test with shorter timeouts to simulate poor mobile connection
            test_cases = [
                {"timeout": 5, "name": "Poor Connection (5s timeout)"},
                {"timeout": 10, "name": "Moderate Connection (10s timeout)"},
                {"timeout": 20, "name": "Good Connection (20s timeout)"}
            ]
            
            question = "What clearances do I need for a fireplace?"
            
            for test_case in test_cases:
                try:
                    payload = {
                        "message": question,
                        "session_id": f"network_test_{test_case['timeout']}"
                    }
                    
                    start_time = time.time()
                    response = self.session.post(
                        f"{API_BASE}/chat/enhanced", 
                        json=payload, 
                        timeout=test_case['timeout']
                    )
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status_code == 200:
                        data = response.json()
                        ai_response = data.get('response', '')
                        
                        if ai_response and len(ai_response) > 100:
                            self.log_test(test_case['name'], True, f"Success in {response_time:.0f}ms")
                        else:
                            self.log_test(test_case['name'], False, "Empty or poor response")
                    else:
                        self.log_test(test_case['name'], False, f"HTTP {response.status_code}")
                        
                except requests.exceptions.Timeout:
                    self.log_test(test_case['name'], False, f"Timeout after {test_case['timeout']}s - user would see 'no response'")
                except Exception as e:
                    self.log_test(test_case['name'], False, f"Network error: {str(e)}")
                
                time.sleep(2)
            
            return True
            
        except Exception as e:
            self.log_test("Network Conditions", False, f"Error: {str(e)}")
            return False
    
    def test_concurrent_users(self):
        """Test if concurrent users might be causing issues"""
        try:
            print("\n👥 Testing Concurrent User Scenarios...")
            
            import threading
            import queue
            
            results_queue = queue.Queue()
            
            def make_chat_request(user_id):
                try:
                    payload = {
                        "message": f"What are fireplace clearances? (User {user_id})",
                        "session_id": f"concurrent_user_{user_id}"
                    }
                    
                    start_time = time.time()
                    response = requests.post(f"{API_BASE}/chat/enhanced", json=payload, timeout=30)
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status_code == 200:
                        data = response.json()
                        ai_response = data.get('response', '')
                        results_queue.put({
                            'user_id': user_id,
                            'success': True,
                            'response_length': len(ai_response),
                            'response_time': response_time
                        })
                    else:
                        results_queue.put({
                            'user_id': user_id,
                            'success': False,
                            'error': f"HTTP {response.status_code}"
                        })
                        
                except Exception as e:
                    results_queue.put({
                        'user_id': user_id,
                        'success': False,
                        'error': str(e)
                    })
            
            # Simulate 3 concurrent users
            threads = []
            for i in range(3):
                thread = threading.Thread(target=make_chat_request, args=(i+1,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Collect results
            results = []
            while not results_queue.empty():
                results.append(results_queue.get())
            
            successful_requests = [r for r in results if r['success']]
            failed_requests = [r for r in results if not r['success']]
            
            if len(successful_requests) == 3:
                avg_response_time = sum(r['response_time'] for r in successful_requests) / len(successful_requests)
                avg_response_length = sum(r['response_length'] for r in successful_requests) / len(successful_requests)
                
                details = {
                    "successful_requests": len(successful_requests),
                    "failed_requests": len(failed_requests),
                    "avg_response_time_ms": avg_response_time,
                    "avg_response_length": avg_response_length
                }
                
                self.log_test("Concurrent Users", True, "All concurrent requests succeeded", details)
                return True
            else:
                details = {
                    "successful_requests": len(successful_requests),
                    "failed_requests": len(failed_requests),
                    "failures": [r['error'] for r in failed_requests]
                }
                
                self.log_test("Concurrent Users", False, f"Some concurrent requests failed", details)
                return False
                
        except Exception as e:
            self.log_test("Concurrent Users", False, f"Error: {str(e)}")
            return False
    
    def test_session_persistence(self):
        """Test if session persistence issues might be causing problems"""
        try:
            print("\n💾 Testing Session Persistence...")
            
            session_id = f"persistence_test_{uuid.uuid4()}"
            
            # Send first message
            first_message = {
                "message": "What are fireplace clearances?",
                "session_id": session_id
            }
            
            response1 = self.session.post(f"{API_BASE}/chat/enhanced", json=first_message, timeout=20)
            
            if response1.status_code != 200:
                self.log_test("Session Persistence", False, f"First message failed: HTTP {response1.status_code}")
                return False
            
            time.sleep(2)  # Simulate user pause
            
            # Send follow-up message
            followup_message = {
                "message": "What about for timber floors specifically?",
                "session_id": session_id
            }
            
            response2 = self.session.post(f"{API_BASE}/chat/enhanced", json=followup_message, timeout=20)
            
            if response2.status_code != 200:
                self.log_test("Session Persistence", False, f"Follow-up message failed: HTTP {response2.status_code}")
                return False
            
            # Check chat history
            time.sleep(1)
            history_response = self.session.get(f"{API_BASE}/chat/{session_id}/history", timeout=10)
            
            if history_response.status_code == 200:
                history = history_response.json()
                
                if isinstance(history, list) and len(history) >= 4:  # 2 user + 2 bot messages
                    user_messages = [msg for msg in history if msg.get('sender') == 'user']
                    bot_messages = [msg for msg in history if msg.get('sender') == 'bot']
                    
                    details = {
                        "total_messages": len(history),
                        "user_messages": len(user_messages),
                        "bot_messages": len(bot_messages),
                        "session_id": session_id
                    }
                    
                    if len(user_messages) >= 2 and len(bot_messages) >= 2:
                        self.log_test("Session Persistence", True, "Session maintained across multiple messages", details)
                        return True
                    else:
                        self.log_test("Session Persistence", False, "Missing messages in session", details)
                        return False
                else:
                    self.log_test("Session Persistence", False, f"Insufficient messages in history: {len(history) if isinstance(history, list) else 'not a list'}")
                    return False
            else:
                self.log_test("Session Persistence", False, f"History retrieval failed: HTTP {history_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Session Persistence", False, f"Error: {str(e)}")
            return False
    
    def run_user_experience_tests(self):
        """Run all user experience tests"""
        print(f"\n🎯 STRYDA.ai User Experience Testing")
        print(f"Backend URL: {API_BASE}")
        print(f"Testing to identify why user reports 'STRYDA not responding'")
        print("=" * 80)
        
        # Run tests in order of user experience flow
        tests = [
            ("Frontend-Backend Integration", self.test_frontend_backend_integration),
            ("Mobile App Scenarios", self.test_mobile_app_scenarios),
            ("Network Conditions", self.test_network_conditions),
            ("Session Persistence", self.test_session_persistence),
            ("Concurrent Users", self.test_concurrent_users)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 Testing: {test_name}")
            if test_func():
                passed += 1
            time.sleep(1)
        
        print("\n" + "=" * 80)
        print(f"🏁 User Experience Summary: {passed}/{total} test suites passed")
        
        # Analyze results
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print(f"\n❌ Issues Found ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['message']}")
            
            print(f"\n🔍 Possible Reasons User Sees 'No Response':")
            
            timeout_issues = [t for t in failed_tests if 'timeout' in t['message'].lower() or 'timed out' in t['message'].lower()]
            if timeout_issues:
                print(f"   • Network timeouts ({len(timeout_issues)} cases) - slow mobile connection")
            
            response_quality_issues = [t for t in failed_tests if 'response' in t['message'].lower() and ('short' in t['message'].lower() or 'empty' in t['message'].lower())]
            if response_quality_issues:
                print(f"   • Poor response quality ({len(response_quality_issues)} cases) - AI not generating proper responses")
            
            session_issues = [t for t in failed_tests if 'session' in t['message'].lower()]
            if session_issues:
                print(f"   • Session management issues ({len(session_issues)} cases) - conversation state problems")
                
        else:
            print(f"\n🎉 All user experience tests passed!")
            print(f"\n💡 Possible reasons for user's 'no response' issue:")
            print(f"   • User might be using a different endpoint or old app version")
            print(f"   • User might have very poor network connection (< 5s timeout)")
            print(f"   • User might be experiencing frontend JavaScript errors")
            print(f"   • User might be testing during a temporary service interruption")
        
        return passed == total

if __name__ == "__main__":
    tester = UserExperienceTester()
    success = tester.run_user_experience_tests()
    
    if success:
        print("\n✅ Backend chat functionality is working perfectly!")
        print("   The issue may be on the frontend or user's specific environment.")
        exit(0)
    else:
        print("\n⚠️  Found issues that could explain user's problem!")
        exit(1)