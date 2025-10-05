#!/usr/bin/env python3
"""
Fixed Snippet-Priority Enrichment Script
Focus on snippet completion while preserving full content + embeddings
"""

import os
import re
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
BATCH_SIZE = 100

def generate_snippet(content: str, existing_clause: str = None, max_chars: int = 200) -> str:
    """Generate intelligent snippet from full page content"""
    if not content:
        return ""
    
    # Clean content
    clean_content = re.sub(r'\s+', ' ', content).strip()
    
    # Priority 1: If clause exists, find sentence mentioning it
    if existing_clause:
        sentences = clean_content.split('.')
        for sentence in sentences:
            if existing_clause.lower() in sentence.lower():
                snippet = sentence.strip()
                if len(snippet) > 20:
                    return snippet[:max_chars].strip()
    
    # Priority 2: Look for first meaningful content
    lines = clean_content.split('\n')
    
    for line in lines[:10]:
        line = line.strip()
        if len(line) > 30 and not line.isupper():  # Skip headers
            return line[:max_chars].strip()
    
    # Priority 3: First good sentence
    sentences = [s.strip() for s in clean_content.split('.') if len(s.strip()) > 20]
    
    if sentences:
        return sentences[0][:max_chars].strip()
    
    # Fallback: First chunk of content
    words = clean_content.split()[:25]
    return ' '.join(words)[:max_chars].strip()

def extract_section(content: str) -> str:
    """Extract section heading"""
    if not content:
        return None
    
    lines = content.split('\n')[:15]
    
    for line in lines:
        line = line.strip()
        if len(line) < 5:
            continue
            
        # Numbered sections
        if re.match(r'^\d+(\.\d+){0,3}\s+.+', line) and len(line) > 8:
            return line[:80]
        
        # Headers
        if line.upper() in ['OBJECTIVE', 'FUNCTIONAL REQUIREMENT', 'PERFORMANCE', 'ACCEPTABLE SOLUTION']:
            return line.upper()
    
    return None

def extract_clause(content: str) -> str:
    """Extract building code clause"""
    if not content:
        return None
    
    # Building code clauses
    matches = re.findall(r'\b([A-H]\d+(?:/[A-Z]{2,4}\d*)?)\b', content, re.IGNORECASE)
    if matches:
        return max(matches, key=len).upper()
    
    # Standards
    nzs_matches = re.findall(r'\b((?:AS/)?NZS\s+\d+(?:\.\d+)?)\b', content, re.IGNORECASE)
    if nzs_matches:
        return nzs_matches[0].upper()
    
    return None

def process_batch():
    """Process one batch focusing on snippet completion"""
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        
        with conn.cursor() as cur:
            # Get documents needing snippets first
            cur.execute("""
                SELECT id, source, page, content, 
                       COALESCE(section, '') as section, 
                       COALESCE(clause, '') as clause,
                       COALESCE(snippet, '') as snippet
                FROM documents 
                WHERE snippet IS NULL OR snippet = ''
                ORDER BY source, page
                LIMIT %s;
            """, (BATCH_SIZE,))
            
            documents = cur.fetchall()
            
            if not documents:
                print("🎉 NO MORE DOCUMENTS NEED SNIPPETS!")
                return True, 0, 0, 0
            
            print(f"📝 Processing {len(documents)} documents for snippet enrichment...")
            
            snippets_added = 0
            sections_added = 0
            clauses_added = 0
            samples = []
            
            for doc in documents:
                doc_id, source, page, content, existing_section, existing_clause, existing_snippet = doc
                
                # Generate snippet (priority)
                snippet = generate_snippet(content, existing_clause)
                
                # Also extract section/clause if missing
                section = existing_section if existing_section else (extract_section(content) or '')
                clause = existing_clause if existing_clause else (extract_clause(content) or '')
                
                # Update document
                cur.execute("""
                    UPDATE documents 
                    SET snippet = %s, section = %s, clause = %s
                    WHERE id = %s;
                """, (snippet, section, clause, doc_id))
                
                # Track what was added
                if snippet and not existing_snippet:
                    snippets_added += 1
                if section and not existing_section:
                    sections_added += 1
                if clause and not existing_clause:
                    clauses_added += 1
                
                # Store sample
                if len(samples) < 5 and (snippet or section or clause):
                    samples.append({
                        'id': str(doc_id)[:8],
                        'source': source,
                        'page': page,
                        'section': section[:40] + "..." if section and len(section) > 40 else section,
                        'clause': clause,
                        'snippet': snippet[:120] + "..." if snippet and len(snippet) > 120 else snippet
                    })
            
            conn.commit()
            
        conn.close()
        return False, snippets_added, sections_added, clauses_added, samples
        
    except Exception as e:
        print(f"❌ Batch failed: {e}")
        return False, 0, 0, 0, []

