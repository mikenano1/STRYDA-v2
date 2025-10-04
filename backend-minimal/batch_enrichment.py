#!/usr/bin/env python3
"""
Manual Batch Processing for Metadata Enrichment
Process one batch and show detailed results
"""

import os
import re
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

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
            
        # Numbered sections
        if re.match(r'^\d+(\.\d+){1,3}\s+.+', line):
            return line[:80]
        
        # ALL CAPS headings (filter out common headers)
        if len(line) > 5 and line.isupper() and len(line.split()) > 1:
            exclude_words = ['PAGE', 'CHAPTER', 'PART', 'SECTION', 'VERSION', 'MINISTRY', 'HANDBOOK', 'INNOVATION', 'EMPLOYMENT', 'DEPARTMENT', 'HOUSING']
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
    
    return None

def process_batch():
    """Process one batch and return detailed results"""
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Get current overall stats
            cur.execute("SELECT COUNT(*) FROM documents;")
            total = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM documents WHERE section IS NOT NULL;")
            sections_before = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM documents WHERE clause IS NOT NULL;")
            clauses_before = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM documents WHERE section IS NULL;")
            remaining = cur.fetchone()[0]
            
            print(f"📊 BATCH PROCESSING REPORT")
            print("=" * 40)
            print(f"Before batch: {sections_before}/{total} processed ({sections_before/total*100:.1f}%)")
            print(f"Sections: {sections_before}, Clauses: {clauses_before}")
            print(f"Remaining: {remaining}")
            
            if remaining == 0:
                print("\n🎉 NO DOCUMENTS REMAINING - 100% COMPLETE!")
                return True
            
            # Get next batch (documents that haven't been processed yet)
            cur.execute("""
                SELECT id, source, page, content 
                FROM documents 
                WHERE section IS NULL AND clause IS NULL
                ORDER BY source, page
                LIMIT %s;
            """, (BATCH_SIZE,))
            
            documents = cur.fetchall()
            
            if not documents:
                print("🎉 NO MORE DOCUMENTS TO PROCESS!")
                return True
            
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
                
                # Update document
                cur.execute("""
                    UPDATE documents 
                    SET section = %s, clause = %s
                    WHERE id = %s;
                """, (section, clause, doc_id))
                
                # Track results
                if section or clause:
                    updated_docs.append({
                        'id': str(doc_id)[:8],
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
            
            # Get updated stats
            cur.execute("SELECT COUNT(*) FROM documents WHERE section IS NOT NULL;")
            sections_after = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM documents WHERE clause IS NOT NULL;")
            clauses_after = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM documents WHERE section IS NULL;")
            remaining_after = cur.fetchone()[0]
            
            print(f"\n✅ BATCH COMPLETE:")
            print(f"• Processed: {len(documents)} documents")
            print(f"• Found: {sections_found} sections, {clauses_found} clauses")
            print(f"• Progress: {sections_after}/{total} ({sections_after/total*100:.1f}%)")
            print(f"• Section coverage: {sections_after} documents")
            print(f"• Clause coverage: {clauses_after} documents") 
            print(f"• Remaining: {remaining_after}")
            
            print(f"\n📋 Last batch doc_ids with metadata:")
            for doc in updated_docs:
                metadata_parts = []
                if doc['section']:
                    metadata_parts.append(f"§{doc['section'][:25]}...")
                if doc['clause']:
                    metadata_parts.append(f"[{doc['clause']}]")
                
                metadata_str = ' | '.join(metadata_parts) if metadata_parts else 'no metadata found'
                print(f"  • {doc['id']}... ({doc['source']} p.{doc['page']}) - {metadata_str}")
            
        conn.close()
        return False
        
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")
        return False

if __name__ == "__main__":
    completed = process_batch()
    if completed:
        print("\n🎉 METADATA ENRICHMENT COMPLETED!")
    else:
        print("\n⏳ Batch completed. Run script again to continue with next batch.")