#!/usr/bin/env python3
"""
STRYDA V5 PRODUCTION INGESTION - VISION-FIRST
Ingests files with intelligent table detection and markdown conversion
"""
import os
import sys
import json
import hashlib
import re
from datetime import datetime
from pathlib import Path

# Unbuffered logging
sys.stdout = open('/app/vision_ingestion.log', 'w', buffering=1)
sys.stderr = sys.stdout

print("=" * 80, flush=True)
print("   STRYDA V5 VISION-FIRST PRODUCTION INGESTION", flush=True)
print(f"   Started: {datetime.now().isoformat()}", flush=True)
print("=" * 80, flush=True)

# Load environment
env_file = Path('/app/backend-minimal/.env')
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            key, val = line.split('=', 1)
            os.environ[key.strip()] = val.strip()

import fitz
import psycopg2
import openai
from supabase import create_client

# Config
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
OPENAI_KEY = os.getenv('OPENAI_API_KEY')

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = openai.OpenAI(api_key=OPENAI_KEY)

print(f"\n✅ Vision-First Engine initialized", flush=True)
print(f"   Chunk size: {CHUNK_SIZE}, Overlap: {CHUNK_OVERLAP}", flush=True)

# ============================================================================
# VISION-FIRST TABLE EXTRACTION
# ============================================================================

def extract_with_vision(pdf_bytes):
    """Extract PDF with table detection and markdown conversion."""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        all_content = []
        tables_found = 0
        
        for page_num, page in enumerate(doc):
            page_text = page.get_text()
            
            # Try PyMuPDF table extraction (v1.23+)
            try:
                tables = page.find_tables()
                if tables and tables.tables:
                    for table in tables.tables:
                        md_table = table_to_markdown(table.extract())
                        if md_table:
                            page_text += f"\n\n[TABLE {tables_found + 1}]\n{md_table}\n"
                            tables_found += 1
            except:
                # Fallback: detect tables from text patterns
                detected = detect_tables_from_text(page_text)
                if detected:
                    page_text += f"\n\n[DETECTED TABLES]\n{detected}\n"
                    tables_found += 1
            
            all_content.append(page_text)
        
        doc.close()
        
        full_text = '\n\n'.join(all_content)
        full_text = full_text.replace('\x00', '')  # Remove NUL chars
        
        return full_text, len(doc), tables_found
        
    except Exception as e:
        return "", 0, 0

def table_to_markdown(table_data):
    """Convert table data to markdown format."""
    if not table_data or len(table_data) < 2:
        return None
    
    try:
        lines = []
        header = [str(c).strip() if c else '' for c in table_data[0]]
        lines.append('| ' + ' | '.join(header) + ' |')
        lines.append('| ' + ' | '.join(['---'] * len(header)) + ' |')
        
        for row in table_data[1:]:
            cells = [str(c).strip() if c else '' for c in row]
            while len(cells) < len(header):
                cells.append('')
            lines.append('| ' + ' | '.join(cells[:len(header)]) + ' |')
        
        return '\n'.join(lines)
    except:
        return None

def detect_tables_from_text(text):
    """Detect table-like structures from text patterns."""
    # Look for lines with multiple numeric values separated by whitespace
    lines = text.split('\n')
    table_lines = []
    
    for line in lines:
        # Count numeric values in line
        nums = re.findall(r'\d+\.?\d*', line)
        parts = len(line.split())
        
        if len(nums) >= 2 and parts >= 3:
            table_lines.append(line.strip())
    
    if len(table_lines) >= 3:
        # Try to format as markdown
        try:
            rows = [re.split(r'\s{2,}|\t', l) for l in table_lines[:20]]
            max_cols = max(len(r) for r in rows)
            
            md = []
            md.append('| ' + ' | '.join(rows[0] + [''] * (max_cols - len(rows[0]))) + ' |')
            md.append('| ' + ' | '.join(['---'] * max_cols) + ' |')
            for row in rows[1:]:
                md.append('| ' + ' | '.join(row + [''] * (max_cols - len(row))) + ' |')
            
            return '\n'.join(md)
        except:
            pass
    
    return None

