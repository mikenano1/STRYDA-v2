#!/usr/bin/env python3
"""
STRYDA.ai Enhanced PDF Processing System Testing Suite
Tests the new Enhanced PDF Processing endpoints and functionality
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
BACKEND_URL = os.getenv('EXPO_PUBLIC_BACKEND_URL', 'https://gemini-stryda.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class EnhancedPDFTester:
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
        if details and not success:
            print(f"   Details: {details}")
    
    def test_enhanced_pdf_status_endpoint(self):
        """Test GET /api/knowledge/enhanced-pdf-status endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/knowledge/enhanced-pdf-status")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields in response
                required_fields = ['last_updated']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    # Check for processing statistics
                    has_stats = any(key in data for key in ['total_documents', 'total_chunks', 'recent_batches'])
                    
                    details = {
                        "response_structure": list(data.keys()),
                        "has_processing_stats": has_stats,
                        "recent_batches_count": len(data.get('recent_batches', []))
                    }
                    
                    self.log_test("Enhanced PDF Status Endpoint", True, 
                                "Status endpoint accessible with proper structure", details)
                    return True
                else:
                    self.log_test("Enhanced PDF Status Endpoint", False, 
                                f"Missing required fields: {missing_fields}", data)
                    return False
            else:
                self.log_test("Enhanced PDF Status Endpoint", False, 
                            f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Enhanced PDF Status Endpoint", False, f"Connection error: {str(e)}")
            return False
    
    def test_batch_processing_structure(self):
        """Test POST /api/knowledge/process-pdf-batch endpoint structure"""
        try:
            # Test with minimal valid structure (don't actually process)
            test_batch = {
                "pdf_sources": [
                    {
                        "url": "https://example.com/test.pdf",
                        "title": "Test Building Code Document",
                        "type": "building_code",
                        "organization": "MBIE"
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/knowledge/process-pdf-batch", json=test_batch)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                required_fields = ['message', 'batch_id', 'total_pdfs', 'processing_started']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    details = {
                        "batch_id": data.get('batch_id'),
                        "total_pdfs": data.get('total_pdfs'),
                        "processing_started": data.get('processing_started'),
                        "message": data.get('message')
                    }
                    
                    self.log_test("Batch Processing Structure", True, 
                                "Batch processing endpoint accepts requests with proper response structure", details)
                    return True
                else:
                    self.log_test("Batch Processing Structure", False, 
                                f"Missing required response fields: {missing_fields}", data)
                    return False
            else:
                self.log_test("Batch Processing Structure", False, 
                            f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Batch Processing Structure", False, f"Error: {str(e)}")
            return False
    
    def test_pdf_classification_system(self):
        """Test document type classification capabilities"""
        try:
            # Test different document types
            document_types = [
                {
                    "url": "https://example.com/building-code.pdf",
                    "title": "NZ Building Code Handbook",
                    "type": "building_code",
                    "organization": "MBIE"
                },
                {
                    "url": "https://example.com/council-regulation.pdf", 
                    "title": "Auckland Council Building Regulations",
                    "type": "council_regulation",
                    "organization": "Auckland Council"
                },
                {
                    "url": "https://example.com/manufacturer-spec.pdf",
                    "title": "GIB Installation Guide",
                    "type": "manufacturer_spec", 
                    "organization": "GIB"
                },
                {
                    "url": "https://example.com/nz-standard.pdf",
                    "title": "NZS 3604:2011 Timber Framing",
                    "type": "nz_standard",
                    "organization": "Standards NZ"
                }
            ]
            
            test_batch = {"pdf_sources": document_types}
            response = self.session.post(f"{API_BASE}/knowledge/process-pdf-batch", json=test_batch)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if all document types are accepted
                if data.get('total_pdfs') == len(document_types):
                    details = {
                        "document_types_tested": [doc['type'] for doc in document_types],
                        "total_accepted": data.get('total_pdfs'),
                        "batch_id": data.get('batch_id')
                    }
                    
                    self.log_test("PDF Classification System", True, 
                                "All document types accepted by classification system", details)
                    return True
                else:
                    self.log_test("PDF Classification System", False, 
                                f"Expected {len(document_types)} PDFs, got {data.get('total_pdfs')}", data)
                    return False
            else:
                self.log_test("PDF Classification System", False, 
                            f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("PDF Classification System", False, f"Error: {str(e)}")
            return False
    
    def test_batch_validation(self):
        """Test validation system for PDF source requirements"""
        try:
            # Test missing required fields
            invalid_batches = [
                {
                    "name": "Missing URL",
                    "batch": {
                        "pdf_sources": [
                            {
                                "title": "Test Document",
                                "type": "building_code"
                                # Missing 'url' field
                            }
                        ]
                    },
                    "expected_error": "Missing required fields"
                },
                {
                    "name": "Missing Title", 
                    "batch": {
                        "pdf_sources": [
                            {
                                "url": "https://example.com/test.pdf",
                                "type": "building_code"
                                # Missing 'title' field
                            }
                        ]
                    },
                    "expected_error": "Missing required fields"
                },
                {
                    "name": "Empty PDF Sources",
                    "batch": {
                        "pdf_sources": []
                    },
                    "expected_error": "Empty batch"
                }
            ]
            
            validation_passed = 0
            total_validations = len(invalid_batches)
            
            for test_case in invalid_batches:
                response = self.session.post(f"{API_BASE}/knowledge/process-pdf-batch", json=test_case["batch"])
                
                # Should return 400, 422, or 500 with proper error message for validation errors
                if response.status_code in [400, 422, 500]:
                    # Check if error message indicates validation failure
                    try:
                        error_data = response.json()
                        error_detail = error_data.get('detail', '')
                        if 'Missing required fields' in error_detail or 'cannot be empty' in error_detail:
                            validation_passed += 1
                            self.log_test(f"Validation - {test_case['name']}", True, 
                                        f"Properly rejected invalid batch with validation error")
                        else:
                            self.log_test(f"Validation - {test_case['name']}", False, 
                                        f"Error message doesn't indicate validation failure: {error_detail}")
                    except:
                        # If we can't parse JSON, still count as validation if status code is right
                        validation_passed += 1
                        self.log_test(f"Validation - {test_case['name']}", True, 
                                    f"Properly rejected invalid batch with HTTP {response.status_code}")
                else:
                    self.log_test(f"Validation - {test_case['name']}", False, 
                                f"Expected 400/422/500, got {response.status_code}", response.text)
            
            if validation_passed == total_validations:
                self.log_test("Batch Validation System", True, 
                            f"All {total_validations} validation tests passed")
                return True
            else:
                self.log_test("Batch Validation System", False, 
                            f"Only {validation_passed}/{total_validations} validation tests passed")
                return False
                
        except Exception as e:
            self.log_test("Batch Validation System", False, f"Error: {str(e)}")
            return False
    
    def test_processing_status_tracking(self):
        """Test status tracking system for batch operations"""
        try:
            # First, submit a small test batch
            test_batch = {
                "pdf_sources": [
                    {
                        "url": "https://example.com/test-status.pdf",
                        "title": "Status Tracking Test Document",
                        "type": "building_code",
                        "organization": "Test"
                    }
                ]
            }
            
            batch_response = self.session.post(f"{API_BASE}/knowledge/process-pdf-batch", json=test_batch)
            
            if batch_response.status_code == 200:
                batch_data = batch_response.json()
                batch_id = batch_data.get('batch_id')
                
                # Wait a moment for processing to potentially start
                time.sleep(2)
                
                # Check status endpoint for tracking information
                status_response = self.session.get(f"{API_BASE}/knowledge/enhanced-pdf-status")
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    
                    # Check for status tracking features
                    has_recent_batches = 'recent_batches' in status_data
                    has_success_rates = False
                    
                    if has_recent_batches and status_data['recent_batches']:
                        # Check if recent batches have success rate information
                        for batch in status_data['recent_batches']:
                            if 'success_rate' in batch or ('successful' in batch and 'failed' in batch):
                                has_success_rates = True
                                break
                    
                    details = {
                        "batch_id_submitted": batch_id,
                        "has_recent_batches": has_recent_batches,
                        "has_success_rates": has_success_rates,
                        "recent_batches_count": len(status_data.get('recent_batches', []))
                    }
                    
                    if has_recent_batches:
                        self.log_test("Processing Status Tracking", True, 
                                    "Status tracking system operational with batch history", details)
                        return True
                    else:
                        self.log_test("Processing Status Tracking", False, 
                                    "Status tracking missing recent batches information", details)
                        return False
                else:
                    self.log_test("Processing Status Tracking", False, 
                                f"Status endpoint error: HTTP {status_response.status_code}")
                    return False
            else:
                self.log_test("Processing Status Tracking", False, 
                            f"Failed to submit test batch: HTTP {batch_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Processing Status Tracking", False, f"Error: {str(e)}")
            return False
    
    def test_enhanced_error_handling(self):
        """Test enhanced error handling and validation"""
        try:
            # Test malformed JSON
            malformed_response = self.session.post(f"{API_BASE}/knowledge/process-pdf-batch", 
                                                 data="invalid json")
            
            # Should handle malformed JSON gracefully
            if malformed_response.status_code in [400, 422]:
                self.log_test("Enhanced Error Handling - Malformed JSON", True, 
                            f"Properly handled malformed JSON with HTTP {malformed_response.status_code}")
            else:
                self.log_test("Enhanced Error Handling - Malformed JSON", False, 
                            f"Unexpected response to malformed JSON: {malformed_response.status_code}")
                return False
            
            # Test invalid URL format
            invalid_url_batch = {
                "pdf_sources": [
                    {
                        "url": "not-a-valid-url",
                        "title": "Test Document",
                        "type": "building_code"
                    }
                ]
            }
            
            invalid_url_response = self.session.post(f"{API_BASE}/knowledge/process-pdf-batch", 
                                                   json=invalid_url_batch)
            
            # Should accept the request (URL validation might happen during processing)
            if invalid_url_response.status_code in [200, 400, 422]:
                self.log_test("Enhanced Error Handling - Invalid URL", True, 
                            f"Handled invalid URL appropriately with HTTP {invalid_url_response.status_code}")
                return True
            else:
                self.log_test("Enhanced Error Handling - Invalid URL", False, 
                            f"Unexpected response to invalid URL: {invalid_url_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Enhanced Error Handling", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all Enhanced PDF Processing tests"""
        print(f"\n🚀 Starting STRYDA.ai Enhanced PDF Processing Tests")
        print(f"Backend URL: {API_BASE}")
        print("=" * 70)
        
        # Run tests in order
        tests = [
            ("Enhanced PDF Status Endpoint", self.test_enhanced_pdf_status_endpoint),
            ("Batch Processing Structure", self.test_batch_processing_structure),
            ("PDF Classification System", self.test_pdf_classification_system),
            ("Batch Validation", self.test_batch_validation),
            ("Processing Status Tracking", self.test_processing_status_tracking),
            ("Enhanced Error Handling", self.test_enhanced_error_handling)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 Testing: {test_name}")
            if test_func():
                passed += 1
            time.sleep(1)  # Brief pause between test suites
        
        print("\n" + "=" * 70)
        print(f"🏁 Enhanced PDF Processing Test Summary: {passed}/{total} test suites passed")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['message']}")
        
        return passed == total

if __name__ == "__main__":
    tester = EnhancedPDFTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All Enhanced PDF Processing tests passed!")
        exit(0)
    else:
        print("\n⚠️  Some Enhanced PDF Processing tests failed!")
        exit(1)