#!/usr/bin/env python3
"""
STRYDA.ai Chat Troubleshooting Test Suite
Focused testing for chat functionality issues reported by user
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
BACKEND_URL = os.getenv('EXPO_PUBLIC_BACKEND_URL', 'https://integrity-hub-5.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class ChatTroubleshootingTester:
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
        elif details and success:
            print(f"   Info: {details}")
    
    def test_backend_server_status(self):
        """Test backend server status and connectivity"""
        try:
            print("\n🔍 Testing Backend Server Status...")
            
            # Test root endpoint
            response = self.session.get(f"{API_BASE}/")
            if response.status_code == 200:
                data = response.json()
                self.log_test("Backend Server", True, f"Server responding: {data.get('message', '')}")
                return True
            else:
                self.log_test("Backend Server", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Backend Server", False, f"Connection error: {str(e)}")
            return False
    
    def test_enhanced_chat_endpoint(self):
        """Test the /api/chat/enhanced endpoint specifically"""
        try:
            print("\n🔍 Testing Enhanced Chat Endpoint...")
            
            # Test with a simple building code question
            test_question = "What clearances do I need for a fireplace?"
            
            enhanced_chat_data = {
                "message": test_question,
                "session_id": self.session_id,
                "enable_compliance_analysis": True,
                "enable_query_processing": True
            }
            
            start_time = time.time()
            response = self.session.post(f"{API_BASE}/chat/enhanced", json=enhanced_chat_data, timeout=30)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                chat_response = response.json()
                
                # Check response structure
                required_fields = ['response', 'citations', 'session_id', 'confidence_score', 'processing_time_ms']
                missing_fields = [field for field in required_fields if field not in chat_response]
                
                if missing_fields:
                    self.log_test("Enhanced Chat Structure", False, f"Missing fields: {missing_fields}", chat_response)
                    return False
                
                ai_response = chat_response.get('response', '')
                citations = chat_response.get('citations', [])
                confidence = chat_response.get('confidence_score', 0)
                processing_time = chat_response.get('processing_time_ms', 0)
                
                # Check if we got a meaningful response
                if ai_response and len(ai_response) > 50:
                    details = {
                        "response_length": len(ai_response),
                        "citations_count": len(citations),
                        "confidence_score": confidence,
                        "processing_time_ms": processing_time,
                        "actual_response_time_ms": response_time,
                        "response_preview": ai_response[:200] + "..." if len(ai_response) > 200 else ai_response
                    }
                    self.log_test("Enhanced Chat Response", True, f"Got comprehensive response ({len(ai_response)} chars)", details)
                    return True
                else:
                    self.log_test("Enhanced Chat Response", False, f"Response too short or empty: '{ai_response}'", chat_response)
                    return False
            else:
                self.log_test("Enhanced Chat Endpoint", False, f"HTTP {response.status_code}", response.text[:500])
                return False
                
        except requests.exceptions.Timeout:
            self.log_test("Enhanced Chat Endpoint", False, "Request timed out after 30 seconds")
            return False
        except Exception as e:
            self.log_test("Enhanced Chat Endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_simple_chat_flow(self):
        """Test simple chat message flow end-to-end"""
        try:
            print("\n🔍 Testing Simple Chat Flow...")
            
            # Test with the exact question from review request
            test_question = "What clearances do I need for a fireplace?"
            
            # Test legacy chat endpoint first
            legacy_chat_data = {
                "message": test_question,
                "session_id": self.session_id
            }
            
            start_time = time.time()
            response = self.session.post(f"{API_BASE}/chat", json=legacy_chat_data, timeout=30)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                chat_response = response.json()
                ai_response = chat_response.get('response', '')
                
                if ai_response and len(ai_response) > 20:
                    details = {
                        "response_length": len(ai_response),
                        "response_time_ms": response_time,
                        "has_fireplace_content": "fireplace" in ai_response.lower() or "hearth" in ai_response.lower(),
                        "response_preview": ai_response[:150] + "..." if len(ai_response) > 150 else ai_response
                    }
                    self.log_test("Simple Chat Flow", True, "Legacy chat endpoint working", details)
                    return True
                else:
                    self.log_test("Simple Chat Flow", False, f"Empty or minimal response: '{ai_response}'")
                    return False
            else:
                self.log_test("Simple Chat Flow", False, f"HTTP {response.status_code}", response.text[:300])
                return False
                
        except requests.exceptions.Timeout:
            self.log_test("Simple Chat Flow", False, "Request timed out after 30 seconds")
            return False
        except Exception as e:
            self.log_test("Simple Chat Flow", False, f"Error: {str(e)}")
            return False
    
    def test_mongodb_connectivity(self):
        """Test MongoDB connectivity through API endpoints"""
        try:
            print("\n🔍 Testing MongoDB Connectivity...")
            
            # Test knowledge stats endpoint (requires MongoDB)
            response = self.session.get(f"{API_BASE}/knowledge/stats", timeout=15)
            
            if response.status_code == 200:
                stats = response.json()
                
                # Check if we have meaningful data
                total_docs = stats.get('total_documents', 0)
                total_chunks = stats.get('total_chunks', 0)
                
                if total_docs > 0 and total_chunks > 0:
                    details = {
                        "total_documents": total_docs,
                        "total_chunks": total_chunks,
                        "documents_by_type": stats.get('documents_by_type', {}),
                        "enhanced_features": stats.get('enhanced_features', {})
                    }
                    self.log_test("MongoDB Connectivity", True, f"Database accessible with {total_docs} docs, {total_chunks} chunks", details)
                    return True
                else:
                    self.log_test("MongoDB Connectivity", False, f"Database appears empty: {total_docs} docs, {total_chunks} chunks", stats)
                    return False
            else:
                self.log_test("MongoDB Connectivity", False, f"HTTP {response.status_code}", response.text[:300])
                return False
                
        except requests.exceptions.Timeout:
            self.log_test("MongoDB Connectivity", False, "Request timed out after 15 seconds")
            return False
        except Exception as e:
            self.log_test("MongoDB Connectivity", False, f"Error: {str(e)}")
            return False
    
    def test_knowledge_base_functionality(self):
        """Test document processor and knowledge base functionality"""
        try:
            print("\n🔍 Testing Knowledge Base Functionality...")
            
            # Test knowledge search endpoint
            search_data = {
                "query": "fireplace clearances NZ building code",
                "limit": 5,
                "enable_query_processing": True
            }
            
            response = self.session.post(f"{API_BASE}/knowledge/search", json=search_data, timeout=20)
            
            if response.status_code == 200:
                search_results = response.json()
                
                results = search_results.get('results', [])
                total_found = search_results.get('total_found', 0)
                search_time = search_results.get('search_time_ms', 0)
                
                if total_found > 0 and len(results) > 0:
                    # Check if results are relevant
                    relevant_results = []
                    for result in results:
                        content = result.get('content', '').lower()
                        if any(keyword in content for keyword in ['fireplace', 'hearth', 'clearance', 'g5']):
                            relevant_results.append(result)
                    
                    details = {
                        "total_found": total_found,
                        "results_returned": len(results),
                        "relevant_results": len(relevant_results),
                        "search_time_ms": search_time,
                        "query_analysis": search_results.get('query_analysis')
                    }
                    
                    if len(relevant_results) > 0:
                        self.log_test("Knowledge Base Search", True, f"Found {len(relevant_results)} relevant results", details)
                        return True
                    else:
                        self.log_test("Knowledge Base Search", False, "No relevant results found", details)
                        return False
                else:
                    self.log_test("Knowledge Base Search", False, f"No search results: {total_found} found", search_results)
                    return False
            else:
                self.log_test("Knowledge Base Search", False, f"HTTP {response.status_code}", response.text[:300])
                return False
                
        except requests.exceptions.Timeout:
            self.log_test("Knowledge Base Search", False, "Request timed out after 20 seconds")
            return False
        except Exception as e:
            self.log_test("Knowledge Base Search", False, f"Error: {str(e)}")
            return False
    
    def test_comprehensive_chat_scenarios(self):
        """Test comprehensive chat scenarios that might reveal issues"""
        try:
            print("\n🔍 Testing Comprehensive Chat Scenarios...")
            
            test_scenarios = [
                {
                    "name": "Simple Fireplace Question",
                    "message": "What clearances do I need for a fireplace?",
                    "expected_keywords": ["clearance", "fireplace", "hearth"]
                },
                {
                    "name": "Complex Building Code Query",
                    "message": "I'm installing a Metrofires fireplace on a timber floor in Auckland H1 zone. What are the specific clearance requirements and do I need building consent?",
                    "expected_keywords": ["metrofires", "timber", "clearance", "consent", "auckland"]
                },
                {
                    "name": "Insulation Query",
                    "message": "What R-value insulation do I need for walls in Wellington?",
                    "expected_keywords": ["r-value", "insulation", "wellington", "h1"]
                }
            ]
            
            all_passed = True
            
            for scenario in test_scenarios:
                try:
                    # Test with enhanced endpoint
                    enhanced_data = {
                        "message": scenario["message"],
                        "session_id": f"{self.session_id}_{scenario['name'].replace(' ', '_')}",
                        "enable_compliance_analysis": True,
                        "enable_query_processing": True
                    }
                    
                    start_time = time.time()
                    response = self.session.post(f"{API_BASE}/chat/enhanced", json=enhanced_data, timeout=30)
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status_code == 200:
                        chat_response = response.json()
                        ai_response = chat_response.get('response', '')
                        
                        if ai_response and len(ai_response) > 100:
                            # Check for expected keywords
                            response_lower = ai_response.lower()
                            found_keywords = [kw for kw in scenario["expected_keywords"] if kw.lower() in response_lower]
                            
                            details = {
                                "response_length": len(ai_response),
                                "response_time_ms": response_time,
                                "found_keywords": found_keywords,
                                "expected_keywords": scenario["expected_keywords"],
                                "citations_count": len(chat_response.get('citations', [])),
                                "confidence_score": chat_response.get('confidence_score', 0)
                            }
                            
                            if len(found_keywords) >= len(scenario["expected_keywords"]) // 2:  # At least half the keywords
                                self.log_test(f"Chat Scenario: {scenario['name']}", True, f"Comprehensive response with relevant content", details)
                            else:
                                self.log_test(f"Chat Scenario: {scenario['name']}", False, f"Response lacks expected keywords", details)
                                all_passed = False
                        else:
                            self.log_test(f"Chat Scenario: {scenario['name']}", False, f"Response too short: '{ai_response}'")
                            all_passed = False
                    else:
                        self.log_test(f"Chat Scenario: {scenario['name']}", False, f"HTTP {response.status_code}", response.text[:200])
                        all_passed = False
                        
                    time.sleep(2)  # Pause between scenarios
                    
                except requests.exceptions.Timeout:
                    self.log_test(f"Chat Scenario: {scenario['name']}", False, "Request timed out")
                    all_passed = False
                except Exception as e:
                    self.log_test(f"Chat Scenario: {scenario['name']}", False, f"Error: {str(e)}")
                    all_passed = False
            
            return all_passed
            
        except Exception as e:
            self.log_test("Comprehensive Chat Scenarios", False, f"Error: {str(e)}")
            return False
    
    def test_session_management(self):
        """Test session management and message storage"""
        try:
            print("\n🔍 Testing Session Management...")
            
            # Create a unique session for this test
            test_session_id = f"session_test_{uuid.uuid4()}"
            
            # Send a message
            chat_data = {
                "message": "Test message for session management",
                "session_id": test_session_id
            }
            
            response = self.session.post(f"{API_BASE}/chat/enhanced", json=chat_data, timeout=20)
            
            if response.status_code == 200:
                # Now try to retrieve the chat history
                time.sleep(1)  # Brief pause
                
                history_response = self.session.get(f"{API_BASE}/chat/{test_session_id}/history", timeout=10)
                
                if history_response.status_code == 200:
                    history = history_response.json()
                    
                    if isinstance(history, list) and len(history) >= 2:  # Should have user and bot messages
                        user_msgs = [msg for msg in history if msg.get('sender') == 'user']
                        bot_msgs = [msg for msg in history if msg.get('sender') == 'bot']
                        
                        details = {
                            "total_messages": len(history),
                            "user_messages": len(user_msgs),
                            "bot_messages": len(bot_msgs),
                            "session_id": test_session_id
                        }
                        
                        if len(user_msgs) > 0 and len(bot_msgs) > 0:
                            self.log_test("Session Management", True, "Messages stored and retrieved correctly", details)
                            return True
                        else:
                            self.log_test("Session Management", False, "Missing user or bot messages", details)
                            return False
                    else:
                        self.log_test("Session Management", False, f"Insufficient messages in history: {len(history) if isinstance(history, list) else 'not a list'}")
                        return False
                else:
                    self.log_test("Session Management", False, f"History retrieval failed: HTTP {history_response.status_code}")
                    return False
            else:
                self.log_test("Session Management", False, f"Chat message failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Session Management", False, f"Error: {str(e)}")
            return False
    
    def run_troubleshooting_tests(self):
        """Run all troubleshooting tests"""
        print(f"\n🔧 STRYDA.ai Chat Troubleshooting Tests")
        print(f"Backend URL: {API_BASE}")
        print(f"Session ID: {self.session_id}")
        print("=" * 80)
        
        # Run tests in order of importance
        tests = [
            ("Backend Server Status", self.test_backend_server_status),
            ("Enhanced Chat Endpoint", self.test_enhanced_chat_endpoint),
            ("Simple Chat Flow", self.test_simple_chat_flow),
            ("MongoDB Connectivity", self.test_mongodb_connectivity),
            ("Knowledge Base Functionality", self.test_knowledge_base_functionality),
            ("Session Management", self.test_session_management),
            ("Comprehensive Chat Scenarios", self.test_comprehensive_chat_scenarios)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 Testing: {test_name}")
            if test_func():
                passed += 1
            time.sleep(1)  # Brief pause between test suites
        
        print("\n" + "=" * 80)
        print(f"🏁 Troubleshooting Summary: {passed}/{total} test suites passed")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['message']}")
        else:
            print(f"\n🎉 All troubleshooting tests passed! Chat functionality appears to be working correctly.")
        
        return passed == total

if __name__ == "__main__":
    tester = ChatTroubleshootingTester()
    success = tester.run_troubleshooting_tests()
    
    if success:
        print("\n✅ Chat functionality is working correctly!")
        exit(0)
    else:
        print("\n⚠️  Issues found with chat functionality!")
        exit(1)