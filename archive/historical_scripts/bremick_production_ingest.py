#!/usr/bin/env python3
"""
STRYDA PRODUCTION BUILD - Bremick Ingestion
Ingest 287 Bremick TDS files into vector database
"""
import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path

# Unbuffered logging
sys.stdout = open('/app/bremick_ingestion.log', 'w', buffering=1)
sys.stderr = sys.stdout

print("=" * 80)
print("        STRYDA PRODUCTION BUILD - BREMICK INGESTION")
print(f"        Started: {datetime.now().isoformat()}")
print("=" * 80)

# Load environment
env_file = Path('/app/backend-minimal/.env')
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            key, val = line.split('=', 1)
            os.environ[key.strip()] = val.strip()

import fitz  # PyMuPDF
import psycopg2
import openai
from supabase import create_client

# Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
OPENAI_KEY = os.getenv('OPENAI_API_KEY')

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
BUCKET = "product-library"
BREMICK_BASE = "F_Manufacturers/Fasteners/Bremick"

# Initialize clients
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = openai.OpenAI(api_key=OPENAI_KEY)

print(f"\n✅ Clients initialized")
print(f"   Chunk size: {CHUNK_SIZE} chars")
print(f"   Overlap: {CHUNK_OVERLAP} chars")
print(f"   Embedding model: text-embedding-3-small")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_embedding(text):
    """Generate embedding using OpenAI text-embedding-3-small"""
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text[:8000],
            dimensions=1536
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"      ⚠️ Embedding error: {str(e)[:50]}")
        return None

def extract_text_from_pdf(pdf_bytes):
    """Extract text from PDF using PyMuPDF"""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        pages = len(doc)
        doc.close()
        # Remove NUL characters
        text = text.replace('\x00', '')
        return text, pages
    except Exception as e:
        print(f"      ⚠️ PDF extraction error: {str(e)[:50]}")
        return "", 0

def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into overlapping chunks"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap
    return chunks

def get_product_name(filename):
    """Extract clean product name from filename"""
    name = filename.replace('.pdf', '').replace('-', ' ').replace('_', ' ')
    # Title case
    name = ' '.join(word.capitalize() for word in name.split())
    return name[:80]

# ============================================================================
# SCAN BREMICK FILES
# ============================================================================

print(f"\n{'='*80}")
print("   PHASE 1: SCANNING BREMICK FILES IN STORAGE")
print("="*80)

# Get all subfolders
subfolders = [
    "Chemical_Anchors", "Drop_In_Anchors", "Galvanised", "General",
    "Hex_Bolts", "Hex_Nuts", "Sleeve_Anchors", "Stainless_Steel",
    "Washers", "Zinc_Plated"
]

all_files = []

for subfolder in subfolders:
    folder_path = f"{BREMICK_BASE}/{subfolder}"
    try:
        items = supabase.storage.from_(BUCKET).list(folder_path, {'limit': 500})
        pdfs = [{'name': i['name'], 'path': f"{folder_path}/{i['name']}", 'subfolder': subfolder} 
                for i in items if i['name'].lower().endswith('.pdf')]
        all_files.extend(pdfs)
        print(f"   📂 {subfolder}: {len(pdfs)} files")
    except Exception as e:
        print(f"   ⚠️ {subfolder}: Error - {str(e)[:30]}")

print(f"\n   📊 TOTAL FILES TO INGEST: {len(all_files)}")

# ============================================================================
# INGESTION LOOP
# ============================================================================

print(f"\n{'='*80}")
print("   PHASE 2: CHUNK, EMBED & PUSH TO DATABASE")
print("="*80)

stats = {
    'processed': 0,
    'chunks_created': 0,
    'errors': 0,
    'skipped': 0
}

register_entries = []

