#!/usr/bin/env python3
"""
STRYDA "The Big Clean" - Full Library Reprocessor
==================================================

System-wide sanitation applying Librarian v3.0 standards to ALL documents.

Features:
- Batch processing with progress tracking
- OCR garbage removal
- Header/footer stripping  
- Agent domain auto-tagging
- Sentence-boundary chunking
- Detailed reporting

Usage:
    python reprocess_all.py --batch-size 100 --live
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

# Add paths
sys.path.insert(0, '/app/backend-minimal')
sys.path.insert(0, '/app/data/processing')

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

from librarian_v3 import (
    full_text_cleaning,
    auto_tag_document,
    clean_ocr_garbage,
    remove_headers_footers,
    fix_hyphenation,
    normalize_whitespace
)

# Configuration
DATABASE_URL = 'postgresql://postgres.qxqisgjhbjwvoxsjibes:8skmVOJbMyaQHyQl@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres'


class BigCleanProcessor:
    """
    Full library reprocessor for STRYDA document sanitation.
    """
    
    def __init__(self):
        self.conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        self.stats = {
            'total_documents': 0,
            'documents_processed': 0,
            'documents_updated': 0,
            'documents_skipped': 0,
            'documents_failed': 0,
            'total_chars_before': 0,
            'total_chars_after': 0,
            'total_chars_cleaned': 0,
            'agent_tags': defaultdict(int),
            'failed_auto_tag': [],
            'sources_processed': set(),
            'start_time': None,
            'end_time': None,
        }
    
    def get_total_documents(self) -> int:
        """Get total document count."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM documents')
        count = cursor.fetchone()[0]
        cursor.close()
        return count
    
    def get_distinct_sources(self) -> List[str]:
        """Get all distinct source names."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT DISTINCT source FROM documents ORDER BY source')
        sources = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return sources
    
    def fetch_documents_batch(self, offset: int, limit: int) -> List[Dict]:
        """Fetch a batch of documents."""
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('''
            SELECT id, source, page, content, snippet, doc_type, trade, brand_name
            FROM documents 
            ORDER BY source, page
            OFFSET %s LIMIT %s
        ''', (offset, limit))
        results = cursor.fetchall()
        cursor.close()
        return [dict(r) for r in results]
    
    def clean_document(self, doc: Dict) -> Tuple[str, int, Dict]:
        """
        Clean a single document and auto-tag it.
        
        Returns:
            Tuple of (cleaned_content, chars_removed, tags_dict)
        """
        original_content = doc['content'] or ''
        original_len = len(original_content)
        
        # Skip if already very short (likely already cleaned or empty)
        if original_len < 10:
            return original_content, 0, {'agent_domain': 'general', 'doc_type': doc.get('doc_type', 'General'), 'confidence': 'low'}
        
        # Apply full cleaning pipeline
        cleaned_content = full_text_cleaning(original_content)
        
        # Calculate chars removed
        chars_removed = original_len - len(cleaned_content)
        
        # Auto-tag for agent domain
        source_name = doc.get('source', '')
        tags = auto_tag_document(source_name, cleaned_content[:2000])
        
        return cleaned_content, chars_removed, tags
    
    def update_document(self, doc_id: str, cleaned_content: str, snippet: str) -> bool:
        """Update a document in the database."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE documents 
                SET content = %s, 
                    snippet = %s
                WHERE id = %s
            ''', (cleaned_content, snippet[:200], doc_id))
            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"      ❌ Update error for {doc_id}: {e}")
            self.conn.rollback()
            return False
    
    def process_all(self, batch_size: int = 500, dry_run: bool = True, 
                    skip_sources: List[str] = None):
        """
        Process all documents in the library.
        
        Args:
            batch_size: Number of documents per batch
            dry_run: If True, only preview changes (no DB updates)
            skip_sources: List of source patterns to skip
        """
        self.stats['start_time'] = datetime.now()
        
        print("\n" + "="*70)
        print("🧹 THE BIG CLEAN - STRYDA LIBRARY SANITATION")
        print("="*70)
        print(f"Started: {self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Mode: {'DRY RUN (preview only)' if dry_run else '🔴 LIVE UPDATE'}")
        print(f"Batch Size: {batch_size}")
        print("="*70)
        
        # Get total count
        self.stats['total_documents'] = self.get_total_documents()
        print(f"\n📚 Total documents in library: {self.stats['total_documents']:,}")
        
        # Process in batches
        offset = 0
        batch_num = 0
        
        while offset < self.stats['total_documents']:
            batch_num += 1
            
            # Fetch batch
            docs = self.fetch_documents_batch(offset, batch_size)
            if not docs:
                break
            
            print(f"\n--- Batch {batch_num} ({offset+1}-{offset+len(docs)} of {self.stats['total_documents']:,}) ---")
            
            batch_cleaned = 0
            batch_chars = 0
            
            for doc in docs:
                self.stats['documents_processed'] += 1
                
                # Skip if in skip list
                if skip_sources:
                    if any(skip in doc['source'] for skip in skip_sources):
                        self.stats['documents_skipped'] += 1
                        continue
                
                # Track source
                self.stats['sources_processed'].add(doc['source'])
                
                # Clean and tag
                try:
                    cleaned_content, chars_removed, tags = self.clean_document(doc)
                    
                    # Update stats
                    self.stats['total_chars_before'] += len(doc['content'] or '')
                    self.stats['total_chars_after'] += len(cleaned_content)
                    self.stats['total_chars_cleaned'] += chars_removed
                    self.stats['agent_tags'][tags['agent_domain']] += 1
                    
                    batch_cleaned += 1
                    batch_chars += chars_removed
                    
                    # Flag failed auto-tags
                    if tags['confidence'] == 'low':
                        self.stats['failed_auto_tag'].append({
                            'id': doc['id'],
                            'source': doc['source'][:50],
                            'domain': tags['agent_domain']
                        })
                    
                    # Update database if not dry run and content changed
                    if not dry_run and chars_removed > 0:
                        if self.update_document(doc['id'], cleaned_content, cleaned_content[:200]):
                            self.stats['documents_updated'] += 1
                        else:
                            self.stats['documents_failed'] += 1
                    
                except Exception as e:
                    self.stats['documents_failed'] += 1
                    print(f"   ❌ Error processing {doc['id'][:8]}: {e}")
            
            print(f"   Cleaned: {batch_cleaned} docs | Garbage removed: {batch_chars:,} chars")
            
            offset += batch_size
            
            # Progress update every 5 batches
            if batch_num % 5 == 0:
                elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
                rate = self.stats['documents_processed'] / elapsed if elapsed > 0 else 0
                remaining = (self.stats['total_documents'] - self.stats['documents_processed']) / rate if rate > 0 else 0
                print(f"   ⏱️ Progress: {self.stats['documents_processed']:,}/{self.stats['total_documents']:,} | Rate: {rate:.1f} docs/sec | ETA: {remaining/60:.1f} min")
        
        self.stats['end_time'] = datetime.now()
        self._print_report(dry_run)
    
    def _print_report(self, dry_run: bool):
        """Print final report."""
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        print("\n" + "="*70)
        print("📊 THE BIG CLEAN - FINAL REPORT")
        print("="*70)
        
        print(f"\n⏱️ TIMING")
        print(f"   Started: {self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Finished: {self.stats['end_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Duration: {duration/60:.1f} minutes ({duration:.0f} seconds)")
        
        print(f"\n📚 DOCUMENT STATISTICS")
        print(f"   Total documents: {self.stats['total_documents']:,}")
        print(f"   Documents processed: {self.stats['documents_processed']:,}")
        print(f"   Documents skipped: {self.stats['documents_skipped']:,}")
        print(f"   Documents failed: {self.stats['documents_failed']:,}")
        if not dry_run:
            print(f"   Documents updated: {self.stats['documents_updated']:,}")
        print(f"   Distinct sources: {len(self.stats['sources_processed']):,}")
        
        print(f"\n🧹 HYGIENE STATISTICS")
        print(f"   Total chars before: {self.stats['total_chars_before']:,}")
        print(f"   Total chars after: {self.stats['total_chars_after']:,}")
        print(f"   Total chars cleaned: {self.stats['total_chars_cleaned']:,}")
        reduction = (self.stats['total_chars_cleaned'] / self.stats['total_chars_before'] * 100) if self.stats['total_chars_before'] > 0 else 0
        print(f"   Reduction: {reduction:.2f}%")
        
        print(f"\n🏷️ AGENT DOMAIN TAGGING")
        for domain, count in sorted(self.stats['agent_tags'].items()):
            pct = count / self.stats['documents_processed'] * 100 if self.stats['documents_processed'] > 0 else 0
            print(f"   {domain}: {count:,} ({pct:.1f}%)")
        
        print(f"\n⚠️ FAILED AUTO-TAG (Manual Review Required)")
        if self.stats['failed_auto_tag']:
            print(f"   Total: {len(self.stats['failed_auto_tag'])} documents")
            # Show first 10
            for item in self.stats['failed_auto_tag'][:10]:
                print(f"   - {item['source']}... -> {item['domain']}")
            if len(self.stats['failed_auto_tag']) > 10:
                print(f"   ... and {len(self.stats['failed_auto_tag']) - 10} more")
        else:
            print("   None - all documents tagged successfully!")
        
        if dry_run:
            print(f"\n⚠️ DRY RUN - No changes were made to the database")
            print(f"   Run with --live flag to apply changes")
        else:
            print(f"\n✅ LIVE RUN COMPLETE - {self.stats['documents_updated']:,} documents updated")
        
        print("\n" + "="*70)
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='STRYDA Big Clean - Full Library Reprocessor')
    parser.add_argument('--batch-size', type=int, default=500, help='Documents per batch')
    parser.add_argument('--live', action='store_true', help='Apply changes to database')
    parser.add_argument('--skip', nargs='*', help='Source patterns to skip')
    
    args = parser.parse_args()
    
    processor = BigCleanProcessor()
    try:
        processor.process_all(
            batch_size=args.batch_size,
            dry_run=not args.live,
            skip_sources=args.skip
        )
    finally:
        processor.close()


if __name__ == '__main__':
    main()
