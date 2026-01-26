#!/usr/bin/env python3
"""
STRYDA-v2 PDF Ingestion Status Report
Read-only report showing which PDFs from manifest are ingested
"""

import json
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Configuration
MANIFEST_PATH = "/app/backend-minimal/training/docs_manifest.jsonl"
DATABASE_URL = os.getenv("DATABASE_URL")

def main():
    """Generate ingestion status report"""
    print("="*80)
    print("STRYDA-v2 PDF INGESTION STATUS REPORT")
    print("="*80)
    
    # Load manifest
    with open(MANIFEST_PATH, 'r') as f:
        manifest_entries = [json.loads(line) for line in f if line.strip()]
    
    # Connect to database
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    cur = conn.cursor()
    
    # Get global totals
    cur.execute("SELECT COUNT(DISTINCT source) FROM documents;")
    total_documents = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM documents;")
    total_chunks = cur.fetchone()[0]
    
    # Print summary
    print(f"\nTOTAL DOCUMENTS: {total_documents}")
    print(f"TOTAL CHUNKS: {total_chunks}")
    print(f"MANIFEST ENTRIES: {len(manifest_entries)}")
    
    # Check each manifest entry
    print(f"\n{'='*80}")
    print("MANIFEST ENTRY STATUS")
    print(f"{'='*80}\n")
    
    ingested_count = 0
    missing_count = 0
    
    for entry in manifest_entries:
        supabase_path = entry["supabase_path"]
        phase = entry.get("phase", 0)
        category = entry.get("category", "unknown")
        trade = entry.get("trade", "unknown")
        status = entry.get("status", "unknown")
        
        # Try to find matching document
        # Use same logic as pdf_ingest.py - source name without .pdf extension
        source_name = supabase_path.replace(".pdf", "")
        
        cur.execute("""
            SELECT source, COUNT(*) as chunk_count
            FROM documents
            WHERE source = %s OR source LIKE %s
            GROUP BY source;
        """, (source_name, f"%{source_name}%"))
        
        result = cur.fetchone()
        
        if result:
            actual_source, chunk_count = result
            ingestion_status = "INGESTED"
            completion_pct = 100
            ingested_count += 1
        else:
            chunk_count = 0
            ingestion_status = "MISSING"
            completion_pct = 0
            missing_count += 1
        
        # Print entry status
        print(f"{supabase_path:60} | status={ingestion_status:8} | chunks={chunk_count:4} | completion={completion_pct:3}% | phase={phase} | category={category:30} | trade={trade}")
    
    # Summary stats
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"INGESTED: {ingested_count}")
    print(f"MISSING: {missing_count}")
    print(f"Total manifest entries: {len(manifest_entries)}")
    
    conn.close()

if __name__ == "__main__":
    main()
