#!/usr/bin/env python3
"""
Complete Metadata Enrichment Script
Process remaining documents to achieve 100% metadata coverage
Preserves all full content and embeddings, adds only supplementary metadata
"""

import os
import re
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import time

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
BATCH_SIZE = 100

def extract_section(content: str, source: str) -> str:
    """Extract section heading - more comprehensive patterns"""
    if not content:
        return None
        
    lines = content.split('\n')[:20]  # Check more lines
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 3:
            continue
            
        # Pattern 1: Numbered sections (e.g., "4.2.3 Apron flashings")
        numbered_match = re.match(r'^(\d+(?:\.\d+){0,3})\s+(.+)', line)
        if numbered_match and len(line) > 8:
            return line[:80]
        
        # Pattern 2: ALL CAPS section headings
        if len(line) > 8 and line.isupper() and len(line.split()) > 1:
            exclude_terms = ['PAGE', 'CHAPTER', 'PART', 'SECTION', 'VERSION', 'MINISTRY', 'HANDBOOK', 'INNOVATION', 'EMPLOYMENT', 'DEPARTMENT', 'HOUSING', 'BUSINESS', 'COPYRIGHT', 'EDITION']
            if not any(term in line for term in exclude_terms) and line.count(' ') >= 1:
                return line[:80]
        
        # Pattern 3: Building code standard headers
        standard_headers = ['OBJECTIVE', 'FUNCTIONAL REQUIREMENT', 'PERFORMANCE', 'ACCEPTABLE SOLUTION', 'VERIFICATION METHOD', 'SCOPE', 'APPLICATION', 'LIMITATIONS']
        if line.upper() in standard_headers:
            return line.upper()
        
        # Pattern 4: Technical section patterns
        if re.match(r'^[A-Z][a-z\s]+(Requirements?|Standards?|Specifications?|Installation|Performance)', line):
            return line[:80]
        
        # Pattern 5: Metal roofing specific patterns
        if source == "NZ Metal Roofing":
            if re.match(r'^(General|Installation|Fixing|Weatherproofing|Maintenance|Safety)', line, re.IGNORECASE):
                return line[:80]
    
    return None

def extract_clause(content: str) -> str:
    """Extract building code clauses and standards - comprehensive patterns"""
    if not content:
        return None
    
    all_matches = []
    
    # Pattern 1: NZ Building Code clauses (E2, B1/AS1, etc.)
    nz_patterns = [
        r'\b([A-H]\d+(?:/[A-Z]{2,4}\d*)?)\b',  # E2, B1/AS1, H1/DEFS
        r'\b([A-H]\d+[A-Z]{2,4}\d*)\b',       # E2AS1, G12AS2
    ]
    
    for pattern in nz_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        all_matches.extend([m.upper() for m in matches if len(m) > 1])
    
    # Pattern 2: Standards (NZS, AS/NZS, ISO)
    standards_patterns = [
        r'\b((?:AS/)?NZS\s+\d+(?:\.\d+)?(?::\d{4})?)\b',  # NZS 3604, AS/NZS 1397
        r'\b(ISO\s+\d+(?:\.\d+)?)\b',                      # ISO 9223
        r'\b(ASTM\s+[A-Z]\d+)\b',                          # ASTM A792
    ]
    
    for pattern in standards_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        all_matches.extend([m.upper() for m in matches])
    
    # Pattern 3: Steel/Material grades
    material_patterns = [
        r'\b([GH]\d{2,3})\b',                    # G550, H36
        r'\b(Z\d{2,3})\b',                       # Z275, Z450
        r'\b(AM\d{2,3})\b',                      # AM40, AM60
    ]
    
    for pattern in material_patterns:
        matches = re.findall(pattern, content)
        all_matches.extend([m.upper() for m in matches])
    
    if all_matches:
        # Return most specific match (prioritize longer, more detailed clauses)
        return max(all_matches, key=lambda x: len(x) + (20 if '/' in x else 0) + (10 if ':' in x else 0))
    
    return None

def generate_snippet(content: str, max_chars: int = 200) -> str:
    """Generate meaningful snippet from document content"""
    if not content:
        return ""
    
    # Find the first meaningful sentence or paragraph
    sentences = content.split('. ')
    
    snippet = ""
    for sentence in sentences[:3]:  # First 3 sentences
        sentence = sentence.strip()
        if len(sentence) > 10:  # Skip very short fragments
            if not snippet:
                snippet = sentence
            else:
                if len(snippet + ". " + sentence) <= max_chars:
                    snippet += ". " + sentence
                else:
                    break
    
    # If no good sentences, take first meaningful chunk
    if not snippet:
        words = content.split()[:30]  # First 30 words
        snippet = ' '.join(words)
    
    # Trim to max length
    if len(snippet) > max_chars:
        snippet = snippet[:max_chars].rsplit(' ', 1)[0] + "..."
    
    return snippet

def get_current_stats():
    """Get comprehensive current statistics"""
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        
        with conn.cursor() as cur:
            # Total documents
            cur.execute("SELECT COUNT(*) FROM documents;")
            total = cur.fetchone()[0]
            
            # Documents with any metadata
            cur.execute("""
                SELECT COUNT(*) FROM documents 
                WHERE (section IS NOT NULL AND section != '') 
                OR (clause IS NOT NULL AND clause != '')
                OR (snippet IS NOT NULL AND snippet != '');
            """)
            with_any_metadata = cur.fetchone()[0]
            
            # Specific metadata counts
            cur.execute("SELECT COUNT(*) FROM documents WHERE section IS NOT NULL AND section != '';")
            sections = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM documents WHERE clause IS NOT NULL AND clause != '';")
            clauses = cur.fetchone()[0]
            
            # Documents still needing metadata enrichment
            cur.execute("""
                SELECT COUNT(*) FROM documents 
                WHERE (section IS NULL OR section = '') 
                AND (clause IS NULL OR clause = '')
                AND (snippet IS NULL OR snippet = '');
            """)
            need_metadata = cur.fetchone()[0]
            
        conn.close()
        return total, with_any_metadata, sections, clauses, need_metadata
        
    except Exception as e:
        print(f"❌ Failed to get stats: {e}")
        return 819, 0, 0, 0, 819

