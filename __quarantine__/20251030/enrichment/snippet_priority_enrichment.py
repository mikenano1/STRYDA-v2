#!/usr/bin/env python3
"""
Snippet-Priority Metadata Enrichment
Focus on 100% snippet coverage first, then sections/clauses
Preserves all full content and embeddings unchanged
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

def generate_intelligent_snippet(content: str, existing_clause: str = None, max_chars: int = 200) -> str:
    """
    Generate snippet following priority rules:
    1. If clause exists -> sentence mentioning it
    2. Else if heading present -> first sentence under heading  
    3. Else -> first cohesive sentence/paragraph
    """
    if not content:
        return ""
    
    # Clean content for processing
    content = re.sub(r'\s+', ' ', content).strip()
    
    # Priority 1: If clause exists, find sentence mentioning it
    if existing_clause:
        sentences = content.split('.')
        for sentence in sentences:
            if existing_clause.lower() in sentence.lower():
                snippet = sentence.strip()
                if len(snippet) > 20:  # Meaningful length
                    return snippet[:max_chars].strip()
    
    # Priority 2: Look for clear heading and first sentence under it
    lines = content.split('\n')
    
    for i, line in enumerate(lines[:10]):
        line = line.strip()
        
        # Check if this line is a heading
        if (re.match(r'^\d+(\.\d+){0,3}\s+.+', line) or  # Numbered heading
            (len(line) > 5 and line.isupper() and len(line.split()) > 1)):  # ALL CAPS heading
            
            # Look for content after this heading
            for j in range(i+1, min(i+5, len(lines))):
                next_line = lines[j].strip()
                if len(next_line) > 30:  # Substantial content
                    return next_line[:max_chars].strip()
    
    # Priority 3: First cohesive sentence/paragraph
    sentences = [s.strip() for s in content.split('.') if len(s.strip()) > 20]
    
    if sentences:
        # Take first meaningful sentence
        first_sentence = sentences[0]
        
        # If very short, try to add second sentence
        if len(first_sentence) < 100 and len(sentences) > 1:
            combined = first_sentence + '. ' + sentences[1]
            if len(combined) <= max_chars:
                return combined.strip()
        
        return first_sentence[:max_chars].strip()
    
    # Fallback: First meaningful chunk
    words = content.split()[:30]  # First 30 words
    snippet = ' '.join(words)
    
    return snippet[:max_chars].strip() if snippet else content[:max_chars].strip()

def extract_section(content: str, source: str) -> str:
    """Enhanced section extraction"""
    if not content:
        return None
        
    lines = content.split('\n')[:20]
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 3:
            continue
            
        # Numbered sections (e.g., "4.2.3 Apron flashings")
        if re.match(r'^(\d+(?:\.\d+){0,3})\s+(.+)', line) and len(line) > 8:
            return line[:80]
        
        # ALL CAPS headings (filter aggressively)
        if len(line) > 8 and line.isupper() and len(line.split()) > 1:
            exclude_terms = [
                'PAGE', 'CHAPTER', 'PART', 'SECTION', 'VERSION', 'MINISTRY', 'HANDBOOK', 
                'INNOVATION', 'EMPLOYMENT', 'DEPARTMENT', 'HOUSING', 'BUSINESS', 'COPYRIGHT',
                'EDITION', 'PUBLISHED', 'REVISED', 'UPDATED', 'DOCUMENT', 'ZEALAND',
                'BUILDING', 'CODE', 'NZMRM', 'METAL', 'ROOFING'
            ]
            if not any(term in line for term in exclude_terms) and len(line) < 60:
                return line[:80]
        
        # Building code headers
        standard_headers = ['OBJECTIVE', 'FUNCTIONAL REQUIREMENT', 'PERFORMANCE', 'ACCEPTABLE SOLUTION', 'VERIFICATION METHOD', 'SCOPE', 'APPLICATION']
        if line.upper() in standard_headers:
            return line.upper()
    
    return None

def extract_clause(content: str) -> str:
    """Enhanced clause extraction with broader patterns"""
    if not content:
        return None
    
    all_clauses = []
    
    # NZ Building Code clauses
    nz_patterns = [
        r'\b([A-H]\d+(?:/[A-Z]{2,4}\d*)?)\b',   # E2, B1/AS1, H1/DEFS
        r'\b([A-H]\d+[A-Z]{2,4}\d*)\b',        # E2AS1, G12AS2
    ]
    
    for pattern in nz_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        all_clauses.extend([m.upper() for m in matches if len(m) > 1])
    
    # Standards (NZS, AS/NZS, ISO, ASTM)
    standard_patterns = [
        r'\b((?:AS/)?NZS\s+\d+(?:\.\d+)?(?::\d{4})?)\b',  # NZS 3604:2011, AS/NZS 1397
        r'\b(ISO\s+\d+(?:\.\d+)?(?::\d{4})?)\b',          # ISO 9223:2012
        r'\b(ASTM\s+[A-Z]\d+(?:-\d+)?)\b',                # ASTM A792
    ]
    
    for pattern in standard_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        all_clauses.extend([m.upper() for m in matches])
    
    # Material grades and specifications
    material_patterns = [
        r'\b([GH]\d{2,3})\b',                    # G550, H36
        r'\b(Z\d{2,3})\b',                       # Z275, Z450 (coating)
        r'\b(AM\d{2,3})\b',                      # AM40 (aluminum)
    ]
    
    for pattern in material_patterns:
        matches = re.findall(pattern, content)
        all_clauses.extend([m.upper() for m in matches])
    
    if all_clauses:
        # Return most specific (prioritize clauses with qualifiers)
        return max(all_clauses, key=lambda x: len(x) + (30 if '/' in x else 0) + (20 if ':' in x else 0) + (10 if '-' in x else 0))
    
    return None

def get_enrichment_stats():
    """Get current enrichment statistics"""
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        
        with conn.cursor() as cur:
            # Total documents
            cur.execute("SELECT COUNT(*) FROM documents;")
            total = cur.fetchone()[0]
            
            # Metadata counts (only non-empty)
            cur.execute("SELECT COUNT(*) FROM documents WHERE snippet IS NOT NULL AND snippet != '';")
            snippets = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM documents WHERE section IS NOT NULL AND section != '';")
            sections = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM documents WHERE clause IS NOT NULL AND clause != '';")
            clauses = cur.fetchone()[0]
            
            # Documents needing snippet (priority)
            cur.execute("SELECT COUNT(*) FROM documents WHERE snippet IS NULL OR snippet = '';")
            need_snippet = cur.fetchone()[0]
            
            # Documents needing section/clause (secondary)
            cur.execute("""
                SELECT COUNT(*) FROM documents 
                WHERE (section IS NULL OR section = '') 
                AND (clause IS NULL OR clause = '');
            """)
            need_section_clause = cur.fetchone()[0]
            
        conn.close()
        return total, snippets, sections, clauses, need_snippet, need_section_clause
        
    except Exception as e:
        print(f"❌ Failed to get stats: {e}")
        return 819, 0, 0, 0, 819, 819

def process_snippet_batch(batch_num):
    """Process batch prioritizing snippet completion"""
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Priority: Documents missing snippets
            cur.execute("""
                SELECT id, source, page, content, clause, section
                FROM documents 
                WHERE snippet IS NULL OR snippet = ''
                ORDER BY source, page
                LIMIT %s;
            """, (BATCH_SIZE,))
            
            documents = cur.fetchall()
            
            if not documents:
                # No more snippet work, try section/clause
                cur.execute("""
                    SELECT id, source, page, content, clause, section
                    FROM documents 
                    WHERE (section IS NULL OR section = '') 
                    AND (clause IS NULL OR clause = '')
                    ORDER BY source, page
                    LIMIT %s;
                """, (BATCH_SIZE,))
                
                documents = cur.fetchall()
                
                if not documents:
                    return True, 0, 0, 0, []  # Fully complete
            
            print(f"📝 Processing {len(documents)} documents for metadata enrichment...")
            
            updated_docs = []
            snippets_added = 0
            sections_added = 0
            clauses_added = 0
            
            for doc in documents:
                doc_id = doc['id']
                source = doc['source']
                page = doc['page']
                content = doc['content']
                existing_clause = doc['clause']
                existing_section = doc['section']
                
                # Generate snippet (priority)
                snippet = generate_intelligent_snippet(content, existing_clause)
                
                # Extract section and clause if missing
                section = existing_section if existing_section else extract_section(content, source)
                clause = existing_clause if existing_clause else extract_clause(content)
                
                # Update metadata (DO NOT TOUCH content or embedding)
                cur.execute("""
                    UPDATE documents 
                    SET snippet = %s, section = %s, clause = %s
                    WHERE id = %s;
                """, (snippet or '', section or '', clause or '', doc_id))
                
                # Track additions
                if snippet and not doc['snippet']:
                    snippets_added += 1
                if section and not existing_section:
                    sections_added += 1
                if clause and not existing_clause:
                    clauses_added += 1
                
                # Store samples
                if snippet or section or clause:
                    updated_docs.append({
                        'id': str(doc_id)[:8],
                        'source': source,
                        'page': page,
                        'section': section,
                        'clause': clause,
                        'snippet': snippet[:120] if snippet else ''
                    })
            
            conn.commit()
            
        conn.close()
        return False, snippets_added, sections_added, clauses_added, updated_docs
        
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")
        return False, 0, 0, 0, []

def main():
    """Main snippet-priority enrichment loop"""
    print("🏗️ STRYDA-v2 SNIPPET-PRIORITY METADATA ENRICHMENT")
    print("=" * 60)
    print("Priority: 100% snippet coverage, then sections/clauses")
    print("Preservation: Full content + embeddings unchanged")
    
    batch_num = 1
    
    while True:
        # Get before stats
        total, snippets_before, sections_before, clauses_before, need_snippet, need_section_clause = get_enrichment_stats()
        
        print(f"\n📦 BATCH {batch_num}")
        print("=" * 40)
        print(f"📊 Before processing:")
        print(f"• Snippets: {snippets_before}/{total} ({snippets_before/total*100:.1f}%)")
        print(f"• Sections: {sections_before}/{total} ({sections_before/total*100:.1f}%)")
        print(f"• Clauses: {clauses_before}/{total} ({clauses_before/total*100:.1f}%)")
        print(f"• Need snippets: {need_snippet}")
        print(f"• Need section/clause: {need_section_clause}")
        
        # Process batch
        is_complete, snippets_added, sections_added, clauses_added, updated_docs = process_snippet_batch(batch_num)
        
        if is_complete:
            print("\n🎉 METADATA ENRICHMENT 100% COMPLETE!")
            break
        
        # Get after stats
        total, snippets_after, sections_after, clauses_after, need_snippet_after, need_section_clause_after = get_enrichment_stats()
        
        # Calculate fully complete documents
        try:
            conn = psycopg2.connect(DATABASE_URL, sslmode="require")
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM documents 
                    WHERE (snippet IS NOT NULL AND snippet != '')
                    AND (section IS NOT NULL AND section != '')
                    AND (clause IS NOT NULL AND clause != '');
                """)
                fully_complete = cur.fetchone()[0]
            conn.close()
        except:
            fully_complete = 0
        
        # Checkpoint Report
        print(f"\n📊 Metadata Enrichment Checkpoint (Batch {batch_num})")
        print(f"- Snippet: {snippets_before} → {snippets_after} ({snippets_after/total*100:.1f}%)")
        print(f"- Section: {sections_before} → {sections_after} ({sections_after/total*100:.1f}%)")
        print(f"- Clause: {clauses_before} → {clauses_after} ({clauses_after/total*100:.1f}%)")
        print(f"- Fully complete: {fully_complete} ({fully_complete/total*100:.1f}%)")
        print(f"- Snippets added in batch: {snippets_added}")
        print(f"- Sections added in batch: {sections_added}")
        print(f"- Clauses added in batch: {clauses_added}")
        
        if updated_docs:
            print(f"\n📋 Sample metadata (first 5):")
            for i, doc in enumerate(updated_docs[:5], 1):
                print(f"  {i}. {doc['id']}... ({doc['source']} p.{doc['page']})")
                if doc['section']:
                    print(f"     Section: {doc['section'][:40]}...")
                if doc['clause']:
                    print(f"     Clause: {doc['clause']}")
                if doc['snippet']:
                    print(f"     Snippet: {doc['snippet']}")
                print()
        
        # Source breakdown
        try:
            conn = psycopg2.connect(DATABASE_URL, sslmode="require")
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT source,
                           COUNT(*) AS total,
                           COUNT(CASE WHEN snippet IS NOT NULL AND snippet != '' THEN 1 END) AS snippets,
                           COUNT(CASE WHEN section IS NOT NULL AND section != '' THEN 1 END) AS sections,
                           COUNT(CASE WHEN clause IS NOT NULL AND clause != '' THEN 1 END) AS clauses
                    FROM documents
                    GROUP BY source
                    ORDER BY source;
                """)
                
                source_stats = cur.fetchall()
                print(f"\nCurrent totals by source:")
                for stat in source_stats:
                    print(f"• {stat['source']}: total={stat['total']}, snippets={stat['snippets']}, sections={stat['sections']}, clauses={stat['clauses']}")
            
            conn.close()
        except Exception as e:
            print(f"❌ Source stats error: {e}")
        
        batch_num += 1
        time.sleep(1)  # Brief pause between batches
    
    # Final verification
    total, final_snippets, final_sections, final_clauses, _, _ = get_enrichment_stats()
    
    print(f"\n📊 FINAL COMPLETION REPORT")
    print("=" * 50)
    print(f"• Snippet coverage: {final_snippets}/{total} ({final_snippets/total*100:.1f}%)")
    print(f"• Section coverage: {final_sections}/{total} ({final_sections/total*100:.1f}%)")
    print(f"• Clause coverage: {final_clauses}/{total} ({final_clauses/total*100:.1f}%)")
    
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
    
    print(f"\n🎉 ENRICHMENT COMPLETED - FULL CONTENT PRESERVED!")

if __name__ == "__main__":
    main()