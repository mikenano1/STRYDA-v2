#!/usr/bin/env python3
"""
Auto-Loop Metadata Enrichment with 100-Document Batches
Processes all remaining documents until 100% completion
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
    """Extract section heading from document content"""
    lines = content.split('\n')[:15]
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 3:
            continue
            
        # Numbered sections (e.g., "4.2.3 Apron flashings")
        if re.match(r'^\d+(\.\d+){1,3}\s+.+', line):
            return line[:80]
        
        # ALL CAPS headings (filter out common headers)
        if len(line) > 5 and line.isupper() and len(line.split()) > 1:
            exclude_words = ['PAGE', 'CHAPTER', 'PART', 'SECTION', 'VERSION', 'MINISTRY', 'HANDBOOK', 'INNOVATION', 'EMPLOYMENT', 'DEPARTMENT', 'HOUSING', 'BUSINESS']
            if not any(word in line for word in exclude_words):
                return line[:80]
        
        # Building code headers
        if line.upper() in ['OBJECTIVE', 'FUNCTIONAL REQUIREMENT', 'PERFORMANCE', 'ACCEPTABLE SOLUTION', 'VERIFICATION METHOD']:
            return line
    
    return None

def extract_clause(content: str) -> str:
    """Extract clauses with comprehensive patterns"""
    # NZ Building Code clauses (E2, B1/AS1, etc.)
    nz_pattern = r'\b([A-H]\d+(?:/[A-Z]{2,4}\d*)?)\b'
    nz_matches = re.findall(nz_pattern, content, re.IGNORECASE)
    
    if nz_matches:
        return max(nz_matches, key=len).upper()
    
    # NZS/AS Standards
    nzs_pattern = r'\b((?:AS/)?NZS\s+\d+(?:\.\d+)?(?::\d{4})?)\b'
    nzs_matches = re.findall(nzs_pattern, content, re.IGNORECASE)
    
    if nzs_matches:
        return nzs_matches[0].upper()
    
    # Steel grade patterns (G550, H36, etc.)
    steel_pattern = r'\b([GH]\d{2,3})\b'
    steel_matches = re.findall(steel_pattern, content)
    
    if steel_matches:
        return steel_matches[0].upper()
    
    return None

def get_current_stats():
    """Get current processing statistics"""
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM documents;")
            total = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM documents WHERE section IS NOT NULL;")
            sections = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM documents WHERE clause IS NOT NULL;")
            clauses = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM documents WHERE section IS NULL AND clause IS NULL;")
            remaining = cur.fetchone()[0]
            
            processed = total - remaining
            
        conn.close()
        return total, processed, sections, clauses, remaining
        
    except Exception as e:
        print(f"❌ Failed to get stats: {e}")
        return 819, 0, 0, 0, 819

def process_batch(batch_num):
    """Process one batch and return results"""
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        
        # Get before stats
        total, processed_before, sections_before, clauses_before, remaining_before = get_current_stats()
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            print(f"\n📦 BATCH {batch_num}")
            print("=" * 40)
            print(f"📊 Before processing:")
            print(f"• Processed: {processed_before}/{total} ({processed_before/total*100:.1f}%)")
            print(f"• Sections: {sections_before}")
            print(f"• Clauses: {clauses_before}")
            print(f"• Remaining: {remaining_before}")
            
            # Get next batch (unprocessed documents)
            cur.execute("""
                SELECT id, source, page, content 
                FROM documents 
                WHERE section IS NULL AND clause IS NULL
                ORDER BY source, page
                LIMIT %s;
            """, (BATCH_SIZE,))
            
            documents = cur.fetchall()
            
            if not documents:
                print("\n🎉 NO MORE DOCUMENTS TO PROCESS!")
                return True, 0, 0, [], total, total
            
            print(f"\n📝 Processing {len(documents)} documents...")
            
            updated_docs = []
            sections_found = 0
            clauses_found = 0
            
            for doc in documents:
                doc_id = doc['id']
                source = doc['source']
                page = doc['page']
                content = doc['content']
                
                # Extract metadata
                section = extract_section(content, source)
                clause = extract_clause(content)
                
                # Update document (mark as processed even if no metadata found)
                cur.execute("""
                    UPDATE documents 
                    SET section = COALESCE(%s, ''), clause = COALESCE(%s, '')
                    WHERE id = %s;
                """, (section, clause, doc_id))
                
                # Track interesting results
                if section or clause:
                    updated_docs.append({
                        'id': str(doc_id)[:8],
                        'source': source,
                        'page': page,
                        'section': section,
                        'clause': clause
                    })
                
                if section and section != '':
                    sections_found += 1
                if clause and clause != '':
                    clauses_found += 1
            
            conn.commit()
            
        conn.close()
        
        # Get after stats
        total, processed_after, sections_after, clauses_after, remaining_after = get_current_stats()
        
        return False, sections_found, clauses_found, updated_docs, processed_after, remaining_after
        
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")
        return False, 0, 0, [], 0, 819

def main():
    """Auto-loop processing until completion"""
    print("🏗️ STRYDA-v2 AUTO-LOOP METADATA ENRICHMENT")
    print("=" * 60)
    print("Mode: 100-document batches with automatic progression")
    print("Target: 100% completion of all 819 documents")
    
    batch_num = 1
    start_time = time.time()
    
    while True:
        # Process batch
        is_complete, sections_found, clauses_found, updated_docs, processed_after, remaining_after = process_batch(batch_num)
        
        if is_complete:
            print(f"\n🎉 METADATA ENRICHMENT 100% COMPLETE!")
            
            # Final verification
            total, final_processed, final_sections, final_clauses, final_remaining = get_current_stats()
            
            print(f"\n📊 FINAL COMPLETION REPORT")
            print("=" * 40)
            print(f"• Total documents processed: {final_processed}/{total}")
            print(f"• Final section coverage: {final_sections} documents")
            print(f"• Final clause coverage: {final_clauses} documents")
            print(f"• Processing completion: 100%")
            
            elapsed = time.time() - start_time
            print(f"• Total processing time: {elapsed/60:.1f} minutes")
            print(f"• Batches processed: {batch_num-1}")
            break
        
        # Report checkpoint
        total, _, _, _, _ = get_current_stats()
        
        print(f"\n📊 Metadata Enrichment Checkpoint (Batch {batch_num})")
        print(f"- Documents processed before: {processed_after - len([d for d in updated_docs])} / {total}")
        print(f"- Documents processed after: {processed_after} / {total}")
        print(f"- % Completion: {processed_after/total*100:.1f}%")
        print(f"- Sections found in this batch: {sections_found}")
        print(f"- Clauses found in this batch: {clauses_found}")
        
        if updated_docs:
            print(f"- Sample metadata extracted:")
            for doc in updated_docs[:5]:  # Show first 5
                metadata_parts = []
                if doc['section'] and doc['section'] != '':
                    metadata_parts.append(f"§{doc['section'][:25]}...")
                if doc['clause'] and doc['clause'] != '':
                    metadata_parts.append(f"[{doc['clause']}]")
                
                if metadata_parts:
                    print(f"  • {' | '.join(metadata_parts)} ({doc['source']} p.{doc['page']})")
        
        # Current totals
        _, _, sections_total, clauses_total, remaining = get_current_stats()
        print(f"\nCurrent Status:")
        print(f"- Total sections populated: {sections_total}")
        print(f"- Total clauses populated: {clauses_total}")
        print(f"- Remaining documents: {remaining}")
        
        batch_num += 1
        
        # Small delay between batches
        time.sleep(2)

if __name__ == "__main__":
    main()