#!/usr/bin/env python3
"""
Minimal seed routine for testing RAG pipeline
Inserts 2 test documents with mock embeddings for testing
"""

import os
import sys
import psycopg2
import psycopg2.extras
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def generate_mock_embedding(text: str, dim: int = 1536) -> list:
    """Generate a reproducible mock embedding based on text"""
    # Use text hash as seed for reproducibility
    seed = hash(text) % (2**32)
    random.seed(seed)
    
    # Generate normalized random vector
    embedding = [random.uniform(-0.5, 0.5) for _ in range(dim)]
    
    # Normalize to unit length (common for embeddings)
    magnitude = sum(x*x for x in embedding) ** 0.5
    embedding = [x / magnitude for x in embedding]
    
    return embedding

def seed_test_documents():
    """Seed 2 test documents with mock embeddings"""
    
    # Test documents
    test_docs = [
        {
            "source": "TEST_GUIDE",
            "page": 1,
            "content": "Apron flashing cover must be 150 mm in standard conditions."
        },
        {
            "source": "TEST_WIND", 
            "page": 2,
            "content": "In very high wind zones, apron flashing cover increases to 200 mm."
        }
    ]
    
    # Get database connection
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in environment")
        return False
    
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        print("✅ Connected to database")
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Process each document
            for doc in test_docs:
                print(f"\n🔄 Processing document: {doc['source']} page {doc['page']}")
                print(f"   Content: {doc['content'][:50]}...")
                
                # Generate mock embedding (reproducible based on content)
                embedding = generate_mock_embedding(doc['content'])
                print(f"✅ Generated mock embedding ({len(embedding)} dimensions)")
                
                # Insert document with embedding
                try:
                    cur.execute("""
                        INSERT INTO documents (source, page, content, embedding, created_at)
                        VALUES (%s, %s, %s, %s, NOW())
                    """, (doc['source'], doc['page'], doc['content'], embedding))
                    print(f"✅ Inserted document: {doc['source']}")
                except Exception as e:
                    print(f"❌ Database insertion failed for {doc['source']}: {e}")
                    return False
            
            # Commit all changes
            conn.commit()
            print(f"\n✅ Successfully seeded {len(test_docs)} documents with mock embeddings")
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection/operation failed: {e}")
        return False

def verify_seeding():
    """Verify the seeding worked with SQL queries"""
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found")
        return
    
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            print("\n📊 VERIFICATION RESULTS:")
            print("=" * 50)
            
            # Count total documents
            cur.execute("SELECT COUNT(*) AS n FROM documents;")
            count = cur.fetchone()['n']
            print(f"Total documents: {count}")
            
            # Show recent documents
            cur.execute("""
                SELECT source, page, LEFT(content, 80) AS preview 
                FROM documents 
                ORDER BY created_at DESC 
                LIMIT 5;
            """)
            rows = cur.fetchall()
            
            print("\nRecent documents:")
            for row in rows:
                print(f"  • {row['source']} (p.{row['page']}): {row['preview']}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")

if __name__ == "__main__":
    print("🌱 Starting minimal seed routine for RAG testing")
    print("🎯 Target: 2 test documents with mock embeddings")
    print("⚠️  Note: Using mock embeddings due to LLM API compatibility issues")
    
    success = seed_test_documents()
    
    if success:
        verify_seeding()
        print("\n🎉 SEEDING COMPLETED SUCCESSFULLY!")
        print("Ready for end-to-end RAG testing (with mock embeddings)")
    else:
        print("\n❌ SEEDING FAILED")
        print("Check logs above for details")
        sys.exit(1)