for i, file_info in enumerate(all_files, 1):
    filename = file_info['name']
    filepath = file_info['path']
    subfolder = file_info['subfolder']
    
    print(f"\n[{i:3}/{len(all_files)}] {filename[:50]}...", flush=True)
    
    try:
        # Download PDF
        pdf_data = supabase.storage.from_(BUCKET).download(filepath)
        if not pdf_data:
            print(f"      ⏭️ Skip: Download failed")
            stats['skipped'] += 1
            continue
        
        # Extract text
        text, pages = extract_text_from_pdf(pdf_data)
        if not text or len(text) < 100:
            print(f"      ⏭️ Skip: No/little text extracted")
            stats['skipped'] += 1
            continue
        
        # Generate content hash for deduplication
        content_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        
        # Chunk text
        chunks = chunk_text(text)
        print(f"      📄 {pages} pages, {len(text)} chars → {len(chunks)} chunks")
        
        # Get product name for source field
        product_name = get_product_name(filename)
        source_name = f"Bremick - {product_name}"
        
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cur = conn.cursor()
        
        # Check if already exists
        cur.execute("SELECT 1 FROM documents WHERE page_hash LIKE %s LIMIT 1", (f"{content_hash}%",))
        if cur.fetchone():
            print(f"      ⏭️ Skip: Already in database")
            stats['skipped'] += 1
            conn.close()
            continue
        
        # Process each chunk
        chunks_inserted = 0
        for ci, chunk in enumerate(chunks):
            # Get embedding
            embedding = get_embedding(chunk)
            if not embedding:
                continue
            
            # Insert into database
            try:
                cur.execute("""
                    INSERT INTO documents (
                        content, source, page, embedding, page_hash, chunk_hash,
                        trade, priority, is_active, doc_type, hierarchy_level
                    )
                    VALUES (%s, %s, %s, %s::vector, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    chunk,
                    source_name,
                    ci + 1,
                    embedding,
                    f"{content_hash}_{ci}",
                    hashlib.md5(chunk.encode()).hexdigest()[:12],
                    'fasteners',
                    85,  # High priority for TDS
                    True,
                    'Technical_Data_Sheet',
                    4  # Tier 4: Manufacturer
                ))
                chunks_inserted += 1
            except Exception as e:
                print(f"      ⚠️ Insert error chunk {ci}: {str(e)[:40]}")
        
        conn.commit()
        conn.close()
        
        if chunks_inserted > 0:
            stats['processed'] += 1
            stats['chunks_created'] += chunks_inserted
            print(f"      ✅ Ingested {chunks_inserted} chunks")
            
            # Add to register
            register_entries.append({
                'brand': 'Bremick',
                'product': filename,
                'sector': 'fasteners',
                'status': 'CERTIFIED'
            })
        
    except Exception as e:
        print(f"      ❌ Error: {str(e)[:60]}")
        stats['errors'] += 1
    
    # Checkpoint every 50 files
    if i % 50 == 0:
        print(f"\n   📊 CHECKPOINT [{i}/{len(all_files)}]")
        print(f"      Processed: {stats['processed']}")
        print(f"      Chunks: {stats['chunks_created']}")
        print(f"      Errors: {stats['errors']}")
        print(f"      Skipped: {stats['skipped']}\n", flush=True)

# ============================================================================
# UPDATE COMPLIANCE REGISTER
# ============================================================================

print(f"\n{'='*80}")
print("   PHASE 3: UPDATE COMPLIANCE MASTER REGISTER")
print("="*80)

import csv

register_path = '/app/protocols/Compliance_Master_Register.csv'

# Read existing register
existing_entries = []
try:
    with open(register_path, 'r') as f:
        reader = csv.DictReader(f)
        existing_entries = list(reader)
    print(f"   📋 Existing entries: {len(existing_entries)}")
except:
    print(f"   📋 Creating new register")

# Add new Bremick entries
all_entries = existing_entries + register_entries

# Write updated register
with open(register_path, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['brand', 'product', 'sector', 'status'])
    writer.writeheader()
    writer.writerows(all_entries)

print(f"   ✅ Added {len(register_entries)} Bremick entries")
print(f"   📊 Total register entries: {len(all_entries)}")

# ============================================================================
# FINAL REPORT
# ============================================================================

print(f"\n{'='*80}")
print("        STRYDA PRODUCTION BUILD - COMPLETE")
print("="*80)
print(f"\n📊 FINAL STATISTICS:")
print(f"   Files Processed: {stats['processed']}")
print(f"   Chunks Created: {stats['chunks_created']}")
print(f"   Files Skipped: {stats['skipped']}")
print(f"   Errors: {stats['errors']}")
print(f"\n📋 REGISTER:")
print(f"   New CERTIFIED entries: {len(register_entries)}")
print(f"\n⏱️ Completed: {datetime.now().isoformat()}")
print("="*80)

# Save detailed report
report = {
    'completed': datetime.now().isoformat(),
    'files_processed': stats['processed'],
    'chunks_created': stats['chunks_created'],
    'files_skipped': stats['skipped'],
    'errors': stats['errors'],
    'register_entries_added': len(register_entries)
}
with open('/app/bremick_ingestion_report.json', 'w') as f:
    json.dump(report, f, indent=2)

print(f"\n✅ Report saved to /app/bremick_ingestion_report.json")
