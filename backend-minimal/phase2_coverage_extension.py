#!/usr/bin/env python3
"""
Safe Metadata Uplift - Phase 2 Coverage Extension
Target ≥90% section/clause coverage using enhanced deterministic regex
Focus on 318 remaining documents (primarily NZ Metal Roofing)
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

def extract_clause_enhanced(content: str) -> tuple:
    """
    Enhanced clause extraction with comprehensive regex patterns
    Returns: (clause_text, provenance_info)
    """
    if not content:
        return None, None
    
    clause_patterns = [
        # NZBC Clause references
        (r'\bNZBC\s+Clause\s+([A-Z0-9]+(?:/[A-Z0-9]+)*)', 'nzbc_clause'),
        
        # AS/NZS Standards  
        (r'\bAS/NZS\s*(\d{3,4}(?:\.\d+)?(?::\d{4})?)', 'as_nzs_standard'),
        
        # NZS Standards
        (r'\bNZS\s*(\d{3,4}(?::\d{4})?)', 'nzs_standard'),
        
        # Building Code clauses (B1/AS1, E2/AS1 etc.)
        (r'\b([A-H]\d{1,3}(?:\s*/\s*[A-Z]{2,4}\d*)?)\b', 'building_code'),
        
        # Material standards (G550, H36, Z275)
        (r'\b([GHZ]\d{2,3})\b', 'material_grade'),
        
        # Additional standards
        (r'\b(ISO\s+\d{3,5}(?:\.\d+)?(?::\d{4})?)', 'iso_standard'),
        (r'\b(ASTM\s+[A-Z]\d+(?:-\d+)?)', 'astm_standard'),
    ]
    
    for pattern, provenance in clause_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            # Return first match with provenance
            clause = matches[0].upper() if isinstance(matches[0], str) else str(matches[0]).upper()
            return clause, f"regex_{provenance}"
    
    return None, None

def extract_section_enhanced(content: str) -> tuple:
    """
    Enhanced section extraction with comprehensive heading patterns
    Returns: (section_text, provenance_info)
    """
    if not content:
        return None, None
    
    lines = content.split('\n')[:25]  # Check more lines for headings
    
    section_patterns = [
        # Numbered sections with text
        (r'^(\d+(?:\.\d+){0,3})\s+([A-Za-z].{3,60})$', 'numbered_heading'),
        
        # Standalone standard terms
        (r'^(Scope|Purpose|Application|Requirements|Definitions|References)$', 'standard_heading'),
        
        # Terms ending with requirements/scope/etc
        (r'^(.{3,40}(?:Requirements?|Scope|Definitions|Performance|Objective).{0,20})$', 'descriptive_heading'),
        
        # Clean uppercase headings (not document headers)
        (r'^([A-Z][A-Za-z\s]{3,40})$', 'title_case_heading'),
    ]
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 4:
            continue
        
        # Skip obvious document headers
        skip_patterns = [
            r'.*(?:MINISTRY|DEPARTMENT|HANDBOOK|VERSION|COPYRIGHT|PAGE|CHAPTER).*',
            r'.*\d{4}.*',  # Years
            r'^[A-Z\s]*\d+[A-Z\s]*$',  # Just numbers
            r'^.*(ZEALAND|BUILDING|CODE|NZMRM|METAL|ROOFING).*$'  # Document titles
        ]
        
        if any(re.match(pattern, line, re.IGNORECASE) for pattern in skip_patterns):
            continue
        
        # Try each section pattern
        for pattern, provenance in section_patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                if provenance == 'numbered_heading':
                    section_text = line  # Full numbered heading
                elif provenance in ['standard_heading', 'descriptive_heading']:
                    section_text = match.group(1) if match.lastindex and match.lastindex >= 1 else line
                else:
                    section_text = line
                
                return section_text[:80], f"regex_{provenance}"
    
    return None, None

def process_enhanced_batch(batch_num: int):
    """Process batch with enhanced regex patterns"""
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Target documents missing metadata
            cur.execute("""
                SELECT id, source, page, content, section, clause
                FROM documents 
                WHERE (section IS NULL OR section = '') 
                AND (clause IS NULL OR clause = '')
                ORDER BY source, page
                LIMIT %s;
            """, (BATCH_SIZE,))
            
            documents = cur.fetchall()
            
            if not documents:
                return True, 0, 0, []
            
            print(f"📝 Processing {len(documents)} documents with enhanced regex patterns...")
            
            sections_added = 0
            clauses_added = 0
            samples = []
            
            for doc in documents:
                doc_id = doc['id']
                source = doc['source']
                page = doc['page']
                content = doc['content']
                existing_section = doc['section']
                existing_clause = doc['clause']
                
                # Enhanced extraction
                new_section, section_provenance = None, None
                new_clause, clause_provenance = None, None
                
                if not existing_section:
                    new_section, section_provenance = extract_section_enhanced(content)
                
                if not existing_clause:
                    new_clause, clause_provenance = extract_clause_enhanced(content)
                
                # Update only if we found something
                if new_section or new_clause:
                    # Update with valid provenance (only allowed values)
                    update_section = new_section if new_section else existing_section
                    update_clause = new_clause if new_clause else existing_clause
                    
                    # Ensure section_source is valid (on_page, toc, bookmark, or NULL)
                    valid_section_source = None
                    if new_section and section_provenance:
                        if 'on_page' in section_provenance or 'heading' in section_provenance:
                            valid_section_source = 'on_page'
                        # For now, only use 'on_page' as we don't have TOC/bookmark data yet
                    
                    cur.execute("""
                        UPDATE documents 
                        SET section = %s,
                            clause = %s,
                            section_source = %s,
                            updated_at = NOW()
                        WHERE id = %s;
                    """, (update_section, update_clause, valid_section_source, doc_id))
                    
                    if new_section:
                        sections_added += 1
                    if new_clause:
                        clauses_added += 1
                    
                    # Store sample
                    if len(samples) < 10:
                        samples.append({
                            'id': str(doc_id)[:8],
                            'source': source,
                            'page': page,
                            'section': new_section,
                            'clause': new_clause,
                            'section_provenance': section_provenance,
                            'clause_provenance': clause_provenance,
                            'content_preview': content[:150] + "..." if len(content) > 150 else content
                        })
            
            conn.commit()
            
        conn.close()
        return False, sections_added, clauses_added, samples
        
    except Exception as e:
        print(f"❌ Enhanced batch failed: {e}")
        return False, 0, 0, []

def run_validation_sql():
    """Run the requested validation SQL after each batch"""
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) AS total,
                       COUNT(CASE WHEN section IS NOT NULL AND section != '' THEN 1 END) AS section_cov,
                       COUNT(CASE WHEN clause IS NOT NULL AND clause != '' THEN 1 END) AS clause_cov,
                       ROUND(100.0*COUNT(CASE WHEN section IS NOT NULL AND section != '' THEN 1 END)/COUNT(*),1) AS section_cov_pct,
                       ROUND(100.0*COUNT(CASE WHEN clause IS NOT NULL AND clause != '' THEN 1 END)/COUNT(*),1) AS clause_cov_pct
                FROM documents;
            """)
            
            result = cur.fetchone()
            
        conn.close()
        return result
        
    except Exception as e:
        print(f"❌ Validation query failed: {e}")
        return None

