#!/usr/bin/env python3
"""
STRYDA.ai NZ Building Code Integration Testing Suite
Comprehensive testing for the newly integrated complete NZ Building Code knowledge base.

Focus Areas:
1. Enhanced Chat System with Real Building Code Data
2. Knowledge Base Stats (600+ documents from processed Building Code PDF)
3. PDF Processing System
4. Real Building Code Citations (actual NZBC clauses)
5. Performance with Large Knowledge Base (33 to 748+ chunks)
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
BACKEND_URL = os.getenv('EXPO_PUBLIC_BACKEND_URL', 'https://stresstest-nz.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class NZBuildingCodeIntegrationTester:
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
    
    def test_knowledge_base_expansion(self):
        """Test that knowledge base has been expanded to 600+ documents from Building Code PDF"""
        try:
            response = self.session.get(f"{API_BASE}/knowledge/stats")
            
            if response.status_code == 200:
                stats = response.json()
                
                total_docs = stats.get('total_documents', 0)
                total_chunks = stats.get('total_chunks', 0)
                doc_types = stats.get('documents_by_type', {})
                
                # Check for dramatic expansion (from 33 to 748+ chunks)
                has_major_expansion = total_chunks >= 600  # Should be 748+ based on integration
                has_building_code_docs = doc_types.get('nzbc', 0) >= 500  # Should have 600+ NZBC docs
                
                details = {
                    "total_documents": total_docs,
                    "total_chunks": total_chunks,
                    "nzbc_documents": doc_types.get('nzbc', 0),
                    "documents_by_type": doc_types
                }
                
                if has_major_expansion and has_building_code_docs:
                    self.log_test("Knowledge Base Expansion", True, f"Major expansion confirmed: {total_docs} docs, {total_chunks} chunks, {doc_types.get('nzbc', 0)} NZBC docs", details)
                    return True
                else:
                    issues = []
                    if not has_major_expansion:
                        issues.append(f"Insufficient chunks: {total_chunks} (expected 600+)")
                    if not has_building_code_docs:
                        issues.append(f"Insufficient NZBC docs: {doc_types.get('nzbc', 0)} (expected 500+)")
                    
                    self.log_test("Knowledge Base Expansion", False, f"Expansion incomplete: {', '.join(issues)}", details)
                    return False
            else:
                self.log_test("Knowledge Base Expansion", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Knowledge Base Expansion", False, f"Error: {str(e)}")
            return False
    
    def test_real_building_code_queries(self):
        """Test enhanced chat with specific NZ Building Code queries using real data"""
        real_building_code_queries = [
            {
                "query": "What are the specific clearance requirements for solid fuel burning appliances according to NZBC G5?",
                "expected_clauses": ["G5", "solid fuel", "clearance", "appliance"],
                "expected_response_length": 800,  # Should be comprehensive with real data
                "description": "G5 Fire Safety - Solid Fuel Appliances"
            },
            {
                "query": "What are the minimum insulation R-values for residential buildings in different climate zones under H1?",
                "expected_clauses": ["H1", "insulation", "R-value", "climate zone", "residential"],
                "expected_response_length": 1000,  # Should cover multiple zones
                "description": "H1 Energy Efficiency - Insulation Requirements"
            },
            {
                "query": "What are the weathertightness requirements for external cladding systems under E2?",
                "expected_clauses": ["E2", "weathertight", "cladding", "external", "moisture"],
                "expected_response_length": 900,  # Should be detailed with real E2 requirements
                "description": "E2 External Moisture - Weathertightness"
            }
        ]
        
        all_passed = True
        
        for i, test_case in enumerate(real_building_code_queries):
            try:
                chat_data = {
                    "message": test_case["query"],
                    "enable_compliance_analysis": True,
                    "enable_query_processing": True,
                    "session_id": self.session_id
                }
                
                start_time = time.time()
                response = self.session.post(f"{API_BASE}/chat/enhanced", json=chat_data)
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    result = response.json()
                    
                    ai_response = result.get('response', '')
                    citations = result.get('citations', [])
                    confidence_score = result.get('confidence_score', 0)
                    sources_used = result.get('sources_used', [])
                    processing_time = result.get('processing_time_ms', 0)
                    
                    # Check for real Building Code content
                    response_lower = ai_response.lower()
                    has_expected_clauses = all(clause.lower() in response_lower for clause in test_case["expected_clauses"])
                    has_real_citations = len(citations) > 0
                    substantial_response = len(ai_response) >= test_case["expected_response_length"]
                    has_nzbc_sources = any("nzbc" in source.lower() or "building code" in source.lower() for source in sources_used)
                    reasonable_confidence = confidence_score > 0.6  # Should be high with real data
                    
                    # Check for specific real Building Code indicators
                    real_code_indicators = [
                        "clause" in response_lower,
                        "nzbc" in response_lower or "new zealand building code" in response_lower,
                        any(section in response_lower for section in ["g5.", "h1.", "e2.", "b1.", "f2."]),
                        "acceptable solution" in response_lower or "verification method" in response_lower
                    ]
                    has_real_code_content = sum(real_code_indicators) >= 2
                    
                    details = {
                        "response_length": len(ai_response),
                        "citations_count": len(citations),
                        "confidence_score": confidence_score,
                        "sources_used": sources_used,
                        "processing_time_ms": processing_time,
                        "response_time_ms": response_time,
                        "has_expected_clauses": has_expected_clauses,
                        "real_code_indicators": sum(real_code_indicators),
                        "sample_response": ai_response[:300] + "..." if len(ai_response) > 300 else ai_response
                    }
                    
                    if (has_expected_clauses and has_real_citations and substantial_response and 
                        has_nzbc_sources and reasonable_confidence and has_real_code_content):
                        self.log_test(f"Real Building Code Query {i+1} ({test_case['description']})", True, 
                                    f"Excellent real Building Code response: {len(ai_response)} chars, {len(citations)} citations, {confidence_score:.2f} confidence", details)
                    else:
                        issues = []
                        if not has_expected_clauses:
                            issues.append("Missing expected clauses")
                        if not has_real_citations:
                            issues.append("No citations")
                        if not substantial_response:
                            issues.append(f"Response too short: {len(ai_response)}")
                        if not has_nzbc_sources:
                            issues.append("No NZBC sources")
                        if not reasonable_confidence:
                            issues.append(f"Low confidence: {confidence_score}")
                        if not has_real_code_content:
                            issues.append("Lacks real Building Code content")
                        
                        self.log_test(f"Real Building Code Query {i+1} ({test_case['description']})", False, 
                                    f"Issues with real Building Code data: {', '.join(issues)}", details)
                        all_passed = False
                else:
                    self.log_test(f"Real Building Code Query {i+1} ({test_case['description']})", False, 
                                f"HTTP {response.status_code}", response.text)
                    all_passed = False
                    
                # Pause between queries
                time.sleep(2)
                    
            except Exception as e:
                self.log_test(f"Real Building Code Query {i+1} ({test_case['description']})", False, f"Error: {str(e)}")
                all_passed = False
        
        return all_passed
    
    def test_real_building_code_citations(self):
        """Test that citations now include proper references from actual NZBC clauses"""
        try:
            citation_test_query = {
                "message": "What are the structural requirements for timber framing under NZS 3604 and NZBC B1?",
                "enable_compliance_analysis": True,
                "enable_query_processing": True
            }
            
            response = self.session.post(f"{API_BASE}/chat/enhanced", json=citation_test_query)
            
            if response.status_code == 200:
                result = response.json()
                
                citations = result.get('citations', [])
                ai_response = result.get('response', '')
                sources_used = result.get('sources_used', [])
                
                # Analyze citation quality for real Building Code content
                real_nzbc_citations = 0
                citation_quality_scores = []
                
                for citation in citations:
                    title = citation.get('title', '').lower()
                    url = citation.get('url', '').lower()
                    snippet = citation.get('snippet', '').lower()
                    
                    # Check for real NZBC citation indicators
                    is_real_nzbc = any([
                        'nzbc' in title or 'building code' in title,
                        'nzs 3604' in title or 'nzs 4230' in title,
                        'clause' in snippet,
                        'acceptable solution' in snippet,
                        'verification method' in snippet,
                        any(section in snippet for section in ['b1.', 'e2.', 'g5.', 'h1.', 'f2.'])
                    ])
                    
                    if is_real_nzbc:
                        real_nzbc_citations += 1
                    
                    # Score citation quality
                    quality_score = 0
                    if citation.get('title'): quality_score += 1
                    if citation.get('url'): quality_score += 1
                    if citation.get('snippet') and len(citation.get('snippet', '')) > 50: quality_score += 1
                    if is_real_nzbc: quality_score += 2
                    
                    citation_quality_scores.append(quality_score)
                
                avg_citation_quality = sum(citation_quality_scores) / len(citation_quality_scores) if citation_quality_scores else 0
                has_real_nzbc_sources = any('nzbc' in source.lower() or 'building code' in source.lower() for source in sources_used)
                
                details = {
                    "total_citations": len(citations),
                    "real_nzbc_citations": real_nzbc_citations,
                    "avg_citation_quality": avg_citation_quality,
                    "sources_used": sources_used,
                    "has_real_nzbc_sources": has_real_nzbc_sources,
                    "sample_citations": citations[:2] if citations else []
                }
                
                if real_nzbc_citations >= 2 and avg_citation_quality >= 3 and has_real_nzbc_sources:
                    self.log_test("Real Building Code Citations", True, 
                                f"Excellent real NZBC citations: {real_nzbc_citations}/{len(citations)} real NZBC, quality {avg_citation_quality:.1f}/5", details)
                    return True
                else:
                    issues = []
                    if real_nzbc_citations < 2:
                        issues.append(f"Too few real NZBC citations: {real_nzbc_citations}")
                    if avg_citation_quality < 3:
                        issues.append(f"Low citation quality: {avg_citation_quality:.1f}")
                    if not has_real_nzbc_sources:
                        issues.append("No real NZBC sources")
                    
                    self.log_test("Real Building Code Citations", False, 
                                f"Citation quality issues: {', '.join(issues)}", details)
                    return False
            else:
                self.log_test("Real Building Code Citations", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Real Building Code Citations", False, f"Error: {str(e)}")
            return False
    
    def test_search_performance_with_large_knowledge_base(self):
        """Test search performance with dramatically expanded knowledge base (33 to 748+ chunks)"""
        performance_queries = [
            "NZBC G5 solid fuel appliance clearances",
            "H1 insulation R-values climate zones",
            "E2 weathertightness external cladding",
            "B1 structural timber framing NZS 3604",
            "F2 hazardous building materials asbestos"
        ]
        
        all_passed = True
        performance_results = []
        
        for i, query in enumerate(performance_queries):
            try:
                search_data = {
                    "query": query,
                    "limit": 10,
                    "enable_query_processing": True
                }
                
                start_time = time.time()
                response = self.session.post(f"{API_BASE}/knowledge/search", json=search_data)
                search_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    result = response.json()
                    
                    results = result.get('results', [])
                    total_found = result.get('total_found', 0)
                    reported_search_time = result.get('search_time_ms', 0)
                    
                    # Performance criteria for large knowledge base
                    fast_search = search_time < 2000  # Less than 2 seconds
                    good_results = len(results) >= 5  # Should find relevant results
                    high_relevance = any(res.get('similarity_score', 0) > 0.7 for res in results) if results else False
                    
                    performance_data = {
                        "query": query,
                        "search_time_ms": search_time,
                        "reported_time_ms": reported_search_time,
                        "results_count": len(results),
                        "total_found": total_found,
                        "max_similarity": max((res.get('similarity_score', 0) for res in results), default=0)
                    }
                    performance_results.append(performance_data)
                    
                    if fast_search and good_results and high_relevance:
                        self.log_test(f"Search Performance {i+1}", True, 
                                    f"Excellent performance: {search_time:.0f}ms, {len(results)} results, max similarity {performance_data['max_similarity']:.2f}")
                    else:
                        issues = []
                        if not fast_search:
                            issues.append(f"Slow search: {search_time:.0f}ms")
                        if not good_results:
                            issues.append(f"Few results: {len(results)}")
                        if not high_relevance:
                            issues.append("Low relevance scores")
                        
                        self.log_test(f"Search Performance {i+1}", False, 
                                    f"Performance issues: {', '.join(issues)}", performance_data)
                        all_passed = False
                else:
                    self.log_test(f"Search Performance {i+1}", False, f"HTTP {response.status_code}", response.text)
                    all_passed = False
                    
                time.sleep(0.5)  # Brief pause between searches
                    
            except Exception as e:
                self.log_test(f"Search Performance {i+1}", False, f"Error: {str(e)}")
                all_passed = False
        
        # Overall performance summary
        if performance_results:
            avg_search_time = sum(p['search_time_ms'] for p in performance_results) / len(performance_results)
            avg_results = sum(p['results_count'] for p in performance_results) / len(performance_results)
            avg_similarity = sum(p['max_similarity'] for p in performance_results) / len(performance_results)
            
            summary_details = {
                "avg_search_time_ms": avg_search_time,
                "avg_results_count": avg_results,
                "avg_max_similarity": avg_similarity,
                "all_performance_data": performance_results
            }
            
            if avg_search_time < 1500 and avg_results >= 5 and avg_similarity > 0.6:
                self.log_test("Overall Search Performance", True, 
                            f"Excellent overall performance: {avg_search_time:.0f}ms avg, {avg_results:.1f} results avg, {avg_similarity:.2f} similarity avg", summary_details)
            else:
                self.log_test("Overall Search Performance", False, 
                            f"Performance concerns: {avg_search_time:.0f}ms avg, {avg_results:.1f} results avg, {avg_similarity:.2f} similarity avg", summary_details)
                all_passed = False
        
        return all_passed
    
    def test_pdf_processing_system(self):
        """Test PDF processing endpoints and status tracking"""
        try:
            # Test PDF processing status endpoint
            response = self.session.get(f"{API_BASE}/knowledge/pdf-status")
            
            if response.status_code == 200:
                status_data = response.json()
                
                total_pdf_docs = status_data.get('total_pdf_documents', 0)
                total_pdf_chunks = status_data.get('total_pdf_chunks', 0)
                recent_docs = status_data.get('recent_pdf_documents', [])
                
                # Check for evidence of PDF processing
                has_pdf_documents = total_pdf_docs > 0
                has_pdf_chunks = total_pdf_chunks >= 500  # Should have many chunks from Building Code PDF
                has_recent_processing = len(recent_docs) > 0
                
                # Check for Building Code PDF specifically
                building_code_processed = False
                if recent_docs:
                    for doc in recent_docs:
                        title = doc.get('title', '').lower()
                        if 'building code' in title or 'nzbc' in title or 'handbook' in title:
                            building_code_processed = True
                            break
                
                details = {
                    "total_pdf_documents": total_pdf_docs,
                    "total_pdf_chunks": total_pdf_chunks,
                    "recent_pdf_documents": recent_docs,
                    "building_code_processed": building_code_processed
                }
                
                if has_pdf_documents and has_pdf_chunks and building_code_processed:
                    self.log_test("PDF Processing System", True, 
                                f"PDF processing confirmed: {total_pdf_docs} docs, {total_pdf_chunks} chunks, Building Code processed", details)
                    return True
                else:
                    issues = []
                    if not has_pdf_documents:
                        issues.append("No PDF documents found")
                    if not has_pdf_chunks:
                        issues.append(f"Insufficient PDF chunks: {total_pdf_chunks}")
                    if not building_code_processed:
                        issues.append("Building Code PDF not found in recent processing")
                    
                    self.log_test("PDF Processing System", False, 
                                f"PDF processing issues: {', '.join(issues)}", details)
                    return False
            else:
                self.log_test("PDF Processing System", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("PDF Processing System", False, f"Error: {str(e)}")
            return False
    
    def test_comprehensive_building_code_coverage(self):
        """Test comprehensive coverage of different Building Code sections"""
        building_code_sections = [
            {
                "section": "B1 - Structure",
                "query": "What are the structural design requirements for residential timber framing under B1?",
                "expected_terms": ["b1", "structural", "timber", "framing", "design"]
            },
            {
                "section": "E2 - External Moisture",
                "query": "What are the E2 requirements for cavity construction and drainage?",
                "expected_terms": ["e2", "moisture", "cavity", "drainage", "external"]
            },
            {
                "section": "F2 - Hazardous Building Materials",
                "query": "What are the F2 requirements for asbestos management in renovations?",
                "expected_terms": ["f2", "hazardous", "asbestos", "materials", "renovation"]
            },
            {
                "section": "G5 - Interior Environment",
                "query": "What are the G5 requirements for solid fuel appliance installations?",
                "expected_terms": ["g5", "interior", "solid fuel", "appliance", "installation"]
            },
            {
                "section": "H1 - Energy Efficiency",
                "query": "What are the H1 thermal envelope requirements for different climate zones?",
                "expected_terms": ["h1", "energy", "thermal", "envelope", "climate"]
            }
        ]
        
        all_passed = True
        coverage_results = []
        
        for section_test in building_code_sections:
            try:
                chat_data = {
                    "message": section_test["query"],
                    "enable_compliance_analysis": True,
                    "enable_query_processing": True
                }
                
                response = self.session.post(f"{API_BASE}/chat/enhanced", json=chat_data)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    ai_response = result.get('response', '')
                    citations = result.get('citations', [])
                    sources_used = result.get('sources_used', [])
                    
                    # Check coverage quality
                    response_lower = ai_response.lower()
                    has_expected_terms = sum(1 for term in section_test["expected_terms"] if term in response_lower)
                    has_section_citations = any(section_test["section"].lower()[:2] in str(citation).lower() for citation in citations)
                    substantial_coverage = len(ai_response) > 600
                    has_nzbc_sources = any('nzbc' in source.lower() for source in sources_used)
                    
                    coverage_score = (has_expected_terms / len(section_test["expected_terms"])) * 100
                    
                    section_result = {
                        "section": section_test["section"],
                        "coverage_score": coverage_score,
                        "response_length": len(ai_response),
                        "citations_count": len(citations),
                        "has_section_citations": has_section_citations,
                        "has_nzbc_sources": has_nzbc_sources
                    }
                    coverage_results.append(section_result)
                    
                    if coverage_score >= 80 and substantial_coverage and has_nzbc_sources:
                        self.log_test(f"Building Code Coverage - {section_test['section']}", True, 
                                    f"Excellent coverage: {coverage_score:.0f}% terms, {len(ai_response)} chars, {len(citations)} citations")
                    else:
                        issues = []
                        if coverage_score < 80:
                            issues.append(f"Low term coverage: {coverage_score:.0f}%")
                        if not substantial_coverage:
                            issues.append(f"Short response: {len(ai_response)} chars")
                        if not has_nzbc_sources:
                            issues.append("No NZBC sources")
                        
                        self.log_test(f"Building Code Coverage - {section_test['section']}", False, 
                                    f"Coverage issues: {', '.join(issues)}", section_result)
                        all_passed = False
                else:
                    self.log_test(f"Building Code Coverage - {section_test['section']}", False, 
                                f"HTTP {response.status_code}", response.text)
                    all_passed = False
                    
                time.sleep(1)  # Brief pause between sections
                    
            except Exception as e:
                self.log_test(f"Building Code Coverage - {section_test['section']}", False, f"Error: {str(e)}")
                all_passed = False
        
        # Overall coverage summary
        if coverage_results:
            avg_coverage = sum(r['coverage_score'] for r in coverage_results) / len(coverage_results)
            avg_response_length = sum(r['response_length'] for r in coverage_results) / len(coverage_results)
            sections_with_citations = sum(1 for r in coverage_results if r['has_section_citations'])
            
            summary_details = {
                "avg_coverage_score": avg_coverage,
                "avg_response_length": avg_response_length,
                "sections_with_citations": sections_with_citations,
                "total_sections_tested": len(coverage_results),
                "detailed_results": coverage_results
            }
            
            if avg_coverage >= 75 and sections_with_citations >= 3:
                self.log_test("Overall Building Code Coverage", True, 
                            f"Comprehensive coverage: {avg_coverage:.0f}% avg, {sections_with_citations}/{len(coverage_results)} sections with citations", summary_details)
            else:
                self.log_test("Overall Building Code Coverage", False, 
                            f"Coverage gaps: {avg_coverage:.0f}% avg, {sections_with_citations}/{len(coverage_results)} sections with citations", summary_details)
                all_passed = False
        
        return all_passed
    
    def run_integration_tests(self):
        """Run all NZ Building Code integration tests"""
        print(f"\n🏗️  Starting STRYDA.ai NZ Building Code Integration Tests")
        print(f"Backend URL: {API_BASE}")
        print(f"Session ID: {self.session_id}")
        print("=" * 90)
        print("Testing the newly integrated complete NZ Building Code knowledge base")
        print("Focus: Real Building Code data, 600+ documents, actual NZBC clauses")
        print("=" * 90)
        
        # Integration test suites
        test_suites = [
            ("Knowledge Base Expansion (33→748+ chunks)", self.test_knowledge_base_expansion),
            ("Real Building Code Queries", self.test_real_building_code_queries),
            ("Real Building Code Citations", self.test_real_building_code_citations),
            ("Search Performance (Large Knowledge Base)", self.test_search_performance_with_large_knowledge_base),
            ("PDF Processing System", self.test_pdf_processing_system),
            ("Comprehensive Building Code Coverage", self.test_comprehensive_building_code_coverage)
        ]
        
        passed = 0
        total = len(test_suites)
        
        for test_name, test_func in test_suites:
            print(f"\n🔍 Testing: {test_name}")
            if test_func():
                passed += 1
            time.sleep(2)  # Pause between test suites for system stability
        
        print("\n" + "=" * 90)
        print(f"🏁 NZ Building Code Integration Test Summary: {passed}/{total} test suites passed")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['message']}")
        else:
            print(f"\n🎉 Complete NZ Building Code integration working perfectly!")
            print("✅ Real Building Code data successfully integrated")
            print("✅ 600+ documents from processed Building Code PDF")
            print("✅ Actual NZBC clause references and citations")
            print("✅ Excellent performance with expanded knowledge base")
        
        return passed == total

if __name__ == "__main__":
    tester = NZBuildingCodeIntegrationTester()
    success = tester.run_integration_tests()
    
    if success:
        print("\n🎉 All NZ Building Code integration tests passed!")
        print("The complete Building Code knowledge base is working excellently!")
        exit(0)
    else:
        print("\n⚠️  Some NZ Building Code integration tests failed!")
        print("The Building Code integration may need attention.")
        exit(1)