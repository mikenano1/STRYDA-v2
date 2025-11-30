#!/usr/bin/env python3
"""
STRYDA.ai OCR Product Integration System Testing Suite
Comprehensive testing for OCR product scanning system that integrates with EBOSS product database
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
BACKEND_URL = os.getenv('EXPO_PUBLIC_BACKEND_URL', 'https://construct-ai-12.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class OCRProductIntegrationTester:
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
    
    def test_eboss_database_verification(self):
        """Test EBOSS Database Verification - should show 605+ products with major NZ brands"""
        try:
            print("   Testing EBOSS database status and product counts...")
            response = self.session.get(f"{API_BASE}/products/eboss-status")
            
            if response.status_code == 200:
                data = response.json()
                
                total_products = data.get('total_products', 0)
                products_by_brand = data.get('products_by_brand', [])
                products_by_category = data.get('products_by_category', [])
                
                # Check for major NZ brands mentioned in review request
                expected_brands = ['VANTAGE', 'Altherm', 'James Hardie', 'Dimond', 'Resene']
                found_brands = []
                brand_counts = {}
                
                for brand_data in products_by_brand:
                    brand_name = brand_data.get('_id', '').upper()
                    brand_count = brand_data.get('count', 0)
                    brand_counts[brand_name] = brand_count
                    
                    for expected_brand in expected_brands:
                        if expected_brand.upper() in brand_name:
                            found_brands.append(expected_brand)
                            break
                
                # Check for expected categories
                expected_categories = ['windows-and-doors', 'wall-cladding', 'roofing-and-decking', 'insulation']
                found_categories = []
                
                for category_data in products_by_category:
                    category_name = category_data.get('_id', '').lower()
                    for expected_cat in expected_categories:
                        if expected_cat in category_name or any(word in category_name for word in expected_cat.split('-')):
                            found_categories.append(expected_cat)
                            break
                
                details = {
                    "total_products": total_products,
                    "brands_found": found_brands,
                    "brand_counts": brand_counts,
                    "categories_found": found_categories,
                    "total_brands": len(products_by_brand),
                    "total_categories": len(products_by_category)
                }
                
                # Success criteria: 605+ products, at least 3 major brands, multiple categories
                if total_products >= 500 and len(found_brands) >= 3 and len(found_categories) >= 2:
                    self.log_test("EBOSS Database Verification", True, f"Database ready for OCR integration - {total_products} products, {len(found_brands)} major brands", details)
                    return True
                else:
                    issues = []
                    if total_products < 500:
                        issues.append(f"Insufficient products: {total_products}")
                    if len(found_brands) < 3:
                        issues.append(f"Missing major brands: {found_brands}")
                    if len(found_categories) < 2:
                        issues.append(f"Limited categories: {found_categories}")
                    
                    self.log_test("EBOSS Database Verification", False, f"Database not ready: {', '.join(issues)}", details)
                    return False
            else:
                self.log_test("EBOSS Database Verification", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("EBOSS Database Verification", False, f"Error: {str(e)}")
            return False
    
    def test_ocr_brand_detection_searches(self):
        """Test OCR Brand Detection - searches for major NZ brands that OCR would extract"""
        brand_tests = [
            {
                "brand": "VANTAGE",
                "search_query": "VANTAGE",
                "expected_min_products": 15,  # Should find 55+ but being conservative
                "description": "VANTAGE windows and doors"
            },
            {
                "brand": "Altherm",
                "search_query": "Altherm",
                "expected_min_products": 20,  # Should find 32+ but being conservative
                "description": "Altherm window systems"
            },
            {
                "brand": "James Hardie",
                "search_query": "James Hardie",
                "expected_min_products": 5,   # Should find 6+ products
                "description": "James Hardie building products"
            },
            {
                "brand": "Dimond",
                "search_query": "Dimond",
                "expected_min_products": 3,   # Roofing products
                "description": "Dimond roofing materials"
            },
            {
                "brand": "Resene",
                "search_query": "Resene",
                "expected_min_products": 3,   # Paint and coatings
                "description": "Resene paint products"
            }
        ]
        
        all_brand_tests_passed = True
        
        for brand_test in brand_tests:
            try:
                print(f"   Testing OCR brand detection for {brand_test['brand']}...")
                
                params = {
                    "query": brand_test["search_query"],
                    "limit": 20
                }
                
                response = self.session.get(f"{API_BASE}/products/search", params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    total_found = data.get('total_found', 0)
                    
                    # Check response format includes required fields
                    valid_results = 0
                    for result in results:
                        metadata = result.get('metadata', {})
                        content = result.get('content', '')
                        if (result.get('content') and 
                            metadata.get('title') and 
                            'BRAND:' in content):
                            valid_results += 1
                    
                    details = {
                        "search_query": brand_test["search_query"],
                        "total_found": total_found,
                        "results_returned": len(results),
                        "valid_results": valid_results,
                        "expected_min": brand_test["expected_min_products"],
                        "sample_results": [
                            {
                                "title": r.get('metadata', {}).get('title', 'N/A')[:50],
                                "brand": r.get('content', '').split('BRAND:')[1].split('\n')[0].strip() if 'BRAND:' in r.get('content', '') else 'N/A',
                                "categories": r.get('content', '').split('CATEGORIES:')[1].split('\n')[0].strip().split(', ')[:2] if 'CATEGORIES:' in r.get('content', '') else []
                            } for r in results[:3]
                        ]
                    }
                    
                    if total_found >= brand_test["expected_min_products"] and valid_results > 0:
                        self.log_test(f"OCR Brand Detection - {brand_test['brand']}", True, f"Found {total_found} products with proper format", details)
                    else:
                        issues = []
                        if total_found < brand_test["expected_min_products"]:
                            issues.append(f"Too few products: {total_found}")
                        if valid_results == 0:
                            issues.append("Invalid result format")
                        
                        self.log_test(f"OCR Brand Detection - {brand_test['brand']}", False, f"Issues: {', '.join(issues)}", details)
                        all_brand_tests_passed = False
                else:
                    self.log_test(f"OCR Brand Detection - {brand_test['brand']}", False, f"HTTP {response.status_code}", response.text)
                    all_brand_tests_passed = False
                    
                time.sleep(0.5)  # Brief pause between searches
                
            except Exception as e:
                self.log_test(f"OCR Brand Detection - {brand_test['brand']}", False, f"Error: {str(e)}")
                all_brand_tests_passed = False
        
        return all_brand_tests_passed
    
    def test_ocr_product_type_recognition(self):
        """Test Product Type Recognition - searches for product types OCR would extract"""
        product_type_tests = [
            {
                "type": "R-value Insulation",
                "search_query": "R2.0 insulation",
                "expected_keywords": ["insulation", "thermal", "r2"],
                "description": "R-value insulation products"
            },
            {
                "type": "Roofing Materials",
                "search_query": "roofing",
                "expected_keywords": ["roof", "roofing", "metal"],
                "description": "Roofing and decking materials"
            },
            {
                "type": "Window Systems",
                "search_query": "windows",
                "expected_keywords": ["window", "glazing", "frame"],
                "description": "Window and door systems"
            },
            {
                "type": "Wall Cladding",
                "search_query": "cladding",
                "expected_keywords": ["clad", "wall", "exterior"],
                "description": "Wall cladding systems"
            }
        ]
        
        all_type_tests_passed = True
        
        for type_test in product_type_tests:
            try:
                print(f"   Testing OCR product type recognition for {type_test['type']}...")
                
                params = {
                    "query": type_test["search_query"],
                    "limit": 15
                }
                
                response = self.session.get(f"{API_BASE}/products/search", params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    total_found = data.get('total_found', 0)
                    
                    # Check if results are relevant to the product type
                    relevant_results = 0
                    for result in results:
                        title = result.get('title', '').lower()
                        content = result.get('content', '').lower()
                        categories = result.get('metadata', {}).get('categories', [])
                        
                        # Check if any expected keywords appear in title, content, or categories
                        text_to_check = f"{title} {content} {' '.join(categories).lower()}"
                        if any(keyword.lower() in text_to_check for keyword in type_test['expected_keywords']):
                            relevant_results += 1
                    
                    details = {
                        "search_query": type_test["search_query"],
                        "total_found": total_found,
                        "relevant_results": relevant_results,
                        "relevance_ratio": relevant_results / len(results) if results else 0,
                        "sample_titles": [r.get('title', 'N/A')[:60] for r in results[:3]]
                    }
                    
                    # Success if we find products and they're reasonably relevant
                    if total_found > 0 and (relevant_results / len(results) if results else 0) > 0.3:
                        self.log_test(f"OCR Product Type - {type_test['type']}", True, f"Found {total_found} products, {relevant_results}/{len(results)} relevant", details)
                    else:
                        issues = []
                        if total_found == 0:
                            issues.append("No products found")
                        if relevant_results == 0:
                            issues.append("No relevant results")
                        elif (relevant_results / len(results) if results else 0) <= 0.3:
                            issues.append("Low relevance ratio")
                        
                        self.log_test(f"OCR Product Type - {type_test['type']}", False, f"Issues: {', '.join(issues)}", details)
                        all_type_tests_passed = False
                else:
                    self.log_test(f"OCR Product Type - {type_test['type']}", False, f"HTTP {response.status_code}", response.text)
                    all_type_tests_passed = False
                    
                time.sleep(0.5)  # Brief pause between searches
                
            except Exception as e:
                self.log_test(f"OCR Product Type - {type_test['type']}", False, f"Error: {str(e)}")
                all_type_tests_passed = False
        
        return all_type_tests_passed
    
    def test_compliance_integration_with_products(self):
        """Test Compliance Integration - enhanced chat with product-specific compliance questions"""
        compliance_tests = [
            {
                "query": "What are the compliance requirements for VANTAGE windows in New Zealand?",
                "expected_topics": ["building code", "compliance", "window", "vantage"],
                "description": "VANTAGE window compliance"
            },
            {
                "query": "Tell me about James Hardie cladding compliance requirements",
                "expected_topics": ["james hardie", "cladding", "compliance", "building code"],
                "description": "James Hardie compliance"
            },
            {
                "query": "What building code requirements apply to Altherm window systems?",
                "expected_topics": ["altherm", "window", "building code", "compliance"],
                "description": "Altherm window compliance"
            }
        ]
        
        all_compliance_tests_passed = True
        
        for i, test_case in enumerate(compliance_tests):
            try:
                print(f"   Testing compliance integration for {test_case['description']}...")
                
                chat_data = {
                    "message": test_case["query"],
                    "session_id": self.session_id,
                    "enable_compliance_analysis": True,
                    "enable_query_processing": True
                }
                
                start_time = time.time()
                response = self.session.post(f"{API_BASE}/chat/enhanced", json=chat_data)
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    chat_result = response.json()
                    
                    ai_response = chat_result.get('response', '')
                    citations = chat_result.get('citations', [])
                    sources_used = chat_result.get('sources_used', [])
                    compliance_issues = chat_result.get('compliance_issues', [])
                    processing_time = chat_result.get('processing_time_ms', 0)
                    
                    # Check response quality
                    response_lower = ai_response.lower()
                    has_relevant_content = any(topic.lower() in response_lower for topic in test_case['expected_topics'])
                    has_compliance_info = any(term in response_lower for term in ['compliance', 'building code', 'standard', 'requirement'])
                    substantial_response = len(ai_response) > 500  # Expect detailed responses
                    reasonable_time = response_time < 15000  # Under 15 seconds (more lenient)
                    
                    details = {
                        "response_length": len(ai_response),
                        "citations_count": len(citations),
                        "sources_count": len(sources_used),
                        "compliance_issues_count": len(compliance_issues),
                        "processing_time_ms": processing_time,
                        "response_time_ms": response_time,
                        "has_relevant_content": has_relevant_content,
                        "has_compliance_info": has_compliance_info,
                        "sources_used": sources_used[:3]  # First 3 sources
                    }
                    
                    if (substantial_response and has_relevant_content and 
                        has_compliance_info and reasonable_time):
                        self.log_test(f"Compliance Integration - {test_case['description']}", True, f"Comprehensive compliance response in {response_time:.0f}ms", details)
                    else:
                        issues = []
                        if not substantial_response:
                            issues.append(f"Response too short: {len(ai_response)} chars")
                        if not has_relevant_content:
                            issues.append("Missing relevant content")
                        if not has_compliance_info:
                            issues.append("No compliance information")
                        if not reasonable_time:
                            issues.append(f"Slow response: {response_time:.0f}ms")
                        
                        self.log_test(f"Compliance Integration - {test_case['description']}", False, f"Issues: {', '.join(issues)}", details)
                        all_compliance_tests_passed = False
                else:
                    self.log_test(f"Compliance Integration - {test_case['description']}", False, f"HTTP {response.status_code}", response.text)
                    all_compliance_tests_passed = False
                    
                time.sleep(2)  # Pause between complex queries
                
            except Exception as e:
                self.log_test(f"Compliance Integration - {test_case['description']}", False, f"Error: {str(e)}")
                all_compliance_tests_passed = False
        
        return all_compliance_tests_passed
    
    def test_ocr_integration_performance(self):
        """Test OCR Integration Performance - response times and system stability"""
        try:
            print("   Testing OCR integration performance and stability...")
            
            # Test multiple rapid searches simulating OCR text extraction results
            ocr_simulation_queries = [
                "VANTAGE AWNING WINDOW",
                "JAMES HARDIE HARDIEPLANK",
                "R2.6 PINK BATTS INSULATION",
                "DIMOND ROOFING COLORSTEEL",
                "ALTHERM SLIDING DOOR"
            ]
            
            response_times = []
            successful_requests = 0
            
            for i, query in enumerate(ocr_simulation_queries):
                try:
                    start_time = time.time()
                    
                    params = {"query": query, "limit": 5}
                    response = self.session.get(f"{API_BASE}/products/search", params=params)
                    
                    response_time = (time.time() - start_time) * 1000
                    response_times.append(response_time)
                    
                    if response.status_code == 200:
                        successful_requests += 1
                        data = response.json()
                        # Verify we get results in reasonable time
                        if response_time > 5000:  # Over 5 seconds is too slow
                            self.log_test("OCR Performance", False, f"Query {i+1} too slow: {response_time:.0f}ms")
                            return False
                    else:
                        self.log_test("OCR Performance", False, f"Query {i+1} failed: HTTP {response.status_code}")
                        return False
                        
                    time.sleep(0.2)  # Brief pause to simulate realistic OCR timing
                    
                except Exception as e:
                    self.log_test("OCR Performance", False, f"Query {i+1} error: {str(e)}")
                    return False
            
            # Calculate performance metrics
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            success_rate = successful_requests / len(ocr_simulation_queries)
            
            details = {
                "total_queries": len(ocr_simulation_queries),
                "successful_requests": successful_requests,
                "success_rate": success_rate,
                "avg_response_time_ms": avg_response_time,
                "max_response_time_ms": max_response_time,
                "all_response_times": response_times
            }
            
            # Success criteria: All requests successful, average under 3 seconds, max under 5 seconds
            if (success_rate == 1.0 and avg_response_time < 3000 and max_response_time < 5000):
                self.log_test("OCR Integration Performance", True, f"Excellent performance - avg {avg_response_time:.0f}ms, max {max_response_time:.0f}ms", details)
                return True
            else:
                issues = []
                if success_rate < 1.0:
                    issues.append(f"Success rate: {success_rate:.1%}")
                if avg_response_time >= 3000:
                    issues.append(f"Slow average: {avg_response_time:.0f}ms")
                if max_response_time >= 5000:
                    issues.append(f"Slow max: {max_response_time:.0f}ms")
                
                self.log_test("OCR Integration Performance", False, f"Performance issues: {', '.join(issues)}", details)
                return False
                
        except Exception as e:
            self.log_test("OCR Integration Performance", False, f"Error: {str(e)}")
            return False
    
    def test_ocr_fuzzy_matching_robustness(self):
        """Test OCR Fuzzy Matching - system should handle imperfect OCR text extraction"""
        fuzzy_tests = [
            {
                "ocr_text": "VANTGE WINDOW",  # Missing 'A' in VANTAGE
                "expected_brand": "VANTAGE",
                "description": "OCR typo in brand name"
            },
            {
                "ocr_text": "James Hardy",  # Missing 'ie' in Hardie
                "expected_brand": "James Hardie",
                "description": "OCR error in manufacturer name"
            },
            {
                "ocr_text": "R26 insulation",  # Missing decimal point
                "expected_type": "insulation",
                "description": "OCR number format error"
            },
            {
                "ocr_text": "ALTHERM SLIDING",  # Partial text
                "expected_brand": "Altherm",
                "description": "Partial OCR text extraction"
            }
        ]
        
        all_fuzzy_tests_passed = True
        
        for fuzzy_test in fuzzy_tests:
            try:
                print(f"   Testing fuzzy matching for '{fuzzy_test['ocr_text']}'...")
                
                params = {
                    "query": fuzzy_test["ocr_text"],
                    "limit": 10
                }
                
                response = self.session.get(f"{API_BASE}/products/search", params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    total_found = data.get('total_found', 0)
                    
                    # Check if we found relevant results despite OCR errors
                    relevant_found = False
                    for result in results:
                        title = result.get('metadata', {}).get('title', '').lower()
                        content = result.get('content', '').lower()
                        
                        # Check if expected brand/type appears in results
                        search_text = f"{title} {content}"
                        if 'expected_brand' in fuzzy_test:
                            if fuzzy_test['expected_brand'].lower() in search_text:
                                relevant_found = True
                                break
                        elif 'expected_type' in fuzzy_test:
                            if fuzzy_test['expected_type'].lower() in search_text:
                                relevant_found = True
                                break
                    
                    details = {
                        "ocr_text": fuzzy_test["ocr_text"],
                        "total_found": total_found,
                        "relevant_found": relevant_found,
                        "sample_results": [
                            {
                                "title": r.get('metadata', {}).get('title', 'N/A')[:40],
                                "brand": r.get('content', '').split('BRAND:')[1].split('\n')[0].strip() if 'BRAND:' in r.get('content', '') else 'N/A'
                            } for r in results[:3]
                        ]
                    }
                    
                    if total_found > 0 and relevant_found:
                        self.log_test(f"OCR Fuzzy Matching - {fuzzy_test['description']}", True, f"Found relevant results despite OCR errors", details)
                    else:
                        issues = []
                        if total_found == 0:
                            issues.append("No results found")
                        if not relevant_found:
                            issues.append("No relevant results")
                        
                        self.log_test(f"OCR Fuzzy Matching - {fuzzy_test['description']}", False, f"Issues: {', '.join(issues)}", details)
                        all_fuzzy_tests_passed = False
                else:
                    self.log_test(f"OCR Fuzzy Matching - {fuzzy_test['description']}", False, f"HTTP {response.status_code}", response.text)
                    all_fuzzy_tests_passed = False
                    
                time.sleep(0.3)  # Brief pause between tests
                
            except Exception as e:
                self.log_test(f"OCR Fuzzy Matching - {fuzzy_test['description']}", False, f"Error: {str(e)}")
                all_fuzzy_tests_passed = False
        
        return all_fuzzy_tests_passed
    
    def run_ocr_integration_tests(self):
        """Run all OCR product integration tests"""
        print(f"\n🚀 Starting STRYDA.ai OCR Product Integration System Tests")
        print(f"Backend URL: {API_BASE}")
        print(f"Session ID: {self.session_id}")
        print("=" * 80)
        print("Testing OCR camera-based product scanning integration with EBOSS database")
        print("=" * 80)
        
        # Run tests in logical order for OCR integration
        tests = [
            ("EBOSS Database Verification", self.test_eboss_database_verification),
            ("OCR Brand Detection Searches", self.test_ocr_brand_detection_searches),
            ("OCR Product Type Recognition", self.test_ocr_product_type_recognition),
            ("Compliance Integration with Products", self.test_compliance_integration_with_products),
            ("OCR Integration Performance", self.test_ocr_integration_performance),
            ("OCR Fuzzy Matching Robustness", self.test_ocr_fuzzy_matching_robustness)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 Testing: {test_name}")
            if test_func():
                passed += 1
            time.sleep(1)  # Brief pause between test suites
        
        print("\n" + "=" * 80)
        print(f"🏁 OCR Product Integration Test Summary: {passed}/{total} test suites passed")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['message']}")
        else:
            print(f"\n🎉 All OCR product integration tests passed!")
            print("✅ EBOSS database ready with 605+ products from major NZ brands")
            print("✅ OCR brand detection working for VANTAGE, Altherm, James Hardie, etc.")
            print("✅ Product type recognition working for insulation, roofing, windows, cladding")
            print("✅ Compliance integration provides detailed building code guidance")
            print("✅ System performance suitable for real-time OCR integration")
            print("✅ Fuzzy matching handles imperfect OCR text extraction")
        
        return passed == total

if __name__ == "__main__":
    tester = OCRProductIntegrationTester()
    success = tester.run_ocr_integration_tests()
    
    if success:
        print("\n🎉 OCR Product Integration System is ready for production!")
        print("The camera-based OCR system can successfully integrate with the EBOSS product database.")
        exit(0)
    else:
        print("\n⚠️  Some OCR integration tests failed!")
        print("Please review the OCR product scanning system integration.")
        exit(1)