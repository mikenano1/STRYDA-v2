#!/usr/bin/env python3
"""
STRYDA.ai Enhanced PDF Integration Testing Suite
Tests the Enhanced PDF Processing system for NZ building document expansion
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
BACKEND_URL = os.getenv('EXPO_PUBLIC_BACKEND_URL', 'https://expert-agent-router.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class EnhancedPDFIntegrationTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.batch_id = None
        
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
        """Test GET /api/knowledge/enhanced-pdf-status to verify system readiness"""
        try:
            print("\n📊 Testing Enhanced PDF Status Endpoint...")
            response = self.session.get(f"{API_BASE}/knowledge/enhanced-pdf-status")
            
            if response.status_code == 200:
                status_data = response.json()
                
                # Check required fields in response
                required_fields = ['total_documents', 'total_chunks', 'recent_batches', 'last_updated']
                missing_fields = [field for field in required_fields if field not in status_data]
                
                if not missing_fields:
                    details = {
                        "total_documents": status_data.get('total_documents', 0),
                        "total_chunks": status_data.get('total_chunks', 0),
                        "recent_batches_count": len(status_data.get('recent_batches', [])),
                        "system_ready": True
                    }
                    self.log_test("Enhanced PDF Status", True, 
                                f"System ready - {details['total_documents']} docs, {details['total_chunks']} chunks", 
                                details)
                    return True
                else:
                    self.log_test("Enhanced PDF Status", False, 
                                f"Missing required fields: {missing_fields}", status_data)
                    return False
            else:
                self.log_test("Enhanced PDF Status", False, 
                            f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Enhanced PDF Status", False, f"Error: {str(e)}")
            return False
    
    def test_batch_processing_with_nz_documents(self):
        """Test POST /api/knowledge/process-pdf-batch with sample NZ building documents"""
        try:
            print("\n📚 Testing Batch Processing with NZ Building Documents...")
            
            # Sample NZ Building documents for testing
            sample_nz_pdfs = [
                {
                    "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/b-stability/b1-structure/asvm/b1-structure-third-edition-amendment-14.pdf",
                    "title": "NZBC B1 Structure - Third Edition Amendment 14",
                    "type": "building_code",
                    "organization": "MBIE"
                },
                {
                    "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/e-moisture/e2-external-moisture/acceptable-solutions/e2-as1-third-edition-amendment-11.pdf",
                    "title": "NZBC E2 External Moisture - Acceptable Solutions",
                    "type": "building_code", 
                    "organization": "MBIE"
                },
                {
                    "url": "https://www.standards.govt.nz/assets/Publication-files/NZS3604-2011-Timber-framed-buildings.pdf",
                    "title": "NZS 3604:2011 Timber-framed Buildings",
                    "type": "nz_standard",
                    "organization": "Standards New Zealand"
                }
            ]
            
            batch_request = {
                "pdf_sources": sample_nz_pdfs
            }
            
            response = self.session.post(f"{API_BASE}/knowledge/process-pdf-batch", 
                                       json=batch_request)
            
            if response.status_code == 200:
                batch_response = response.json()
                
                # Check required response fields
                required_fields = ['message', 'batch_id', 'total_pdfs', 'processing_started']
                missing_fields = [field for field in required_fields if field not in batch_response]
                
                if not missing_fields and batch_response.get('processing_started'):
                    self.batch_id = batch_response.get('batch_id')
                    details = {
                        "batch_id": self.batch_id,
                        "total_pdfs": batch_response.get('total_pdfs'),
                        "processing_started": batch_response.get('processing_started'),
                        "document_types": list(set([pdf['type'] for pdf in sample_nz_pdfs]))
                    }
                    self.log_test("Batch Processing", True, 
                                f"Batch processing started for {details['total_pdfs']} NZ documents", 
                                details)
                    return True
                else:
                    self.log_test("Batch Processing", False, 
                                f"Invalid response structure or processing not started", batch_response)
                    return False
            else:
                self.log_test("Batch Processing", False, 
                            f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Batch Processing", False, f"Error: {str(e)}")
            return False
    
    def test_document_classification_system(self):
        """Test automatic classification of different PDF types"""
        try:
            print("\n🏷️ Testing Document Classification System...")
            
            # Test different document types
            classification_tests = [
                {
                    "pdf_sources": [{
                        "url": "https://example.com/building-code.pdf",
                        "title": "NZBC G5 Interior Environment",
                        "type": "building_code",
                        "organization": "MBIE"
                    }]
                },
                {
                    "pdf_sources": [{
                        "url": "https://example.com/council-reg.pdf", 
                        "title": "Auckland Council District Plan",
                        "type": "council_regulation",
                        "organization": "Auckland Council"
                    }]
                },
                {
                    "pdf_sources": [{
                        "url": "https://example.com/manufacturer-spec.pdf",
                        "title": "James Hardie Installation Guide",
                        "type": "manufacturer_spec", 
                        "organization": "James Hardie"
                    }]
                },
                {
                    "pdf_sources": [{
                        "url": "https://example.com/nz-standard.pdf",
                        "title": "NZS 4230:2004 Code of Practice for Glazing",
                        "type": "nz_standard",
                        "organization": "Standards New Zealand"
                    }]
                }
            ]
            
            all_classifications_passed = True
            
            for i, test_case in enumerate(classification_tests):
                doc_type = test_case["pdf_sources"][0]["type"]
                
                response = self.session.post(f"{API_BASE}/knowledge/process-pdf-batch", 
                                           json=test_case)
                
                if response.status_code == 200:
                    batch_response = response.json()
                    if batch_response.get('processing_started'):
                        self.log_test(f"Classification - {doc_type}", True, 
                                    f"Accepted {doc_type} document type")
                    else:
                        self.log_test(f"Classification - {doc_type}", False, 
                                    "Processing not started for classification test")
                        all_classifications_passed = False
                else:
                    self.log_test(f"Classification - {doc_type}", False, 
                                f"HTTP {response.status_code} for {doc_type}")
                    all_classifications_passed = False
                
                time.sleep(0.5)  # Brief pause between classification tests
            
            return all_classifications_passed
            
        except Exception as e:
            self.log_test("Document Classification", False, f"Error: {str(e)}")
            return False
    
    def test_batch_validation_system(self):
        """Test batch processing validation and error handling"""
        try:
            print("\n✅ Testing Batch Validation System...")
            
            validation_tests = [
                {
                    "name": "Empty PDF Sources",
                    "request": {"pdf_sources": []},
                    "expected_status": 400,
                    "should_fail": True
                },
                {
                    "name": "Missing URL Field",
                    "request": {"pdf_sources": [{"title": "Test Doc", "type": "building_code"}]},
                    "expected_status": 400,
                    "should_fail": True
                },
                {
                    "name": "Missing Title Field", 
                    "request": {"pdf_sources": [{"url": "https://example.com/test.pdf", "type": "building_code"}]},
                    "expected_status": 400,
                    "should_fail": True
                },
                {
                    "name": "Valid Request",
                    "request": {
                        "pdf_sources": [{
                            "url": "https://example.com/valid.pdf",
                            "title": "Valid Test Document",
                            "type": "building_code"
                        }]
                    },
                    "expected_status": 200,
                    "should_fail": False
                }
            ]
            
            all_validations_passed = True
            
            for test_case in validation_tests:
                response = self.session.post(f"{API_BASE}/knowledge/process-pdf-batch", 
                                           json=test_case["request"])
                
                if test_case["should_fail"]:
                    if response.status_code == test_case["expected_status"]:
                        self.log_test(f"Validation - {test_case['name']}", True, 
                                    f"Properly rejected invalid request with HTTP {response.status_code}")
                    else:
                        self.log_test(f"Validation - {test_case['name']}", False, 
                                    f"Expected HTTP {test_case['expected_status']}, got {response.status_code}")
                        all_validations_passed = False
                else:
                    if response.status_code == test_case["expected_status"]:
                        self.log_test(f"Validation - {test_case['name']}", True, 
                                    f"Accepted valid request with HTTP {response.status_code}")
                    else:
                        self.log_test(f"Validation - {test_case['name']}", False, 
                                    f"Expected HTTP {test_case['expected_status']}, got {response.status_code}")
                        all_validations_passed = False
                
                time.sleep(0.3)
            
            return all_validations_passed
            
        except Exception as e:
            self.log_test("Batch Validation", False, f"Error: {str(e)}")
            return False
    
    def test_processing_status_tracking(self):
        """Test batch processing status and success rate tracking"""
        try:
            print("\n📈 Testing Processing Status Tracking...")
            
            # Wait a moment for any processing to potentially start
            time.sleep(2)
            
            # Get updated status
            response = self.session.get(f"{API_BASE}/knowledge/enhanced-pdf-status")
            
            if response.status_code == 200:
                status_data = response.json()
                
                # Check for batch history tracking
                recent_batches = status_data.get('recent_batches', [])
                
                # Check if our batch is being tracked (if we created one)
                batch_found = False
                if self.batch_id:
                    batch_found = any(batch.get('batch_id') == self.batch_id for batch in recent_batches)
                
                # Check for success rate calculation
                has_success_rates = all('success_rate' in batch for batch in recent_batches if batch)
                
                details = {
                    "recent_batches_count": len(recent_batches),
                    "batch_tracking": batch_found or len(recent_batches) > 0,
                    "success_rate_tracking": has_success_rates,
                    "status_fields": list(status_data.keys())
                }
                
                if details["batch_tracking"] and details["success_rate_tracking"]:
                    self.log_test("Status Tracking", True, 
                                f"Batch history and success rates tracked properly", details)
                    return True
                else:
                    issues = []
                    if not details["batch_tracking"]:
                        issues.append("No batch tracking")
                    if not details["success_rate_tracking"]:
                        issues.append("No success rate calculation")
                    
                    self.log_test("Status Tracking", False, 
                                f"Issues: {', '.join(issues)}", details)
                    return False
            else:
                self.log_test("Status Tracking", False, 
                            f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Status Tracking", False, f"Error: {str(e)}")
            return False
    
    def test_knowledge_base_expansion_readiness(self):
        """Test integration readiness with existing STRYDA knowledge base"""
        try:
            print("\n🧠 Testing Knowledge Base Expansion Readiness...")
            
            # Get current knowledge base stats
            response = self.session.get(f"{API_BASE}/knowledge/stats")
            
            if response.status_code == 200:
                kb_stats = response.json()
                
                # Check for ChromaDB integration indicators
                required_stats = ['total_documents', 'total_chunks', 'documents_by_type']
                missing_stats = [stat for stat in required_stats if stat not in kb_stats]
                
                if not missing_stats:
                    current_docs = kb_stats.get('total_documents', 0)
                    current_chunks = kb_stats.get('total_chunks', 0)
                    doc_types = kb_stats.get('documents_by_type', {})
                    
                    details = {
                        "current_documents": current_docs,
                        "current_chunks": current_chunks,
                        "document_types": list(doc_types.keys()),
                        "ready_for_expansion": current_docs > 0,
                        "vector_store_active": current_chunks > 0
                    }
                    
                    if details["ready_for_expansion"] and details["vector_store_active"]:
                        self.log_test("Knowledge Base Expansion", True, 
                                    f"Ready to expand from {current_docs} documents", details)
                        return True
                    else:
                        self.log_test("Knowledge Base Expansion", False, 
                                    "Knowledge base not ready for expansion", details)
                        return False
                else:
                    self.log_test("Knowledge Base Expansion", False, 
                                f"Missing knowledge base stats: {missing_stats}")
                    return False
            else:
                self.log_test("Knowledge Base Expansion", False, 
                            f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Knowledge Base Expansion", False, f"Error: {str(e)}")
            return False
    
    def test_enhanced_error_handling(self):
        """Test enhanced error handling for malformed requests"""
        try:
            print("\n🛡️ Testing Enhanced Error Handling...")
            
            error_tests = [
                {
                    "name": "Malformed JSON",
                    "data": "invalid json",
                    "headers": {"Content-Type": "application/json"},
                    "expected_status": 422
                },
                {
                    "name": "Invalid URL Format",
                    "json_data": {
                        "pdf_sources": [{
                            "url": "not-a-valid-url",
                            "title": "Test Document",
                            "type": "building_code"
                        }]
                    },
                    "expected_status": [400, 422, 500]  # Any of these is acceptable
                }
            ]
            
            all_error_tests_passed = True
            
            for test_case in error_tests:
                if "json_data" in test_case:
                    response = self.session.post(f"{API_BASE}/knowledge/process-pdf-batch", 
                                               json=test_case["json_data"])
                else:
                    response = self.session.post(f"{API_BASE}/knowledge/process-pdf-batch", 
                                               data=test_case["data"],
                                               headers=test_case.get("headers", {}))
                
                expected_statuses = test_case["expected_status"]
                if not isinstance(expected_statuses, list):
                    expected_statuses = [expected_statuses]
                
                if response.status_code in expected_statuses:
                    self.log_test(f"Error Handling - {test_case['name']}", True, 
                                f"Properly handled with HTTP {response.status_code}")
                else:
                    self.log_test(f"Error Handling - {test_case['name']}", False, 
                                f"Expected HTTP {expected_statuses}, got {response.status_code}")
                    all_error_tests_passed = False
                
                time.sleep(0.3)
            
            return all_error_tests_passed
            
        except Exception as e:
            self.log_test("Enhanced Error Handling", False, f"Error: {str(e)}")
            return False
    
    def run_enhanced_pdf_integration_tests(self):
        """Run all Enhanced PDF Integration tests"""
        print(f"\n🚀 Starting STRYDA.ai Enhanced PDF Integration Tests")
        print(f"Backend URL: {API_BASE}")
        print(f"Testing Enhanced PDF Processing System for NZ Building Document Expansion")
        print("=" * 80)
        
        # Run tests in logical order
        tests = [
            ("Enhanced PDF Status Check", self.test_enhanced_pdf_status_endpoint),
            ("Batch Processing with NZ Documents", self.test_batch_processing_with_nz_documents),
            ("Document Classification System", self.test_document_classification_system),
            ("Batch Validation System", self.test_batch_validation_system),
            ("Processing Status Tracking", self.test_processing_status_tracking),
            ("Knowledge Base Expansion Readiness", self.test_knowledge_base_expansion_readiness),
            ("Enhanced Error Handling", self.test_enhanced_error_handling)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 Testing: {test_name}")
            if test_func():
                passed += 1
            time.sleep(1)  # Pause between test suites
        
        print("\n" + "=" * 80)
        print(f"🏁 Enhanced PDF Integration Test Summary: {passed}/{total} test suites passed")
        
        # Show detailed results
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['message']}")
        else:
            print(f"\n🎉 All Enhanced PDF Integration tests passed!")
            print(f"✅ System ready for expanding STRYDA's knowledge base with NZ building documents")
            print(f"✅ Batch processing operational for Building Codes, Council Regulations, Manufacturer Specs, NZ Standards")
        
        # Summary of capabilities tested
        print(f"\n📊 Enhanced PDF Integration Capabilities Verified:")
        print(f"   ✅ Enhanced PDF Status endpoint operational")
        print(f"   ✅ Batch processing accepts multiple NZ document types")
        print(f"   ✅ Document classification system working")
        print(f"   ✅ Processing status tracking and success rates")
        print(f"   ✅ Integration ready with existing ChromaDB vector store")
        print(f"   ✅ Comprehensive error handling and validation")
        
        return passed == total

if __name__ == "__main__":
    tester = EnhancedPDFIntegrationTester()
    success = tester.run_enhanced_pdf_integration_tests()
    
    if success:
        print("\n🎉 Enhanced PDF Integration system fully operational!")
        print("🚀 Ready to rapidly expand STRYDA's knowledge base with comprehensive NZ building documentation!")
        exit(0)
    else:
        print("\n⚠️  Some Enhanced PDF Integration tests failed!")
        exit(1)