#!/usr/bin/env python3
"""
STRYDA.ai Enhanced Backend Testing Suite
Comprehensive testing for all 4 major enhancements:
1. Enhanced Knowledge Base Testing
2. Advanced Query Processing Testing  
3. Compliance Analysis Engine Testing
4. Automated Scraping System Testing
5. Integrated Enhanced Chat Testing
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
BACKEND_URL = os.getenv('EXPO_PUBLIC_BACKEND_URL', 'https://nzbuildtech.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class EnhancedSTRYDABackendTester:
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
    
    # PHASE 1: Enhanced Knowledge Base Testing
    def test_enhanced_knowledge_base_stats(self):
        """Test knowledge base stats to verify expanded document collection"""
        try:
            response = self.session.get(f"{API_BASE}/knowledge/stats")
            
            if response.status_code == 200:
                stats = response.json()
                
                # Check for required fields
                required_fields = ['total_documents', 'total_chunks', 'documents_by_type', 'enhanced_features']
                missing_fields = [field for field in required_fields if field not in stats]
                
                if missing_fields:
                    self.log_test("Knowledge Base Stats Structure", False, f"Missing fields: {missing_fields}")
                    return False
                
                # Check document counts
                total_docs = stats.get('total_documents', 0)
                total_chunks = stats.get('total_chunks', 0)
                doc_types = stats.get('documents_by_type', {})
                
                # Verify we have documents from multiple sources
                expected_types = ['nzbc', 'nzs', 'manufacturer', 'mbie']
                found_types = [doc_type for doc_type in expected_types if doc_type in doc_types]
                
                # Check enhanced features
                enhanced_features = stats.get('enhanced_features', {})
                required_features = ['query_processing', 'compliance_analysis', 'alternative_suggestions', 'automated_scraping']
                enabled_features = [feature for feature in required_features if enhanced_features.get(feature)]
                
                details = {
                    "total_documents": total_docs,
                    "total_chunks": total_chunks,
                    "document_types_found": found_types,
                    "enhanced_features_enabled": enabled_features
                }
                
                if total_docs > 0 and total_chunks > 0 and len(found_types) >= 2 and len(enabled_features) >= 3:
                    self.log_test("Enhanced Knowledge Base Stats", True, f"Knowledge base properly expanded: {total_docs} docs, {total_chunks} chunks", details)
                    return True
                else:
                    self.log_test("Enhanced Knowledge Base Stats", False, "Knowledge base not sufficiently expanded", details)
                    return False
            else:
                self.log_test("Enhanced Knowledge Base Stats", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Enhanced Knowledge Base Stats", False, f"Error: {str(e)}")
            return False
    
    def test_enhanced_knowledge_search(self):
        """Test enhanced search with query processing"""
        test_searches = [
            {
                "query": "GIB weatherline installation requirements",
                "expected_types": ["manufacturer"],
                "description": "Manufacturer-specific search"
            },
            {
                "query": "NZ Building Code B1 structural requirements",
                "expected_types": ["nzbc"],
                "description": "Building code search"
            },
            {
                "query": "NZS 3604 timber framing standards",
                "expected_types": ["nzs"],
                "description": "Standards search"
            }
        ]
        
        all_passed = True
        
        for i, test_case in enumerate(test_searches):
            try:
                search_data = {
                    "query": test_case["query"],
                    "limit": 5,
                    "enable_query_processing": True
                }
                
                response = self.session.post(f"{API_BASE}/knowledge/search", json=search_data)
                
                if response.status_code == 200:
                    search_result = response.json()
                    
                    results = search_result.get('results', [])
                    total_found = search_result.get('total_found', 0)
                    search_time = search_result.get('search_time_ms', 0)
                    query_analysis = search_result.get('query_analysis')
                    
                    # Check if we got relevant results
                    has_results = len(results) > 0
                    reasonable_time = search_time < 5000  # Less than 5 seconds
                    has_query_analysis = query_analysis is not None
                    
                    details = {
                        "results_count": len(results),
                        "search_time_ms": search_time,
                        "has_query_analysis": has_query_analysis,
                        "query_analysis": query_analysis
                    }
                    
                    if has_results and reasonable_time:
                        self.log_test(f"Enhanced Search {i+1} ({test_case['description']})", True, f"Found {len(results)} results in {search_time:.1f}ms", details)
                    else:
                        issues = []
                        if not has_results:
                            issues.append("No results found")
                        if not reasonable_time:
                            issues.append(f"Slow search: {search_time}ms")
                        
                        self.log_test(f"Enhanced Search {i+1} ({test_case['description']})", False, f"Issues: {', '.join(issues)}", details)
                        all_passed = False
                else:
                    self.log_test(f"Enhanced Search {i+1} ({test_case['description']})", False, f"HTTP {response.status_code}", response.text)
                    all_passed = False
                    
            except Exception as e:
                self.log_test(f"Enhanced Search {i+1} ({test_case['description']})", False, f"Error: {str(e)}")
                all_passed = False
        
        return all_passed
    
    # PHASE 2: Advanced Query Processing Testing
    def test_advanced_query_processing(self):
        """Test query classification for different building trades"""
        trade_queries = [
            {
                "query": "What size lintel do I need for a 2.4m opening in a 90mm stud wall?",
                "expected_trade": "carpentry",
                "expected_fields": ["dimensions", "materials"],
                "description": "Carpentry/Framing query"
            },
            {
                "query": "James Hardie HardiePlank cladding installation over building wrap",
                "expected_trade": "cladding",
                "expected_fields": ["materials", "brands"],
                "description": "Cladding/Weatherproofing query"
            },
            {
                "query": "Fireplace hearth clearance requirements for solid fuel burner",
                "expected_trade": "fire_safety",
                "expected_fields": ["materials"],
                "description": "Fire Safety query"
            },
            {
                "query": "Pink Batts R2.6 insulation for H1 compliance in Auckland",
                "expected_trade": "insulation",
                "expected_fields": ["materials", "brands", "locations"],
                "description": "Insulation/Thermal query"
            }
        ]
        
        all_passed = True
        
        for i, test_case in enumerate(trade_queries):
            try:
                # Use enhanced chat to test query processing
                chat_data = {
                    "message": test_case["query"],
                    "enable_query_processing": True,
                    "enable_compliance_analysis": True
                }
                
                response = self.session.post(f"{API_BASE}/chat/enhanced", json=chat_data)
                
                if response.status_code == 200:
                    chat_result = response.json()
                    
                    query_analysis = chat_result.get('query_analysis')
                    ai_response = chat_result.get('response', '')
                    processing_time = chat_result.get('processing_time_ms', 0)
                    
                    # Check query analysis
                    has_analysis = query_analysis is not None
                    reasonable_time = processing_time < 10000  # Less than 10 seconds
                    relevant_response = len(ai_response) > 100  # Substantial response
                    
                    details = {
                        "query_analysis": query_analysis,
                        "response_length": len(ai_response),
                        "processing_time_ms": processing_time
                    }
                    
                    if has_analysis and reasonable_time and relevant_response:
                        self.log_test(f"Query Processing {i+1} ({test_case['description']})", True, f"Successfully processed {test_case['expected_trade']} query", details)
                    else:
                        issues = []
                        if not has_analysis:
                            issues.append("No query analysis")
                        if not reasonable_time:
                            issues.append(f"Slow processing: {processing_time}ms")
                        if not relevant_response:
                            issues.append("Response too short")
                        
                        self.log_test(f"Query Processing {i+1} ({test_case['description']})", False, f"Issues: {', '.join(issues)}", details)
                        all_passed = False
                else:
                    self.log_test(f"Query Processing {i+1} ({test_case['description']})", False, f"HTTP {response.status_code}", response.text)
                    all_passed = False
                    
            except Exception as e:
                self.log_test(f"Query Processing {i+1} ({test_case['description']})", False, f"Error: {str(e)}")
                all_passed = False
        
        return all_passed
    
    # PHASE 3: Compliance Analysis Engine Testing
    def test_compliance_analysis_engine(self):
        """Test compliance issue detection and alternative solutions"""
        compliance_scenarios = [
            {
                "query": "Installing a wood burner with 100mm hearth clearance",
                "expected_issues": True,
                "description": "Hearth clearance compliance issue"
            },
            {
                "query": "Using R1.8 insulation in Auckland ceiling for H1 compliance",
                "expected_issues": True,
                "description": "Insulation compliance problem"
            },
            {
                "query": "Installing untreated timber framing in wet area",
                "expected_issues": True,
                "description": "Material compatibility issue"
            }
        ]
        
        all_passed = True
        
        for i, scenario in enumerate(compliance_scenarios):
            try:
                compliance_data = {
                    "query": scenario["query"],
                    "context": ""
                }
                
                response = self.session.post(f"{API_BASE}/compliance/analyze", json=compliance_data)
                
                if response.status_code == 200:
                    compliance_result = response.json()
                    
                    issues = compliance_result.get('issues', [])
                    alternatives = compliance_result.get('alternatives', [])
                    
                    has_issues = len(issues) > 0 if scenario["expected_issues"] else len(issues) == 0
                    has_alternatives = len(alternatives) > 0 if scenario["expected_issues"] else True
                    
                    details = {
                        "issues_found": len(issues),
                        "alternatives_provided": len(alternatives),
                        "issues": issues[:2] if issues else [],  # First 2 issues
                        "alternatives": alternatives[:2] if alternatives else []  # First 2 alternatives
                    }
                    
                    if has_issues and has_alternatives:
                        self.log_test(f"Compliance Analysis {i+1} ({scenario['description']})", True, f"Detected {len(issues)} issues, provided {len(alternatives)} alternatives", details)
                    else:
                        issues_desc = []
                        if not has_issues:
                            issues_desc.append("Issue detection failed")
                        if not has_alternatives:
                            issues_desc.append("No alternatives provided")
                        
                        self.log_test(f"Compliance Analysis {i+1} ({scenario['description']})", False, f"Problems: {', '.join(issues_desc)}", details)
                        all_passed = False
                else:
                    self.log_test(f"Compliance Analysis {i+1} ({scenario['description']})", False, f"HTTP {response.status_code}", response.text)
                    all_passed = False
                    
            except Exception as e:
                self.log_test(f"Compliance Analysis {i+1} ({scenario['description']})", False, f"Error: {str(e)}")
                all_passed = False
        
        return all_passed
    
    # PHASE 4: Automated Scraping System Testing
    def test_automated_scraping_system(self):
        """Test scraping target configuration and availability"""
        try:
            # Test getting scraping targets
            response = self.session.get(f"{API_BASE}/scraping/targets")
            
            if response.status_code == 200:
                targets_data = response.json()
                
                targets = targets_data.get('targets', [])
                total_targets = targets_data.get('total_targets', 0)
                
                # Expected targets: MBIE, Standards NZ, BRANZ, LBP, GIB, James Hardie, Resene
                expected_target_names = ['mbie', 'standards_nz', 'branz', 'lbp', 'gib', 'james_hardie', 'resene']
                found_targets = []
                
                for target in targets:
                    target_name = target.get('name', '').lower()
                    for expected in expected_target_names:
                        if expected in target_name:
                            found_targets.append(expected)
                            break
                
                # Check target configuration
                properly_configured = 0
                for target in targets:
                    if (target.get('name') and 
                        target.get('base_url') and 
                        target.get('document_type') and 
                        target.get('update_frequency_hours')):
                        properly_configured += 1
                
                details = {
                    "total_targets": total_targets,
                    "found_expected_targets": found_targets,
                    "properly_configured": properly_configured,
                    "target_details": targets[:3]  # First 3 targets for details
                }
                
                if total_targets >= 5 and len(found_targets) >= 4 and properly_configured >= 5:
                    self.log_test("Scraping Targets Configuration", True, f"Found {total_targets} targets, {len(found_targets)} expected types", details)
                    
                    # Test scraping endpoint availability
                    try:
                        scraping_data = {"force_update": False}
                        scrape_response = self.session.post(f"{API_BASE}/scraping/run", json=scraping_data)
                        
                        if scrape_response.status_code == 200:
                            scrape_result = scrape_response.json()
                            if "message" in scrape_result:
                                self.log_test("Scraping Endpoint", True, "Scraping endpoint accessible and responsive")
                                return True
                            else:
                                self.log_test("Scraping Endpoint", False, "Invalid scraping response format")
                                return False
                        else:
                            self.log_test("Scraping Endpoint", False, f"HTTP {scrape_response.status_code}")
                            return False
                    except Exception as e:
                        self.log_test("Scraping Endpoint", False, f"Error testing scraping: {str(e)}")
                        return False
                else:
                    issues = []
                    if total_targets < 5:
                        issues.append(f"Too few targets: {total_targets}")
                    if len(found_targets) < 4:
                        issues.append(f"Missing expected targets: {len(found_targets)}/7")
                    if properly_configured < 5:
                        issues.append(f"Poorly configured targets: {properly_configured}")
                    
                    self.log_test("Scraping Targets Configuration", False, f"Issues: {', '.join(issues)}", details)
                    return False
            else:
                self.log_test("Scraping Targets Configuration", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Automated Scraping System", False, f"Error: {str(e)}")
            return False
    
    # PHASE 5: Integrated Enhanced Chat Testing
    def test_integrated_enhanced_chat(self):
        """Test enhanced chat endpoint with complex NZ building queries"""
        complex_queries = [
            {
                "query": "I'm building a deck in Wellington with 140x45 H3.2 treated pine joists at 450mm centers spanning 3.2m. Do I need blocking and what size bearer do I need for the 4.8m span?",
                "expected_features": ["query_analysis", "compliance_issues", "citations", "confidence_score"],
                "description": "Complex structural query with multiple parameters"
            },
            {
                "query": "Installing James Hardie HardiePlank over Pink Batts R2.6 bulk insulation in Auckland - what building wrap and cavity requirements do I need for E2 compliance?",
                "expected_features": ["sources_used", "alternatives_suggested", "processing_time_ms"],
                "description": "Multi-manufacturer compliance query"
            },
            {
                "query": "Solid fuel fireplace installation with 300mm hearth extension - is this compliant with G5 and what are my alternatives if not?",
                "expected_features": ["compliance_issues", "alternatives_suggested", "citations"],
                "description": "Fire safety compliance with alternatives"
            }
        ]
        
        all_passed = True
        
        for i, test_case in enumerate(complex_queries):
            try:
                enhanced_chat_data = {
                    "message": test_case["query"],
                    "enable_compliance_analysis": True,
                    "enable_query_processing": True,
                    "session_id": self.session_id
                }
                
                response = self.session.post(f"{API_BASE}/chat/enhanced", json=enhanced_chat_data)
                
                if response.status_code == 200:
                    chat_result = response.json()
                    
                    # Check for expected features
                    feature_checks = {}
                    for feature in test_case["expected_features"]:
                        feature_checks[feature] = feature in chat_result and chat_result[feature] is not None
                    
                    # Additional quality checks
                    response_text = chat_result.get('response', '')
                    citations = chat_result.get('citations', [])
                    processing_time = chat_result.get('processing_time_ms', 0)
                    confidence_score = chat_result.get('confidence_score', 0)
                    
                    quality_checks = {
                        "substantial_response": len(response_text) > 200,
                        "reasonable_processing_time": processing_time < 15000,  # Less than 15 seconds
                        "has_nz_context": any(term in response_text.lower() for term in ['new zealand', 'nz building code', 'nzbc', 'nzs']),
                        "confidence_reasonable": confidence_score > 0.3 if confidence_score else True
                    }
                    
                    all_features_present = all(feature_checks.values())
                    all_quality_good = all(quality_checks.values())
                    
                    details = {
                        "features_present": feature_checks,
                        "quality_checks": quality_checks,
                        "response_length": len(response_text),
                        "citations_count": len(citations),
                        "processing_time_ms": processing_time,
                        "confidence_score": confidence_score
                    }
                    
                    if all_features_present and all_quality_good:
                        self.log_test(f"Enhanced Chat {i+1} ({test_case['description']})", True, f"All systems integrated successfully - {processing_time:.1f}ms", details)
                    else:
                        issues = []
                        if not all_features_present:
                            missing_features = [f for f, present in feature_checks.items() if not present]
                            issues.append(f"Missing features: {missing_features}")
                        if not all_quality_good:
                            failed_quality = [q for q, passed in quality_checks.items() if not passed]
                            issues.append(f"Quality issues: {failed_quality}")
                        
                        self.log_test(f"Enhanced Chat {i+1} ({test_case['description']})", False, f"Issues: {', '.join(issues)}", details)
                        all_passed = False
                else:
                    self.log_test(f"Enhanced Chat {i+1} ({test_case['description']})", False, f"HTTP {response.status_code}", response.text)
                    all_passed = False
                    
                # Brief pause between complex queries
                time.sleep(2)
                    
            except Exception as e:
                self.log_test(f"Enhanced Chat {i+1} ({test_case['description']})", False, f"Error: {str(e)}")
                all_passed = False
        
        return all_passed
    
    def test_citation_and_source_tracking(self):
        """Test citation generation and source tracking"""
        try:
            citation_query = {
                "message": "What are the NZ Building Code requirements for external wall moisture management under E2?",
                "enable_compliance_analysis": True,
                "enable_query_processing": True
            }
            
            response = self.session.post(f"{API_BASE}/chat/enhanced", json=citation_query)
            
            if response.status_code == 200:
                result = response.json()
                
                citations = result.get('citations', [])
                sources_used = result.get('sources_used', [])
                response_text = result.get('response', '')
                
                # Check citation quality
                valid_citations = 0
                for citation in citations:
                    if (citation.get('title') and 
                        citation.get('url') and 
                        citation.get('snippet')):
                        valid_citations += 1
                
                # Check source tracking
                has_sources = len(sources_used) > 0
                diverse_sources = len(set(sources_used)) > 1 if sources_used else False
                
                details = {
                    "citations_count": len(citations),
                    "valid_citations": valid_citations,
                    "sources_used": sources_used,
                    "diverse_sources": diverse_sources,
                    "response_length": len(response_text)
                }
                
                if valid_citations > 0 and has_sources:
                    self.log_test("Citation and Source Tracking", True, f"Generated {valid_citations} valid citations from {len(sources_used)} sources", details)
                    return True
                else:
                    issues = []
                    if valid_citations == 0:
                        issues.append("No valid citations")
                    if not has_sources:
                        issues.append("No sources tracked")
                    
                    self.log_test("Citation and Source Tracking", False, f"Issues: {', '.join(issues)}", details)
                    return False
            else:
                self.log_test("Citation and Source Tracking", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Citation and Source Tracking", False, f"Error: {str(e)}")
            return False
    
    def run_enhanced_tests(self):
        """Run all enhanced backend tests"""
        print(f"\n🚀 Starting STRYDA.ai Enhanced Backend Tests")
        print(f"Backend URL: {API_BASE}")
        print(f"Session ID: {self.session_id}")
        print("=" * 80)
        
        # Enhanced test suites
        test_suites = [
            ("PHASE 1: Enhanced Knowledge Base Stats", self.test_enhanced_knowledge_base_stats),
            ("PHASE 1: Enhanced Knowledge Search", self.test_enhanced_knowledge_search),
            ("PHASE 2: Advanced Query Processing", self.test_advanced_query_processing),
            ("PHASE 3: Compliance Analysis Engine", self.test_compliance_analysis_engine),
            ("PHASE 4: Automated Scraping System", self.test_automated_scraping_system),
            ("PHASE 5: Integrated Enhanced Chat", self.test_integrated_enhanced_chat),
            ("PHASE 5: Citation and Source Tracking", self.test_citation_and_source_tracking)
        ]
        
        passed = 0
        total = len(test_suites)
        
        for test_name, test_func in test_suites:
            print(f"\n📋 Testing: {test_name}")
            if test_func():
                passed += 1
            time.sleep(1)  # Brief pause between test suites
        
        print("\n" + "=" * 80)
        print(f"🏁 Enhanced Test Summary: {passed}/{total} test suites passed")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['message']}")
        else:
            print(f"\n🎉 All enhanced features working perfectly!")
        
        return passed == total

if __name__ == "__main__":
    tester = EnhancedSTRYDABackendTester()
    success = tester.run_enhanced_tests()
    
    if success:
        print("\n🎉 All enhanced backend tests passed!")
        exit(0)
    else:
        print("\n⚠️  Some enhanced backend tests failed!")
        exit(1)