#!/usr/bin/env python3
"""
STRYDA.ai Critical Phase Knowledge Expansion Testing Suite
Tests the critical phase knowledge expansion functionality specifically
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
BACKEND_URL = os.getenv('EXPO_PUBLIC_BACKEND_URL', 'https://stryda-rag.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class CriticalExpansionTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.expansion_id = None
        
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
    
    def test_backend_connectivity(self):
        """Test basic backend connectivity"""
        try:
            response = self.session.get(f"{API_BASE}/")
            if response.status_code == 200:
                data = response.json()
                if "STRYDA.ai" in data.get('message', ''):
                    self.log_test("Backend Connectivity", True, "Backend API accessible")
                    return True
                else:
                    self.log_test("Backend Connectivity", False, "Unexpected response message", data)
                    return False
            else:
                self.log_test("Backend Connectivity", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Backend Connectivity", False, f"Connection error: {str(e)}")
            return False
    
    def test_knowledge_stats_before_expansion(self):
        """Get knowledge base stats before expansion"""
        try:
            response = self.session.get(f"{API_BASE}/knowledge/stats")
            if response.status_code == 200:
                stats = response.json()
                total_docs = stats.get('total_documents', 0)
                total_chunks = stats.get('total_chunks', 0)
                
                self.initial_stats = {
                    'documents': total_docs,
                    'chunks': total_chunks
                }
                
                self.log_test("Pre-Expansion Knowledge Stats", True, 
                             f"Current knowledge base: {total_docs} documents, {total_chunks} chunks",
                             stats)
                return True
            else:
                self.log_test("Pre-Expansion Knowledge Stats", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Pre-Expansion Knowledge Stats", False, f"Error: {str(e)}")
            return False
    
    def test_expansion_summary_endpoint(self):
        """Test expansion summary endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/knowledge/expansion-summary")
            if response.status_code == 200:
                summary = response.json()
                
                # Check for required fields
                required_fields = ['current_knowledge_base', 'expansion_plan', 'expansion_progress']
                missing_fields = [field for field in required_fields if field not in summary]
                
                if not missing_fields:
                    expansion_plan = summary.get('expansion_plan', {})
                    total_sources = expansion_plan.get('total_sources_available', 0)
                    critical_sources = expansion_plan.get('critical_sources', 0)
                    
                    self.log_test("Expansion Summary Endpoint", True, 
                                 f"Expansion plan available: {total_sources} total sources, {critical_sources} critical sources",
                                 summary)
                    return True
                else:
                    self.log_test("Expansion Summary Endpoint", False, f"Missing fields: {missing_fields}")
                    return False
            else:
                self.log_test("Expansion Summary Endpoint", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Expansion Summary Endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_start_critical_expansion(self):
        """Test starting critical phase expansion"""
        try:
            print("\n🔥 INITIATING CRITICAL PHASE EXPANSION...")
            print("⚡ Focus: Essential safety, fire, structural, and compliance documents")
            
            response = self.session.post(f"{API_BASE}/knowledge/expand-critical")
            
            if response.status_code == 200:
                expansion_response = response.json()
                
                # Check response structure
                required_fields = ['expansion_started', 'phase_name', 'total_sources', 'estimated_time_minutes', 'expansion_id']
                missing_fields = [field for field in required_fields if field not in expansion_response]
                
                if not missing_fields:
                    self.expansion_id = expansion_response.get('expansion_id')
                    phase_name = expansion_response.get('phase_name')
                    total_sources = expansion_response.get('total_sources')
                    estimated_time = expansion_response.get('estimated_time_minutes')
                    
                    if expansion_response.get('expansion_started') and total_sources == 23:
                        self.log_test("Start Critical Expansion", True, 
                                     f"Critical expansion started: {phase_name}, {total_sources} sources, ~{estimated_time} minutes",
                                     expansion_response)
                        return True
                    else:
                        self.log_test("Start Critical Expansion", False, 
                                     f"Expansion not started properly or incorrect source count: {total_sources}")
                        return False
                else:
                    self.log_test("Start Critical Expansion", False, f"Missing response fields: {missing_fields}")
                    return False
            else:
                self.log_test("Start Critical Expansion", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Start Critical Expansion", False, f"Error: {str(e)}")
            return False
    
    def test_expansion_progress_monitoring(self):
        """Monitor expansion progress over time"""
        try:
            print("\n📊 MONITORING EXPANSION PROGRESS...")
            
            # Monitor progress for up to 20 minutes (1200 seconds)
            max_monitoring_time = 1200
            check_interval = 30  # Check every 30 seconds
            start_time = time.time()
            
            progress_checks = 0
            last_completion_percentage = 0
            
            while time.time() - start_time < max_monitoring_time:
                response = self.session.get(f"{API_BASE}/knowledge/expansion-progress")
                
                if response.status_code == 200:
                    progress = response.json()
                    
                    current_phase = progress.get('current_phase')
                    completion_percentage = progress.get('completion_percentage', 0)
                    documents_processed = progress.get('documents_processed', 0)
                    chunks_created = progress.get('chunks_created', 0)
                    processing_status = progress.get('processing_status', 'unknown')
                    
                    progress_checks += 1
                    
                    # Log progress update
                    if current_phase:
                        print(f"   📈 Progress Update {progress_checks}: {completion_percentage:.1f}% complete")
                        print(f"      Phase: {current_phase}")
                        print(f"      Documents: {documents_processed}, Chunks: {chunks_created}")
                        print(f"      Status: {processing_status}")
                    else:
                        print(f"   📈 Progress Update {progress_checks}: No active expansion")
                    
                    # Check if expansion is complete
                    if processing_status == "idle" and completion_percentage >= 100:
                        self.log_test("Expansion Progress Monitoring", True, 
                                     f"Critical expansion completed successfully after {progress_checks} checks",
                                     {
                                         'final_completion': completion_percentage,
                                         'documents_processed': documents_processed,
                                         'chunks_created': chunks_created,
                                         'monitoring_time_seconds': int(time.time() - start_time)
                                     })
                        return True
                    
                    # Check if expansion is still active
                    elif processing_status == "active" or current_phase:
                        # Continue monitoring
                        last_completion_percentage = completion_percentage
                        time.sleep(check_interval)
                        continue
                    
                    # Check if expansion failed or stalled
                    elif progress_checks > 5 and completion_percentage == last_completion_percentage and processing_status == "idle":
                        self.log_test("Expansion Progress Monitoring", False, 
                                     f"Expansion appears to have stalled at {completion_percentage}%")
                        return False
                    
                    else:
                        # Continue monitoring for a bit more
                        time.sleep(check_interval)
                        continue
                        
                else:
                    self.log_test("Expansion Progress Monitoring", False, 
                                 f"Failed to get progress: HTTP {response.status_code}")
                    return False
            
            # If we reach here, monitoring timed out
            self.log_test("Expansion Progress Monitoring", False, 
                         f"Monitoring timed out after {max_monitoring_time} seconds")
            return False
            
        except Exception as e:
            self.log_test("Expansion Progress Monitoring", False, f"Error: {str(e)}")
            return False
    
    def test_knowledge_stats_after_expansion(self):
        """Verify knowledge base stats after expansion"""
        try:
            response = self.session.get(f"{API_BASE}/knowledge/stats")
            if response.status_code == 200:
                stats = response.json()
                total_docs = stats.get('total_documents', 0)
                total_chunks = stats.get('total_chunks', 0)
                
                # Compare with initial stats
                if hasattr(self, 'initial_stats'):
                    docs_added = total_docs - self.initial_stats['documents']
                    chunks_added = total_chunks - self.initial_stats['chunks']
                    
                    # Expect significant increase in documents and chunks
                    if docs_added > 0 and chunks_added > 0:
                        self.log_test("Post-Expansion Knowledge Stats", True, 
                                     f"Knowledge base expanded: +{docs_added} documents, +{chunks_added} chunks",
                                     {
                                         'before': self.initial_stats,
                                         'after': {'documents': total_docs, 'chunks': total_chunks},
                                         'increase': {'documents': docs_added, 'chunks': chunks_added}
                                     })
                        return True
                    else:
                        self.log_test("Post-Expansion Knowledge Stats", False, 
                                     f"No significant increase detected: +{docs_added} docs, +{chunks_added} chunks")
                        return False
                else:
                    self.log_test("Post-Expansion Knowledge Stats", True, 
                                 f"Final knowledge base: {total_docs} documents, {total_chunks} chunks",
                                 stats)
                    return True
            else:
                self.log_test("Post-Expansion Knowledge Stats", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Post-Expansion Knowledge Stats", False, f"Error: {str(e)}")
            return False
    
    def test_critical_documents_verification(self):
        """Verify that critical safety documents are accessible"""
        try:
            # Test queries for critical safety documents
            critical_safety_queries = [
                {
                    "query": "fire safety clearances solid fuel appliances",
                    "expected_codes": ["G5", "fire", "clearance"],
                    "description": "Fire safety (NZBC G5)"
                },
                {
                    "query": "structural requirements timber framing",
                    "expected_codes": ["B1", "B2", "structural", "timber"],
                    "description": "Structural requirements (NZBC B1-B2)"
                },
                {
                    "query": "weathertightness external moisture",
                    "expected_codes": ["E1", "E2", "weathertight", "moisture"],
                    "description": "Weathertightness (NZBC E1-E2)"
                },
                {
                    "query": "electrical safety installation requirements",
                    "expected_codes": ["G9", "electrical", "safety"],
                    "description": "Electrical safety (NZBC G9)"
                },
                {
                    "query": "building safety means of escape",
                    "expected_codes": ["F4", "F5", "F6", "F7", "escape", "safety"],
                    "description": "Building safety (NZBC F4-F7)"
                }
            ]
            
            all_queries_passed = True
            
            for i, test_case in enumerate(critical_safety_queries):
                try:
                    # Use enhanced chat endpoint for better results
                    chat_data = {
                        "message": test_case["query"],
                        "session_id": f"critical_test_{i}",
                        "enable_compliance_analysis": True,
                        "enable_query_processing": True
                    }
                    
                    response = self.session.post(f"{API_BASE}/chat/enhanced", json=chat_data)
                    
                    if response.status_code == 200:
                        chat_response = response.json()
                        ai_response = chat_response.get('response', '')
                        citations = chat_response.get('citations', [])
                        confidence_score = chat_response.get('confidence_score', 0)
                        
                        # Check if response contains relevant content
                        response_lower = ai_response.lower()
                        has_relevant_content = any(keyword.lower() in response_lower for keyword in test_case["expected_codes"])
                        
                        # Check for NZ Building Code references
                        has_nzbc_references = "nzbc" in response_lower or "building code" in response_lower
                        
                        # Check response quality
                        response_quality = len(ai_response) > 200  # Expect detailed responses
                        
                        if ai_response and has_relevant_content and has_nzbc_references and response_quality:
                            details = {
                                "response_length": len(ai_response),
                                "citations_count": len(citations),
                                "confidence_score": confidence_score,
                                "has_nzbc_context": has_nzbc_references
                            }
                            self.log_test(f"Critical Document Query: {test_case['description']}", True, 
                                         f"AI provided comprehensive response with relevant safety information", details)
                        else:
                            issues = []
                            if not ai_response:
                                issues.append("No AI response")
                            if not has_relevant_content:
                                issues.append("Response lacks relevant safety keywords")
                            if not has_nzbc_references:
                                issues.append("No NZBC references found")
                            if not response_quality:
                                issues.append("Response too brief")
                            
                            self.log_test(f"Critical Document Query: {test_case['description']}", False, 
                                         f"Issues: {', '.join(issues)}", {
                                "response_preview": ai_response[:200] + "..." if len(ai_response) > 200 else ai_response,
                                "citations": len(citations)
                            })
                            all_queries_passed = False
                    else:
                        self.log_test(f"Critical Document Query: {test_case['description']}", False, 
                                     f"HTTP {response.status_code}", response.text)
                        all_queries_passed = False
                        
                    # Small delay between requests
                    time.sleep(2)
                    
                except Exception as e:
                    self.log_test(f"Critical Document Query: {test_case['description']}", False, f"Error: {str(e)}")
                    all_queries_passed = False
            
            return all_queries_passed
            
        except Exception as e:
            self.log_test("Critical Documents Verification", False, f"Error: {str(e)}")
            return False
    
    def run_critical_expansion_tests(self):
        """Run all critical expansion tests"""
        print(f"\n🔥 STARTING STRYDA.ai CRITICAL PHASE EXPANSION TESTING")
        print(f"Backend URL: {API_BASE}")
        print(f"Target: 23 critical safety and compliance documents")
        print("=" * 80)
        
        # Run tests in order
        tests = [
            ("Backend Connectivity", self.test_backend_connectivity),
            ("Pre-Expansion Knowledge Stats", self.test_knowledge_stats_before_expansion),
            ("Expansion Summary Endpoint", self.test_expansion_summary_endpoint),
            ("Start Critical Expansion", self.test_start_critical_expansion),
            ("Expansion Progress Monitoring", self.test_expansion_progress_monitoring),
            ("Post-Expansion Knowledge Stats", self.test_knowledge_stats_after_expansion),
            ("Critical Documents Verification", self.test_critical_documents_verification)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 Testing: {test_name}")
            if test_func():
                passed += 1
            else:
                # If critical expansion start fails, skip monitoring
                if test_name == "Start Critical Expansion":
                    print("⚠️  Skipping expansion monitoring due to start failure")
                    break
            time.sleep(1)  # Brief pause between test suites
        
        print("\n" + "=" * 80)
        print(f"🏁 Critical Expansion Test Summary: {passed}/{total} test suites passed")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['message']}")
        
        # Show success summary
        if passed == total:
            print(f"\n🎉 CRITICAL PHASE EXPANSION COMPLETED SUCCESSFULLY!")
            print(f"✅ STRYDA.ai now has enhanced safety and compliance knowledge")
            print(f"✅ 23 critical safety documents processed")
            print(f"✅ Essential building safety knowledge expanded")
        else:
            print(f"\n⚠️  Critical expansion testing incomplete: {passed}/{total} tests passed")
        
        return passed == total

if __name__ == "__main__":
    tester = CriticalExpansionTester()
    success = tester.run_critical_expansion_tests()
    
    if success:
        print("\n🚀 CRITICAL PHASE EXPANSION TESTING COMPLETED SUCCESSFULLY!")
        print("🏗️  STRYDA.ai is now the ultimate NZ building safety authority!")
        exit(0)
    else:
        print("\n⚠️  Critical expansion testing failed or incomplete!")
        exit(1)