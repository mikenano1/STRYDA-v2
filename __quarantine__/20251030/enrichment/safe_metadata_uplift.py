#!/usr/bin/env python3
"""
Safe Metadata Uplift with Full Provenance Tracking
Deterministic extraction without guessing - traceable to source
Preserves all full content and embeddings unchanged
"""

import os
import re
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import time
from typing import Optional, Dict, List, Tuple

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
BATCH_SIZE = 150

def extract_clause_deterministic(content: str) -> Optional[str]:
    """
    Extract clauses using deterministic regex patterns only
    No guessing - only exact matches from content
    """
    if not content:
        return None
    
    # Building Code clause patterns (case-sensitive where specified)
    patterns = [
        # Primary NZ Building Code clauses: E2/AS1, B1/VM1, H1/DEFS, etc.
        r'\b([A-H][0-9](?:/[A-Z0-9]+)*(?:\.[0-9]+){0,3})\b',
        
        # Explicit clause/section references
        r'\b(?:Clause|Section)\s+([A-H]?[0-9]+(?:\.[0-9]+){0,3})\b',
        
        # Standards (NZS, AS/NZS, ISO)
        r'\b((?:AS/)?NZS\s+[0-9]+(?:\.[0-9]+)?(?::[0-9]{4})?)\b',
        r'\b(ISO\s+[0-9]+(?:\.[0-9]+)?(?::[0-9]{4})?)\b',
        
        # Material grades (only clear patterns)
        r'\b([GH][0-9]{2,3})\b',  # G550, H36
        r'\b(Z[0-9]{2,3})\b',     # Z275, Z450
    ]
    
    all_matches = []
    
    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            if isinstance(match, str) and len(match) > 1:
                all_matches.append(match.upper())
    
    if all_matches:
        # Return first match in reading order (deterministic)
        return all_matches[0]
    
    return None

def extract_section_on_page(content: str) -> Optional[str]:
    """
    Extract section heading from on-page content only
    Deterministic - no guessing
    """
    if not content:
        return None
    
    lines = content.split('\n')[:int(len(content.split('\n')) * 0.2)]  # Top 20% of page
    
    for line in lines:
        line = line.strip()
        if len(line) < 3 or len(line) > 90:
            continue
        
        # Skip lines ending with sentence punctuation
        if line.endswith(('.', '?', '!')):
            continue
        
        # Pattern 1: Numbered sections (e.g., "4.2.3 Apron flashings")
        if re.match(r'^[0-9]+(?:\.[0-9]+){0,3}\s+[A-Za-z].+', line):
            return line[:80]
        
        # Pattern 2: ALL CAPS headings (filter conservatively)
        if line.isupper() and len(line.split()) > 1:
            # Exclude common document headers
            exclude_patterns = [
                r'.*(?:MINISTRY|DEPARTMENT|HANDBOOK|VERSION|COPYRIGHT).*',
                r'.*(?:PAGE|CHAPTER|PART|DOCUMENT|EDITION).*',
                r'.*[0-9]{4}.*',  # Years
                r'^[A-Z\s]*[0-9]+[A-Z\s]*$',  # Just numbers with letters
            ]
            
            excluded = any(re.match(pattern, line) for pattern in exclude_patterns)
            
            if not excluded and len(line) < 70:
                return line
        
        # Pattern 3: Title Case technical headings
        if (re.match(r'^[A-Z][a-z].*[a-z]$', line) and 
            any(term in line.lower() for term in ['objective', 'performance', 'requirement', 'solution', 'application'])):
            return line
    
    return None

