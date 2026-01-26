#!/usr/bin/env python3
"""
STRYDA RAG Backend Testing Suite
Tests the backend-minimal RAG system with Supabase database connection
"""

import requests
import json
import time
import os
import sys
import psycopg2
import psycopg2.extras
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from backend-minimal
load_dotenv('/app/backend-minimal/.env')

# Configuration
BACKEND_URL = "http://localhost:8000"  # backend-minimal runs on port 8000
DATABASE_URL = os.getenv('DATABASE_URL')
EMERGENT_LLM_KEY = os.getenv('EMERGENT_LLM_KEY')

class RAGBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.db_conn = None
        
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
    
    def test_database_connection(self):
        """Test database connection to Supabase"""
        try:
            if not DATABASE_URL:
                self.log_test("Database Connection", False, "DATABASE_URL not configured")
                return False
            
            print(f"   Connecting to: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'database'}")
            
            # Test connection
            conn = psycopg2.connect(DATABASE_URL)
            self.db_conn = conn
            
            # Test basic query
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                
            self.log_test("Database Connection", True, f"Connected to Supabase PostgreSQL", {"version": version[:50] + "..."})
            return True
            
        except psycopg2.OperationalError as e:
            error_msg = str(e)
            if "Tenant or user not found" in error_msg:
                self.log_test("Database Connection", False, "Tenant or user not found error - DATABASE_URL may be incorrect", {"error": error_msg})
            else:
                self.log_test("Database Connection", False, f"Database connection failed: {error_msg}")
            return False
        except Exception as e:
            self.log_test("Database Connection", False, f"Unexpected error: {str(e)}")
            return False
    
    def test_documents_table_schema(self):
        """Test if documents table exists with required schema"""
        if not self.db_conn:
            self.log_test("Documents Table Schema", False, "No database connection available")
            return False
        
        try:
            with self.db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Check if documents table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'documents'
                    );
                """)
                table_exists = cur.fetchone()[0]
                
                if not table_exists:
                    self.log_test("Documents Table Schema", False, "Documents table does not exist")
                    return False
                
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
                    'id': 'uuid',
                    'source': 'text',
                    'page': 'integer',
                    'content': 'text',
                    'embedding': 'USER-DEFINED',  # vector type shows as USER-DEFINED
                    'created_at': 'timestamp'
                }
                
                found_columns = {col['column_name']: col['data_type'] for col in columns}
                
                # Check required columns
                missing_columns = []
                for col_name, expected_type in expected_columns.items():
                    if col_name not in found_columns:
                        missing_columns.append(col_name)
                    elif col_name == 'embedding' and found_columns[col_name] != 'USER-DEFINED':
                        missing_columns.append(f"{col_name} (wrong type: {found_columns[col_name]})")
                
                if missing_columns:
                    self.log_test("Documents Table Schema", False, f"Missing or incorrect columns: {missing_columns}", {"found_columns": found_columns})
                    return False
                
                # Check if there are any documents
                cur.execute("SELECT COUNT(*) FROM documents;")
                doc_count = cur.fetchone()[0]
                
                # Check embedding dimension if documents exist
                embedding_dim = None
                if doc_count > 0:
                    cur.execute("SELECT array_length(embedding, 1) FROM documents LIMIT 1;")
                    embedding_dim = cur.fetchone()[0]
                
                self.log_test("Documents Table Schema", True, f"Schema valid with {doc_count} documents", {
                    "columns": found_columns,
                    "document_count": doc_count,
                    "embedding_dimension": embedding_dim
                })
                return True
                
        except Exception as e:
            self.log_test("Documents Table Schema", False, f"Schema check failed: {str(e)}")
            return False
    
    def test_health_endpoint(self):
        """Test /health endpoint"""
        try:
            response = self.session.get(f"{BACKEND_URL}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = ['ok', 'version']
                
                if all(field in data for field in expected_fields) and data['ok'] is True:
                    self.log_test("Health Endpoint", True, f"Health check passed", data)
                    return True
                else:
                    self.log_test("Health Endpoint", False, f"Invalid health response structure", data)
                    return False
            else:
                self.log_test("Health Endpoint", False, f"HTTP {response.status_code}", response.text[:200])
                return False
                
        except requests.exceptions.ConnectionError:
            self.log_test("Health Endpoint", False, "Backend server not running on port 8000")
            return False
        except Exception as e:
            self.log_test("Health Endpoint", False, f"Health check failed: {str(e)}")
            return False
    
    def test_rag_pipeline_ask_endpoint(self):
        """Test the full RAG pipeline via /api/ask endpoint"""
        test_queries = [
            {
                "query": "What are the minimum clearances for solid fuel appliances?",
                "expected_keywords": ["clearance", "solid fuel", "appliance", "minimum"]
            },
            {
                "query": "What insulation requirements apply to H1 climate zones?",
                "expected_keywords": ["insulation", "h1", "climate", "zone"]
            },
            {
                "query": "What are weathertightness requirements for external walls?",
                "expected_keywords": ["weathertight", "external", "wall", "moisture"]
            }
        ]
        
        all_tests_passed = True
        
        for i, test_case in enumerate(test_queries):
            try:
                payload = {
                    "query": test_case["query"],
                    "history": []
                }
                
                print(f"   Testing query: {test_case['query'][:50]}...")
                response = self.session.post(f"{BACKEND_URL}/api/ask", json=payload, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check response structure
                    required_fields = ['answer', 'notes', 'citation']
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_test(f"RAG Query {i+1}", False, f"Missing response fields: {missing_fields}", data)
                        all_tests_passed = False
                        continue
                    
                    answer = data.get('answer', '')
                    notes = data.get('notes', [])
                    citations = data.get('citation', [])
                    
                    # Check if it's a fallback response
                    is_fallback = any('fallback' in str(note).lower() for note in notes)
                    
                    if is_fallback:
                        self.log_test(f"RAG Query {i+1}", False, "Received fallback response - RAG pipeline not working", {
                            "answer": answer[:100] + "..." if len(answer) > 100 else answer,
                            "notes": notes,
                            "citations_count": len(citations)
                        })
                        all_tests_passed = False
                    else:
                        # Check if answer contains relevant keywords
                        answer_lower = answer.lower()
                        relevant_keywords = [kw for kw in test_case["expected_keywords"] if kw.lower() in answer_lower]
                        
                        # Check answer quality
                        answer_quality = {
                            "length": len(answer),
                            "has_relevant_keywords": len(relevant_keywords) > 0,
                            "citations_count": len(citations),
                            "notes": notes
                        }
                        
                        if len(answer) > 50 and answer_quality["has_relevant_keywords"]:
                            self.log_test(f"RAG Query {i+1}", True, f"RAG pipeline working - generated {len(answer)} char response with {len(citations)} citations", answer_quality)
                        else:
                            self.log_test(f"RAG Query {i+1}", False, f"Poor quality response", answer_quality)
                            all_tests_passed = False
                else:
                    self.log_test(f"RAG Query {i+1}", False, f"HTTP {response.status_code}", response.text[:200])
                    all_tests_passed = False
                
                # Small delay between requests
                time.sleep(1)
                
            except Exception as e:
                self.log_test(f"RAG Query {i+1}", False, f"Request failed: {str(e)}")
                all_tests_passed = False
        
        return all_tests_passed
    
    def test_embedding_search_functionality(self):
        """Test if embedding search is working by checking database directly"""
        if not self.db_conn:
            self.log_test("Embedding Search", False, "No database connection available")
            return False
        
        try:
            with self.db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Check if we have documents with embeddings
                cur.execute("SELECT COUNT(*) FROM documents WHERE embedding IS NOT NULL;")
                docs_with_embeddings = cur.fetchone()[0]
                
                if docs_with_embeddings == 0:
                    self.log_test("Embedding Search", False, "No documents with embeddings found in database")
                    return False
                
                # Test a simple similarity search (using a dummy vector)
                # Create a dummy 1536-dimensional vector (OpenAI embedding size)
                dummy_vector = [0.1] * 1536
                
                cur.execute("""
                    SELECT id, source, page, content,
                           1 - (embedding <=> %s::vector) AS score
                    FROM documents
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> %s::vector
                    LIMIT 3;
                """, (dummy_vector, dummy_vector))
                
                results = cur.fetchall()
                
                if len(results) > 0:
                    self.log_test("Embedding Search", True, f"Vector search working - found {len(results)} results", {
                        "docs_with_embeddings": docs_with_embeddings,
                        "sample_sources": [r['source'] for r in results[:3]],
                        "sample_scores": [float(r['score']) for r in results[:3]]
                    })
                    return True
                else:
                    self.log_test("Embedding Search", False, "Vector search returned no results")
                    return False
                    
        except Exception as e:
            error_msg = str(e)
            if "vector" in error_msg.lower():
                self.log_test("Embedding Search", False, f"Vector extension not available: {error_msg}")
            else:
                self.log_test("Embedding Search", False, f"Embedding search test failed: {error_msg}")
            return False
    
    def test_llm_integration(self):
        """Test LLM integration with EMERGENT_LLM_KEY"""
        if not EMERGENT_LLM_KEY:
            self.log_test("LLM Integration", False, "EMERGENT_LLM_KEY not configured")
            return False
        
        try:
            # Test with a simple query that should trigger LLM if working
            payload = {
                "query": "Hello, can you help me with building codes?",
                "history": []
            }
            
            response = self.session.post(f"{BACKEND_URL}/api/ask", json=payload, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get('answer', '')
                notes = data.get('notes', [])
                
                # Check if it's using LLM (not fallback)
                is_fallback = any('fallback' in str(note).lower() for note in notes)
                has_llm_response = len(answer) > 20 and not is_fallback
                
                if has_llm_response:
                    self.log_test("LLM Integration", True, f"LLM responding - generated {len(answer)} character response", {
                        "answer_preview": answer[:100] + "..." if len(answer) > 100 else answer,
                        "notes": notes
                    })
                    return True
                else:
                    self.log_test("LLM Integration", False, f"LLM not responding properly", {
                        "answer": answer,
                        "notes": notes,
                        "is_fallback": is_fallback
                    })
                    return False
            else:
                self.log_test("LLM Integration", False, f"HTTP {response.status_code}", response.text[:200])
                return False
                
        except Exception as e:
            self.log_test("LLM Integration", False, f"LLM test failed: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all RAG backend tests"""
        print(f"\n🔍 Starting STRYDA RAG Backend Tests")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Database: {'Configured' if DATABASE_URL else 'Not configured'}")
        print(f"LLM Key: {'Configured' if EMERGENT_LLM_KEY else 'Not configured'}")
        print("=" * 70)
        
        # Run tests in logical order
        tests = [
            ("Database Connection", self.test_database_connection),
            ("Documents Table Schema", self.test_documents_table_schema),
            ("Health Endpoint", self.test_health_endpoint),
            ("Embedding Search Functionality", self.test_embedding_search_functionality),
            ("LLM Integration", self.test_llm_integration),
            ("RAG Pipeline (/api/ask)", self.test_rag_pipeline_ask_endpoint)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 Testing: {test_name}")
            if test_func():
                passed += 1
            time.sleep(0.5)
        
        print("\n" + "=" * 70)
        print(f"🏁 RAG Backend Test Summary: {passed}/{total} test suites passed")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['message']}")
        
        # Close database connection
        if self.db_conn:
            self.db_conn.close()
        
        return passed == total

if __name__ == "__main__":
    print("🚀 STRYDA RAG Backend Testing Suite")
    print("Testing backend-minimal RAG system with Supabase database")
    
    tester = RAGBackendTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All RAG backend tests passed!")
        exit(0)
    else:
        print("\n⚠️  Some RAG backend tests failed!")
        exit(1)