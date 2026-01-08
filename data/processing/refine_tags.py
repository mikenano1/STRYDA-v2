#!/usr/bin/env python3
"""
STRYDA Re-Tagging Script - Metadata Update
===========================================

Refines agent_domain tags for documents currently marked as 'general'
by applying stricter keyword matching on filenames/source names.

This does NOT re-process text - only updates metadata tags.
"""

import os
import sys
import re
from typing import List, Dict, Tuple
from collections import defaultdict

sys.path.insert(0, '/app/backend-minimal')

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

DATABASE_URL = 'postgresql://postgres.qxqisgjhbjwvoxsjibes:8skmVOJbMyaQHyQl@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres'

# =============================================================================
# ENHANCED KEYWORD LISTS FOR RE-TAGGING
# =============================================================================

# Keywords that indicate PRODUCT documents (The Manuals/Specs)
PRODUCT_REP_KEYWORDS = [
    # Document types (ENHANCED)
    "manual", "guide", "specification", "install", "datasheet", "data sheet",
    "tds", "sds", "appraisal", "codemark", "cert", "warranty", "branz",
    "brochure", "catalogue", "catalog", "product", "range", "series",
    "technical", "spec sheet", "details", "drawings", "certificate",
    
    # Major NZ Brands - Building/Construction
    "abodo", "gib", "james hardie", "hardie", "kingspan", "expol", 
    "resene", "sika", "knauf", "csr", "bostik", "dulux", "holdfast",
    
    # Insulation brands (ENHANCED - therm catch-all)
    "greenstuf", "earthwool", "pink batts", "autex", "mammoth", 
    "thermakraft", "thermaslab", "styrofoam", "therm",
    
    # Timber/Framing brands (ENHANCED - frame, truss catch-all)
    "red stag", "redstag", "hyne", "futurebuild", "future build",
    "j-frame", "jframe", "triboard", "xlam", "wesbeam", "carter holt",
    "frame", "truss",
    
    # Roofing/Cladding
    "colorsteel", "metalcraft", "dimond", "roofing industries",
    "marley", "monier", "nuralite", "viking",
    
    # Fasteners/Fixings
    "paslode", "ramset", "hilti", "fischer", "buildex", "nz nail",
    "mitek", "pryda", "multinail",
    
    # Windows/Doors
    "altherm", "fletcher", "metro", "aws", "fairview",
    
    # Plumbing/HVAC
    "marley", "iplex", "heatcraft", "mitsubishi", "daikin", "fujitsu",
    
    # Other major suppliers
    "nuplex", "selleys", "parex", "mapei", "fosroc", "denso",
    "tremco", "soudal", "everbuild", "geocel", "dow corning",
    
    # Additional NZ brands
    "asona", "bradford", "ecko", "firth", "bremick", "delfast", 
    "macsim", "mainland", "simpson", "spax", "titan", "zenith",
    "j&l duke", "metal roofing", "fasteners", "nz_nails", "nz nails",
    "placemakers", "nz_metal",
]

# Keywords that indicate COMPLIANCE/INSPECTOR documents (The Rules)
INSPECTOR_KEYWORDS = [
    # Standards & Codes (ENHANCED)
    "nzs", "as/nzs", "as1", "as2", "as3", "vm1", "vm2",
    "building code", "building-code", "nzbc", "building act", "act", "regulation",
    "clause", "schedule",
    
    # Compliance documents (ENHANCED)
    "determination", "acceptable solution", "verification method",
    "compliance", "amendment", "code of practice",
    
    # Regulatory bodies
    "mbie", "ministry", "branz appraisal",  # Note: BRANZ appraisals go to inspector
    "council", "consent", "codemark certificate",
    
    # Specific code clauses
    "b1", "b2", "e1", "e2", "e3", "f1", "f2", "f4", "f7",
    "g1", "g4", "g7", "g12", "h1", "c/as", "d1",
]