def generate_safe_snippet(content: str, clause: str = None, max_chars: int = 200) -> str:
    """
    Generate snippet focusing on strongest technical content
    Priority: clause context > heading context > dense technical content
    """
    if not content:
        return ""
    
    clean_content = re.sub(r'\s+', ' ', content).strip()
    
    # Priority 1: Content around clause if present
    if clause:
        # Find sentence containing the clause
        sentences = clean_content.split('.')
        for sentence in sentences:
            if clause.lower() in sentence.lower():
                snippet = sentence.strip()
                if 20 <= len(snippet) <= max_chars:
                    return snippet
                elif len(snippet) > max_chars:
                    return snippet[:max_chars-3] + "..."
    
    # Priority 2: Content after clear headings
    lines = clean_content.split('\n')
    for i, line in enumerate(lines[:15]):
        line = line.strip()
        
        # If this looks like a heading, get content after it
        if (re.match(r'^[0-9]+(?:\.[0-9]+){0,3}\s+', line) or
            (line.isupper() and 5 < len(line) < 50)):
            
            # Look for substantive content in next few lines
            for j in range(i+1, min(i+5, len(lines))):
                next_line = lines[j].strip()
                if len(next_line) > 30 and not next_line.isupper():
                    return next_line[:max_chars-3] + "..." if len(next_line) > max_chars else next_line
    
    # Priority 3: Most technical dense paragraph
    paragraphs = [p.strip() for p in clean_content.split('\n\n') if len(p.strip()) > 50]
    
    if paragraphs:
        # Score paragraphs by technical density
        best_para = ""
        best_score = 0
        
        for para in paragraphs[:5]:  # Check first 5 paragraphs
            # Technical terms score
            technical_terms = ['requirement', 'standard', 'specification', 'shall', 'must', 'minimum', 'maximum', 'compliance', 'performance']
            score = sum(1 for term in technical_terms if term in para.lower())
            
            if score > best_score and len(para) >= 50:
                best_score = score
                best_para = para
        
        if best_para:
            return best_para[:max_chars-3] + "..." if len(best_para) > max_chars else best_para
    
    # Fallback: First meaningful sentence
    sentences = [s.strip() for s in clean_content.split('.') if len(s.strip()) > 30]
    if sentences:
        return sentences[0][:max_chars-3] + "..." if len(sentences[0]) > max_chars else sentences[0]
    
    # Last resort: First content chunk
    words = clean_content.split()[:30]
    result = ' '.join(words)
    return result[:max_chars-3] + "..." if len(result) > max_chars else result

def process_safe_batch(batch_num: int) -> Tuple[bool, int, int, int, int, int, List[Dict]]:
    """
    Process one batch with safe, deterministic extraction
    Returns: (is_complete, updated_section_onpage, updated_section_toc, updated_section_bookmark, updated_clause_regex, skipped_no_signal, samples)
    """
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Get documents needing processing (conservative - avoid overwriting good data)
            cur.execute("""
                SELECT id, source, page, content, section, clause, snippet
                FROM documents 
                WHERE (section IS NULL OR section = '') 
                OR (clause IS NULL OR clause = '')
                OR (snippet IS NULL OR snippet = '')
                ORDER BY source, page
                LIMIT %s;
            """, (BATCH_SIZE,))
            
            documents = cur.fetchall()
            
            if not documents:
                return True, 0, 0, 0, 0, 0, []
            
            print(f"📝 Processing {len(documents)} documents with safe extraction...")
            
            # Counters
            updated_section_onpage = 0
            updated_section_toc = 0
            updated_section_bookmark = 0
            updated_clause_regex = 0
            skipped_no_signal = 0
            
            samples = []
            
            for doc in documents:
                doc_id = doc['id']
                source = doc['source']
                page = doc['page']
                content = doc['content']
                existing_section = doc['section']
                existing_clause = doc['clause']
                existing_snippet = doc['snippet']
                
                # Extract using deterministic methods
                new_section = None
                new_clause = None
                new_snippet = None
                section_source = None
                
                # Safe section extraction (on-page only for now)
                if not existing_section:
                    on_page_section = extract_section_on_page(content)
                    if on_page_section:
                        new_section = on_page_section
                        section_source = 'on_page'
                        updated_section_onpage += 1
                
                # Safe clause extraction
                if not existing_clause:
                    extracted_clause = extract_clause_deterministic(content)
                    if extracted_clause:
                        new_clause = extracted_clause
                        updated_clause_regex += 1
                
                # Safe snippet generation
                if not existing_snippet:
                    new_snippet = generate_safe_snippet(content, new_clause or existing_clause)
                
                # Update only if we found something or need to mark as processed
                if new_section or new_clause or new_snippet or (not existing_section and not existing_clause):
                    cur.execute("""
                        UPDATE documents 
                        SET section = COALESCE(%s, section, ''),
                            clause = COALESCE(%s, clause, ''),
                            snippet = COALESCE(%s, snippet, ''),
                            section_source = COALESCE(%s, section_source),
                            updated_at = NOW()
                        WHERE id = %s;
                    """, (new_section, new_clause, new_snippet, section_source, doc_id))
                    
                    # Store sample for reporting
                    if (new_section or new_clause) and len(samples) < 20:
                        samples.append({
                            'id': str(doc_id)[:8],
                            'source': source,
                            'page': page,
                            'section': new_section,
                            'clause': new_clause,
                            'section_source': section_source,
                            'content_preview': content[:160] + "..." if len(content) > 160 else content
                        })
                else:
                    skipped_no_signal += 1
            
            conn.commit()
            
        conn.close()
        return False, updated_section_onpage, updated_section_toc, updated_section_bookmark, updated_clause_regex, skipped_no_signal, samples
        
    except Exception as e:
        print(f"❌ Safe batch processing failed: {e}")
        return False, 0, 0, 0, 0, 0, []

