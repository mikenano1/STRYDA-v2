#!/usr/bin/env python3
"""
STRYDA Targeted Reprocessing Script
====================================

Fetches documents from the database, processes through Librarian v3.0,
and updates the vector store with cleaned, properly tagged chunks.

Usage:
    python reprocess_targeted.py --source "kingspan%ks1000rw%roof%"
"""

import os
import sys
import json
import hashlib
from typing import List, Dict, Optional

# Add paths
sys.path.insert(0, '/app/backend-minimal')
sys.path.insert(0, '/app/data/processing')

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

from openai import OpenAI
from librarian_v3 import (
    STRYDALibrarian, 
    IngestionConfig,
    full_text_cleaning,
    auto_tag_document,
    RecursiveTextSplitter
)

# Configuration
DATABASE_URL = 'postgresql://postgres.qxqisgjhbjwvoxsjibes:8skmVOJbMyaQHyQl@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres'
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"


class TargetedReprocessor:
    """
    Reprocesses documents through Librarian v3.0 and updates the vector store.
    """
    
    def __init__(self):
        self.conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        self.openai = OpenAI(api_key=OPENAI_API_KEY)
        self.librarian = STRYDALibrarian()
        self.stats = {
            'documents_fetched': 0,
            'documents_cleaned': 0,
            'chunks_created': 0,
            'chunks_updated': 0,
            'chars_cleaned': 0,
        }
    
    def fetch_documents(self, source_pattern: str, page: int = None) -> List[Dict]:
        """Fetch documents matching the source pattern."""
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        if page:
            cursor.execute('''
                SELECT id, source, page, content, snippet, doc_type, trade, brand_name
                FROM documents 
                WHERE source ILIKE %s AND page = %s
                ORDER BY page
            ''', (f'%{source_pattern}%', page))
        else:
            cursor.execute('''
                SELECT id, source, page, content, snippet, doc_type, trade, brand_name
                FROM documents 
                WHERE source ILIKE %s
                ORDER BY page
            ''', (f'%{source_pattern}%',))
        
        results = cursor.fetchall()
        cursor.close()
        self.stats['documents_fetched'] = len(results)
        return [dict(r) for r in results]
    
    def clean_document(self, doc: Dict) -> Dict:
        """Clean a single document through Librarian v3.0."""
        original_content = doc['content']
        original_len = len(original_content)
        
        # Apply full cleaning pipeline
        cleaned_content = full_text_cleaning(original_content)
        
        # Track stats
        chars_removed = original_len - len(cleaned_content)
        self.stats['chars_cleaned'] += chars_removed
        self.stats['documents_cleaned'] += 1
        
        # Auto-tag for agent domain
        source_name = doc.get('source', '')
        tags = auto_tag_document(source_name, cleaned_content[:2000])
        
        return {
            **doc,
            'original_content': original_content,
            'content': cleaned_content,
            'agent_domain': tags['agent_domain'],
            'auto_doc_type': tags['doc_type'],
            'chars_removed': chars_removed,
        }
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text."""
        try:
            response = self.openai.embeddings.create(
                model=EMBEDDING_MODEL,
                input=text[:20000]
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"   ⚠️ Embedding error: {e}")
            return None
    
    def update_document(self, doc_id: str, cleaned_content: str, agent_domain: str, 
                        embedding: List[float] = None) -> bool:
        """Update a document in the database."""
        try:
            cursor = self.conn.cursor()
            
            if embedding:
                embedding_str = '[' + ','.join(map(str, embedding)) + ']'
                cursor.execute('''
                    UPDATE documents 
                    SET content = %s, 
                        snippet = %s,
                        embedding = %s::vector
                    WHERE id = %s
                ''', (cleaned_content, cleaned_content[:200], embedding_str, doc_id))
            else:
                cursor.execute('''
                    UPDATE documents 
                    SET content = %s, 
                        snippet = %s
                    WHERE id = %s
                ''', (cleaned_content, cleaned_content[:200], doc_id))
            
            self.conn.commit()
            cursor.close()
            self.stats['chunks_updated'] += 1
            return True
        except Exception as e:
            print(f"   ❌ Update error: {e}")
            self.conn.rollback()
            return False
    
    def reprocess_source(self, source_pattern: str, target_page: int = None, 
                         dry_run: bool = True, regenerate_embeddings: bool = False):
        """
        Reprocess documents matching the source pattern.
        
        Args:
            source_pattern: SQL LIKE pattern for source column
            target_page: Specific page to process (None for all)
            dry_run: If True, only show what would change (no DB updates)
            regenerate_embeddings: If True, regenerate embeddings for cleaned text
        """
        print("\n" + "="*70)
        print("STRYDA TARGETED REPROCESSOR")
        print("="*70)
        print(f"Source Pattern: {source_pattern}")
        print(f"Target Page: {target_page or 'ALL'}")
        print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE UPDATE'}")
        print(f"Regenerate Embeddings: {regenerate_embeddings}")
        print("="*70)
        
        # Fetch documents
        print("\n📥 Fetching documents...")
        docs = self.fetch_documents(source_pattern, target_page)
        print(f"   Found {len(docs)} documents")
        
        if not docs:
            print("   ❌ No documents found matching pattern")
            return
        
        # Process each document
        print("\n🔧 Processing documents through Librarian v3.0...")
        
        for i, doc in enumerate(docs):
            print(f"\n--- Document {i+1}/{len(docs)} ---")
            print(f"   ID: {doc['id']}")
            print(f"   Source: {doc['source'][:50]}...")
            print(f"   Page: {doc['page']}")
            
            # Clean the document
            cleaned_doc = self.clean_document(doc)
            
            # Show before/after comparison
            print(f"\n   📊 BEFORE ({len(doc['content'])} chars):")
            print(f"   {doc['content'][:300]}...")
            
            print(f"\n   📊 AFTER ({len(cleaned_doc['content'])} chars):")
            print(f"   {cleaned_doc['content'][:300]}...")
            
            print(f"\n   🧹 Chars removed: {cleaned_doc['chars_removed']}")
            print(f"   🏷️ Agent domain: {cleaned_doc['agent_domain']}")
            
            # Update database if not dry run
            if not dry_run:
                embedding = None
                if regenerate_embeddings:
                    print(f"   🔄 Regenerating embedding...")
                    embedding = self.generate_embedding(cleaned_doc['content'])
                
                if self.update_document(doc['id'], cleaned_doc['content'], 
                                       cleaned_doc['agent_domain'], embedding):
                    print(f"   ✅ Updated in database")
                else:
                    print(f"   ❌ Update failed")
        
        # Summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"   Documents fetched: {self.stats['documents_fetched']}")
        print(f"   Documents cleaned: {self.stats['documents_cleaned']}")
        print(f"   Total chars cleaned: {self.stats['chars_cleaned']}")
        if not dry_run:
            print(f"   Documents updated: {self.stats['chunks_updated']}")
        else:
            print("   (DRY RUN - no changes made)")
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='STRYDA Targeted Reprocessor')
    parser.add_argument('--source', required=True, help='Source pattern to match (SQL LIKE)')
    parser.add_argument('--page', type=int, help='Specific page to process')
    parser.add_argument('--live', action='store_true', help='Apply changes to database')
    parser.add_argument('--embeddings', action='store_true', help='Regenerate embeddings')
    
    args = parser.parse_args()
    
    reprocessor = TargetedReprocessor()
    try:
        reprocessor.reprocess_source(
            source_pattern=args.source,
            target_page=args.page,
            dry_run=not args.live,
            regenerate_embeddings=args.embeddings
        )
    finally:
        reprocessor.close()


if __name__ == '__main__':
    main()
