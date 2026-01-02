#!/usr/bin/env python3
"""
STRYDA Diagnostic: Inspect Supabase Vector Store for Section 8 (Wall Framing) Content
Goal: Determine if table data was properly ingested or if we have "Table Blindness"
"""

import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def inspect_section8_chunks():
    """Query for Section 8 Wall Framing related chunks"""
    
    print("=" * 80)
    print("🔍 STRYDA DIAGNOSTIC: Section 8 Wall Framing Chunk Inspection")
    print("=" * 80)
    
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # First, let's see what tables exist
    print("\n📊 Available tables:")
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)
    tables = cursor.fetchall()
    for t in tables:
        print(f"   - {t['table_name']}")
    
    # Get the documents table structure
    print("\n📋 Document chunks table structure:")
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'document_chunks'
        ORDER BY ordinal_position
    """)
    columns = cursor.fetchall()
    for col in columns:
        print(f"   - {col['column_name']}: {col['data_type']}")
    
    # Count total chunks for NZS 3604
    print("\n📈 NZS 3604 Chunk Statistics:")
    cursor.execute("""
        SELECT 
            source,
            COUNT(*) as chunk_count,
            MIN(LENGTH(content)) as min_len,
            MAX(LENGTH(content)) as max_len,
            AVG(LENGTH(content))::int as avg_len
        FROM document_chunks 
        WHERE source ILIKE '%3604%'
        GROUP BY source
    """)
    stats = cursor.fetchall()
    for s in stats:
        print(f"   Source: {s['source']}")
        print(f"   Chunks: {s['chunk_count']}, Len: min={s['min_len']}, max={s['max_len']}, avg={s['avg_len']}")
    
    # Search for Section 8 / Wall Framing content
    print("\n" + "=" * 80)
    print("🔎 Searching for 'Section 8' or 'Wall Framing' content...")
    print("=" * 80)
    
    cursor.execute("""
        SELECT id, source, content, metadata
        FROM document_chunks
        WHERE source ILIKE '%3604%'
        AND (
            content ILIKE '%section 8%' 
            OR content ILIKE '%wall framing%'
            OR content ILIKE '%stud%'
            OR content ILIKE '%8.5%'
            OR content ILIKE '%8.6%'
        )
        ORDER BY id
        LIMIT 20
    """)
    
    results = cursor.fetchall()
    print(f"\n✅ Found {len(results)} chunks mentioning Section 8/Wall Framing:\n")
    
    for i, r in enumerate(results, 1):
        print(f"--- Chunk {i} (ID: {r['id']}) ---")
        print(f"Source: {r['source']}")
        print(f"Content preview ({len(r['content'])} chars):")
        # Show first 500 chars
        preview = r['content'][:500].replace('\n', ' ')
        print(f"   {preview}...")
        print()
    
    # Now specifically look for TABLE-like content
    print("\n" + "=" * 80)
    print("🔎 Searching for TABLE-like content (spans, sizes, dimensions)...")
    print("=" * 80)
    
    cursor.execute("""
        SELECT id, source, content
        FROM document_chunks
        WHERE source ILIKE '%3604%'
        AND (
            content ILIKE '%table 8%'
            OR content ILIKE '%span%mm%'
            OR content ILIKE '%90 x 45%'
            OR content ILIKE '%140 x 45%'
            OR content ILIKE '%joist span%'
            OR content ILIKE '%maximum span%'
        )
        ORDER BY id
        LIMIT 15
    """)
    
    table_results = cursor.fetchall()
    print(f"\n✅ Found {len(table_results)} chunks with potential table data:\n")
    
    for i, r in enumerate(table_results, 1):
        print(f"--- Table Chunk {i} (ID: {r['id']}) ---")
        preview = r['content'][:600].replace('\n', ' ')
        print(f"   {preview}...")
        
        # Check for numeric patterns (indicates table data)
        import re
        numbers = re.findall(r'\b\d{3,4}\b', r['content'])
        if numbers:
            print(f"   📊 Numbers found: {numbers[:10]}...")
        print()
    
    # Check for specific stud queries
    print("\n" + "=" * 80)
    print("🔎 Searching for STUD SIZE content (90mm, 140mm studs)...")
    print("=" * 80)
    
    cursor.execute("""
        SELECT id, content
        FROM document_chunks
        WHERE source ILIKE '%3604%'
        AND (
            content ILIKE '%90%stud%'
            OR content ILIKE '%stud%90%'
            OR content ILIKE '%140%stud%'
            OR content ILIKE '%stud size%'
            OR content ILIKE '%wall stud%'
        )
        LIMIT 10
    """)
    
    stud_results = cursor.fetchall()
    print(f"\n✅ Found {len(stud_results)} chunks mentioning stud sizes:\n")
    
    for i, r in enumerate(stud_results, 1):
        print(f"--- Stud Chunk {i} ---")
        preview = r['content'][:400].replace('\n', ' ')
        print(f"   {preview}...")
        print()
    
    # Final diagnosis
    print("\n" + "=" * 80)
    print("📋 DIAGNOSIS SUMMARY")
    print("=" * 80)
    
    if len(results) < 5:
        print("⚠️  LOW Section 8 content - possible ingestion gap")
    else:
        print("✅ Section 8 content exists")
    
    if len(table_results) < 3:
        print("❌ TABLE BLINDNESS CONFIRMED - Very few table data chunks found")
        print("   → Tables were likely not parsed properly during ingestion")
    else:
        print("✅ Some table data exists")
    
    if len(stud_results) < 3:
        print("⚠️  LIMITED stud-related content - may need re-ingestion")
    
    conn.close()
    print("\n✅ Diagnostic complete")

if __name__ == "__main__":
    inspect_section8_chunks()
