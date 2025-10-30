#!/usr/bin/env python3
"""
Self-Monitoring Metadata Extraction with Heartbeat and Auto-Restart
Robust enrichment process with stall detection and automatic recovery
"""

import os
import re
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import time
import signal
import sys
import threading
import datetime
import json
import requests

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
ALERT_WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL")
BATCH_SIZE = 50
HEARTBEAT_INTERVAL = 300  # 5 minutes
STALL_TIMEOUT = 900      # 15 minutes
MAX_RESTARTS = 3

# Global state
processed_count = 0
total_docs = 0
last_progress_time = time.time()
restart_count = 0
should_stop = False

def signal_handler(signum, frame):
    """Handle interrupt signals gracefully"""
    global should_stop
    should_stop = True
    print(f"\n🛑 Shutdown signal received. Processed {processed_count} documents.")
    
    # Update process status as stopped
    update_process_status(note="stopped")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def get_current_stats():
    """Get current document processing statistics"""
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require", connect_timeout=10)
        
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
        return 0, 0, 0, 0, 0

def update_process_status(note=None):
    """Update process status in database"""
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require", connect_timeout=10)
        
        total, processed, sections, clauses, remaining = get_current_stats()
        
        with conn.cursor() as cur:
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
            """, (processed, total, sections, clauses, note))
            
            conn.commit()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Failed to update process status: {e}")

def send_alert(event_type, message):
    """Send alert webhook if configured"""
    if not ALERT_WEBHOOK_URL:
        return
        
    try:
        payload = {
            "event": event_type,
            "message": message,
            "timestamp": datetime.datetime.now().isoformat(),
            "process": "metadata_enrichment",
            "processed": processed_count,
            "total": total_docs
        }
        
        requests.post(ALERT_WEBHOOK_URL, json=payload, timeout=10)
        print(f"📤 Alert sent: {event_type}")
        
    except Exception as e:
        print(f"❌ Alert failed: {e}")

def heartbeat_worker():
    """Background heartbeat worker thread"""
    global should_stop, processed_count, total_docs, last_progress_time, restart_count
    
    while not should_stop:
        try:
            # Get current statistics
            total, processed, sections, clauses, remaining = get_current_stats()
            
            # Check for progress
            if processed > processed_count:
                last_progress_time = time.time()
                processed_count = processed
                total_docs = total
            
            # Emit heartbeat
            iso_timestamp = datetime.datetime.now().isoformat()
            pct = (processed / total * 100) if total > 0 else 0
            
            heartbeat_msg = f"[Heartbeat] Enrichment running: {processed}/{total} ({pct:.1f}%) | sections={sections} clauses={clauses} | restarts={restart_count} | {iso_timestamp}"
            print(heartbeat_msg)
            
            # Update database
            update_process_status(note=f"running (restarts: {restart_count})")
            
            # Check for stall
            time_since_progress = time.time() - last_progress_time
            if time_since_progress >= STALL_TIMEOUT:
                stall_msg = f"⚠️ Enrichment stalled at {processed}/{total} ({pct:.1f}%) since {datetime.datetime.fromtimestamp(last_progress_time).isoformat()}"
                print(stall_msg)
                
                # Update status as stalled
                update_process_status(note="stalled")
                
                # Send alert
                send_alert("stalled", stall_msg)
                
                # Trigger restart if we haven't exceeded limit
                if restart_count < MAX_RESTARTS:
                    restart_count += 1
                    print(f"🔄 Auto-restart #{restart_count}/{MAX_RESTARTS} initiated...")
                    
                    # Reset progress timer
                    last_progress_time = time.time()
                    
                    # Don't break the heartbeat loop - let main process handle restart
                else:
                    fatal_msg = f"❌ Enrichment halted after {MAX_RESTARTS} restart attempts"
                    print(fatal_msg)
                    update_process_status(note="halted")
                    send_alert("halted", fatal_msg)
                    should_stop = True
                    break
            
        except Exception as e:
            print(f"❌ Heartbeat error: {e}")
        
        # Wait for next heartbeat
        time.sleep(HEARTBEAT_INTERVAL)

def extract_section(content: str, source: str) -> str:
    """Enhanced section extraction with better patterns"""
    lines = content.split('\n')[:20]
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 3:
            continue
            
        # Pattern 1: Numbered sections
        numbered_match = re.match(r'^(\d+(?:\.\d+){1,3})\s+(.+)', line)
        if numbered_match:
            return line[:80]
        
        # Pattern 2: ALL CAPS headings
        if len(line) > 5 and line.isupper() and len(line.split()) > 1:
            if not any(word in line for word in ['PAGE', 'CHAPTER', 'PART', 'SECTION', 'VERSION']):
                return line[:80]
        
        # Pattern 3: Building code headers
        if source == "NZ Building Code":
            standard_headers = ['OBJECTIVE', 'FUNCTIONAL REQUIREMENT', 'PERFORMANCE', 'ACCEPTABLE SOLUTION', 'VERIFICATION METHOD']
            if line.upper() in standard_headers:
                return line
        
        # Pattern 4: Definition patterns
        if re.match(r'^[A-Za-z][a-z\s]+\s+[A-Z]', line) and any(term in line.lower() for term in ['flashing', 'membrane', 'fastener']):
            return line[:80]
    
    return None

def extract_clause(content: str, source: str) -> str:
    """Enhanced clause extraction with comprehensive patterns"""
    # NZ Building Code patterns
    patterns = [
        r'\b([A-H]\d+(?:/[A-Z]{2,4}\d*)?)\b',  # E2, E2/AS1, B1/VM1
        r'\b((?:AS/)?NZS\s+\d+(?:\.\d+)?(?::\d{4})?)\b',  # NZS 3604, AS/NZS 1562
        r'\b(NZMRM\s+\d+(?:\.\d+){1,3})\b'  # NZMRM sections
    ]
    
    all_matches = []
    
    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            if isinstance(match, str):
                clause = match.upper().strip()
                if len(clause) > 1:
                    all_matches.append(clause)
    
    if all_matches:
        # Prioritize most specific (longer with qualifiers)
        return max(all_matches, key=lambda x: len(x) + (20 if '/' in x else 0))
    
    return None

def process_batch():
    """Process a single batch of documents"""
    global processed_count, last_progress_time
    
    if not DATABASE_URL:
        return 0
    
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require", connect_timeout=30)
        
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
                return 0
            
            updated_count = 0
            
            for doc in documents:
                if should_stop:
                    break
                    
                doc_id = doc['id']
                source = doc['source']
                page = doc['page']
                content = doc['content']
                
                # Extract metadata
                section = extract_section(content, source)
                clause = extract_clause(content, source)
                
                # Update document
                cur.execute("""
                    UPDATE documents 
                    SET section = %s, clause = %s
                    WHERE id = %s;
                """, (section, clause, doc_id))
                
                updated_count += 1
                
                # Update progress tracking
                if updated_count % 10 == 0:
                    processed_count += 10
                    last_progress_time = time.time()
            
            conn.commit()
            
            # Final progress update
            processed_count += updated_count % 10
            last_progress_time = time.time()
            
        conn.close()
        return updated_count
        
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")
        return 0

def main_enrichment_loop():
    """Main enrichment processing loop with restart capability"""
    global processed_count, total_docs, should_stop, restart_count
    
    print("🏗️ STRYDA-v2 SELF-MONITORING METADATA ENRICHMENT")
    print("=" * 60)
    
    # Read startup state
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("SELECT * FROM process_status WHERE id = 'enrichment';")
            status = cur.fetchone()
            
            if status:
                print(f"📋 Previous state: {status['processed']}/{status['total']} processed")
                print(f"   Last heartbeat: {status['last_heartbeat']}")
                print(f"   Note: {status['note']}")
        conn.close()
    except:
        print("📋 No previous state found")
    
    # Get initial stats
    total_docs, processed_count, sections, clauses, remaining = get_current_stats()
    
    # Start heartbeat thread
    heartbeat_thread = threading.Thread(target=heartbeat_worker, daemon=True)
    heartbeat_thread.start()
    
    # Emit first heartbeat immediately
    iso_timestamp = datetime.datetime.now().isoformat()
    pct = (processed_count / total_docs * 100) if total_docs > 0 else 0
    print(f"[Heartbeat] Enrichment starting: {processed_count}/{total_docs} ({pct:.1f}%) | sections={sections} clauses={clauses} | {iso_timestamp}")
    
    batch_count = 0
    
    while not should_stop:
        try:
            # Process batch
            batch_updated = process_batch()
            
            if batch_updated == 0:
                print("✅ All documents processed - enrichment complete!")
                update_process_status(note="completed")
                break
            
            batch_count += 1
            
            # Small delay between batches
            time.sleep(0.5)
            
        except Exception as e:
            print(f"❌ Processing error: {e}")
            time.sleep(5)
    
    # Final status update
    final_total, final_processed, final_sections, final_clauses, final_remaining = get_current_stats()
    
    print(f"\n🎉 ENRICHMENT COMPLETED!")
    print(f"Final results: {final_processed}/{final_total} documents")
    print(f"Sections: {final_sections}, Clauses: {final_clauses}")
    print(f"Restart count: {restart_count}")
    
    update_process_status(note="completed")

def restart_enrichment():
    """Restart the enrichment process after a stall"""
    global should_stop, restart_count, last_progress_time
    
    print(f"🔄 RESTARTING ENRICHMENT (attempt {restart_count}/{MAX_RESTARTS})")
    print("=" * 50)
    
    # Reset state
    should_stop = False
    last_progress_time = time.time()
    
    # Sleep before restart
    print("😴 Waiting 30 seconds before restart...")
    time.sleep(30)
    
    # Restart main loop
    main_enrichment_loop()

def main():
    """Main entry point with auto-restart logic"""
    global restart_count
    
    while restart_count < MAX_RESTARTS:
        try:
            main_enrichment_loop()
            break  # Completed successfully
            
        except KeyboardInterrupt:
            print("🛑 Manual stop requested")
            break
            
        except Exception as e:
            print(f"❌ Enrichment failed: {e}")
            
            restart_count += 1
            if restart_count < MAX_RESTARTS:
                print(f"🔄 Auto-restart {restart_count}/{MAX_RESTARTS} in 30 seconds...")
                update_process_status(note=f"restarting (attempt {restart_count})")
                time.sleep(30)
            else:
                fatal_msg = f"❌ Enrichment halted after {MAX_RESTARTS} restart attempts"
                print(fatal_msg)
                update_process_status(note="halted")
                send_alert("halted", fatal_msg)
                break
    
    print(f"🏁 Metadata enrichment process ended. Total restarts: {restart_count}")

if __name__ == "__main__":
    main()