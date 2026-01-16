#!/usr/bin/env python3
"""
STRYDA.ai Visual Content Retrieval System Testing Suite
Tests the new Intelligent Visual Content Retrieval system that automatically
provides relevant diagrams from STRYDA's knowledge base.

Focus Areas:
1. Enhanced Chat with Visual Content - POST /api/chat/enhanced
2. Visual Content Matching for building queries
3. Response Structure with visual_content array
4. Text Diagrams (ASCII-style diagrams)
5. Multiple Visuals support
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
BACKEND_URL = os.getenv('EXPO_PUBLIC_BACKEND_URL', 'https://rag-scraper.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class VisualContentRetrievalTester:
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
    
    def test_enhanced_chat_visual_content_structure(self):
        """Test that enhanced chat endpoint returns visual_content array"""
        try:
            test_query = {
                "message": "What clearances do I need for a fireplace hearth?",
                "enable_compliance_analysis": True,
                "enable_query_processing": True,
                "session_id": self.session_id
            }
            
            response = self.session.post(f"{API_BASE}/chat/enhanced", json=test_query)
            
            if response.status_code == 200:
                result = response.json()
                
                # Check for visual_content field
                has_visual_content_field = 'visual_content' in result
                visual_content = result.get('visual_content', [])
                is_array = isinstance(visual_content, list)
                
                # Check response structure
                required_fields = ['response', 'citations', 'session_id', 'confidence_score', 
                                 'sources_used', 'processing_time_ms', 'visual_content']
                missing_fields = [field for field in required_fields if field not in result]
                
                details = {
                    "has_visual_content_field": has_visual_content_field,
                    "visual_content_is_array": is_array,
                    "visual_content_count": len(visual_content) if is_array else 0,
                    "missing_fields": missing_fields,
                    "response_structure": list(result.keys())
                }
                
                if has_visual_content_field and is_array and not missing_fields:
                    self.log_test("Enhanced Chat Visual Content Structure", True, 
                                f"Response includes visual_content array with {len(visual_content)} items", details)
                    return True
                else:
                    issues = []
                    if not has_visual_content_field:
                        issues.append("Missing visual_content field")
                    if not is_array:
                        issues.append("visual_content is not an array")
                    if missing_fields:
                        issues.append(f"Missing fields: {missing_fields}")
                    
                    self.log_test("Enhanced Chat Visual Content Structure", False, 
                                f"Structure issues: {', '.join(issues)}", details)
                    return False
            else:
                self.log_test("Enhanced Chat Visual Content Structure", False, 
                            f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Enhanced Chat Visual Content Structure", False, f"Error: {str(e)}")
            return False
    
    def test_visual_content_matching_queries(self):
        """Test visual content retrieval for specific building queries"""
        test_queries = [
            {
                "query": "What clearances do I need for a fireplace hearth?",
                "expected_keywords": ["hearth", "clearance", "fireplace", "solid fuel"],
                "expected_codes": ["G5"],
                "description": "Hearth clearance query"
            },
            {
                "query": "Show me insulation R-values for Auckland",
                "expected_keywords": ["insulation", "r-value", "thermal", "h1"],
                "expected_codes": ["H1"],
                "description": "Insulation requirements query"
            },
            {
                "query": "Weathertightness requirements for window installation",
                "expected_keywords": ["weathertight", "window", "moisture", "e2"],
                "expected_codes": ["E2"],
                "description": "Weathertightness query"
            },
            {
                "query": "Timber framing connection details",
                "expected_keywords": ["timber", "framing", "connection", "nzs"],
                "expected_codes": ["NZS"],
                "description": "Timber framing query"
            },
            {
                "query": "Foundation requirements",
                "expected_keywords": ["foundation", "concrete", "structural", "b1"],
                "expected_codes": ["B1"],
                "description": "Foundation requirements query"
            }
        ]
        
        all_passed = True
        
        for i, test_case in enumerate(test_queries):
            try:
                enhanced_chat_data = {
                    "message": test_case["query"],
                    "enable_compliance_analysis": True,
                    "enable_query_processing": True,
                    "session_id": self.session_id
                }
                
                response = self.session.post(f"{API_BASE}/chat/enhanced", json=enhanced_chat_data)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    visual_content = result.get('visual_content', [])
                    ai_response = result.get('response', '')
                    processing_time = result.get('processing_time_ms', 0)
                    
                    # Check if visual content is relevant
                    relevant_visuals = 0
                    visual_details = []
                    
                    for visual in visual_content:
                        if isinstance(visual, dict):
                            title = visual.get('title', '').lower()
                            description = visual.get('description', '').lower()
                            keywords = visual.get('keywords', [])
                            codes = visual.get('nz_building_codes', [])
                            
                            # Check relevance
                            title_relevant = any(keyword.lower() in title for keyword in test_case["expected_keywords"])
                            desc_relevant = any(keyword.lower() in description for keyword in test_case["expected_keywords"])
                            code_relevant = any(any(expected_code.lower() in str(code).lower() for code in codes) 
                                              for expected_code in test_case["expected_codes"])
                            
                            if title_relevant or desc_relevant or code_relevant:
                                relevant_visuals += 1
                            
                            visual_details.append({
                                "title": visual.get('title', 'No title'),
                                "content_type": visual.get('content_type', 'Unknown'),
                                "keywords_count": len(keywords) if isinstance(keywords, list) else 0,
                                "codes_count": len(codes) if isinstance(codes, list) else 0,
                                "has_text_diagram": bool(visual.get('text_diagram'))
                            })
                    
                    # Quality checks
                    has_visuals = len(visual_content) > 0
                    has_relevant_visuals = relevant_visuals > 0
                    reasonable_time = processing_time < 15000  # Less than 15 seconds
                    substantial_response = len(ai_response) > 200
                    
                    details = {
                        "visual_content_count": len(visual_content),
                        "relevant_visuals": relevant_visuals,
                        "processing_time_ms": processing_time,
                        "response_length": len(ai_response),
                        "visual_details": visual_details[:2]  # First 2 visuals for details
                    }
                    
                    if has_visuals and reasonable_time and substantial_response:
                        self.log_test(f"Visual Content Query {i+1} ({test_case['description']})", True, 
                                    f"Retrieved {len(visual_content)} visuals ({relevant_visuals} relevant) in {processing_time:.1f}ms", details)
                    else:
                        issues = []
                        if not has_visuals:
                            issues.append("No visual content retrieved")
                        if not reasonable_time:
                            issues.append(f"Slow processing: {processing_time}ms")
                        if not substantial_response:
                            issues.append("Response too short")
                        
                        self.log_test(f"Visual Content Query {i+1} ({test_case['description']})", False, 
                                    f"Issues: {', '.join(issues)}", details)
                        all_passed = False
                else:
                    self.log_test(f"Visual Content Query {i+1} ({test_case['description']})", False, 
                                f"HTTP {response.status_code}", response.text)
                    all_passed = False
                    
                # Brief pause between queries
                time.sleep(1)
                    
            except Exception as e:
                self.log_test(f"Visual Content Query {i+1} ({test_case['description']})", False, f"Error: {str(e)}")
                all_passed = False
        
        return all_passed
    
    def test_visual_content_data_structure(self):
        """Test the structure and completeness of visual content objects"""
        try:
            test_query = {
                "message": "Timber framing connection details for NZS 3604",
                "enable_compliance_analysis": True,
                "enable_query_processing": True,
                "session_id": self.session_id
            }
            
            response = self.session.post(f"{API_BASE}/chat/enhanced", json=test_query)
            
            if response.status_code == 200:
                result = response.json()
                visual_content = result.get('visual_content', [])
                
                if len(visual_content) == 0:
                    self.log_test("Visual Content Data Structure", False, 
                                "No visual content returned to test structure")
                    return False
                
                # Check structure of visual content objects
                required_visual_fields = ['id', 'title', 'description', 'content_type', 
                                        'source_document', 'keywords', 'nz_building_codes', 'text_diagram']
                
                valid_visuals = 0
                structure_issues = []
                visual_analysis = []
                
                for i, visual in enumerate(visual_content):
                    if isinstance(visual, dict):
                        missing_fields = [field for field in required_visual_fields if field not in visual]
                        
                        # Check field types
                        type_issues = []
                        if 'keywords' in visual and not isinstance(visual['keywords'], list):
                            type_issues.append("keywords not a list")
                        if 'nz_building_codes' in visual and not isinstance(visual['nz_building_codes'], list):
                            type_issues.append("nz_building_codes not a list")
                        
                        visual_analysis.append({
                            "index": i,
                            "title": visual.get('title', 'No title')[:50],
                            "content_type": visual.get('content_type', 'Unknown'),
                            "missing_fields": missing_fields,
                            "type_issues": type_issues,
                            "has_text_diagram": bool(visual.get('text_diagram')),
                            "keywords_count": len(visual.get('keywords', [])) if isinstance(visual.get('keywords'), list) else 0,
                            "codes_count": len(visual.get('nz_building_codes', [])) if isinstance(visual.get('nz_building_codes'), list) else 0
                        })
                        
                        if not missing_fields and not type_issues:
                            valid_visuals += 1
                        else:
                            structure_issues.extend(missing_fields + type_issues)
                
                details = {
                    "total_visuals": len(visual_content),
                    "valid_visuals": valid_visuals,
                    "structure_issues": list(set(structure_issues)),
                    "visual_analysis": visual_analysis
                }
                
                if valid_visuals > 0 and len(structure_issues) == 0:
                    self.log_test("Visual Content Data Structure", True, 
                                f"All {valid_visuals} visual objects have correct structure", details)
                    return True
                else:
                    self.log_test("Visual Content Data Structure", False, 
                                f"Structure issues found: {valid_visuals}/{len(visual_content)} valid visuals", details)
                    return False
            else:
                self.log_test("Visual Content Data Structure", False, 
                            f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Visual Content Data Structure", False, f"Error: {str(e)}")
            return False
    
    def test_multiple_visuals_support(self):
        """Test that queries can return multiple relevant diagrams"""
        try:
            # Use a broad query that should return multiple visuals
            broad_query = {
                "message": "Building construction requirements including structural, thermal, and fire safety",
                "enable_compliance_analysis": True,
                "enable_query_processing": True,
                "session_id": self.session_id
            }
            
            response = self.session.post(f"{API_BASE}/chat/enhanced", json=broad_query)
            
            if response.status_code == 200:
                result = response.json()
                visual_content = result.get('visual_content', [])
                processing_time = result.get('processing_time_ms', 0)
                
                # Check for multiple visuals
                has_multiple_visuals = len(visual_content) > 1
                diverse_content_types = len(set(visual.get('content_type', 'unknown') for visual in visual_content if isinstance(visual, dict))) > 1
                diverse_codes = len(set(str(code) for visual in visual_content if isinstance(visual, dict) 
                                      for code in visual.get('nz_building_codes', []))) > 1
                
                # Analyze visual diversity
                content_types = []
                building_codes = []
                trade_categories = []
                
                for visual in visual_content:
                    if isinstance(visual, dict):
                        content_types.append(visual.get('content_type', 'unknown'))
                        building_codes.extend(visual.get('nz_building_codes', []))
                        trade_categories.extend(visual.get('trade_categories', []))
                
                details = {
                    "total_visuals": len(visual_content),
                    "unique_content_types": list(set(content_types)),
                    "unique_building_codes": list(set(building_codes)),
                    "unique_trade_categories": list(set(trade_categories)),
                    "processing_time_ms": processing_time,
                    "diverse_content_types": diverse_content_types,
                    "diverse_codes": diverse_codes
                }
                
                if has_multiple_visuals and (diverse_content_types or diverse_codes):
                    self.log_test("Multiple Visuals Support", True, 
                                f"Retrieved {len(visual_content)} diverse visuals covering multiple aspects", details)
                    return True
                else:
                    issues = []
                    if not has_multiple_visuals:
                        issues.append(f"Only {len(visual_content)} visual(s) returned")
                    if not diverse_content_types and not diverse_codes:
                        issues.append("Visuals lack diversity")
                    
                    self.log_test("Multiple Visuals Support", False, 
                                f"Issues: {', '.join(issues)}", details)
                    return False
            else:
                self.log_test("Multiple Visuals Support", False, 
                            f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Multiple Visuals Support", False, f"Error: {str(e)}")
            return False
    
    def test_text_diagram_generation(self):
        """Test that text diagrams are being generated for NZ building scenarios"""
        try:
            diagram_queries = [
                {
                    "query": "Show me the clearance requirements for a solid fuel fireplace hearth",
                    "expected_diagram_content": ["clearance", "hearth", "fireplace"],
                    "description": "Fireplace clearance diagram"
                },
                {
                    "query": "Timber framing connection details for wall to floor junction",
                    "expected_diagram_content": ["timber", "connection", "wall", "floor"],
                    "description": "Timber connection diagram"
                }
            ]
            
            all_passed = True
            
            for i, test_case in enumerate(diagram_queries):
                enhanced_chat_data = {
                    "message": test_case["query"],
                    "enable_compliance_analysis": True,
                    "enable_query_processing": True,
                    "session_id": self.session_id
                }
                
                response = self.session.post(f"{API_BASE}/chat/enhanced", json=enhanced_chat_data)
                
                if response.status_code == 200:
                    result = response.json()
                    visual_content = result.get('visual_content', [])
                    
                    # Check for text diagrams
                    visuals_with_diagrams = 0
                    diagram_analysis = []
                    
                    for visual in visual_content:
                        if isinstance(visual, dict):
                            text_diagram = visual.get('text_diagram', '')
                            has_diagram = bool(text_diagram and len(str(text_diagram)) > 10)
                            
                            if has_diagram:
                                visuals_with_diagrams += 1
                                # Check if diagram content is relevant
                                diagram_lower = str(text_diagram).lower()
                                relevant_content = any(expected.lower() in diagram_lower 
                                                     for expected in test_case["expected_diagram_content"])
                                
                                diagram_analysis.append({
                                    "title": visual.get('title', 'No title')[:50],
                                    "diagram_length": len(str(text_diagram)),
                                    "has_relevant_content": relevant_content,
                                    "diagram_preview": str(text_diagram)[:100] + "..." if len(str(text_diagram)) > 100 else str(text_diagram)
                                })
                    
                    details = {
                        "total_visuals": len(visual_content),
                        "visuals_with_diagrams": visuals_with_diagrams,
                        "diagram_analysis": diagram_analysis
                    }
                    
                    if visuals_with_diagrams > 0:
                        self.log_test(f"Text Diagram {i+1} ({test_case['description']})", True, 
                                    f"{visuals_with_diagrams}/{len(visual_content)} visuals include text diagrams", details)
                    else:
                        self.log_test(f"Text Diagram {i+1} ({test_case['description']})", False, 
                                    "No text diagrams found in visual content", details)
                        all_passed = False
                else:
                    self.log_test(f"Text Diagram {i+1} ({test_case['description']})", False, 
                                f"HTTP {response.status_code}", response.text)
                    all_passed = False
                
                time.sleep(1)
            
            return all_passed
        except Exception as e:
            self.log_test("Text Diagram Generation", False, f"Error: {str(e)}")
            return False
    
    def test_proactive_visual_system(self):
        """Test that visual content is automatically provided without explicit requests"""
        try:
            # Test queries that don't explicitly ask for diagrams but should get them
            implicit_queries = [
                "What's the minimum R-value for ceiling insulation in Auckland?",
                "How do I install weathertightness membrane around windows?",
                "What size timber do I need for a 3.6m span deck joist?"
            ]
            
            all_passed = True
            
            for i, query in enumerate(implicit_queries):
                enhanced_chat_data = {
                    "message": query,
                    "enable_compliance_analysis": True,
                    "enable_query_processing": True,
                    "session_id": self.session_id
                }
                
                response = self.session.post(f"{API_BASE}/chat/enhanced", json=enhanced_chat_data)
                
                if response.status_code == 200:
                    result = response.json()
                    visual_content = result.get('visual_content', [])
                    ai_response = result.get('response', '')
                    
                    # Check proactive visual provision
                    has_proactive_visuals = len(visual_content) > 0
                    response_mentions_visuals = any(term in ai_response.lower() 
                                                  for term in ['diagram', 'visual', 'illustration', 'drawing'])
                    
                    details = {
                        "query": query,
                        "visual_content_count": len(visual_content),
                        "response_mentions_visuals": response_mentions_visuals,
                        "response_length": len(ai_response)
                    }
                    
                    if has_proactive_visuals:
                        self.log_test(f"Proactive Visual {i+1}", True, 
                                    f"Automatically provided {len(visual_content)} visuals without explicit request", details)
                    else:
                        self.log_test(f"Proactive Visual {i+1}", False, 
                                    "No proactive visual content provided", details)
                        all_passed = False
                else:
                    self.log_test(f"Proactive Visual {i+1}", False, 
                                f"HTTP {response.status_code}", response.text)
                    all_passed = False
                
                time.sleep(1)
            
            return all_passed
        except Exception as e:
            self.log_test("Proactive Visual System", False, f"Error: {str(e)}")
            return False
    
    def run_visual_content_tests(self):
        """Run all visual content retrieval tests"""
        print(f"\n🎯 Starting STRYDA.ai Visual Content Retrieval System Tests")
        print(f"Backend URL: {API_BASE}")
        print(f"Session ID: {self.session_id}")
        print("=" * 80)
        
        # Visual content test suites
        test_suites = [
            ("Enhanced Chat Visual Content Structure", self.test_enhanced_chat_visual_content_structure),
            ("Visual Content Matching Queries", self.test_visual_content_matching_queries),
            ("Visual Content Data Structure", self.test_visual_content_data_structure),
            ("Multiple Visuals Support", self.test_multiple_visuals_support),
            ("Text Diagram Generation", self.test_text_diagram_generation),
            ("Proactive Visual System", self.test_proactive_visual_system)
        ]
        
        passed = 0
        total = len(test_suites)
        
        for test_name, test_func in test_suites:
            print(f"\n📋 Testing: {test_name}")
            if test_func():
                passed += 1
            time.sleep(1)  # Brief pause between test suites
        
        print("\n" + "=" * 80)
        print(f"🏁 Visual Content Test Summary: {passed}/{total} test suites passed")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['message']}")
        else:
            print(f"\n🎉 All visual content retrieval tests passed!")
        
        return passed == total

if __name__ == "__main__":
    tester = VisualContentRetrievalTester()
    success = tester.run_visual_content_tests()
    
    if success:
        print("\n🎉 Visual Content Retrieval System working perfectly!")
        exit(0)
    else:
        print("\n⚠️  Some visual content tests failed!")
        exit(1)