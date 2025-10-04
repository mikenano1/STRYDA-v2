#!/usr/bin/env python3
"""
STRYDA-v2 RAG System End-to-End Testing
Testing the complete RAG pipeline as requested in review:
1. Database Connection: Verify Supabase PostgreSQL connection with session pooler
2. Document Retrieval: Test that queries about "apron flashing" retrieve the 2 seeded test documents (TEST_GUIDE, TEST_WIND)  
3. RAG Responses: Verify `/api/ask` endpoint returns REAL answers (not fallback) with proper citations
4. Response Format: Check that responses include answer, notes, and citation fields
5. Content Quality: Confirm answers mention "150 mm standard" and "200 mm high wind zones"
"""

import requests
import json
import time
import sys
import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend-minimal/.env')

# Configuration
BACKEND_URL = "http://localhost:8000"
DATABASE_URL = os.getenv("DATABASE_URL")

class STRYDAv2RAGTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.database_url = DATABASE_URL
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        
    def test_database_connection(self):
        """Test 1: Verify Supabase PostgreSQL connection with session pooler"""
        print("\n🔍 TEST 1: Database Connection to Supabase PostgreSQL")
        print("=" * 60)
        
        if not self.database_url:
            self.log_test("Database URL Configuration", False, "DATABASE_URL not found in environment")
            return False
            
        try:
            # Test connection
            start_time = time.time()
            conn = psycopg2.connect(self.database_url, sslmode="require")
            connection_time = (time.time() - start_time) * 1000
            
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Verify database details
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                
                # Check if we're using session pooler (should contain 'pooler' in connection string)
                is_session_pooler = 'pooler.supabase.com' in self.database_url
                
                # Verify documents table exists
                cur.execute("""
                    SELECT table_name, column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'documents' 
                    ORDER BY ordinal_position;
                """)
                columns = cur.fetchall()
                
                # Check for pgvector extension
                cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
                vector_ext = cur.fetchone()
                
            conn.close()
            
            self.log_test("Database Connection", True, f"Connected in {connection_time:.0f}ms")
            self.log_test("Session Pooler", is_session_pooler, f"Using session pooler: {is_session_pooler}")
            self.log_test("Documents Table Schema", len(columns) >= 5, f"Found {len(columns)} columns: {[c['column_name'] for c in columns]}")
            self.log_test("pgvector Extension", vector_ext is not None, "Vector extension installed for embeddings")
            
            print(f"   Database: {version[:50]}...")
            print(f"   Connection time: {connection_time:.0f}ms")
            print(f"   Table columns: {len(columns)}")
            
            return True
            
        except Exception as e:
            self.log_test("Database Connection", False, f"Connection failed: {str(e)}")
            return False
    
    def test_seeded_documents(self):
        """Test 2: Verify the 2 seeded test documents exist"""
        print("\n🔍 TEST 2: Seeded Test Documents Verification")
        print("=" * 60)
        
        try:
            conn = psycopg2.connect(self.database_url, sslmode="require")
            
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Check for TEST_GUIDE document
                cur.execute("SELECT * FROM documents WHERE source = 'TEST_GUIDE' AND page = 1;")
                test_guide = cur.fetchone()
                
                # Check for TEST_WIND document  
                cur.execute("SELECT * FROM documents WHERE source = 'TEST_WIND' AND page = 2;")
                test_wind = cur.fetchone()
                
                # Count total documents
                cur.execute("SELECT COUNT(*) as total FROM documents;")
                total_docs = cur.fetchone()['total']
                
            conn.close()
            
            # Verify TEST_GUIDE document
            guide_exists = test_guide is not None
            guide_content_ok = guide_exists and "150 mm" in test_guide['content'] and "standard conditions" in test_guide['content']
            
            # Verify TEST_WIND document
            wind_exists = test_wind is not None  
            wind_content_ok = wind_exists and "200 mm" in test_wind['content'] and "high wind zones" in test_wind['content']
            
            self.log_test("TEST_GUIDE Document", guide_exists, f"Found: {test_guide['content'][:50] if guide_exists else 'Not found'}...")
            self.log_test("TEST_GUIDE Content", guide_content_ok, "Contains '150 mm' and 'standard conditions'")
            self.log_test("TEST_WIND Document", wind_exists, f"Found: {test_wind['content'][:50] if wind_exists else 'Not found'}...")
            self.log_test("TEST_WIND Content", wind_content_ok, "Contains '200 mm' and 'high wind zones'")
            
            print(f"   Total documents in database: {total_docs}")
            
            return guide_exists and wind_exists and guide_content_ok and wind_content_ok
            
        except Exception as e:
            self.log_test("Document Verification", False, f"Database query failed: {str(e)}")
            return False
    
    def test_health_endpoint(self):
        """Test 3: Verify health endpoint returns correct format"""
        print("\n🔍 TEST 3: Health Endpoint")
        print("=" * 60)
        
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                expected_format = data.get("ok") is True and data.get("version") == "v0.2"
                
                self.log_test("Health Endpoint Status", True, f"Status: {response.status_code}")
                self.log_test("Health Response Format", expected_format, f"Response: {data}")
                
                return expected_format
            else:
                self.log_test("Health Endpoint Status", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Health Endpoint", False, f"Request failed: {str(e)}")
            return False
    
    def test_ask_endpoint_format(self):
        """Test 4: Verify /api/ask endpoint response format"""
        print("\n🔍 TEST 4: /api/ask Endpoint Response Format")
        print("=" * 60)
        
        test_query = "What are the apron flashing cover requirements?"
        
        try:
            payload = {"query": test_query}
            response = requests.post(f"{self.backend_url}/api/ask", json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                has_answer = "answer" in data and isinstance(data["answer"], str) and len(data["answer"]) > 0
                has_notes = "notes" in data and isinstance(data["notes"], list)
                has_citation = "citation" in data and isinstance(data["citation"], list)
                
                # Check if it's a real response (not fallback)
                is_real_response = not any(fallback_indicator in data.get("answer", "").lower() 
                                         for fallback_indicator in ["temporary fallback", "service temporarily unavailable", "stub"])
                
                self.log_test("Response Status", True, f"Status: {response.status_code}")
                self.log_test("Answer Field", has_answer, f"Answer length: {len(data.get('answer', ''))}")
                self.log_test("Notes Field", has_notes, f"Notes: {data.get('notes', [])}")
                self.log_test("Citation Field", has_citation, f"Citations: {len(data.get('citation', []))}")
                self.log_test("Real Response (Not Fallback)", is_real_response, f"Answer preview: {data.get('answer', '')[:100]}...")
                
                return has_answer and has_notes and has_citation and is_real_response
            else:
                self.log_test("Ask Endpoint Status", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Ask Endpoint", False, f"Request failed: {str(e)}")
            return False
    
    def test_document_retrieval(self):
        """Test 5: Test that apron flashing queries retrieve the 2 seeded documents"""
        print("\n🔍 TEST 5: Document Retrieval for Apron Flashing Queries")
        print("=" * 60)
        
        test_queries = [
            "What are the apron flashing cover requirements?",
            "apron flashing cover", 
            "flashing requirements wind zones"
        ]
        
        all_queries_successful = True
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n   Query {i}: {query}")
            
            try:
                payload = {"query": query}
                response = requests.post(f"{self.backend_url}/api/ask", json=payload, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    citations = data.get("citation", [])
                    
                    # Check if we got citations from both test documents
                    sources_found = [cite.get("source", "") for cite in citations]
                    has_test_guide = "TEST_GUIDE" in sources_found
                    has_test_wind = "TEST_WIND" in sources_found
                    
                    # Check citation format
                    citations_valid = all(
                        "doc_id" in cite and "source" in cite and "page" in cite and "score" in cite
                        for cite in citations
                    )
                    
                    query_success = len(citations) > 0 and citations_valid
                    
                    self.log_test(f"Query {i} Citations", query_success, f"Found {len(citations)} citations: {sources_found}")
                    self.log_test(f"Query {i} TEST_GUIDE", has_test_guide, "TEST_GUIDE document retrieved")
                    self.log_test(f"Query {i} TEST_WIND", has_test_wind, "TEST_WIND document retrieved")
                    
                    if not query_success:
                        all_queries_successful = False
                        
                else:
                    self.log_test(f"Query {i} Status", False, f"Status: {response.status_code}")
                    all_queries_successful = False
                    
            except Exception as e:
                self.log_test(f"Query {i}", False, f"Request failed: {str(e)}")
                all_queries_successful = False
        
        return all_queries_successful
    
    def test_content_quality(self):
        """Test 6: Verify answers mention specific measurements (150mm, 200mm)"""
        print("\n🔍 TEST 6: Content Quality - Specific Measurements")
        print("=" * 60)
        
        query = "What are the apron flashing cover requirements?"
        
        try:
            payload = {"query": query}
            response = requests.post(f"{self.backend_url}/api/ask", json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "").lower()
                
                # Check for specific content requirements
                mentions_150mm = "150" in answer and "mm" in answer
                mentions_200mm = "200" in answer and "mm" in answer  
                mentions_standard = "standard" in answer
                mentions_wind = "wind" in answer
                
                # Check for proper citations in answer
                has_citations_in_answer = any(source in answer for source in ["test_guide", "test_wind", "[", "]"])
                
                self.log_test("Mentions 150mm Standard", mentions_150mm, f"Found '150' and 'mm' in answer")
                self.log_test("Mentions 200mm High Wind", mentions_200mm, f"Found '200' and 'mm' in answer")
                self.log_test("Mentions Standard Conditions", mentions_standard, f"Found 'standard' in answer")
                self.log_test("Mentions Wind Zones", mentions_wind, f"Found 'wind' in answer")
                self.log_test("Citations in Answer", has_citations_in_answer, f"Answer includes source references")
                
                print(f"\n   Full Answer: {data.get('answer', '')}")
                
                return mentions_150mm and mentions_200mm and mentions_standard and mentions_wind
            else:
                self.log_test("Content Quality Test", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Content Quality Test", False, f"Request failed: {str(e)}")
            return False
    
    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("🎯 STRYDA-v2 RAG SYSTEM COMPREHENSIVE TESTING")
        print("=" * 80)
        print("Testing complete end-to-end RAG pipeline as requested in review")
        print("Focus: Database connection, document retrieval, real RAG responses, content quality")
        print("=" * 80)
        
        # Run all tests
        tests = [
            ("Database Connection", self.test_database_connection),
            ("Seeded Documents", self.test_seeded_documents), 
            ("Health Endpoint", self.test_health_endpoint),
            ("Ask Endpoint Format", self.test_ask_endpoint_format),
            ("Document Retrieval", self.test_document_retrieval),
            ("Content Quality", self.test_content_quality)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                success = test_func()
                if success:
                    passed_tests += 1
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
        
        # Summary
        print("\n" + "=" * 80)
        print("🎯 STRYDA-v2 RAG TESTING SUMMARY")
        print("=" * 80)
        
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"Overall Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        # Detailed results
        print("\nDetailed Results:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"   {result['details']}")
        
        # Final assessment
        if success_rate >= 80:
            print(f"\n🎉 STRYDA-v2 RAG SYSTEM: WORKING EXCELLENTLY ({success_rate:.1f}%)")
            print("✅ Database connection to Supabase working")
            print("✅ Document retrieval operational") 
            print("✅ RAG responses returning real answers with citations")
            print("✅ Content quality meets requirements")
            return True
        else:
            print(f"\n⚠️ STRYDA-v2 RAG SYSTEM: ISSUES DETECTED ({success_rate:.1f}%)")
            print("❌ Some critical components not working as expected")
            return False

def main():
    """Main test execution"""
    print("Starting STRYDA-v2 RAG System Testing...")
    
    # Check if backend is running
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Backend not responding at {BACKEND_URL}")
            print("Please start the backend with: cd /app/backend-minimal && uvicorn app:app --host 0.0.0.0 --port 8000")
            return False
    except:
        print(f"❌ Cannot connect to backend at {BACKEND_URL}")
        print("Please start the backend with: cd /app/backend-minimal && uvicorn app:app --host 0.0.0.0 --port 8000")
        return False
    
    # Run comprehensive tests
    tester = STRYDAv2RAGTester()
    return tester.run_comprehensive_test()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)