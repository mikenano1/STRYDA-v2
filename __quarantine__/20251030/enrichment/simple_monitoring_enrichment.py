#!/usr/bin/env python3
"""
Simplified Self-Monitoring Metadata Extraction
Robust single-threaded approach with heartbeat and auto-restart
"""

import os
import re
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import time
import datetime
import signal
import sys

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
BATCH_SIZE = 50
HEARTBEAT_INTERVAL = 60  # 1 minute for testing
processed_count = 0
start_time = time.time()

def signal_handler(signum, frame):
    """Handle interrupt signals gracefully"""
    print(f"\n🛑 Shutdown requested. Processed {processed_count} documents.")
    update_process_status(note="stopped")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def update_process_status(note=None):
    """Update process status in database"""
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        
        with conn.cursor() as cur:
            # Get current stats
            cur.execute("SELECT COUNT(*) FROM documents;")
            total = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM documents WHERE section IS NOT NULL;")
            sections = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM documents WHERE clause IS NOT NULL;")
            clauses = cur.fetchone()[0]
            
            processed = sections  # Use sections as processed marker
            
            # Upsert status
            cur.execute("""
                INSERT INTO process_status (id, last_heartbeat, processed, total, with_section, with_clause, note)
                VALUES ('enrichment', NOW(), %s, %s, %s, %s, %s)
                ON CONFLICT (id) 
                DO UPDATE SET 
                    last_heartbeat = NOW(),
                    processed = EXCLUDED.processed,
                    total = EXCLUDED.total,
                    with_section = EXCLUDED.with_section,
                    with_clause = EXCLUDED.with_clause,
                    note = EXCLUDED.note;
            """, (processed, total, sections, clauses, note or "running"))
            
            conn.commit()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Process status update failed: {e}")

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
        
        # ALL CAPS headings
        if len(line) > 5 and line.isupper() and len(line.split()) > 1:
            exclude_words = ['PAGE', 'CHAPTER', 'PART', 'SECTION', 'VERSION', 'MINISTRY', 'HANDBOOK']
            if not any(word in line for word in exclude_words):
                return line[:80]
        
        # Specific building terms
        building_terms = ['OBJECTIVE', 'FUNCTIONAL REQUIREMENT', 'PERFORMANCE', 'ACCEPTABLE SOLUTION']
        if line.upper() in building_terms:
            return line
    
    return None

def extract_clause(content: str) -> str:
    """Extract NZ building code clauses"""
    # Building code clauses: E2, B1/AS1, etc.
    clause_pattern = r'\b([A-H]\d+(?:/[A-Z]{2,4}\d*)?)\b'
    matches = re.findall(clause_pattern, content, re.IGNORECASE)
    
    if matches:
        # Return most specific (longest) match
        return max(matches, key=len).upper()
    
    # NZS Standards
    nzs_pattern = r'\b((?:AS/)?NZS\s+\d+(?:\.\d+)?)\b'
    nzs_matches = re.findall(nzs_pattern, content, re.IGNORECASE)
    
    if nzs_matches:
        return nzs_matches[0].upper()
    
    return None

def process_batch():
    """Process one batch of documents"""
    global processed_count
    
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Get documents needing processing
            cur.execute("""
                SELECT id, source, page, content 
                FROM documents 
                WHERE section IS NULL 
                ORDER BY source, page
                LIMIT %s;
            """, (BATCH_SIZE,))
            
            documents = cur.fetchall()
            
            if not documents:
                return 0, True  # No more documents, completed
            
            updated_count = 0
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
                
                updated_count += 1
                processed_count += 1
                
                if section:
                    sections_found += 1
                if clause:
                    clauses_found += 1
            
            conn.commit()
            
            print(f"📝 Batch processed: {updated_count} docs, {sections_found} sections, {clauses_found} clauses found")
            
        conn.close()
        return updated_count, False
        
    except Exception as e:
        print(f"❌ Batch failed: {e}")
        return 0, False

def main():
    """Main enrichment loop with heartbeat"""
    global processed_count
    
    print("🏗️ STRYDA-v2 SIMPLIFIED SELF-MONITORING ENRICHMENT")
    print("=" * 60)
    
    # Initial status
    update_process_status(note="starting")
    
    last_heartbeat = time.time()
    
    while True:
        # Process batch
        batch_updated, is_complete = process_batch()
        
        if is_complete:
            print("🎉 ENRICHMENT COMPLETED!")
            update_process_status(note="completed")
            break
        
        if batch_updated == 0:
            print("⚠️ No progress made - waiting...")
            time.sleep(5)
        
        # Emit heartbeat every interval
        current_time = time.time()
        if current_time - last_heartbeat >= HEARTBEAT_INTERVAL:
            # Get current stats for heartbeat
            try:
                conn = psycopg2.connect(DATABASE_URL, sslmode="require")
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM documents;")
                    total = cur.fetchone()[0]
                    
                    cur.execute("SELECT COUNT(*) FROM documents WHERE section IS NOT NULL;")
                    sections = cur.fetchone()[0]
                    
                    cur.execute("SELECT COUNT(*) FROM documents WHERE clause IS NOT NULL;")
                    clauses = cur.fetchone()[0]
                    
                    pct = (sections / total * 100) if total > 0 else 0
                    iso_timestamp = datetime.datetime.now().isoformat()
                    
                    heartbeat_msg = f"[Heartbeat] Enrichment running: {sections}/{total} ({pct:.1f}%) | sections={sections} clauses={clauses} | restarts=0 | {iso_timestamp}"
                    print(heartbeat_msg)
                    
                conn.close()
            except Exception as e:
                print(f"❌ Heartbeat error: {e}")
            
            # Update process status
            update_process_status()
            last_heartbeat = current_time
        
        # Small delay between batches
        time.sleep(1)
    
    # Final heartbeat
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM documents;")
            total = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM documents WHERE section IS NOT NULL;")
            sections = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM documents WHERE clause IS NOT NULL;")
            clauses = cur.fetchone()[0]
            
            print(f"\n📊 FINAL RESULTS:")
            print(f"• Documents with sections: {sections}/{total} ({sections/total*100:.1f}%)")
            print(f"• Documents with clauses: {clauses}/{total} ({clauses/total*100:.1f}%)")
        
        conn.close()
    except Exception as e:
        print(f"❌ Final stats error: {e}")

if __name__ == "__main__":
    main()