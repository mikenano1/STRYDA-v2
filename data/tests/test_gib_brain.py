#!/usr/bin/env python3
"""
STRYDA Big Brain - GIB Intertwine Test
Tests that GIB documents are properly searchable via the RAG pipeline
"""

import os
import sys
import json

sys.path.insert(0, '/app/backend-minimal')
from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

import psycopg2
import psycopg2.extras
from openai import OpenAI

DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Test queries for GIB content
TEST_QUERIES = [
    {
        "query": "What is the fastener spacing for GIB Braceline?",
        "expected_keywords": ["braceline", "fastener", "spacing", "mm", "screw"],
        "expected_source": "GIB"
    },
    {
        "query": "How do I install GIB plasterboard on steel framing?",
        "expected_keywords": ["steel", "framing", "screw", "fastener", "stud"],
        "expected_source": "GIB"
    },
    {
        "query": "What is the fire rating for GIB Fyreline?",
        "expected_keywords": ["fire", "rating", "fyreline", "minutes", "FRR"],
        "expected_source": "GIB"
    },
    {
        "query": "GIB stopping compound joint treatment",
        "expected_keywords": ["stopping", "compound", "joint", "tape", "coat"],
        "expected_source": "GIB"
    }
]


def test_vector_search(query: str) -> list:
    """Test direct vector search for a query"""
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Generate embedding
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    embedding = response.data[0].embedding
    vector_str = '[' + ','.join(map(str, embedding)) + ']'
    
    # Search database
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cursor.execute("""
        SELECT 
            source, brand_name, page, 
            LEFT(content, 500) as preview,
            (1 - (embedding <=> %s::vector))::float as similarity
        FROM documents
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> %s::vector
        LIMIT 10
    """, (vector_str, vector_str))
    
    results = cursor.fetchall()
    conn.close()
    
    return results


def test_gib_specific_search(query: str) -> list:
    """Test search specifically for GIB content"""
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    embedding = response.data[0].embedding
    vector_str = '[' + ','.join(map(str, embedding)) + ']'
    
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cursor.execute("""
        SELECT 
            source, brand_name, page, 
            LEFT(content, 500) as preview,
            (1 - (embedding <=> %s::vector))::float as similarity
        FROM documents
        WHERE embedding IS NOT NULL
        AND brand_name = 'GIB'
        ORDER BY embedding <=> %s::vector
        LIMIT 5
    """, (vector_str, vector_str))
    
    results = cursor.fetchall()
    conn.close()
    
    return results


def run_tests():
    """Run all intertwine tests"""
    print("=" * 70)
    print("🧠 STRYDA Big Brain - GIB INTERTWINE TEST")
    print("=" * 70)
    
    # First, check GIB content exists
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cursor.execute("""
        SELECT COUNT(*) as count, brand_name, category_code
        FROM documents
        WHERE brand_name = 'GIB'
        GROUP BY brand_name, category_code
    """)
    gib_stats = cursor.fetchall()
    conn.close()
    
    print(f"\n📊 GIB Content in Database:")
    for stat in gib_stats:
        print(f"   Brand: {stat['brand_name']} | Category: {stat['category_code']} | Chunks: {stat['count']}")
    
    if not gib_stats:
        print("❌ No GIB content found in database!")
        return False
    
    print("\n" + "=" * 70)
    print("🔍 RUNNING TEST QUERIES")
    print("=" * 70)
    
    all_passed = True
    
    for i, test in enumerate(TEST_QUERIES, 1):
        print(f"\n--- Test {i}: {test['query'][:50]}... ---")
        
        # Run vector search
        results = test_vector_search(test['query'])
        
        # Check if GIB content appears in top results
        gib_in_top5 = any(r.get('brand_name') == 'GIB' for r in results[:5])
        gib_position = next((i+1 for i, r in enumerate(results) if r.get('brand_name') == 'GIB'), None)
        
        # Check for expected keywords in top result
        top_result = results[0] if results else None
        keywords_found = []
        if top_result:
            preview_lower = top_result['preview'].lower()
            keywords_found = [kw for kw in test['expected_keywords'] if kw.lower() in preview_lower]
        
        # Report
        if gib_in_top5:
            print(f"   ✅ GIB content found at position #{gib_position}")
        else:
            print(f"   ⚠️ GIB content NOT in top 5 (position: {gib_position or 'N/A'})")
            all_passed = False
        
        print(f"   📝 Keywords found: {keywords_found[:5]}")
        
        if top_result:
            print(f"   🥇 Top result: {top_result['source'][:40]}... (sim: {top_result['similarity']:.4f})")
            print(f"      Preview: {top_result['preview'][:100]}...")
        
        # GIB-specific search
        gib_results = test_gib_specific_search(test['query'])
        if gib_results:
            print(f"   🎯 GIB-specific top result: Page {gib_results[0]['page']} (sim: {gib_results[0]['similarity']:.4f})")
    
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    if all_passed:
        print("✅ ALL TESTS PASSED - GIB content is properly intertwined!")
    else:
        print("⚠️ SOME TESTS NEED ATTENTION - Review results above")
    
    return all_passed


def test_chat_endpoint(query: str):
    """Test the actual chat endpoint with a GIB query"""
    import requests
    
    print(f"\n🤖 Testing Chat Endpoint: \"{query}\"")
    
    response = requests.post(
        "http://localhost:8001/api/chat",
        json={
            "session_id": "gib_test_001",
            "message": query
        },
        timeout=60
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Response received ({len(data.get('answer', ''))} chars)")
        print(f"   📝 Answer preview: {data.get('answer', '')[:200]}...")
        
        # Check for GIB mention
        if 'gib' in data.get('answer', '').lower():
            print("   ✅ GIB mentioned in response!")
        else:
            print("   ⚠️ GIB not explicitly mentioned")
        
        return data
    else:
        print(f"   ❌ Error: {response.status_code}")
        return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--chat", action="store_true", help="Also test chat endpoint")
    args = parser.parse_args()
    
    success = run_tests()
    
    if args.chat:
        print("\n" + "=" * 70)
        print("🤖 CHAT ENDPOINT TEST")
        print("=" * 70)
        test_chat_endpoint("What is the fastener spacing for GIB Braceline?")
    
    sys.exit(0 if success else 1)
