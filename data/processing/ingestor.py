#!/usr/bin/env python3
"""
STRYDA Big Brain - Ingestor
Generates embeddings and inserts chunks into Supabase documents table
"""

import os
import sys
import json
import time
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass

import psycopg2
import psycopg2.extras
from openai import OpenAI

# Add backend to path
sys.path.insert(0, '/app/backend-minimal')
from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"
BATCH_SIZE = 20  # Process embeddings in batches
RATE_LIMIT_DELAY = 0.5  # Seconds between batches

@dataclass
class IngestionConfig:
    """Configuration for document ingestion"""
    brand_name: str
    category_code: str
    doc_type: str
    product_family: str
    trade: str
    source_name: str
    priority: int = 80


class BigBrainIngestor:
    """Ingests document chunks into Supabase with embeddings"""
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
        self.conn = None
        self.stats = {
            "chunks_processed": 0,
            "chunks_inserted": 0,
            "chunks_skipped": 0,
            "embeddings_generated": 0,
            "errors": []
        }
    
    def connect_db(self):
        """Establish database connection"""
        if not self.conn or self.conn.closed:
            self.conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        return self.conn
    
    def close_db(self):
        """Close database connection"""
        if self.conn and not self.conn.closed:
            self.conn.close()
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a single text"""
        try:
            # Truncate if too long (OpenAI limit is ~8000 tokens)
            if len(text) > 20000:
                text = text[:20000]
            
            response = self.openai_client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"   ⚠️ Embedding error: {e}")
            self.stats["errors"].append(str(e))
            return None
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate embeddings for a batch of texts"""
        try:
            # Truncate long texts
            cleaned_texts = [t[:20000] if len(t) > 20000 else t for t in texts]
            
            response = self.openai_client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=cleaned_texts
            )
            
            self.stats["embeddings_generated"] += len(texts)
            return [item.embedding for item in response.data]
        except Exception as e:
            print(f"   ⚠️ Batch embedding error: {e}")
            self.stats["errors"].append(str(e))
            return [None] * len(texts)
    
    def chunk_exists(self, file_hash: str, page: int, content_hash: str) -> bool:
        """Check if a chunk already exists (deduplication)"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM documents 
            WHERE file_hash = %s AND page = %s
        """, (file_hash, page))
        count = cursor.fetchone()[0]
        return count > 0
    
    def insert_chunk(self, chunk: Dict, config: IngestionConfig, embedding: List[float]) -> bool:
        """Insert a single chunk into the database"""
        try:
            cursor = self.conn.cursor()
            
            # Generate content hash for deduplication
            content_hash = hashlib.md5(chunk['content'].encode()).hexdigest()
            
            # Prepare embedding as PostgreSQL vector string
            embedding_str = '[' + ','.join(map(str, embedding)) + ']'
            
            # Insert the chunk
            cursor.execute("""
                INSERT INTO documents (
                    source, page, content, embedding, section, snippet,
                    brand_name, category_code, product_family, doc_type, trade,
                    priority, status, ingestion_source, file_hash, ingested_at,
                    created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s::vector, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    NOW(), NOW()
                )
            """, (
                config.source_name,
                chunk.get('page', 0),
                chunk['content'],
                embedding_str,
                chunk.get('section'),
                chunk['content'][:200],  # Snippet
                config.brand_name,
                config.category_code,
                config.product_family,
                config.doc_type,
                config.trade,
                config.priority,
                'active',
                'bigbrain_ingestor',
                content_hash,
                datetime.now()
            ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            self.conn.rollback()
            print(f"   ❌ Insert error: {e}")
            self.stats["errors"].append(str(e))
            return False
    
    def ingest_chunks(self, chunks: List[Dict], config: IngestionConfig) -> Dict:
        """Ingest a list of chunks with embeddings"""
        print("=" * 60)
        print("🧠 STRYDA Big Brain - Ingestor")
        print("=" * 60)
        print(f"\n📚 Source: {config.source_name}")
        print(f"🏷️  Brand: {config.brand_name}")
        print(f"📂 Category: {config.category_code}")
        print(f"📄 Doc Type: {config.doc_type}")
        print(f"\n📦 Total chunks to process: {len(chunks)}")
        
        self.connect_db()
        
        # Process in batches
        total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE
        
        for batch_idx in range(total_batches):
            start_idx = batch_idx * BATCH_SIZE
            end_idx = min(start_idx + BATCH_SIZE, len(chunks))
            batch = chunks[start_idx:end_idx]
            
            print(f"\n📦 Processing batch {batch_idx + 1}/{total_batches} ({len(batch)} chunks)...")
            
            # Generate embeddings for batch
            texts = [c['content'] for c in batch]
            embeddings = self.generate_embeddings_batch(texts)
            
            # Insert each chunk
            for chunk, embedding in zip(batch, embeddings):
                self.stats["chunks_processed"] += 1
                
                if embedding is None:
                    self.stats["chunks_skipped"] += 1
                    continue
                
                if self.insert_chunk(chunk, config, embedding):
                    self.stats["chunks_inserted"] += 1
                else:
                    self.stats["chunks_skipped"] += 1
            
            # Rate limiting
            if batch_idx < total_batches - 1:
                time.sleep(RATE_LIMIT_DELAY)
        
        self.close_db()
        
        # Print summary
        print(f"\n" + "=" * 60)
        print(f"📊 INGESTION SUMMARY")
        print(f"=" * 60)
        print(f"   ✅ Chunks inserted: {self.stats['chunks_inserted']}")
        print(f"   ⏭️  Chunks skipped: {self.stats['chunks_skipped']}")
        print(f"   🔢 Embeddings generated: {self.stats['embeddings_generated']}")
        if self.stats['errors']:
            print(f"   ❌ Errors: {len(self.stats['errors'])}")
        
        return self.stats


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Big Brain Ingestor")
    parser.add_argument("--chunks", "-c", required=True, help="Path to chunks.json file")
    parser.add_argument("--brand", "-b", required=True, help="Brand name")
    parser.add_argument("--category", required=True, help="Category code (e.g., C_Interiors)")
    parser.add_argument("--doc-type", required=True, help="Document type")
    parser.add_argument("--product-family", default="General", help="Product family")
    parser.add_argument("--trade", default="general", help="Trade category")
    parser.add_argument("--source", required=True, help="Source name for database")
    parser.add_argument("--priority", type=int, default=80, help="Priority (0-100)")
    
    args = parser.parse_args()
    
    # Load chunks
    with open(args.chunks) as f:
        chunks = json.load(f)
    
    print(f"📂 Loaded {len(chunks)} chunks from {args.chunks}")
    
    # Create config
    config = IngestionConfig(
        brand_name=args.brand,
        category_code=args.category,
        doc_type=args.doc_type,
        product_family=args.product_family,
        trade=args.trade,
        source_name=args.source,
        priority=args.priority
    )
    
    # Run ingestion
    ingestor = BigBrainIngestor()
    stats = ingestor.ingest_chunks(chunks, config)
    
    # Save stats
    stats_file = args.chunks.replace('.json', '_ingestion_stats.json')
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    print(f"\n📋 Stats saved to: {stats_file}")


if __name__ == "__main__":
    main()
