#!/usr/bin/env python3
"""
Extract section and clause metadata from existing documents
Processes all documents to add section headings and NZ building code clauses
"""

import os
import re
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import time

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def extract_section(content: str) -> str:
    """
    Extract section heading from document content
    Looks for heading-like patterns at the start of content
    """
    lines = content.split('\n')[:10]  # Check first 10 lines
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Pattern 1: Numbered sections (e.g., "4.2.3 Apron flashings")
        if re.match(r'^\d+(\.\d+){1,3}\s+.+', line):
            return line[:100]  # Limit length
        
        # Pattern 2: ALL CAPS headings
        if len(line) > 5 and line.isupper() and not re.match(r'^[A-Z\s]*\d+[A-Z\s]*$', line):
            return line[:100]
        
        # Pattern 3: Title Case headings with common building terms
        if any(term in line.lower() for term in ['flashing', 'roofing', 'installation', 'requirements', 'standards']) and len(line) > 10:
            if line[0].isupper():
                return line[:100]
    
    return None

def extract_clause(content: str) -> str:
    """
    Extract NZ building code clauses from document content
    Looks for patterns like E2, E2/AS1, B1, G12, H1, NZMRM sections
    """
    # NZ Building Code clause patterns (E2, B1, etc.)
    nz_code_pattern = r'\b[A-H]\d+(?:/[A-Z]{2}\d*)?\b'
    
    # NZMRM section patterns (numbered sections)
    nzmrm_pattern = r'\b\d+(?:\.\d+){1,3}\b'
    
    # Find all NZ code matches
    nz_matches = re.findall(nz_code_pattern, content)
    
    # Find NZMRM section matches
    nzmrm_matches = re.findall(nzmrm_pattern, content)
    
    # Prioritize NZ Building Code clauses
    if nz_matches:
        # Return the most specific match (longer is usually more specific)
        return max(nz_matches, key=len)
    
    # Fall back to NZMRM sections if found
    if nzmrm_matches:
        # Return the most specific NZMRM section
        return max(nzmrm_matches, key=lambda x: len(x.split('.')))
    
    return None

def process_documents_batch(batch_size: int = 50) -> int:
    """
    Process documents in batches to extract metadata
    Returns number of documents updated
    """
    if not DATABASE_URL:
        print("❌ DATABASE_URL not configured")
        return 0
    
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Get documents that need metadata extraction (where section IS NULL)
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
            
            for doc in documents:
                doc_id = doc['id']
                source = doc['source']
                page = doc['page']
                content = doc['content']
                
                # Extract metadata
                section = extract_section(content)
                clause = extract_clause(content)
                
                # Update document with metadata
                cur.execute("""
                    UPDATE documents 
                    SET section = %s, clause = %s
                    WHERE id = %s;
                """, (section, clause, doc_id))
                
                updated_count += 1
                
                # Log progress for significant documents
                if section or clause:
                    metadata_info = []
                    if section:
                        metadata_info.append(f"section: {section[:30]}...")
                    if clause:
                        metadata_info.append(f"clause: {clause}")
                    
                    print(f"  ✅ {source} p.{page}: {', '.join(metadata_info)}")
            
            conn.commit()
            print(f"✅ Updated {updated_count} documents with metadata")
            
        conn.close()
        return updated_count
        
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")
        return 0

def main():
    """Main metadata extraction pipeline"""
    print("🏗️ STRYDA-v2 CITATION METADATA EXTRACTION")
    print("=" * 60)
    
    total_updated = 0
    batch_num = 1
    
    while True:
        print(f"\n📦 Processing batch {batch_num}...")
        
        batch_updated = process_documents_batch()
        total_updated += batch_updated
        
        if batch_updated == 0:
            print("✅ All documents processed")
            break
        
        batch_num += 1
        
        # Small delay between batches
        time.sleep(0.5)
    
    # Final verification
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            print(f"\n📊 METADATA EXTRACTION RESULTS")
            print("=" * 50)
            
            # Count documents with sections
            cur.execute("SELECT COUNT(*) FROM documents WHERE section IS NOT NULL;")
            section_count = cur.fetchone()['count']
            
            # Count documents with clauses
            cur.execute("SELECT COUNT(*) FROM documents WHERE clause IS NOT NULL;")
            clause_count = cur.fetchone()['count']
            
            # Total documents
            cur.execute("SELECT COUNT(*) FROM documents;")
            total_count = cur.fetchone()['count']
            
            print(f"Documents with sections: {section_count}/{total_count} ({section_count/total_count*100:.1f}%)")
            print(f"Documents with clauses: {clause_count}/{total_count} ({clause_count/total_count*100:.1f}%)")
            
            # Sample of extracted metadata
            cur.execute("""
                SELECT source, page, section, clause
                FROM documents 
                WHERE (section IS NOT NULL OR clause IS NOT NULL)
                ORDER BY source, page
                LIMIT 10;
            """)
            
            samples = cur.fetchall()
            print(f"\nSample metadata extractions:")
            for sample in samples:
                metadata_parts = []
                if sample['section']:
                    metadata_parts.append(f"section: {sample['section'][:40]}...")
                if sample['clause']:
                    metadata_parts.append(f"clause: {sample['clause']}")
                
                if metadata_parts:
                    print(f"  {sample['source']} p.{sample['page']}: {', '.join(metadata_parts)}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Final verification failed: {e}")
    
    print(f"\n🎉 METADATA EXTRACTION COMPLETED!")
    print(f"Total documents enriched: {total_updated}")
    return total_updated > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)