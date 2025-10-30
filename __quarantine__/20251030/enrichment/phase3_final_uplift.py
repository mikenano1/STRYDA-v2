#!/usr/bin/env python3
"""
Phase 3 - Final Metadata Uplift with Exact Deterministic Patterns
Target: ≥90% section, ≥70% clause coverage
Safety: Full content + embeddings preserved, provenance required
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

def extract_clause_deterministic(content: str) -> tuple:
    """
    Extract clauses using exact regex patterns with provenance IDs
    Returns: (clause, provenance_id)
    """
    if not content:
        return None, None
    
    # Exact patterns as specified
    patterns = [
        (r'\bNZBC\s+Clause\s+([A-Z0-9]+)', 'P1'),
        (r'\bAS\/NZS\s*(\d{3,4}(?:\.\d+)?(?::\d{4})?)', 'P2'),
        (r'\bNZS\s*(\d{3,4}(?::\d{4})?)', 'P3'),
        (r'\b([A-H][0-9]{1,2}(?:\/(AS|VM)[0-9]{1,2})?)', 'P4'),
        (r'\b((?:AS|NZS|AS\/NZS)\s*[0-9]{3,5}(?:\.[0-9]+)?)', 'P5'),
    ]
    
    for pattern, pattern_id in patterns:
        matches = re.findall(pattern, content)
        if matches:
            # Return first match with exact provenance
            if isinstance(matches[0], tuple):
                clause = matches[0][0].upper()
            else:
                clause = matches[0].upper()
            return clause, f'regex:{pattern_id}'
    
    return None, None

def extract_section_deterministic(content: str) -> tuple:
    """
    Extract section headings using exact patterns with provenance
    Returns: (section, provenance_id)
    """
    if not content:
        return None, None
    
    lines = content.split('\n')[:20]  # Top 20% of page
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 3:
            continue
        
        # H1: Standard headings
        if re.match(r'^(Scope|Purpose|Application|Requirements|Definitions|References)$', line):
            return line, 'on_page'
        
        # H2: Standalone heading line
        if re.match(r'^[A-Z][A-Za-z0-9\s\-]{3,60}$', line):
            # Filter out document headers
            exclude_terms = ['MINISTRY', 'DEPARTMENT', 'HANDBOOK', 'VERSION', 'COPYRIGHT', 'ZEALAND', 'BUILDING', 'CODE', 'NZMRM', 'METAL', 'ROOFING', 'INNOVATION', 'EMPLOYMENT']
            if not any(term in line.upper() for term in exclude_terms):
                return line, 'on_page'
        
        # H3: Line with heading hints
        if re.search(r'\b(Requirements|Scope|Definitions|Performance|Objective|Maintenance|Materials|Fixings)\b', line):
            # Must be a clean heading-like line
            if len(line) < 80 and not line.endswith('.') and not re.search(r'\d{4}', line):
                return line, 'on_page'
    
    return None, None

def generate_contextual_snippet(content: str, section: str = None, clause: str = None, max_chars: int = 180) -> str:
    """Generate snippet around best match within 200 chars"""
    if not content:
        return ""
    
    clean_content = re.sub(r'\s+', ' ', content).strip()
    
    # Priority 1: Context around clause
    if clause:
        sentences = clean_content.split('.')
        for sentence in sentences:
            if clause.lower() in sentence.lower():
                snippet = sentence.strip()
                if 20 <= len(snippet) <= max_chars:
                    return snippet
    
    # Priority 2: Context around section
    if section:
        section_words = section.lower().split()[:3]  # First 3 words of section
        for word in section_words:
            if word in clean_content.lower():
                # Find surrounding context
                pos = clean_content.lower().find(word)
                start = max(0, pos - 50)
                end = min(len(clean_content), pos + max_chars - 50)
                snippet = clean_content[start:end].strip()
                if len(snippet) > 20:
                    return snippet[:max_chars]
    
    # Priority 3: First technical paragraph
    paragraphs = [p.strip() for p in clean_content.split('\n') if len(p.strip()) > 30]
    if paragraphs:
        return paragraphs[0][:max_chars]
    
    # Fallback: First content
    return clean_content[:max_chars]

def process_phase3_batch(batch_num: int):
    """Process batch with exact deterministic patterns"""
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Prioritize NZ Metal Roofing docs missing metadata
            cur.execute("""
                SELECT id, source, page, content, section, clause, snippet
                FROM documents 
                WHERE (section IS NULL OR clause IS NULL)
                ORDER BY 
                    CASE source WHEN 'NZ Metal Roofing' THEN 1 ELSE 2 END,
                    source, page
                LIMIT %s;
            """, (BATCH_SIZE,))
            
            documents = cur.fetchall()
            
            if not documents:
                return True, 0, 0, 0, []
            
            print(f"📝 Processing {len(documents)} documents with exact deterministic patterns...")
            
            sections_added = 0
            clauses_added = 0
            snippets_updated = 0
            samples = []
            
            for doc in documents:
                doc_id = doc['id']
                source = doc['source']
                page = doc['page']
                content = doc['content']
                existing_section = doc['section']
                existing_clause = doc['clause']
                existing_snippet = doc['snippet']
                
                # Extract only if missing
                new_section, section_prov = None, None
                new_clause, clause_prov = None, None
                new_snippet = None
                
                if not existing_section:
                    new_section, section_prov = extract_section_deterministic(content)
                    if new_section:
                        sections_added += 1
                
                if not existing_clause:
                    new_clause, clause_prov = extract_clause_deterministic(content)
                    if new_clause:
                        clauses_added += 1
                
                if not existing_snippet or existing_snippet == '':
                    new_snippet = generate_contextual_snippet(content, new_section or existing_section, new_clause or existing_clause)
                    if new_snippet:
                        snippets_updated += 1
                
                # Update only if we found new metadata
                if new_section or new_clause or new_snippet:
                    update_values = {}
                    if new_section:
                        update_values['section'] = new_section
                        update_values['section_source'] = section_prov
                    if new_clause:
                        update_values['clause'] = new_clause
                        update_values['clause_source'] = clause_prov
                    if new_snippet:
                        update_values['snippet'] = new_snippet
                    
                    # Build dynamic update query
                    set_parts = []
                    values = []
                    
                    if 'section' in update_values:
                        set_parts.append('section = %s')
                        values.append(update_values['section'])
                    if 'section_source' in update_values:
                        set_parts.append('section_source = %s')
                        values.append(update_values['section_source'])
                    if 'clause' in update_values:
                        set_parts.append('clause = %s')
                        values.append(update_values['clause'])
                    if 'clause_source' in update_values:
                        set_parts.append('clause_source = %s')
                        values.append(update_values['clause_source'])
                    if 'snippet' in update_values:
                        set_parts.append('snippet = %s')
                        values.append(update_values['snippet'])
                    
                    set_parts.append('updated_at = NOW()')
                    values.append(doc_id)
                    
                    sql = f"UPDATE documents SET {', '.join(set_parts)} WHERE id = %s;"
                    cur.execute(sql, values)
                    
                    # Store sample
                    if len(samples) < 10 and (new_section or new_clause):
                        samples.append({
                            'id': str(doc_id)[:8],
                            'source': source,
                            'page': page,
                            'section': new_section,
                            'section_source': section_prov,
                            'clause': new_clause,
                            'clause_source': clause_prov,
                            'snippet': new_snippet[:120] + "..." if new_snippet and len(new_snippet) > 120 else new_snippet
                        })
            
            conn.commit()
            
        conn.close()
        return False, sections_added, clauses_added, snippets_updated, samples
        
    except Exception as e:
        print(f"❌ Phase 3 batch failed: {e}")
        return False, 0, 0, 0, []

def run_verification_queries():
    """Run all requested verification SQL queries"""
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            results = {}
            
            # Query 1: Overall coverage
            cur.execute("""
                SELECT COUNT(*) AS total,
                       COUNT(section) AS section_cov,
                       COUNT(clause)  AS clause_cov,
                       ROUND(100.0*COUNT(section)/COUNT(*),1) AS section_cov_pct,
                       ROUND(100.0*COUNT(clause)/COUNT(*),1)  AS clause_cov_pct
                FROM documents;
            """)
            results['overall'] = cur.fetchone()
            
            # Query 2: Coverage by source
            cur.execute("""
                SELECT source,
                       COUNT(*) AS total,
                       SUM(CASE WHEN section IS NOT NULL THEN 1 ELSE 0 END) AS section_docs,
                       ROUND(100.0*SUM(CASE WHEN section IS NOT NULL THEN 1 ELSE 0 END)/COUNT(*),1) AS section_pct,
                       SUM(CASE WHEN clause IS NOT NULL THEN 1 ELSE 0 END)  AS clause_docs,
                       ROUND(100.0*SUM(CASE WHEN clause IS NOT NULL THEN 1 ELSE 0 END)/COUNT(*),1)  AS clause_pct
                FROM documents
                GROUP BY source
                ORDER BY source;
            """)
            results['by_source'] = cur.fetchall()
            
            # Query 3: Section provenance
            cur.execute("""
                SELECT section_source, COUNT(*) AS cnt
                FROM documents
                WHERE section IS NOT NULL
                GROUP BY section_source
                ORDER BY cnt DESC;
            """)
            results['section_provenance'] = cur.fetchall()
            
            # Query 4: Clause provenance
            cur.execute("""
                SELECT clause_source, COUNT(*) AS cnt
                FROM documents
                WHERE clause IS NOT NULL
                GROUP BY clause_source
                ORDER BY cnt DESC;
            """)
            results['clause_provenance'] = cur.fetchall()
        
        conn.close()
        return results
        
    except Exception as e:
        print(f"❌ Verification queries failed: {e}")
        return None

def main():
    """Main Phase 3 uplift process"""
    print("🏗️ PHASE 3 - FINAL METADATA UPLIFT (DETERMINISTIC)")
    print("=" * 60)
    print("Targets: ≥90% sections, ≥70% clauses")
    print("Safety: Full content + embeddings preserved")
    print("Method: Exact regex patterns with provenance")
    
    # Initial verification
    print("\n📊 INITIAL COVERAGE:")
    initial_results = run_verification_queries()
    if initial_results:
        overall = initial_results['overall']
        print(f"Section: {overall['section_cov']}/{overall['total']} ({overall['section_cov_pct']}%)")
        print(f"Clause: {overall['clause_cov']}/{overall['total']} ({overall['clause_cov_pct']}%)")
    
    batch_num = 1
    
    while True:
        print(f"\n📦 PHASE 3 BATCH {batch_num}")
        print("=" * 40)
        
        # Process batch
        is_complete, sections_added, clauses_added, snippets_updated, samples = process_phase3_batch(batch_num)
        
        if is_complete:
            print("🎉 NO MORE DOCUMENTS TO PROCESS!")
            break
        
        # Run verification queries after batch
        results = run_verification_queries()
        
        if results:
            overall = results['overall']
            
            print(f"\n📊 VERIFICATION SQL RESULTS (Batch {batch_num}):")
            print("Overall Coverage:")
            print(f"  Total: {overall['total']}, Section: {overall['section_cov']} ({overall['section_cov_pct']}%), Clause: {overall['clause_cov']} ({overall['clause_cov_pct']}%)")
            
            print(f"\nBatch Results:")
            print(f"  Sections added: {sections_added}")
            print(f"  Clauses added: {clauses_added}")  
            print(f"  Snippets updated: {snippets_updated}")
            
            # Check target achievement
            section_pct = float(overall['section_cov_pct'])
            clause_pct = float(overall['clause_cov_pct'])
            
            if section_pct >= 90.0 and clause_pct >= 70.0:
                print(f"🎯 TARGETS ACHIEVED! Sections: {section_pct:.1f}% ≥ 90%, Clauses: {clause_pct:.1f}% ≥ 70%")
                break
            elif section_pct >= 90.0 and clause_pct >= 85.0:
                print(f"🏆 STRETCH TARGETS ACHIEVED! Sections: {section_pct:.1f}% ≥ 90%, Clauses: {clause_pct:.1f}% ≥ 85%")
                break
            else:
                print(f"📈 Progress toward targets:")
                print(f"  Sections: {section_pct:.1f}% (target: 90%, need {90-section_pct:.1f}% more)")
                print(f"  Clauses: {clause_pct:.1f}% (target: 70%, need {70-clause_pct:.1f}% more)")
        
        if samples:
            print(f"\nSample extractions:")
            for sample in samples[:3]:
                print(f"• {sample['id']}... ({sample['source']} p.{sample['page']})")
                if sample['section']:
                    print(f"  Section: {sample['section'][:50]}... [source: {sample['section_source']}]")
                if sample['clause']:
                    print(f"  Clause: {sample['clause']} [source: {sample['clause_source']}]")
        
        batch_num += 1
        
        # Safety: stop if no progress
        if batch_num > 10 and sections_added == 0 and clauses_added == 0:
            print("⚠️ No progress in recent batches - stopping")
            break
        
        time.sleep(0.5)
    
    # FINAL COMPREHENSIVE REPORT
    print(f"\n🎉 PHASE 3 FINAL REPORT")
    print("=" * 60)
    
    final_results = run_verification_queries()
    
    if final_results:
        # Overall coverage results
        overall = final_results['overall']
        print(f"📊 FINAL COVERAGE VERIFICATION SQL:")
        print(f"Total: {overall['total']}, Section: {overall['section_cov']} ({overall['section_cov_pct']}%), Clause: {overall['clause_cov']} ({overall['clause_cov_pct']}%)")
        
        # Coverage by source
        print(f"\n📋 COVERAGE BY SOURCE:")
        for source_stat in final_results['by_source']:
            print(f"• {source_stat['source']}: total={source_stat['total']}, sections={source_stat['section_docs']} ({source_stat['section_pct']}%), clauses={source_stat['clause_docs']} ({source_stat['clause_pct']}%)")
        
        # Provenance distribution
        print(f"\n🔍 SECTION PROVENANCE:")
        for prov in final_results['section_provenance']:
            source_name = prov['section_source'] if prov['section_source'] else 'NULL'
            print(f"  {source_name}: {prov['cnt']} sections")
        
        print(f"\n🔍 CLAUSE PROVENANCE:")
        for prov in final_results['clause_provenance']:
            source_name = prov['clause_source'] if prov['clause_source'] else 'NULL'
            print(f"  {source_name}: {prov['cnt']} clauses")
        
        # Content integrity check
        try:
            conn = psycopg2.connect(DATABASE_URL, sslmode="require")
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) AS total,
                           COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) AS embeddings,
                           COUNT(CASE WHEN content IS NOT NULL AND length(content) > 50 THEN 1 END) AS full_content
                    FROM documents;
                """)
                integrity = cur.fetchone()
                print(f"\n✅ CONTENT INTEGRITY VERIFIED:")
                print(f"  Full content: {integrity[2]}/{integrity[0]} ({integrity[2]/integrity[0]*100:.1f}%)")
                print(f"  Embeddings: {integrity[1]}/{integrity[0]} ({integrity[1]/integrity[0]*100:.1f}%)")
            conn.close()
        except:
            pass
    
    print(f"\n🎉 PHASE 3 DETERMINISTIC UPLIFT COMPLETED!")
    print("• Approach: Exact regex patterns with provenance tracking")
    print("• Safety: Zero changes to content or embeddings")
    print("• Quality: All metadata traceable to source")

if __name__ == "__main__":
    main()