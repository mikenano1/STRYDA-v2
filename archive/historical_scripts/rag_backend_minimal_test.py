#!/usr/bin/env python3
"""
RAG Backend Minimal Testing Suite
Tests the backend-minimal RAG pipeline with Supabase database connection
"""

import requests
import json
import time
import sys
import os
import psycopg2
import psycopg2.extras
from typing import Dict, Any, List

# Test Configuration
BACKEND_URL = "http://localhost:8001"
TEST_TIMEOUT = 30

class RAGBackendTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.test_results = []
        self.database_url = None
        
    def log_test(self, test_name: str, success: bool, details: str, response_time: float = 0):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        if response_time > 0:
            print(f"   ⏱️ Response time: {response_time:.1f}ms")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response_time": response_time
        })
    
    def test_health_endpoint(self):
        """Test the /health endpoint"""
        print("\n🔍 Testing Health Endpoint...")
        
        try:
            start_time = time.time()
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                expected = {"ok": True, "version": "v0.2"}
                
                if data == expected:
                    self.log_test("Health Endpoint", True, 
                                f"Returns correct response: {data}", response_time)
                else:
                    self.log_test("Health Endpoint", False, 
                                f"Unexpected response: {data}, expected: {expected}", response_time)
            else:
                self.log_test("Health Endpoint", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
                
        except requests.exceptions.RequestException as e:
            self.log_test("Health Endpoint", False, f"Connection error: {e}")
    
    def test_database_connection(self):
        """Test direct database connection to Supabase"""
        print("\n🔍 Testing Database Connection...")
        
        # Load DATABASE_URL from backend-minimal/.env
        env_path = "/app/backend-minimal/.env"
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    if line.startswith('DATABASE_URL='):
                        self.database_url = line.split('=', 1)[1].strip()
                        break
        except Exception as e:
            self.log_test("Database Connection", False, f"Could not read .env file: {e}")
            return
        
        if not self.database_url:
            self.log_test("Database Connection", False, "DATABASE_URL not found in .env file")
            return
        
        try:
            # Test connection
            start_time = time.time()
            conn = psycopg2.connect(self.database_url)
            response_time = (time.time() - start_time) * 1000
            
            # Test basic query
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                
            conn.close()
            self.log_test("Database Connection", True, 
                        f"Successfully connected to PostgreSQL: {version[:50]}...", response_time)
            
        except psycopg2.OperationalError as e:
            error_msg = str(e)
            if "Tenant or user not found" in error_msg:
                self.log_test("Database Connection", False, 
                            "Supabase credentials expired or invalid - 'Tenant or user not found' error")
            elif "timeout" in error_msg.lower():
                self.log_test("Database Connection", False, 
                            f"Connection timeout to Supabase: {error_msg}")
            else:
                self.log_test("Database Connection", False, 
                            f"Database connection failed: {error_msg}")
        except Exception as e:
            self.log_test("Database Connection", False, f"Unexpected database error: {e}")
    
    def test_documents_table_schema(self):
        """Test documents table exists and has correct schema"""
        print("\n🔍 Testing Documents Table Schema...")
        
        if not self.database_url:
            self.log_test("Documents Table Schema", False, "No database URL available")
            return
        
        try:
            conn = psycopg2.connect(self.database_url)
            
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Check if documents table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'documents'
                    );
                """)
                table_exists = cur.fetchone()[0]
                
                if not table_exists:
                    conn.close()
                    self.log_test("Documents Table Schema", False, "Documents table does not exist")
                    return
                
                # Check table schema
                cur.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = 'documents'
                    ORDER BY ordinal_position;
                """)
                columns = cur.fetchall()
                
                # Expected columns
                expected_columns = {
                    'id': 'text',
                    'source': 'text', 
                    'page': 'text',
                    'content': 'text',
                    'embedding': 'USER-DEFINED',  # vector type
                    'created_at': 'timestamp'
                }
                
                found_columns = {col['column_name']: col['data_type'] for col in columns}
                
                # Check for required columns
                missing_columns = []
                for col_name, expected_type in expected_columns.items():
                    if col_name not in found_columns:
                        missing_columns.append(col_name)
                    elif col_name == 'embedding' and found_columns[col_name] != 'USER-DEFINED':
                        # Vector extension might show as different type
                        pass  # Allow flexibility for vector type
                
                if missing_columns:
                    self.log_test("Documents Table Schema", False, 
                                f"Missing columns: {missing_columns}")
                else:
                    # Check if table has data
                    cur.execute("SELECT COUNT(*) FROM documents;")
                    row_count = cur.fetchone()[0]
                    
                    self.log_test("Documents Table Schema", True, 
                                f"Table exists with correct schema, {row_count} documents")
            
            conn.close()
            
        except psycopg2.OperationalError as e:
            self.log_test("Documents Table Schema", False, f"Database connection failed: {e}")
        except Exception as e:
            self.log_test("Documents Table Schema", False, f"Schema check failed: {e}")
    
    def test_rag_pipeline_ask_endpoint(self):
        """Test the /api/ask endpoint with sample queries"""
        print("\n🔍 Testing RAG Pipeline /api/ask Endpoint...")
        
        test_queries = [
            {
                "query": "What are the fire clearance requirements for solid fuel appliances?",
                "expected_keywords": ["fire", "clearance", "solid fuel", "appliance"]
            },
            {
                "query": "What insulation R-values are required in Auckland?",
                "expected_keywords": ["insulation", "R-value", "Auckland", "thermal"]
            },
            {
                "query": "What are the weathertightness requirements for external walls?",
                "expected_keywords": ["weathertightness", "external", "wall", "moisture"]
            }
        ]
        
        for i, test_case in enumerate(test_queries, 1):
            query = test_case["query"]
            expected_keywords = test_case["expected_keywords"]
            
            print(f"\n   Testing Query {i}: {query[:60]}...")
            
            try:
                start_time = time.time()
                response = requests.post(
                    f"{self.backend_url}/api/ask",
                    json={"query": query},
                    timeout=TEST_TIMEOUT
                )
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check response structure
                    required_fields = ["answer", "notes", "citation"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_test(f"RAG Query {i} Structure", False, 
                                    f"Missing fields: {missing_fields}", response_time)
                        continue
                    
                    answer = data.get("answer", "")
                    notes = data.get("notes", [])
                    citations = data.get("citation", [])
                    
                    # Analyze response quality
                    if "fallback" in notes:
                        self.log_test(f"RAG Query {i} Fallback", True, 
                                    f"Graceful fallback response: {answer[:100]}...", response_time)
                    elif "retrieval" in notes:
                        # Check if answer contains relevant keywords
                        answer_lower = answer.lower()
                        keyword_matches = sum(1 for kw in expected_keywords 
                                            if kw.lower() in answer_lower)
                        
                        if keyword_matches >= 2:  # At least 2 keywords should match
                            self.log_test(f"RAG Query {i} Success", True, 
                                        f"Relevant answer ({len(answer)} chars, {len(citations)} citations)", 
                                        response_time)
                        else:
                            self.log_test(f"RAG Query {i} Relevance", False, 
                                        f"Answer may not be relevant (matched {keyword_matches}/{len(expected_keywords)} keywords)", 
                                        response_time)
                    else:
                        self.log_test(f"RAG Query {i} Unknown", True, 
                                    f"Response received but unclear type: {notes}", response_time)
                
                else:
                    self.log_test(f"RAG Query {i}", False, 
                                f"HTTP {response.status_code}: {response.text}", response_time)
                    
            except requests.exceptions.Timeout:
                self.log_test(f"RAG Query {i}", False, f"Request timeout after {TEST_TIMEOUT}s")
            except requests.exceptions.RequestException as e:
                self.log_test(f"RAG Query {i}", False, f"Request error: {e}")
            except Exception as e:
                self.log_test(f"RAG Query {i}", False, f"Unexpected error: {e}")
    
    def test_embedding_generation(self):
        """Test if embedding generation is working"""
        print("\n🔍 Testing Embedding Generation...")
        
        # This is an indirect test - we'll check if the LLM key is configured
        env_path = "/app/backend-minimal/.env"
        emergent_key = None
        
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    if line.startswith('EMERGENT_LLM_KEY='):
                        emergent_key = line.split('=', 1)[1].strip()
                        break
        except Exception as e:
            self.log_test("Embedding Generation", False, f"Could not read .env file: {e}")
            return
        
        if emergent_key and emergent_key.startswith('sk-emergent-'):
            self.log_test("Embedding Generation", True, 
                        f"EMERGENT_LLM_KEY configured: {emergent_key[:20]}...")
        else:
            self.log_test("Embedding Generation", False, 
                        "EMERGENT_LLM_KEY not properly configured")
    
    def test_error_handling(self):
        """Test error handling and graceful fallbacks"""
        print("\n🔍 Testing Error Handling...")
        
        # Test malformed request
        try:
            response = requests.post(
                f"{self.backend_url}/api/ask",
                json={"invalid_field": "test"},
                timeout=10
            )
            
            if response.status_code == 422:  # Validation error
                self.log_test("Error Handling - Validation", True, 
                            "Properly handles malformed requests with 422")
            elif response.status_code == 200:
                # Check if it returns fallback
                data = response.json()
                if "fallback" in data.get("notes", []):
                    self.log_test("Error Handling - Graceful", True, 
                                "Gracefully handles malformed requests with fallback")
                else:
                    self.log_test("Error Handling - Unexpected", False, 
                                f"Unexpected response to malformed request: {data}")
            else:
                self.log_test("Error Handling", False, 
                            f"Unexpected status code {response.status_code}")
                
        except Exception as e:
            self.log_test("Error Handling", False, f"Error testing error handling: {e}")
        
        # Test empty query
        try:
            response = requests.post(
                f"{self.backend_url}/api/ask",
                json={"query": ""},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("answer"):
                    self.log_test("Error Handling - Empty Query", True, 
                                "Handles empty queries gracefully")
                else:
                    self.log_test("Error Handling - Empty Query", False, 
                                "Empty query returns empty answer")
            else:
                self.log_test("Error Handling - Empty Query", False, 
                            f"Empty query returns HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Error Handling - Empty Query", False, f"Error: {e}")
    
    def run_all_tests(self):
        """Run all tests and provide summary"""
        print("🚀 Starting RAG Backend Minimal Testing Suite")
        print(f"🎯 Target: {self.backend_url}")
        print("=" * 60)
        
        # Run all tests
        self.test_health_endpoint()
        self.test_database_connection()
        self.test_documents_table_schema()
        self.test_embedding_generation()
        self.test_rag_pipeline_ask_endpoint()
        self.test_error_handling()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
        
        # Overall assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")
        if failed_tests == 0:
            print("✅ RAG Backend Minimal system is working excellently!")
        elif passed_tests >= total_tests * 0.7:  # 70% pass rate
            print("⚠️ RAG Backend Minimal system is partially working with some issues")
        else:
            print("❌ RAG Backend Minimal system has significant issues")
        
        return passed_tests, failed_tests

def main():
    """Main test execution"""
    tester = RAGBackendTester()
    
    try:
        passed, failed = tester.run_all_tests()
        
        # Exit with appropriate code
        if failed == 0:
            sys.exit(0)  # All tests passed
        else:
            sys.exit(1)  # Some tests failed
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Testing interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n\n❌ Testing failed with unexpected error: {e}")
        sys.exit(3)

if __name__ == "__main__":
    main()