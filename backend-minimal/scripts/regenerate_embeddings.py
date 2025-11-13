#!/usr/bin/env python3
"""
STRYDA-v2 Embedding Regeneration Script
Regenerates embeddings for NZS 3604, NZ Building Code, and NZS 4229 documents
using text-embedding-3-small for consistent vector search compatibility
"""

import psycopg2
import psycopg2.extras
from openai import OpenAI
import os
import time
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Configuration
EMBEDDING_MODEL = "text-embedding-3-small"
BATCH_SIZE = 100
TARGET_SOURCES = ['NZS 3604:2011', 'NZ Building Code', 'NZS 4229:2013']

print(f"🔄 STRYDA-v2 Embedding Regeneration")
print(f"   Model: {EMBEDDING_MODEL}")
print(f"   Batch size: {BATCH_SIZE}")
print(f"   Target sources: {TARGET_SOURCES}\n")

client = OpenAI(api_key=OPENAI_API_KEY)

def regenerate_embeddings():
    """Regenerate embeddings for all targeted documents"""
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    
    # Get total count
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*)
        FROM documents
        WHERE source = ANY(%s)
          AND embedding IS NOT NULL;
    """, (TARGET_SOURCES,))
    total_docs = cur.fetchone()[0]
    print(f"📊 Total documents to regenerate: {total_docs}\n")
    cur.close()
    
    # Process in batches
    processed = 0
    failed = 0
    batch_num = 0
    
    while processed < total_docs:
        batch_num += 1
        batch_start = time.time()
        
        print(f"\n{'='*60}")
        print(f"Batch {batch_num} (docs {processed+1}-{min(processed+BATCH_SIZE, total_docs)})")
        print(f"{'='*60}")
        
        # Fetch batch
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT id, source, page, content
            FROM documents
            WHERE source = ANY(%s)
              AND embedding IS NOT NULL
            ORDER BY source, page
            LIMIT %s OFFSET %s;
        """, (TARGET_SOURCES, BATCH_SIZE, processed))
        
        batch_docs = cur.fetchall()
        cur.close()
        
        if not batch_docs:
            break
        
        print(f"  📥 Fetched {len(batch_docs)} documents")
        
        # Generate embeddings
        batch_texts = [doc['content'] for doc in batch_docs]
        batch_ids = [doc['id'] for doc in batch_docs]
        
        try:
            print(f"  ⚡ Generating embeddings...")
            embed_start = time.time()
            
            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=batch_texts
            )
            
            embed_time = time.time() - embed_start
            print(f"  ✅ Generated {len(response.data)} embeddings in {embed_time:.1f}s")
            
            # Update database
            print(f"  💾 Updating database...")
            update_cur = conn.cursor()
            
            for i, embedding_data in enumerate(response.data):
                doc_id = batch_ids[i]
                new_embedding = embedding_data.embedding
                
                update_cur.execute("""
                    UPDATE documents
                    SET embedding = %s
                    WHERE id = %s;
                """, (new_embedding, doc_id))
            
            conn.commit()
            update_cur.close()
            
            print(f"  ✅ Updated {len(response.data)} embeddings in database")
            processed += len(batch_docs)
            
        except Exception as e:
            print(f"  ❌ Batch failed: {e}")
            failed += len(batch_docs)
            conn.rollback()
            processed += len(batch_docs)  # Skip failed batch
        
        batch_time = time.time() - batch_start
        print(f"  ⏱️  Batch completed in {batch_time:.1f}s")
        print(f"  📊 Progress: {processed}/{total_docs} ({processed/total_docs*100:.1f}%)")
    
    conn.close()
    
    return {
        "total": total_docs,
        "processed": processed,
        "failed": failed,
        "batches": batch_num
    }

if __name__ == "__main__":
    start_time = time.time()
    
    stats = regenerate_embeddings()
    
    total_time = time.time() - start_time
    
    print(f"\n{'='*60}")
    print(f"REGENERATION COMPLETE")
    print(f"{'='*60}")
    print(f"  Total documents: {stats['total']}")
    print(f"  Successfully regenerated: {stats['processed'] - stats['failed']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Batches processed: {stats['batches']}")
    print(f"  Total time: {total_time/60:.1f} minutes")
    print(f"\n✅ Embedding regeneration complete!")