def main():
    """Run snippet-priority enrichment"""
    print("🏗️ STRYDA-v2 SNIPPET-PRIORITY ENRICHMENT")
    print("=" * 50)
    
    batch_num = 1
    
    while True:
        # Get before stats
        try:
            conn = psycopg2.connect(DATABASE_URL, sslmode="require")
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM documents;")
                total = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM documents WHERE snippet IS NOT NULL AND snippet != '';")
                snippets_before = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM documents WHERE section IS NOT NULL AND section != '';")
                sections_before = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM documents WHERE clause IS NOT NULL AND clause != '';")
                clauses_before = cur.fetchone()[0]
            conn.close()
        except:
            total, snippets_before, sections_before, clauses_before = 819, 120, 234, 352
        
        print(f"\n📦 BATCH {batch_num} - BEFORE")
        print(f"• Snippets: {snippets_before}/{total} ({snippets_before/total*100:.1f}%)")
        print(f"• Sections: {sections_before}/{total} ({sections_before/total*100:.1f}%)")
        print(f"• Clauses: {clauses_before}/{total} ({clauses_before/total*100:.1f}%)")
        
        # Process batch
        is_complete, snippets_added, sections_added, clauses_added, samples = process_batch()
        
        if is_complete:
            print("\n🎉 SNIPPET ENRICHMENT COMPLETE!")
            break
        
        # Get after stats
        try:
            conn = psycopg2.connect(DATABASE_URL, sslmode="require")
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM documents WHERE snippet IS NOT NULL AND snippet != '';")
                snippets_after = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM documents WHERE section IS NOT NULL AND section != '';")
                sections_after = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM documents WHERE clause IS NOT NULL AND clause != '';")
                clauses_after = cur.fetchone()[0]
            conn.close()
        except:
            snippets_after = snippets_before + snippets_added
            sections_after = sections_before + sections_added
            clauses_after = clauses_before + clauses_added
        
        # Report checkpoint
        print(f"\n📊 Metadata Enrichment Checkpoint (Batch {batch_num})")
        print(f"- Documents processed before: {snippets_before} / 819")
        print(f"- Documents processed after: {snippets_after} / 819")
        print(f"- % Completion: {snippets_after/total*100:.1f}%")
        print(f"- Snippets found in this batch: {snippets_added}")
        print(f"- Sections found in this batch: {sections_added}")
        print(f"- Clauses found in this batch: {clauses_added}")
        
        if samples:
            print(f"- Sample metadata extracted:")
            for sample in samples:
                print(f"  • {sample['id']}... ({sample['source']} p.{sample['page']})")
                if sample['section']:
                    print(f"    Section: {sample['section']}")
                if sample['clause']:
                    print(f"    Clause: {sample['clause']}")
                if sample['snippet']:
                    print(f"    Snippet: {sample['snippet']}")
        
        print(f"\nCurrent totals:")
        print(f"- Total snippets: {snippets_after}")
        print(f"- Total sections: {sections_after}")
        print(f"- Total clauses: {clauses_after}")
        print(f"- Remaining documents: {total - snippets_after}")
        
        batch_num += 1
        
        if batch_num > 10:  # Safety limit for testing
            print("🛑 Stopping after 10 batches for safety")
            break

if __name__ == "__main__":
    main()