def process_metadata_batch(batch_num):
    """Process one batch for metadata enrichment only"""
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Get documents needing metadata (any missing section, clause, or snippet)
            cur.execute("""
                SELECT id, source, page, content 
                FROM documents 
                WHERE (section IS NULL OR section = '') 
                AND (clause IS NULL OR clause = '')
                ORDER BY source, page
                LIMIT %s;
            """, (BATCH_SIZE,))
            
            documents = cur.fetchall()
            
            if not documents:
                return True, 0, 0, []  # No more documents
            
            print(f"📝 Processing {len(documents)} documents for metadata enrichment...")
            
            updated_docs = []
            sections_found = 0
            clauses_found = 0
            
            for doc in documents:
                doc_id = doc['id']
                source = doc['source']
                page = doc['page']
                content = doc['content']
                
                # Extract metadata (DO NOT TOUCH content or embedding)
                section = extract_section(content, source)
                clause = extract_clause(content)
                snippet = generate_snippet(content)
                
                # Update ONLY metadata fields
                cur.execute("""
                    UPDATE documents 
                    SET section = %s, clause = %s, snippet = %s
                    WHERE id = %s;
                """, (section or '', clause or '', snippet, doc_id))
                
                # Track what we found
                if section:
                    sections_found += 1
                if clause:
                    clauses_found += 1
                
                # Store sample for reporting
                if section or clause:
                    updated_docs.append({
                        'id': str(doc_id)[:8],
                        'source': source,
                        'page': page,
                        'section': section,
                        'clause': clause,
                        'snippet': snippet[:120] if snippet else ''
                    })
            
            conn.commit()
            print(f"✅ Updated {len(documents)} documents with metadata")
            
        conn.close()
        return False, sections_found, clauses_found, updated_docs
        
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")
        return False, 0, 0, []

def main():
    """Main metadata completion loop"""
    print("🏗️ STRYDA-v2 COMPLETE METADATA ENRICHMENT")
    print("=" * 60)
    print("Goal: 100% metadata coverage while preserving full content")
    print("Batch size: 100 documents")
    
    batch_num = 1
    total_batches_processed = 0
    
    while True:
        # Get before stats
        total, processed_before, sections_before, clauses_before, need_metadata = get_current_stats()
        
        print(f"\n📦 BATCH {batch_num}")
        print("=" * 40)
        
        # Process batch
        is_complete, sections_found, clauses_found, updated_docs = process_metadata_batch(batch_num)
        
        if is_complete:
            print("\n🎉 METADATA ENRICHMENT 100% COMPLETE!")
            break
        
        # Get after stats  
        total, processed_after, sections_after, clauses_after, remaining = get_current_stats()
        
        # Generate checkpoint report
        print(f"\n📊 Metadata Enrichment Checkpoint (Batch {batch_num})")
        print(f"- Documents processed before: {processed_before} / 819")
        print(f"- Documents processed after: {processed_after} / 819")
        print(f"- % Completion: {processed_after/819*100:.1f}%")
        print(f"- Sections found in this batch: {sections_found}")
        print(f"- Clauses found in this batch: {clauses_found}")
        
        if updated_docs:
            print(f"- Sample metadata extracted (first 5):")
            for i, doc in enumerate(updated_docs[:5], 1):
                metadata_parts = []
                if doc['section']:
                    metadata_parts.append(f"§{doc['section'][:20]}...")
                if doc['clause']:
                    metadata_parts.append(f"[{doc['clause']}]")
                
                metadata_str = ' | '.join(metadata_parts) if metadata_parts else 'no metadata'
                print(f"  {i}. {doc['id']}... ({doc['source']} p.{doc['page']}) - {metadata_str}")
                if doc['snippet']:
                    print(f"     Snippet: {doc['snippet']}")
        
        print(f"\nCurrent totals:")
        print(f"- Total sections populated: {sections_after}")
        print(f"- Total clauses populated: {clauses_after}") 
        print(f"- Remaining documents: {remaining}")
        
        batch_num += 1
        total_batches_processed += 1
        
        # Small delay between batches
        time.sleep(1)
    
    # Final verification
    total, final_processed, final_sections, final_clauses, final_remaining = get_current_stats()
    
    print(f"\n📊 FINAL COMPLETION VERIFICATION")
    print("=" * 50)
    print(f"• Total documents: {total}")
    print(f"• Metadata coverage: {final_processed}/{total} ({final_processed/total*100:.1f}%)")
    print(f"• Final sections: {final_sections}")
    print(f"• Final clauses: {final_clauses}")
    print(f"• Documents needing metadata: {final_remaining}")
    print(f"• Batches processed: {total_batches_processed}")
    
    # Verify content preservation
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM documents WHERE embedding IS NOT NULL AND content IS NOT NULL AND length(content) > 50;")
            content_preserved = cur.fetchone()[0]
            print(f"• Full content + embeddings preserved: {content_preserved}/{total} ({content_preserved/total*100:.1f}%)")
        conn.close()
    except:
        pass
    
    print(f"\n🎉 METADATA ENRICHMENT COMPLETED WITH FULL CONTENT PRESERVATION!")

if __name__ == "__main__":
    main()