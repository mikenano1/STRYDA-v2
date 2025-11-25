#!/usr/bin/env python3
"""
STRYDA-v2 Training Corpus Ingestion Pipeline
Handles validation, embedding generation, and database insertion for training batches
"""

import json
import psycopg2
import psycopg2.extras
from openai import OpenAI
import os
from datetime import datetime
import time
from typing import Dict, List, Any

# Configuration
DATABASE_URL = "postgresql://postgres.qxqisgjhbjwvoxsjibes:8skmVOJbMyaQHyQl@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "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")
EMBEDDING_MODEL = "text-embedding-3-small"
BATCH_SIZE = 50

client = OpenAI(api_key=OPENAI_API_KEY)

def validate_batch_json(batch_path: str) -> Dict[str, Any]:
    """Validate batch.json structure"""
    try:
        with open(batch_path, 'r') as f:
            data = json.load(f)
        
        required_fields = ['batch_id', 'category', 'items']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        return data
    except Exception as e:
        raise Exception(f"Batch validation failed: {e}")

def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for a list of texts"""
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts
        )
        return [item.embedding for item in response.data]
    except Exception as e:
        raise Exception(f"Embedding generation failed: {e}")

def insert_training_items(items: List[Dict], batch_id: str, category: str, conn):
    """Insert training items into database with embeddings"""
    inserted = 0
    failed = 0
    
    # Process in batches
    for i in range(0, len(items), BATCH_SIZE):
        batch = items[i:i + BATCH_SIZE]
        
        try:
            # Extract texts for embedding (use 'question' field for training data)
            texts = [item.get('question', item.get('content', item.get('text', ''))) for item in batch]
            
            # Generate embeddings
            embeddings = generate_embeddings(texts)
            
            # Insert into database
            with conn.cursor() as cur:
                for j, item in enumerate(batch):
                    try:
                        cur.execute("""
                            INSERT INTO training_data 
                            (batch_id, category, content, metadata, embedding)
                            VALUES (%s, %s, %s, %s, %s::vector)
                        """, (
                            batch_id,
                            category,
                            texts[j],
                            json.dumps(item),
                            embeddings[j]
                        ))
                        inserted += 1
                    except Exception as e:
                        print(f"   ⚠️ Failed to insert item {i+j}: {e}")
                        failed += 1
            
            conn.commit()
            print(f"   [{inserted}/{len(items)}] Processed batch {i//BATCH_SIZE + 1}")
            
        except Exception as e:
            print(f"   ❌ Batch processing failed: {e}")
            conn.rollback()
            failed += len(batch)
    
    return inserted, failed

def ingest_batch(batch_num: int) -> Dict[str, Any]:
    """
    Main ingestion function for a specific batch
    """
    batch_id = f"batch_{batch_num:02d}"
    batch_dir = f"/app/backend-minimal/training/batches/{batch_id}"
    batch_path = f"{batch_dir}/batch.json"
    metadata_path = f"{batch_dir}/metadata.json"
    
    print(f"\n{'='*80}")
    print(f"STRYDA-v2 Training Corpus Ingestion - {batch_id.upper()}")
    print(f"{'='*80}\n")
    
    start_time = time.time()
    
    # Step 1: Validate batch JSON
    print("1. Validating batch JSON...")
    try:
        batch_data = validate_batch_json(batch_path)
        print(f"   ✅ Batch validated: {len(batch_data['items'])} items")
    except Exception as e:
        print(f"   ❌ Validation failed: {e}")
        return {"status": "failed", "reason": str(e)}
    
    # Step 2: Connect to database
    print("\n2. Connecting to database...")
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        print("   ✅ Database connected")
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return {"status": "failed", "reason": str(e)}
    
    # Step 3: Insert training items with embeddings
    print("\n3. Generating embeddings and inserting items...")
    try:
        inserted, failed = insert_training_items(
            batch_data['items'],
            batch_id,
            batch_data['category'],
            conn
        )
        print(f"   ✅ Inserted: {inserted}, Failed: {failed}")
    except Exception as e:
        print(f"   ❌ Insertion failed: {e}")
        conn.close()
        return {"status": "failed", "reason": str(e)}
    
    conn.close()
    
    # Step 4: Update metadata
    print("\n4. Updating metadata...")
    try:
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        metadata['ingested_at'] = datetime.now().isoformat()
        metadata['total_items'] = inserted
        metadata['failed_items'] = failed
        metadata['validation_status'] = "complete" if failed == 0 else "partial"
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print("   ✅ Metadata updated")
    except Exception as e:
        print(f"   ⚠️ Metadata update failed: {e}")
    
    # Step 5: Log ingestion
    elapsed = time.time() - start_time
    print(f"\n{'='*80}")
    print(f"✅ Batch {batch_id} ingestion complete")
    print(f"   Total items: {inserted}")
    print(f"   Failed: {failed}")
    print(f"   Time: {elapsed/60:.1f} minutes")
    print(f"{'='*80}\n")
    
    return {
        "status": "success",
        "batch_id": batch_id,
        "inserted": inserted,
        "failed": failed,
        "elapsed_seconds": elapsed
    }

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 ingestion_pipeline.py <batch_number>")
        print("Example: python3 ingestion_pipeline.py 1")
        sys.exit(1)
    
    batch_num = int(sys.argv[1])
    result = ingest_batch(batch_num)
    
    if result['status'] == 'success':
        print(f"\n🎉 Ready for Batch {batch_num + 1:02d}")
    else:
        print(f"\n❌ Ingestion failed: {result.get('reason', 'Unknown error')}")