def get_coverage_stats():
    """Get current coverage statistics"""
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM documents;")
            total = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM documents WHERE section IS NOT NULL AND section != '';")
            section_cov = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM documents WHERE clause IS NOT NULL AND clause != '';")
            clause_cov = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM documents WHERE snippet IS NOT NULL AND snippet != '';")
            snippet_cov = cur.fetchone()[0]
            
        conn.close()
        return total, section_cov, clause_cov, snippet_cov
        
    except Exception as e:
        print(f"❌ Stats query failed: {e}")
        return 819, 0, 0, 0

def main():
    """Main safe metadata uplift process"""
    print("🏗️ STRYDA-v2 SAFE METADATA UPLIFT WITH PROVENANCE")
    print("=" * 60)
    print("Approach: Deterministic extraction, no guessing")
    print("Safety: Full content + embeddings preserved")
    print("Provenance: Every label traceable to source")
    
    batch_num = 1
    total_section_onpage = 0
    total_clause_regex = 0
    total_skipped = 0
    
    # Get initial stats
    total, section_before, clause_before, snippet_before = get_coverage_stats()
    
    print(f"\n📊 INITIAL COVERAGE:")
    print(f"• Total documents: {total}")
    print(f"• Section coverage: {section_before}/{total} ({section_before/total*100:.1f}%)")
    print(f"• Clause coverage: {clause_before}/{total} ({clause_before/total*100:.1f}%)")
    print(f"• Snippet coverage: {snippet_before}/{total} ({snippet_before/total*100:.1f}%)")
    
    while True:
        print(f"\n📦 BATCH {batch_num}")
        print("=" * 40)
        
        # Process batch with safe extraction
        is_complete, section_onpage, section_toc, section_bookmark, clause_regex, skipped, samples = process_safe_batch(batch_num)
        
        if is_complete:
            print("🎉 SAFE METADATA UPLIFT COMPLETE!")
            break
        
        # Update totals
        total_section_onpage += section_onpage
        total_clause_regex += clause_regex
        total_skipped += skipped
        
        # Get after stats
        total, section_after, clause_after, snippet_after = get_coverage_stats()
        
        # Report checkpoint
        print(f"\n📊 Safe Metadata Checkpoint (Batch {batch_num})")
        print(f"- Section coverage: {section_before} → {section_after} ({section_after/total*100:.1f}%)")
        print(f"- Clause coverage: {clause_before} → {clause_after} ({clause_after/total*100:.1f}%)")
        print(f"- Snippet coverage: {snippet_before} → {snippet_after} ({snippet_after/total*100:.1f}%)")
        print(f"- Updated section (on-page): {section_onpage}")
        print(f"- Updated clause (regex): {clause_regex}")
        print(f"- Skipped (no signal): {skipped}")
        
        if samples:
            print(f"- Sample extractions (with provenance):")
            for sample in samples[:5]:
                print(f"  • {sample['id']}... ({sample['source']} p.{sample['page']})")
                if sample['section']:
                    print(f"    Section: {sample['section'][:60]}... [source: {sample['section_source']}]")
                if sample['clause']:
                    print(f"    Clause: {sample['clause']} [regex match]")
                print(f"    Content: {sample['content_preview']}")
                print()
        
        # Update before stats for next iteration
        section_before, clause_before, snippet_before = section_after, clause_after, snippet_after
        
        batch_num += 1
        time.sleep(1)
    
    # Final validation and reporting
    print(f"\n🔍 FINAL VALIDATION QUERIES")
    print("=" * 50)
    
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Coverage summary
            print("Coverage summary:")
            cur.execute("""
                SELECT
                  COUNT(*) AS total,
                  COUNT(section) AS section_cov,
                  COUNT(clause)  AS clause_cov,
                  ROUND(100.0*COUNT(section)/COUNT(*),1) AS section_cov_pct,
                  ROUND(100.0*COUNT(clause)/COUNT(*),1)  AS clause_cov_pct
                FROM documents;
            """)
            
            coverage = cur.fetchone()
            print(f"  Total: {coverage['total']}, Section: {coverage['section_cov']} ({coverage['section_cov_pct']}%), Clause: {coverage['clause_cov']} ({coverage['clause_cov_pct']}%)")
            
            # Provenance breakdown
            print(f"\nProvenance breakdown:")
            cur.execute("""
                SELECT section_source, COUNT(*) AS cnt
                FROM documents
                WHERE section IS NOT NULL AND section != ''
                GROUP BY section_source
                ORDER BY cnt DESC;
            """)
            
            provenance = cur.fetchall()
            for p in provenance:
                source_name = p['section_source'] if p['section_source'] else 'unspecified'
                print(f"  {source_name}: {p['cnt']} sections")
            
            # Sample recently updated documents
            print(f"\nRecently updated samples (last hour):")
            cur.execute("""
                SELECT id, source, page, section_source, section, clause, LEFT(content,160) AS preview
                FROM documents
                WHERE updated_at >= NOW() - INTERVAL '1 hour'
                AND (section IS NOT NULL AND section != '' OR clause IS NOT NULL AND clause != '')
                ORDER BY updated_at DESC
                LIMIT 10;
            """)
            
            recent = cur.fetchall()
            for i, doc in enumerate(recent, 1):
                print(f"  {i}. {str(doc['id'])[:8]}... ({doc['source']} p.{doc['page']})")
                if doc['section']:
                    print(f"     Section: {doc['section'][:50]}... [source: {doc['section_source']}]")
                if doc['clause']:
                    print(f"     Clause: {doc['clause']}")
                print(f"     Content: {doc['preview']}...")
                print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Final validation failed: {e}")
    
    print(f"\n📊 SAFE UPLIFT SUMMARY")
    print("=" * 40)
    print(f"• Total on-page sections: {total_section_onpage}")
    print(f"• Total regex clauses: {total_clause_regex}")
    print(f"• Total skipped (no signal): {total_skipped}")
    print("• Provenance: All labels traceable to deterministic extraction")
    print("• Safety: Full content and embeddings preserved")
    
    print(f"\n🎉 SAFE METADATA UPLIFT COMPLETED!")

if __name__ == "__main__":
    main()