#!/usr/bin/env python3
"""
STRYDA-v2 Complete Embedding Regeneration Script
Regenerates embeddings for ALL documents using text-embedding-3-small
for consistent vector search compatibility across all sources
"""

import psycopg2
import psycopg2.extras
from openai import OpenAI
import os
import time

DATABASE_URL = "postgresql://postgres.qxqisgjhbjwvoxsjibes:8skmVOJbMyaQHyQl@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres"
OPENAI_API_KEY = "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"

# Configuration
EMBEDDING_MODEL = "text-embedding-3-small"
BATCH_SIZE = 50
# Target E2/AS1 specifically (the source with incompatible embeddings)
TARGET_SOURCES = ['E2/AS1', 'B1/AS1', 'NZ Metal Roofing']

print(f"🔄 STRYDA-v2 Complete Embedding Regeneration")
print(f"   Model: {EMBEDDING_MODEL}")
print(f"   Batch size: {BATCH_SIZE}")
print(f"   Target sources: {TARGET_SOURCES}\n")

client = OpenAI(api_key=OPENAI_API_KEY)

def regenerate_embeddings():
    """Regenerate embeddings for targeted documents"""
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    
    # Get total count
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*)
        FROM documents
        WHERE source = ANY(%s);
    """, (TARGET_SOURCES,))
    total_docs = cur.fetchone()[0]
    print(f"📊 Total documents to regenerate: {total_docs}\n")
    cur.close()
    
    # Process in batches
    processed = 0
    failed = 0
    start_time = time.time()
    
    # Fetch documents in batches
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor, name='embedding_regen') as cur:
        cur.execute("""
            SELECT id, content
            FROM documents
            WHERE source = ANY(%s)
            ORDER BY id;
        """, (TARGET_SOURCES,))
        
        batch = []
        for row in cur:
            batch.append(row)
            
            if len(batch) >= BATCH_SIZE:
                processed += process_batch(batch, conn)
                batch = []
                
                # Progress update
                pct = (processed / total_docs) * 100
                elapsed = time.time() - start_time
                rate = processed / elapsed if elapsed > 0 else 0
                eta = (total_docs - processed) / rate if rate > 0 else 0
                print(f"   [{processed}/{total_docs}] {pct:.1f}% | {rate:.1f} docs/sec | ETA: {eta/60:.1f}min")
        
        # Process remaining
        if batch:
            processed += process_batch(batch, conn)
    
    conn.close()
    
    elapsed = time.time() - start_time
    print(f"\n✅ Regeneration complete!")
    print(f"   Total processed: {processed}")
    print(f"   Failed: {failed}")
    print(f"   Time: {elapsed/60:.1f} minutes")
    print(f"   Average: {processed/elapsed:.1f} docs/sec")

def process_batch(batch, conn):
    """Process a batch of documents"""
    try:
        # Generate embeddings
        texts = [row['content'] for row in batch]
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts
        )
        
        # Update database
        with conn.cursor() as cur:
            for i, row in enumerate(batch):
                embedding = response.data[i].embedding
                cur.execute("""
                    UPDATE documents
                    SET embedding = %s::vector
                    WHERE id = %s;
                """, (embedding, row['id']))
        
        conn.commit()
        return len(batch)
        
    except Exception as e:
        print(f"   ❌ Batch failed: {e}")
        conn.rollback()
        return 0

if __name__ == "__main__":
    regenerate_embeddings()