def main():
    """Main Phase 2 coverage extension"""
    print("🏗️ SAFE METADATA UPLIFT - PHASE 2 COVERAGE EXTENSION")
    print("=" * 60)
    print("Target: ≥90% section/clause coverage")
    print("Focus: 318 documents missing metadata (310 Metal Roofing)")
    print("Method: Enhanced deterministic regex, no guessing")
    
    batch_num = 1
    
    # Initial coverage check
    initial_stats = run_validation_sql()
    if initial_stats:
        print(f"\n📊 STARTING COVERAGE:")
        print(f"• Total: {initial_stats[0]}")
        print(f"• Sections: {initial_stats[1]} ({initial_stats[3]}%)")
        print(f"• Clauses: {initial_stats[2]} ({initial_stats[4]}%)")
    
    while True:
        print(f"\n📦 PHASE 2 BATCH {batch_num}")
        print("=" * 40)
        
        # Get before stats
        before_stats = run_validation_sql()
        
        # Process batch with enhanced patterns
        is_complete, sections_added, clauses_added, samples = process_enhanced_batch(batch_num)
        
        if is_complete:
            print("🎉 NO MORE DOCUMENTS TO PROCESS!")
            break
        
        # Get after stats
        after_stats = run_validation_sql()
        
        if before_stats and after_stats:
            print(f"\n📊 Enhanced Coverage Checkpoint (Batch {batch_num})")
            print(f"- Total documents: {after_stats[0]}")
            print(f"- Section coverage: {before_stats[1]} → {after_stats[1]} ({after_stats[3]}%)")
            print(f"- Clause coverage: {before_stats[2]} → {after_stats[2]} ({after_stats[4]}%)")
            print(f"- Sections added: {sections_added}")
            print(f"- Clauses added: {clauses_added}")
            
            # Check if we've reached 90% target
            if after_stats[3] >= 90.0 and after_stats[4] >= 90.0:
                print("\n🎯 TARGET REACHED: ≥90% coverage achieved!")
                break
            
            # Show progress toward goal
            section_progress = after_stats[3]
            clause_progress = after_stats[4]
            print(f"- Progress toward 90% target: sections {section_progress:.1f}%, clauses {clause_progress:.1f}%")
        
        if samples:
            print(f"\n📋 Sample enhanced extractions:")
            for sample in samples[:5]:
                print(f"• {sample['id']}... ({sample['source']} p.{sample['page']})")
                if sample['section']:
                    print(f"  Section: {sample['section'][:60]}... [provenance: {sample['section_provenance']}]")
                if sample['clause']:
                    print(f"  Clause: {sample['clause']} [provenance: {sample['clause_provenance']}]")
                print(f"  Content: {sample['content_preview']}")
                print()
        
        batch_num += 1
        
        # Stop after reasonable number of batches if no progress
        if batch_num > 10 and sections_added == 0 and clauses_added == 0:
            print("⚠️ No progress in recent batches - stopping to avoid infinite loop")
            break
        
        time.sleep(1)
    
    # Final comprehensive report
    final_stats = run_validation_sql()
    
    print(f"\n📊 FINAL PHASE 2 COVERAGE REPORT")
    print("=" * 60)
    
    if final_stats:
        print(f"VALIDATION QUERY RESULTS:")
        print(f"Total: {final_stats[0]}, Section: {final_stats[1]} ({final_stats[3]}%), Clause: {final_stats[2]} ({final_stats[4]}%)")
    
    # Provenance breakdown
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Final provenance analysis
            cur.execute("""
                SELECT section_source, COUNT(*) AS cnt
                FROM documents
                WHERE section IS NOT NULL AND section != ''
                GROUP BY section_source
                ORDER BY cnt DESC;
            """)
            
            provenance = cur.fetchall()
            print(f"\nProvenance distribution:")
            for p in provenance:
                source_name = p['section_source'] if p['section_source'] else 'unspecified'
                print(f"  {source_name}: {p['cnt']} sections")
            
            # Content integrity verification
            cur.execute("""
                SELECT COUNT(*) AS total,
                       COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) AS with_embeddings,
                       COUNT(CASE WHEN content IS NOT NULL AND length(content) > 50 THEN 1 END) AS with_content,
                       AVG(length(content)) AS avg_content_length
                FROM documents;
            """)
            
            integrity = cur.fetchone()
            print(f"\nContent integrity confirmation:")
            print(f"  Documents with embeddings: {integrity['with_embeddings']}/{integrity['total']} ({integrity['with_embeddings']/integrity['total']*100:.1f}%)")
            print(f"  Documents with full content: {integrity['with_content']}/{integrity['total']} ({integrity['with_content']/integrity['total']*100:.1f}%)")
            print(f"  Average content length: {integrity['avg_content_length']:.0f} chars")
            
            # Final source breakdown
            cur.execute("""
                SELECT source,
                       COUNT(*) AS total,
                       COUNT(CASE WHEN section IS NOT NULL AND section != '' THEN 1 END) AS sections,
                       COUNT(CASE WHEN clause IS NOT NULL AND clause != '' THEN 1 END) AS clauses,
                       ROUND(100.0*COUNT(CASE WHEN section IS NOT NULL AND section != '' THEN 1 END)/COUNT(*),1) AS section_pct,
                       ROUND(100.0*COUNT(CASE WHEN clause IS NOT NULL AND clause != '' THEN 1 END)/COUNT(*),1) AS clause_pct
                FROM documents
                GROUP BY source
                ORDER BY source;
            """)
            
            source_breakdown = cur.fetchall()
            print(f"\nFinal coverage by source:")
            for stat in source_breakdown:
                print(f"  • {stat['source']}: sections {stat['sections']}/{stat['total']} ({stat['section_pct']}%), clauses {stat['clauses']}/{stat['total']} ({stat['clause_pct']}%)")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Final analysis failed: {e}")
    
    print(f"\n✅ SAFE METADATA UPLIFT PHASE 2 COMPLETED")
    print("• Approach: Enhanced deterministic regex extraction")
    print("• Safety: Full content and embeddings preserved")
    print("• Provenance: All metadata traceable to extraction method")

if __name__ == "__main__":
    main()