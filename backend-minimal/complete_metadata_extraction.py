#!/usr/bin/env python3
"""
Complete Metadata Extraction Script
Processes ALL remaining documents to achieve 100% metadata coverage
Enhanced with better pattern recognition and progress tracking
"""

import os
import re
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import time
import signal
import sys

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
BATCH_SIZE = 100  # Larger batches for efficiency
processed_count = 0

def signal_handler(signum, frame):
    """Handle interrupt signals gracefully"""
    print(f"\n🛑 Received interrupt signal. Processed {processed_count} documents so far.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def extract_section(content: str, source: str) -> str:
    """
    Extract section heading from document content
    Enhanced with source-specific patterns
    """
    lines = content.split('\n')[:15]  # Check more lines for headings
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 3:
            continue
            
        # Pattern 1: Numbered sections (e.g., "4.2.3 Apron flashings", "10.5 Building Airtightness")
        numbered_match = re.match(r'^(\d+(?:\.\d+){1,3})\s+(.+)', line)
        if numbered_match:
            return line[:80]  # Return full heading
        
        # Pattern 2: ALL CAPS headings (common in building codes)
        if len(line) > 5 and line.isupper() and not re.match(r'^[A-Z\s]*\d+[A-Z\s]*$', line):
            # Filter out page headers and numbers-only lines
            if not any(word in line for word in ['PAGE', 'CHAPTER', 'PART', 'SECTION']) and len(line.split()) > 1:
                return line[:80]
        
        # Pattern 3: Building code specific headers (e.g., "OBJECTIVE", "FUNCTIONAL REQUIREMENT")
        if source == "NZ Building Code" and line.upper() in ['OBJECTIVE', 'FUNCTIONAL REQUIREMENT', 'PERFORMANCE', 'ACCEPTABLE SOLUTION', 'VERIFICATION METHOD']:
            return line
        
        # Pattern 4: Metal roofing specific sections
        if source == "NZ Metal Roofing":
            # Look for typical NZMRM section patterns
            if re.match(r'^\d+(\.\d+)?\s+(General|Installation|Fixing|Weatherproofing|Maintenance)', line, re.IGNORECASE):
                return line[:80]
        
        # Pattern 5: Title Case headings with building/roofing terms
        building_terms = ['flashing', 'roofing', 'installation', 'requirements', 'standards', 'fastener', 'membrane', 'weatherproofing', 'ventilation']
        if any(term in line.lower() for term in building_terms) and len(line) > 10:
            if line[0].isupper() and not line.isupper():  # Title case
                return line[:80]
    
    return None

def extract_clause(content: str, source: str) -> str:
    """
    Extract NZ building code clauses from document content
    Enhanced with better pattern matching
    """
    # NZ Building Code clause patterns with variations
    patterns = [
        # Standard clauses: E2, B1, G12, H1, etc.
        r'\b([A-H]\d+)(?:/([A-Z]{2}\d*))?\b',
        # AS/NZS patterns: AS/NZS 1562.1, NZS 3604
        r'\b((?:AS/)?NZS\s+\d+(?:\.\d+)?(?::\d{4})?)\b',
        # NZMRM section patterns: specific numbered sections
        r'\b(NZMRM\s+\d+(?:\.\d+){1,3})\b'
    ]
    
    all_matches = []
    
    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                # Handle groups from regex
                clause = ''.join(filter(None, match))
            else:
                clause = match
            
            if clause and len(clause) > 1:
                all_matches.append(clause.upper())
    
    if not all_matches:
        # Look for standalone building code references
        simple_matches = re.findall(r'\b[A-H]\d+\b', content)
        all_matches.extend([m.upper() for m in simple_matches])
    
    if all_matches:
        # Return the most specific match (prioritize longer clauses)
        return max(all_matches, key=lambda x: len(x) + (10 if '/' in x else 0))
    
    return None

def process_documents_comprehensive(batch_size: int = BATCH_SIZE) -> int:
    """
    Process ALL remaining documents to extract metadata
    Returns number of documents updated in this batch
    """
    global processed_count
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL not configured")
        return 0
    
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require", connect_timeout=30)
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Get documents that still need processing
            cur.execute("""
                SELECT id, source, page, content 
                FROM documents 
                WHERE section IS NULL 
                ORDER BY source, page
                LIMIT %s;
            """, (batch_size,))
            
            documents = cur.fetchall()
            
            if not documents:
                return 0
            
            print(f"📝 Processing batch of {len(documents)} documents...")
            
            updated_count = 0
            sections_found = 0
            clauses_found = 0
            
            for doc in documents:
                doc_id = doc['id']
                source = doc['source']
                page = doc['page']
                content = doc['content']
                
                # Extract metadata with enhanced patterns
                section = extract_section(content, source)
                clause = extract_clause(content, source)
                
                # Update document with metadata
                cur.execute("""
                    UPDATE documents 
                    SET section = %s, clause = %s
                    WHERE id = %s;
                """, (section, clause, doc_id))
                
                updated_count += 1
                processed_count += 1
                
                # Track what we found
                if section:
                    sections_found += 1
                if clause:
                    clauses_found += 1
                
                # Log interesting findings
                if section or clause:
                    metadata_parts = []
                    if section:
                        metadata_parts.append(f"section: {section[:40]}...")
                    if clause:
                        metadata_parts.append(f"clause: {clause}")
                    
                    print(f"  ✅ {source} p.{page}: {', '.join(metadata_parts)}")
            
            conn.commit()
            
            print(f"📊 Batch complete: {updated_count} docs processed, {sections_found} sections, {clauses_found} clauses found")
            
        conn.close()
        return updated_count
        
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")
        return 0

def main():
    """Main comprehensive metadata extraction pipeline"""
    print("🏗️ STRYDA-v2 COMPLETE METADATA ENRICHMENT")
    print("=" * 60)
    print("Target: 100% coverage of all 819 documents")
    print("Enhanced patterns for NZ Building Code and Metal Roofing")
    
    batch_num = 1
    total_updated = 0
    start_time = time.time()
    
    while True:
        print(f"\n📦 Processing batch {batch_num}...")
        
        batch_updated = process_documents_comprehensive()
        total_updated += batch_updated
        
        if batch_updated == 0:
            print("✅ All documents processed!")
            break
        
        # Progress reporting
        elapsed = time.time() - start_time
        rate = total_updated / elapsed if elapsed > 0 else 0
        
        print(f"📈 Overall progress: {total_updated} documents processed in {elapsed/60:.1f}min (rate: {rate:.1f} docs/sec)")
        
        batch_num += 1
        
        # Small delay between batches for system stability
        time.sleep(0.2)
    
    # Final comprehensive verification
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            print(f"\n📊 FINAL METADATA ENRICHMENT RESULTS")
            print("=" * 60)
            
            # Final counts
            cur.execute("SELECT COUNT(*) FROM documents;")
            total_docs = cur.fetchone()['count']
            
            cur.execute("SELECT COUNT(*) FROM documents WHERE section IS NOT NULL;")
            final_section_count = cur.fetchone()['count']
            
            cur.execute("SELECT COUNT(*) FROM documents WHERE clause IS NOT NULL;")
            final_clause_count = cur.fetchone()['count']
            
            print(f"📋 Final Coverage Results:")
            print(f"• Total documents: {total_docs}")
            print(f"• Documents with sections: {final_section_count} ({final_section_count/total_docs*100:.1f}%)")
            print(f"• Documents with clauses: {final_clause_count} ({final_clause_count/total_docs*100:.1f}%)")
            
            # Sample of enriched metadata by source
            cur.execute("""
                SELECT source, COUNT(*) as total,
                       COUNT(section) as with_sections,
                       COUNT(clause) as with_clauses
                FROM documents 
                GROUP BY source 
                ORDER BY source;
            """)
            
            source_stats = cur.fetchall()
            print(f"\n📊 Coverage by source:")
            for stat in source_stats:
                total = stat['total']
                sections = stat['with_sections'] 
                clauses = stat['with_clauses']
                print(f"• {stat['source']}: sections {sections}/{total} ({sections/total*100:.0f}%), clauses {clauses}/{total} ({clauses/total*100:.0f}%)")
            
            # Show examples of enriched citations
            cur.execute("""
                SELECT source, page, section, clause, substring(content, 1, 100) as preview
                FROM documents 
                WHERE (section IS NOT NULL OR clause IS NOT NULL)
                ORDER BY 
                    CASE source 
                        WHEN 'NZ Building Code' THEN 1
                        WHEN 'NZ Metal Roofing' THEN 2
                        ELSE 3
                    END, page
                LIMIT 8;
            """)
            
            examples = cur.fetchall()
            print(f"\n📋 Sample enriched metadata:")
            for example in examples:
                metadata_info = []
                if example['section']:
                    metadata_info.append(f"§{example['section'][:30]}")
                if example['clause']:
                    metadata_info.append(f"[{example['clause']}]")
                
                if metadata_info:
                    print(f"• {example['source']} p.{example['page']}: {' '.join(metadata_info)}")
                    print(f"  Content: {example['preview']}...")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Final verification failed: {e}")
    
    print(f"\n🎉 METADATA ENRICHMENT COMPLETED!")
    print(f"Total documents processed: {total_updated}")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)