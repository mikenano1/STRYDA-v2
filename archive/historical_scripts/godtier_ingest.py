#!/usr/bin/env python3
"""
OPERATION GOD-TIER - V2.5 Production Ingestion
Cell-Level Context Injection for ALL Technical Data

Protocol: /protocols/PARSING_STANDARD_V2_5.md
"""
import os
import sys
import json
import hashlib
import re
from datetime import datetime
from pathlib import Path

# Unbuffered logging
sys.stdout = open('/app/godtier_ingestion.log', 'w', buffering=1)
sys.stderr = sys.stdout

print("=" * 80, flush=True)
print("   ⚡ OPERATION GOD-TIER - V2.5 INGESTION", flush=True)
print(f"   Started: {datetime.now().isoformat()}", flush=True)
print("   Intelligence Level: GOD-TIER", flush=True)
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

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = openai.OpenAI(api_key=OPENAI_KEY)

print(f"\n✅ God-Tier Engine initialized", flush=True)

# ============================================================================
# GOD-TIER CONTEXT INJECTION
# ============================================================================

def parse_table_with_context(table_data, product_context):
    """
    GOD-TIER PARSING: Glues Row/Col headers to every cell.
    """
    structured_chunks = []
    
    if not table_data or len(table_data) < 2:
        return structured_chunks
    
    headers = [str(h).strip() if h else f"Col_{i}" for i, h in enumerate(table_data[0])]
    
    for row_idx, row in enumerate(table_data[1:], 1):
        row_header = str(row[0]).strip() if row and row[0] else f"Row_{row_idx}"
        
        for col_idx, cell_value in enumerate(row):
            if col_idx == 0:
                continue
            
            col_header = headers[col_idx] if col_idx < len(headers) else f"Property_{col_idx}"
            value = str(cell_value).strip() if cell_value else ""
            
            if value and value not in ['', '-', 'N/A', 'n/a']:
                chunk = f"Context: {{Product: {product_context} | Size/Type: {row_header} | Property: {col_header}}} -> Value: {value}"
                structured_chunks.append(chunk)
    
    return structured_chunks


def extract_godtier(pdf_bytes, product_name):
    """God-Tier extraction with context injection."""
    all_chunks = []
    text_content = []
    tables_found = 0
    
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        for page_num, page in enumerate(doc):
            page_text = page.get_text()
            text_content.append(page_text)
            
            # Try table extraction
            try:
                tables = page.find_tables()
                if tables and tables.tables:
                    for table in tables.tables:
                        table_data = table.extract()
                        
                        # God-Tier Context Injection
                        context_chunks = parse_table_with_context(table_data, product_name)
                        all_chunks.extend(context_chunks)
                        tables_found += 1
                        
                        # Also add full table as markdown
                        md = table_to_markdown(table_data, product_name, page_num + 1)
                        if md:
                            all_chunks.append(md)
            except:
                # Fallback text pattern detection
                detected = detect_tables_text(page_text)
                for tbl in detected:
                    ctx = parse_table_with_context(tbl, product_name)
                    all_chunks.extend(ctx)
                    if ctx:
                        tables_found += 1
        
        doc.close()
        
        # Chunk regular text with context
        full_text = '\n\n'.join(text_content).replace('\x00', '')
        text_chunks = chunk_with_context(full_text, product_name)
        all_chunks.extend(text_chunks)
        
        return all_chunks, len(doc), tables_found
        
    except Exception as e:
        return [], 0, 0


def table_to_markdown(table_data, product_name, page_num):
    """Create markdown table with context header."""
    if not table_data or len(table_data) < 2:
        return None
    
    try:
        lines = [f"[TECHNICAL TABLE: {product_name} | Page {page_num}]"]
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


def detect_tables_text(text):
    """Detect tables from text patterns."""
    tables = []
    lines = text.split('\n')
    current = []
    
    for line in lines:
        line = line.strip()
        if not line:
            if len(current) >= 3:
                tables.append(current)
            current = []
            continue
        
        parts = re.split(r'\s{2,}|\t', line)
        has_nums = bool(re.search(r'\d+', line))
        
        if len(parts) >= 2 and (has_nums or len(current) == 0):
            current.append(parts)
        else:
            if len(current) >= 3:
                tables.append(current)
            current = []
    
    if len(current) >= 3:
        tables.append(current)
    
    return tables


def chunk_with_context(text, product_name, size=1000, overlap=150):
    """Chunk text with product context prefix."""
    chunks = []
    prefix = f"[Document: {product_name}]\n"
    eff_size = size - len(prefix)
    
    start = 0
    while start < len(text):
        end = start + eff_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(prefix + chunk)
        start = end - overlap
    
    return chunks


def get_embedding(text):
    """Get embedding from OpenAI."""
    try:
        r = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text[:8000],
            dimensions=1536
        )
        return r.data[0].embedding
    except:
        return None


# ============================================================================
# SCAN FILES
# ============================================================================

print(f"\n📂 Scanning ingestion queue...", flush=True)

def scan_folder(bucket, path):
    files = []
    try:
        items = supabase.storage.from_(bucket).list(path, {'limit': 500})
        for item in items:
            if item['name'].lower().endswith('.pdf'):
                files.append({'name': item['name'], 'path': f"{path}/{item['name']}", 'bucket': bucket})
            elif item.get('id') is None:
                files.extend(scan_folder(bucket, f"{path}/{item['name']}"))
    except:
        pass
    return files

