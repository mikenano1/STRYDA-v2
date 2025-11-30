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
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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
    
    # Get all document IDs to process
    cur = conn.cursor()
    cur.execute("""
        SELECT id, content
        FROM documents
        WHERE source = ANY(%s)
        ORDER BY id;
    """, (TARGET_SOURCES,))
    all_docs = cur.fetchall()
    total_docs = len(all_docs)
    cur.close()
    
    print(f"📊 Total documents to regenerate: {total_docs}\n")
    
    # Process in batches
    processed = 0
    failed = 0
    start_time = time.time()
    
    for i in range(0, total_docs, BATCH_SIZE):
        batch = all_docs[i:i + BATCH_SIZE]
        processed += process_batch(batch, conn)
        
        # Progress update
        pct = (processed / total_docs) * 100
        elapsed = time.time() - start_time
        rate = processed / elapsed if elapsed > 0 else 0
        eta = (total_docs - processed) / rate if rate > 0 else 0
        print(f"   [{processed}/{total_docs}] {pct:.1f}% | {rate:.1f} docs/sec | ETA: {eta/60:.1f}min")
    
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
        texts = [row[1] for row in batch]  # content is at index 1
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts
        )
        
        # Update database
        with conn.cursor() as cur:
            for i, row in enumerate(batch):
                embedding = response.data[i].embedding
                doc_id = row[0]  # id is at index 0
                cur.execute("""
                    UPDATE documents
                    SET embedding = %s::vector
                    WHERE id = %s;
                """, (embedding, doc_id))
        
        conn.commit()
        return len(batch)
        
    except Exception as e:
        print(f"   ❌ Batch failed: {e}")
        conn.rollback()
        return 0

if __name__ == "__main__":
    regenerate_embeddings()