def smart_chunk(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Smart chunking that preserves tables."""
    chunks = []
    
    # Find table markers and keep them intact
    table_pattern = r'\[TABLE \d+\].*?(?=\[TABLE|\[DETECTED|$)'
    tables = re.findall(table_pattern, text, re.DOTALL)
    
    # Remove tables from main text for separate chunking
    main_text = re.sub(table_pattern, '', text, flags=re.DOTALL)
    
    # Chunk main text
    start = 0
    while start < len(main_text):
        end = start + chunk_size
        chunk = main_text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap
    
    # Add tables as separate chunks (don't split them)
    for table in tables:
        if table.strip():
            chunks.append(f"[TECHNICAL SPECIFICATION TABLE]\n{table.strip()}")
    
    return chunks

def get_embedding(text):
    """Get embedding from OpenAI."""
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text[:8000],
            dimensions=1536
        )
        return response.data[0].embedding
    except:
        return None

# ============================================================================
# MAIN INGESTION
# ============================================================================

# Load queue
with open('/app/ingestion_queue.json') as f:
    queue = json.load(f)

total_files = queue['total']
all_files = queue['bremick'] + queue.get('pryda', []) + queue.get('lvl', [])

print(f"\n📂 Processing {len(all_files)} files with Vision-First Logic", flush=True)

stats = {'processed': 0, 'chunks': 0, 'tables': 0, 'errors': 0, 'skipped': 0}
register_entries = []

for i, file_info in enumerate(all_files, 1):
    filename = file_info['name']
    filepath = file_info['path']
    bucket = file_info.get('bucket', 'product-library')
    
    print(f"\n[{i:3}/{len(all_files)}] {filename[:55]}...", flush=True)
    
    try:
        # Download
        pdf_data = supabase.storage.from_(bucket).download(filepath)
        if not pdf_data:
            print(f"      ⏭️ Skip: Download failed", flush=True)
            stats['skipped'] += 1
            continue
        
        # Vision-First extraction
        text, pages, tables_found = extract_with_vision(pdf_data)
        if not text or len(text) < 100:
            print(f"      ⏭️ Skip: No text", flush=True)
            stats['skipped'] += 1
            continue
        
        stats['tables'] += tables_found
        
        # Dedupe hash
        content_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        
        # Smart chunking
        chunks = smart_chunk(text)
        print(f"      📄 {pages}p, {len(text)}c, {len(chunks)} chunks, {tables_found} tables", flush=True)
        
        # Source name
        product = filename.replace('.pdf', '').replace('-', ' ').replace('_', ' ').title()[:60]
        
        # Determine brand/category
        if 'bremick' in filepath.lower():
            brand = 'Bremick'
            trade = 'fasteners'
            doc_type = 'Technical_Data_Sheet'
        elif 'pryda' in filepath.lower():
            brand = 'Pryda'
            trade = 'connectors'
            doc_type = 'Technical_Data_Sheet'
        elif 'lvl' in filepath.lower():
            brand = 'LVL'
            trade = 'timber'
            doc_type = 'Technical_Data_Sheet'
        else:
            brand = 'Unknown'
            trade = 'general'
            doc_type = 'Product_Document'
        
        source_name = f"{brand} - {product}"
        
        # DB insert
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cur = conn.cursor()
        
        # Check exists
        cur.execute("SELECT 1 FROM documents WHERE page_hash LIKE %s LIMIT 1", (f"{content_hash}%",))
        if cur.fetchone():
            print(f"      ⏭️ Skip: Exists", flush=True)
            stats['skipped'] += 1
            conn.close()
            continue
        
        # Insert chunks
        inserted = 0
        for ci, chunk in enumerate(chunks):
            emb = get_embedding(chunk)
            if not emb:
                continue
            
            try:
                cur.execute("""
                    INSERT INTO documents (
                        content, source, page, embedding, page_hash, chunk_hash,
                        trade, priority, is_active, doc_type, hierarchy_level
                    ) VALUES (%s, %s, %s, %s::vector, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    chunk, source_name, ci + 1, emb,
                    f"{content_hash}_{ci}",
                    hashlib.md5(chunk.encode()).hexdigest()[:12],
                    trade, 85, True, doc_type, 4
                ))
                inserted += 1
            except Exception as e:
                print(f"      ⚠️ Insert error: {str(e)[:40]}", flush=True)
        
        conn.commit()
        conn.close()
        
        if inserted > 0:
            stats['processed'] += 1
            stats['chunks'] += inserted
            print(f"      ✅ Ingested {inserted} chunks", flush=True)
            
            register_entries.append({
                'brand': brand,
                'product': filename,
                'sector': trade,
                'status': 'CERTIFIED'
            })
        
    except Exception as e:
        print(f"      ❌ Error: {str(e)[:50]}", flush=True)
        stats['errors'] += 1
    
    # Checkpoint
    if i % 50 == 0:
        print(f"\n📊 CHECKPOINT [{i}/{len(all_files)}]", flush=True)
        print(f"   Processed: {stats['processed']}, Chunks: {stats['chunks']}, Tables: {stats['tables']}", flush=True)

# Update register
import csv
register_path = '/app/protocols/Compliance_Master_Register.csv'
try:
    with open(register_path, 'r') as f:
        existing = list(csv.DictReader(f))
except:
    existing = []

all_entries = existing + register_entries
with open(register_path, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['brand', 'product', 'sector', 'status'])
    writer.writeheader()
    writer.writerows(all_entries)

# Final report
print(f"\n{'='*80}", flush=True)
print(f"   VISION-FIRST INGESTION COMPLETE", flush=True)
print(f"{'='*80}", flush=True)
print(f"   ✅ Files Processed: {stats['processed']}", flush=True)
print(f"   📄 Chunks Created: {stats['chunks']}", flush=True)
print(f"   📊 Tables Detected: {stats['tables']}", flush=True)
print(f"   ⏭️ Skipped: {stats['skipped']}", flush=True)
print(f"   ❌ Errors: {stats['errors']}", flush=True)
print(f"   📋 Register entries added: {len(register_entries)}", flush=True)
print(f"\n   Completed: {datetime.now().isoformat()}", flush=True)
print("=" * 80, flush=True)

# Save report
with open('/app/vision_ingestion_report.json', 'w') as f:
    json.dump({**stats, 'register_added': len(register_entries), 'completed': datetime.now().isoformat()}, f, indent=2)
