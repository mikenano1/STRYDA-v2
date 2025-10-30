#!/usr/bin/env python3
"""
Interactive Monitored Batch Processing for Metadata Enrichment
Process documents in controlled batches with progress reporting
"""

import os
import re
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import time

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
BATCH_SIZE = 50

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
        
        # ALL CAPS headings (filter out headers)
        if len(line) > 5 and line.isupper() and len(line.split()) > 1:
            exclude_words = ['PAGE', 'CHAPTER', 'PART', 'SECTION', 'VERSION', 'MINISTRY', 'HANDBOOK', 'INNOVATION', 'EMPLOYMENT']
            if not any(word in line for word in exclude_words):
                return line[:80]
        
        # Building code specific headers
        standard_headers = ['OBJECTIVE', 'FUNCTIONAL REQUIREMENT', 'PERFORMANCE', 'ACCEPTABLE SOLUTION', 'VERIFICATION METHOD']
        if line.upper() in standard_headers:
            return line
    
    return None

def extract_clause(content: str) -> str:
    """Extract NZ building code clauses"""
    # Building code patterns: E2, B1/AS1, etc.
    nz_code_pattern = r'\b([A-H]\d+(?:/[A-Z]{2,4}\d*)?)\b'
    matches = re.findall(nz_code_pattern, content, re.IGNORECASE)
    
    if matches:
        # Return most specific (longest) match
        return max(matches, key=len).upper()
    
    # NZS Standards patterns
    nzs_pattern = r'\b((?:AS/)?NZS\s+\d+(?:\.\d+)?)\b'
    nzs_matches = re.findall(nzs_pattern, content, re.IGNORECASE)
    
    if nzs_matches:
        return nzs_matches[0].upper()
    
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
            
            cur.execute("SELECT COUNT(*) FROM documents WHERE section IS NULL;")
            remaining = cur.fetchone()[0]
            
            processed = total - remaining
            
        conn.close()
        return total, processed, sections, clauses, remaining
        
    except Exception as e:
        print(f"❌ Failed to get stats: {e}")
        return 819, 0, 0, 0, 819

def process_single_batch():
    """Process exactly one batch of 50 documents"""
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Get next batch of documents
            cur.execute("""
                SELECT id, source, page, content 
                FROM documents 
                WHERE section IS NULL 
                ORDER BY source, page
                LIMIT %s;
            """, (BATCH_SIZE,))
            
            documents = cur.fetchall()
            
            if not documents:
                return [], 0, 0, True  # No more documents
            
            print(f"📝 Processing batch of {len(documents)} documents...")
            
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
                
                # Update document
                cur.execute("""
                    UPDATE documents 
                    SET section = %s, clause = %s
                    WHERE id = %s;
                """, (section, clause, doc_id))
                
                # Track what was updated
                updated_docs.append({
                    'id': str(doc_id),
                    'source': source,
                    'page': page,
                    'section': section,
                    'clause': clause
                })
                
                if section:
                    sections_found += 1
                if clause:
                    clauses_found += 1
            
            conn.commit()
            
        conn.close()
        return updated_docs, sections_found, clauses_found, False
        
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")
        return [], 0, 0, False

def main():
    """Interactive batch processing main function"""
    print("🏗️ STRYDA-v2 INTERACTIVE METADATA ENRICHMENT")
    print("=" * 60)
    print("Mode: Monitored batch processing (50 docs per batch)")
    print("Control: Manual progression after each batch")
    
    batch_num = 1
    
    while True:
        print(f"\n" + "=" * 50)
        print(f"📦 BATCH {batch_num}")
        print("=" * 50)
        
        # Get current status before processing
        total, processed_before, sections_before, clauses_before, remaining_before = get_current_stats()
        
        print(f"📊 Before batch:")
        print(f"• Processed: {processed_before}/{total} ({processed_before/total*100:.1f}%)")
        print(f"• Sections: {sections_before}")
        print(f"• Clauses: {clauses_before}")
        print(f"• Remaining: {remaining_before}")
        
        # Process one batch
        updated_docs, sections_found, clauses_found, is_complete = process_single_batch()
        
        if is_complete:
            print("\n🎉 METADATA ENRICHMENT 100% COMPLETE!")
            
            # Final stats
            total, processed_final, sections_final, clauses_final, remaining_final = get_current_stats()
            print(f"\n📊 FINAL RESULTS:")
            print(f"• Total documents: {total}")
            print(f"• Documents with sections: {sections_final} ({sections_final/total*100:.1f}%)")
            print(f"• Documents with clauses: {clauses_final} ({clauses_final/total*100:.1f}%)")
            print(f"• Processing: 100% complete")
            break
        
        # Get updated status after processing
        total, processed_after, sections_after, clauses_after, remaining_after = get_current_stats()
        
        print(f"\n✅ Batch {batch_num} complete:")
        print(f"• Processed: {len(updated_docs)} documents")
        print(f"• Found {sections_found} sections, {clauses_found} clauses")
        print(f"• Progress: {processed_after}/{total} ({processed_after/total*100:.1f}%)")
        print(f"• Section coverage: {sections_after} documents ({sections_after/total*100:.1f}%)")
        print(f"• Clause coverage: {clauses_after} documents ({clauses_after/total*100:.1f}%)")
        print(f"• Remaining: {remaining_after}")
        
        # Show sample of processed doc IDs
        print(f"\n📋 Last batch doc_ids (first 5):")
        for i, doc in enumerate(updated_docs[:5]):
            metadata_info = []
            if doc['section']:
                metadata_info.append(f"§{doc['section'][:30]}...")
            if doc['clause']:
                metadata_info.append(f"[{doc['clause']}]")
            
            metadata_str = ' | '.join(metadata_info) if metadata_info else 'no metadata'
            print(f"  {i+1}. {doc['id'][:8]}... ({doc['source']} p.{doc['page']}) - {metadata_str}")
        
        print(f"\n⏳ Ready for next batch. Waiting for instruction...")
        
        # Wait for user input
        user_input = input("Continue? (y/n/s=status): ").strip().lower()
        
        if user_input == 'n':
            print("🛑 Stopping enrichment by user request")
            break
        elif user_input == 's':
            # Show current status
            continue
        else:
            # Continue to next batch
            batch_num += 1
            continue

if __name__ == "__main__":
    main()