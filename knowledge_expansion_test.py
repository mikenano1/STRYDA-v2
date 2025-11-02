#!/usr/bin/env python3
"""
STRYDA.ai Knowledge Expansion Testing Suite
Tests comprehensive knowledge expansion functionality
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
BACKEND_URL = os.getenv('EXPO_PUBLIC_BACKEND_URL', 'https://citation-guard.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class KnowledgeExpansionTester:
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
    
    def test_expansion_progress_monitoring_fix(self):
        """Test that GET /api/knowledge/expansion-progress now works properly (was returning HTTP 500)"""
        try:
            print("🔍 Testing expansion progress monitoring fix...")
            response = self.session.get(f"{API_BASE}/knowledge/expansion-progress")
            
            if response.status_code == 200:
                progress_data = response.json()
                
                # Check required fields in response
                required_fields = ['completion_percentage', 'documents_processed', 'chunks_created', 'processing_status']
                missing_fields = [field for field in required_fields if field not in progress_data]
                
                if not missing_fields:
                    self.log_test("Progress Monitoring Fix", True, 
                                f"Progress endpoint working - Status: {progress_data.get('processing_status', 'unknown')}")
                    return True
                else:
                    self.log_test("Progress Monitoring Fix", False, 
                                f"Missing required fields: {missing_fields}", progress_data)
                    return False
            else:
                self.log_test("Progress Monitoring Fix", False, 
                            f"HTTP {response.status_code} - Progress endpoint still failing", response.text)
                return False
                
        except Exception as e:
            self.log_test("Progress Monitoring Fix", False, f"Error: {str(e)}")
            return False
    
    def test_knowledge_base_current_state(self):
        """Test current knowledge base state before expansion"""
        try:
            print("📊 Checking current knowledge base state...")
            response = self.session.get(f"{API_BASE}/knowledge/stats")
            
            if response.status_code == 200:
                stats = response.json()
                total_docs = stats.get('total_documents', 0)
                total_chunks = stats.get('total_chunks', 0)
                
                self.log_test("Current Knowledge Base State", True, 
                            f"Current state: {total_docs} documents, {total_chunks} chunks", stats)
                
                # Store baseline for comparison
                self.baseline_docs = total_docs
                self.baseline_chunks = total_chunks
                return True
            else:
                self.log_test("Current Knowledge Base State", False, 
                            f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Current Knowledge Base State", False, f"Error: {str(e)}")
            return False
    
    def test_start_full_expansion(self):
        """Test starting the full comprehensive expansion (all 74 documents)"""
        try:
            print("🚀 Starting FULL COMPREHENSIVE KNOWLEDGE EXPANSION...")
            print("🎯 Target: Process ALL 74 documents across 4 phases")
            
            response = self.session.post(f"{API_BASE}/knowledge/expand-full")
            
            if response.status_code == 200:
                expansion_data = response.json()
                
                # Check required fields
                required_fields = ['expansion_started', 'phase_name', 'total_sources', 'estimated_time_minutes', 'expansion_id']
                missing_fields = [field for field in required_fields if field not in expansion_data]
                
                if not missing_fields:
                    self.expansion_id = expansion_data.get('expansion_id')
                    total_sources = expansion_data.get('total_sources', 0)
                    estimated_time = expansion_data.get('estimated_time_minutes', 0)
                    
                    if total_sources == 74:  # Should be all 74 documents
                        self.log_test("Start Full Expansion", True, 
                                    f"Full expansion started - {total_sources} sources, ~{estimated_time} minutes", 
                                    expansion_data)
                        return True
                    else:
                        self.log_test("Start Full Expansion", False, 
                                    f"Expected 74 sources, got {total_sources}", expansion_data)
                        return False
                else:
                    self.log_test("Start Full Expansion", False, 
                                f"Missing required fields: {missing_fields}", expansion_data)
                    return False
            else:
                self.log_test("Start Full Expansion", False, 
                            f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Start Full Expansion", False, f"Error: {str(e)}")
            return False
    
    def test_monitor_expansion_progress(self):
        """Monitor the complete expansion through all 4 phases"""
        try:
            print("📈 Monitoring expansion progress through all phases...")
            print("Expected phases:")
            print("  Phase 1: Complete NZBC (38 documents)")
            print("  Phase 2: Council Regulations (9 documents)")
            print("  Phase 3: Manufacturer Specs (16 documents)")
            print("  Phase 4: NZ Standards (11 documents)")
            
            max_monitoring_time = 3600  # 60 minutes max
            start_time = time.time()
            last_progress = -1
            phases_seen = set()
            
            while (time.time() - start_time) < max_monitoring_time:
                try:
                    response = self.session.get(f"{API_BASE}/knowledge/expansion-progress")
                    
                    if response.status_code == 200:
                        progress_data = response.json()
                        
                        current_phase = progress_data.get('current_phase')
                        completion_percentage = progress_data.get('completion_percentage', 0)
                        documents_processed = progress_data.get('documents_processed', 0)
                        chunks_created = progress_data.get('chunks_created', 0)
                        processing_status = progress_data.get('processing_status', 'unknown')
                        
                        # Track phases we've seen
                        if current_phase:
                            phases_seen.add(current_phase)
                        
                        # Log progress updates (only when significant change)
                        if completion_percentage > last_progress + 10 or current_phase:
                            print(f"   📊 Progress: {completion_percentage:.1f}% | Phase: {current_phase or 'Starting'} | Docs: {documents_processed} | Chunks: {chunks_created}")
                            last_progress = completion_percentage
                        
                        # Check if expansion is complete
                        if processing_status == "idle" and completion_percentage >= 100:
                            self.log_test("Monitor Expansion Progress", True, 
                                        f"Expansion completed! Final: {documents_processed} docs, {chunks_created} chunks", 
                                        {
                                            "phases_seen": list(phases_seen),
                                            "final_completion": completion_percentage,
                                            "total_time_minutes": (time.time() - start_time) / 60
                                        })
                            return True
                        
                        # Check if expansion failed
                        if processing_status == "failed":
                            self.log_test("Monitor Expansion Progress", False, 
                                        "Expansion failed during processing", progress_data)
                            return False
                    
                    else:
                        print(f"   ⚠️ Progress check failed: HTTP {response.status_code}")
                    
                    # Wait before next check
                    time.sleep(30)  # Check every 30 seconds
                    
                except Exception as e:
                    print(f"   ⚠️ Progress check error: {str(e)}")
                    time.sleep(30)
            
            # Timeout reached
            self.log_test("Monitor Expansion Progress", False, 
                        f"Expansion monitoring timed out after {max_monitoring_time/60} minutes", 
                        {"phases_seen": list(phases_seen)})
            return False
            
        except Exception as e:
            self.log_test("Monitor Expansion Progress", False, f"Error: {str(e)}")
            return False
    
    def test_expansion_summary(self):
        """Test expansion summary and final statistics"""
        try:
            print("📋 Getting expansion summary...")
            response = self.session.get(f"{API_BASE}/knowledge/expansion-summary")
            
            if response.status_code == 200:
                summary_data = response.json()
                
                current_kb = summary_data.get('current_knowledge_base', {})
                expansion_plan = summary_data.get('expansion_plan', {})
                
                total_docs = current_kb.get('total_documents', 0)
                total_chunks = current_kb.get('total_chunks', 0)
                
                # Check if we've significantly expanded from baseline
                if hasattr(self, 'baseline_docs') and hasattr(self, 'baseline_chunks'):
                    docs_increase = total_docs - self.baseline_docs
                    chunks_increase = total_chunks - self.baseline_chunks
                    
                    if docs_increase > 1000 and chunks_increase > 5000:  # Significant expansion
                        self.log_test("Expansion Summary", True, 
                                    f"Massive expansion achieved! +{docs_increase} docs, +{chunks_increase} chunks", 
                                    {
                                        "before": {"docs": self.baseline_docs, "chunks": self.baseline_chunks},
                                        "after": {"docs": total_docs, "chunks": total_chunks},
                                        "expansion_plan": expansion_plan
                                    })
                        return True
                    else:
                        self.log_test("Expansion Summary", False, 
                                    f"Insufficient expansion: +{docs_increase} docs, +{chunks_increase} chunks")
                        return False
                else:
                    self.log_test("Expansion Summary", True, 
                                f"Final knowledge base: {total_docs} docs, {total_chunks} chunks", summary_data)
                    return True
            else:
                self.log_test("Expansion Summary", False, 
                            f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Expansion Summary", False, f"Error: {str(e)}")
            return False
    
    def test_enhanced_ai_responses_post_expansion(self):
        """Test that AI responses are enhanced after knowledge expansion"""
        try:
            print("🧠 Testing enhanced AI responses post-expansion...")
            
            # Test complex NZ building queries that should benefit from expanded knowledge
            test_queries = [
                {
                    "query": "What are the specific requirements for installing a Metrofires fireplace in an Auckland H1 climate zone with timber flooring?",
                    "expected_min_length": 800,
                    "expected_keywords": ["metrofires", "h1", "climate", "timber", "clearance"]
                },
                {
                    "query": "What council consent requirements apply for a two-story extension in Wellington with weatherboard cladding?",
                    "expected_min_length": 800,
                    "expected_keywords": ["wellington", "consent", "weatherboard", "extension"]
                },
                {
                    "query": "What are the NZS 3604 requirements for LVL beam sizing in residential construction?",
                    "expected_min_length": 800,
                    "expected_keywords": ["nzs 3604", "lvl", "beam", "residential"]
                }
            ]
            
            all_passed = True
            
            for i, test_case in enumerate(test_queries):
                try:
                    chat_data = {
                        "message": test_case["query"],
                        "session_id": f"expansion_test_{uuid.uuid4()}"
                    }
                    
                    response = self.session.post(f"{API_BASE}/chat/enhanced", json=chat_data)
                    
                    if response.status_code == 200:
                        chat_response = response.json()
                        ai_response = chat_response.get('response', '')
                        citations = chat_response.get('citations', [])
                        confidence_score = chat_response.get('confidence_score', 0)
                        sources_used = chat_response.get('sources_used', [])
                        
                        # Check response quality
                        response_length = len(ai_response)
                        has_keywords = any(keyword.lower() in ai_response.lower() for keyword in test_case["expected_keywords"])
                        has_citations = len(citations) > 0
                        good_confidence = confidence_score > 0.3
                        
                        if (response_length >= test_case["expected_min_length"] and 
                            has_keywords and has_citations and good_confidence):
                            
                            self.log_test(f"Enhanced AI Response {i+1}", True, 
                                        f"Excellent response: {response_length} chars, {len(citations)} citations, {confidence_score:.2f} confidence", 
                                        {
                                            "sources_used": len(sources_used),
                                            "has_nz_context": "new zealand" in ai_response.lower()
                                        })
                        else:
                            issues = []
                            if response_length < test_case["expected_min_length"]:
                                issues.append(f"Short response ({response_length} chars)")
                            if not has_keywords:
                                issues.append("Missing expected keywords")
                            if not has_citations:
                                issues.append("No citations")
                            if not good_confidence:
                                issues.append(f"Low confidence ({confidence_score:.2f})")
                            
                            self.log_test(f"Enhanced AI Response {i+1}", False, 
                                        f"Response quality issues: {', '.join(issues)}")
                            all_passed = False
                    else:
                        self.log_test(f"Enhanced AI Response {i+1}", False, 
                                    f"HTTP {response.status_code}", response.text)
                        all_passed = False
                        
                    time.sleep(2)  # Brief pause between queries
                    
                except Exception as e:
                    self.log_test(f"Enhanced AI Response {i+1}", False, f"Error: {str(e)}")
                    all_passed = False
            
            return all_passed
            
        except Exception as e:
            self.log_test("Enhanced AI Responses", False, f"Error: {str(e)}")
            return False
    
    def run_comprehensive_expansion_test(self):
        """Run the complete knowledge expansion test suite"""
        print(f"\n🔥 LAUNCHING FULL COMPREHENSIVE KNOWLEDGE EXPANSION TESTING")
        print(f"🎯 Target: Transform STRYDA into ultimate NZ building authority")
        print(f"Backend URL: {API_BASE}")
        print("=" * 80)
        
        # Test sequence for comprehensive expansion
        tests = [
            ("Progress Monitoring Fix", self.test_expansion_progress_monitoring_fix),
            ("Current Knowledge Base State", self.test_knowledge_base_current_state),
            ("Start Full Expansion", self.test_start_full_expansion),
            ("Monitor Complete Expansion", self.test_monitor_expansion_progress),
            ("Expansion Summary", self.test_expansion_summary),
            ("Enhanced AI Responses", self.test_enhanced_ai_responses_post_expansion)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🧪 Testing: {test_name}")
            if test_func():
                passed += 1
            else:
                # For critical tests, we might want to stop
                if test_name in ["Progress Monitoring Fix", "Start Full Expansion"]:
                    print(f"❌ Critical test failed: {test_name}. Stopping expansion test.")
                    break
            
            time.sleep(1)  # Brief pause between tests
        
        print("\n" + "=" * 80)
        print(f"🏁 Knowledge Expansion Test Summary: {passed}/{total} tests passed")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['message']}")
        else:
            print(f"\n🎉 COMPLETE SUCCESS! STRYDA.ai transformed into ultimate NZ building authority!")
            print(f"✅ All 74 documents processed across 4 phases")
            print(f"✅ Knowledge base massively expanded")
            print(f"✅ AI responses significantly enhanced")
        
        return passed == total

if __name__ == "__main__":
    tester = KnowledgeExpansionTester()
    success = tester.run_comprehensive_expansion_test()
    
    if success:
        print("\n🌟 COMPREHENSIVE KNOWLEDGE EXPANSION SUCCESSFUL!")
        print("🏗️ STRYDA.ai is now the definitive NZ building authority!")
        exit(0)
    else:
        print("\n⚠️ Knowledge expansion testing encountered issues!")
        exit(1)