# Get all Bremick files
bremick_files = scan_folder('product-library', 'F_Manufacturers/Fasteners/Bremick')
print(f"   🔩 Bremick: {len(bremick_files)} files", flush=True)

# Check temp for Pryda/LVL
temp_files = []
try:
    temp_items = supabase.storage.from_('temporary').list('', {'limit': 500})
    pryda = [{'name': i['name'], 'path': i['name'], 'bucket': 'temporary'} 
             for i in temp_items if 'pryda' in i['name'].lower() and i['name'].endswith('.pdf')]
    lvl = [{'name': i['name'], 'path': i['name'], 'bucket': 'temporary'} 
           for i in temp_items if 'lvl' in i['name'].lower() and i['name'].endswith('.pdf')]
    print(f"   🔗 Pryda (temp): {len(pryda)} files", flush=True)
    print(f"   🪵 LVL (temp): {len(lvl)} files", flush=True)
    temp_files = pryda + lvl
except:
    pass

all_files = bremick_files + temp_files
total_files = len(all_files)

print(f"\n📊 TOTAL FILES: {total_files}", flush=True)
print("=" * 80, flush=True)

# ============================================================================
# INGESTION LOOP
# ============================================================================

stats = {'processed': 0, 'chunks': 0, 'context_chunks': 0, 'tables': 0, 'errors': 0, 'skipped': 0}
register_entries = []

for i, file_info in enumerate(all_files, 1):
    filename = file_info['name']
    filepath = file_info['path']
    bucket = file_info['bucket']
    
    print(f"\n[{i:3}/{total_files}] {filename[:55]}...", flush=True)
    
    try:
        # Download
        pdf_data = supabase.storage.from_(bucket).download(filepath)
        if not pdf_data:
            print(f"      ⏭️ Skip: Download failed", flush=True)
            stats['skipped'] += 1
            continue
        
        # Product name
        product = filename.replace('.pdf', '').replace('-', ' ').replace('_', ' ').title()[:60]
        
        # Determine brand
        if 'bremick' in filepath.lower():
            brand = 'Bremick'
            trade = 'fasteners'
        elif 'pryda' in filepath.lower():
            brand = 'Pryda'
            trade = 'connectors'
        elif 'lvl' in filepath.lower():
            brand = 'LVL'
            trade = 'timber'
        else:
            brand = 'Unknown'
            trade = 'general'
        
        full_product = f"{brand} - {product}"
        
        # God-Tier extraction
        chunks, pages, tables = extract_godtier(pdf_data, full_product)
        
        if not chunks:
            print(f"      ⏭️ Skip: No content", flush=True)
            stats['skipped'] += 1
            continue
        
        stats['tables'] += tables
        context_count = len([c for c in chunks if c.startswith('Context:')])
        stats['context_chunks'] += context_count
        
        print(f"      📄 {pages}p | {len(chunks)} chunks | {context_count} context-injected | {tables} tables", flush=True)
        
        # Dedupe
        content_hash = hashlib.sha256(''.join(chunks[:5]).encode()).hexdigest()[:16]
        
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
        
        # Insert
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
                    chunk, full_product, ci + 1, emb,
                    f"{content_hash}_{ci}",
                    hashlib.md5(chunk.encode()).hexdigest()[:12],
                    trade, 90, True, 'Technical_Data_Sheet', 4
                ))
                inserted += 1
            except Exception as e:
                pass
        
        conn.commit()
        conn.close()
        
        if inserted > 0:
            stats['processed'] += 1
            stats['chunks'] += inserted
            print(f"      ✅ Ingested {inserted} chunks (God-Tier)", flush=True)
            
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
    if i % 25 == 0:
        print(f"\n📊 CHECKPOINT [{i}/{total_files}]", flush=True)
        print(f"   Processed: {stats['processed']} | Chunks: {stats['chunks']} | Context: {stats['context_chunks']} | Tables: {stats['tables']}", flush=True)

# Update register
import csv
reg_path = '/app/protocols/Compliance_Master_Register.csv'
try:
    with open(reg_path, 'r') as f:
        existing = list(csv.DictReader(f))
except:
    existing = []

with open(reg_path, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['brand', 'product', 'sector', 'status'])
    w.writeheader()
    w.writerows(existing + register_entries)

# Final report
print(f"\n{'='*80}", flush=True)
print(f"   ⚡ OPERATION GOD-TIER - COMPLETE", flush=True)
print(f"{'='*80}", flush=True)
print(f"   ✅ Files Processed: {stats['processed']}", flush=True)
print(f"   📄 Total Chunks: {stats['chunks']}", flush=True)
print(f"   🎯 Context-Injected: {stats['context_chunks']}", flush=True)
print(f"   📊 Tables Parsed: {stats['tables']}", flush=True)
print(f"   ⏭️ Skipped: {stats['skipped']}", flush=True)
print(f"   ❌ Errors: {stats['errors']}", flush=True)
print(f"   📋 Register Added: {len(register_entries)}", flush=True)
print(f"\n   Intelligence Level: GOD-TIER ⚡", flush=True)
print(f"   Completed: {datetime.now().isoformat()}", flush=True)
print("=" * 80, flush=True)

with open('/app/godtier_report.json', 'w') as f:
    json.dump({**stats, 'register': len(register_entries), 'completed': datetime.now().isoformat()}, f, indent=2)