def classify_source(source: str) -> Tuple[str, str]:
    """
    Classify a source/filename into agent domain.
    
    Returns:
        Tuple of (domain, matched_keyword)
    """
    source_lower = source.lower()
    
    # Check INSPECTOR keywords first (compliance takes priority)
    for keyword in INSPECTOR_KEYWORDS:
        if keyword in source_lower:
            return ('inspector', keyword)
    
    # Check PRODUCT_REP keywords
    for keyword in PRODUCT_REP_KEYWORDS:
        if keyword in source_lower:
            return ('product_rep', keyword)
    
    # No match - stays general
    return ('general', None)


class ReTagProcessor:
    """Re-tags documents based on enhanced keyword matching."""
    
    def __init__(self):
        self.conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        self.stats = {
            'total_general': 0,
            'moved_to_inspector': 0,
            'moved_to_product_rep': 0,
            'still_general': 0,
            'failed': 0,
            'keyword_matches': defaultdict(int),
        }
    
    def get_general_documents(self) -> List[Dict]:
        """Fetch all documents with 'general' tag or no tag."""
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get documents that need re-tagging
        # We'll check for doc_type patterns that suggest general/untagged
        cursor.execute('''
            SELECT DISTINCT source 
            FROM documents 
            ORDER BY source
        ''')
        
        sources = [dict(r) for r in cursor.fetchall()]
        cursor.close()
        return sources
    
    def count_documents_by_source(self, source: str) -> int:
        """Count how many chunks belong to a source."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM documents WHERE source = %s', (source,))
        count = cursor.fetchone()[0]
        cursor.close()
        return count
    
    def update_source_tags(self, source: str, new_domain: str) -> int:
        """Update all documents with given source to new domain tag."""
        try:
            cursor = self.conn.cursor()
            
            # We need to add agent_domain to the documents table if it doesn't exist
            # For now, we'll update doc_type based on the domain
            # This maps to the existing AGENT_SCOPES in simple_tier1_retrieval.py
            
            # Map domain to appropriate doc_type values
            if new_domain == 'inspector':
                # Keep existing doc_type but ensure it's in inspector scope
                cursor.execute('''
                    UPDATE documents 
                    SET doc_type = CASE 
                        WHEN doc_type IS NULL OR doc_type = '' OR doc_type = 'General_Document' 
                        THEN 'Compliance_Document'
                        ELSE doc_type 
                    END
                    WHERE source = %s
                ''', (source,))
            elif new_domain == 'product_rep':
                cursor.execute('''
                    UPDATE documents 
                    SET doc_type = CASE 
                        WHEN doc_type IS NULL OR doc_type = '' OR doc_type = 'General_Document' 
                        THEN 'Technical_Data_Sheet'
                        ELSE doc_type 
                    END
                    WHERE source = %s
                ''', (source,))
            
            affected = cursor.rowcount
            self.conn.commit()
            cursor.close()
            return affected
        except Exception as e:
            print(f"   ❌ Error updating {source[:50]}: {e}")
            self.conn.rollback()
            self.stats['failed'] += 1
            return 0
    
    def process_all(self, dry_run: bool = True):
        """Process all sources and re-tag based on keywords."""
        print("\n" + "="*70)
        print("🏷️ STRYDA RE-TAGGING - METADATA UPDATE")
        print("="*70)
        print(f"Mode: {'DRY RUN (preview only)' if dry_run else '🔴 LIVE UPDATE'}")
        print("="*70)
        
        # Get all distinct sources
        print("\n📥 Fetching all document sources...")
        sources = self.get_general_documents()
        print(f"   Found {len(sources)} distinct sources")
        
        # Classify each source
        print("\n🔍 Classifying sources by keywords...")
        
        inspector_sources = []
        product_sources = []
        general_sources = []
        
        for item in sources:
            source = item['source']
            domain, keyword = classify_source(source)
            
            if domain == 'inspector':
                inspector_sources.append((source, keyword))
                self.stats['keyword_matches'][keyword] += 1
            elif domain == 'product_rep':
                product_sources.append((source, keyword))
                self.stats['keyword_matches'][keyword] += 1
            else:
                general_sources.append(source)
        
        print(f"\n📊 Classification Results:")
        print(f"   → Inspector (Compliance): {len(inspector_sources)} sources")
        print(f"   → Product Rep (Manuals): {len(product_sources)} sources")
        print(f"   → Still General: {len(general_sources)} sources")
        
        # Show sample matches
        print(f"\n📋 Sample Inspector matches:")
        for source, keyword in inspector_sources[:5]:
            print(f"   • [{keyword}] {source[:60]}...")
        
        print(f"\n📋 Sample Product Rep matches:")
        for source, keyword in product_sources[:10]:
            print(f"   • [{keyword}] {source[:60]}...")
        
        # Update database if not dry run
        if not dry_run:
            print(f"\n🔄 Updating database...")
            
            # Update Inspector sources
            print(f"\n   Updating {len(inspector_sources)} Inspector sources...")
            for i, (source, keyword) in enumerate(inspector_sources):
                count = self.update_source_tags(source, 'inspector')
                self.stats['moved_to_inspector'] += count
                if (i + 1) % 50 == 0:
                    print(f"      Progress: {i+1}/{len(inspector_sources)}")
            
            # Update Product Rep sources
            print(f"\n   Updating {len(product_sources)} Product Rep sources...")
            for i, (source, keyword) in enumerate(product_sources):
                count = self.update_source_tags(source, 'product_rep')
                self.stats['moved_to_product_rep'] += count
                if (i + 1) % 50 == 0:
                    print(f"      Progress: {i+1}/{len(product_sources)}")
        
        # Final report
        self._print_report(dry_run, inspector_sources, product_sources, general_sources)
    
    def _print_report(self, dry_run: bool, inspector: List, product: List, general: List):
        """Print final report."""
        print("\n" + "="*70)
        print("📊 RE-TAGGING FINAL REPORT")
        print("="*70)
        
        print(f"\n🏷️ SOURCE CLASSIFICATION")
        print(f"   Total distinct sources: {len(inspector) + len(product) + len(general)}")
        print(f"   → Inspector (Compliance): {len(inspector)} sources")
        print(f"   → Product Rep (Manuals): {len(product)} sources")
        print(f"   → Still General: {len(general)} sources")
        
        if not dry_run:
            print(f"\n📝 DATABASE UPDATES")
            print(f"   Documents moved to Inspector: {self.stats['moved_to_inspector']:,}")
            print(f"   Documents moved to Product Rep: {self.stats['moved_to_product_rep']:,}")
            print(f"   Total documents re-tagged: {self.stats['moved_to_inspector'] + self.stats['moved_to_product_rep']:,}")
            print(f"   Failed updates: {self.stats['failed']}")
        
        print(f"\n🔑 TOP MATCHING KEYWORDS")
        sorted_keywords = sorted(self.stats['keyword_matches'].items(), key=lambda x: x[1], reverse=True)
        for keyword, count in sorted_keywords[:15]:
            print(f"   • '{keyword}': {count} matches")
        
        print(f"\n📋 REMAINING GENERAL SOURCES (Sample)")
        for source in general[:20]:
            print(f"   • {source[:70]}...")
        if len(general) > 20:
            print(f"   ... and {len(general) - 20} more")
        
        if dry_run:
            print(f"\n⚠️ DRY RUN - No changes made. Run with --live to apply.")
        else:
            print(f"\n✅ RE-TAGGING COMPLETE")
        
        print("\n" + "="*70)
    
    def close(self):
        if self.conn:
            self.conn.close()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='STRYDA Re-Tagging Script')
    parser.add_argument('--live', action='store_true', help='Apply changes to database')
    args = parser.parse_args()
    
    processor = ReTagProcessor()
    try:
        processor.process_all(dry_run=not args.live)
    finally:
        processor.close()


if __name__ == '__main__':
    main()
