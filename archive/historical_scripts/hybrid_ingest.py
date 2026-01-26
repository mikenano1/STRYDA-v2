#!/usr/bin/env python3
"""
STRYDA V2.5 HYBRID OCR INGESTION
Protocol: /protocols/PARSING_STANDARD_V2_5.md

Smart Switch Logic:
- Text Layer PDFs → PyMuPDF extraction
- Image/Scan PDFs → OCR via Tesseract
- All Tables → Context Injection
"""
import os
import sys
import json
import hashlib
import re
from datetime import datetime
from pathlib import Path
from io import BytesIO

# Unbuffered logging
sys.stdout = open('/app/hybrid_ingestion.log', 'w', buffering=1)
sys.stderr = sys.stdout

print("=" * 80, flush=True)
print("   ⚡ STRYDA V2.5 HYBRID OCR INGESTION", flush=True)
print(f"   Started: {datetime.now().isoformat()}", flush=True)
print("   Protocol: PARSING_STANDARD_V2_5.md", flush=True)
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
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image

# Config
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
OPENAI_KEY = os.getenv('OPENAI_API_KEY')

MIN_TEXT_THRESHOLD = 50  # If less than this, use OCR

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = openai.OpenAI(api_key=OPENAI_KEY)

print(f"\n✅ Hybrid Engine initialized", flush=True)
print(f"   OCR Engine: Tesseract {pytesseract.get_tesseract_version()}", flush=True)
print(f"   Text threshold: {MIN_TEXT_THRESHOLD} chars", flush=True)

# ============================================================================
# SMART SWITCH: TEXT vs OCR
# ============================================================================

def extract_hybrid(pdf_bytes, product_name):
    """
    Smart Switch: Try text extraction first, fall back to OCR.
    Returns (chunks, pages, tables_found, method_used)
    """
    # First, try PyMuPDF text extraction
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text_content = []
        total_text = ""
        
        for page in doc:
            page_text = page.get_text()
            text_content.append(page_text)
            total_text += page_text
        
        pages = len(doc)
        doc.close()
        
        # SMART SWITCH: Check if we got enough text
        if len(total_text.strip()) >= MIN_TEXT_THRESHOLD:
            # Text layer exists - use PyMuPDF
            chunks, tables = process_text_content(text_content, product_name)
            return chunks, pages, tables, "TEXT_LAYER"
        else:
            # Image-only PDF - use OCR
            chunks, tables = process_with_ocr(pdf_bytes, product_name)
            return chunks, pages, tables, "OCR_TESSERACT"
            
    except Exception as e:
        print(f"      ⚠️ Extraction error: {str(e)[:50]}", flush=True)
        return [], 0, 0, "ERROR"


def process_text_content(text_pages, product_name):
    """Process text-layer PDF content."""
    all_chunks = []
    tables_found = 0
    
    full_text = '\n\n'.join(text_pages).replace('\x00', '')
    
    # Detect and process tables
    tables = detect_tables_from_text(full_text)
    for table in tables:
        context_chunks = parse_table_with_context(table, product_name)
        all_chunks.extend(context_chunks)
        if context_chunks:
            tables_found += 1
    
    # Chunk remaining text with context
    text_chunks = chunk_with_context(full_text, product_name)
    all_chunks.extend(text_chunks)
    
    return all_chunks, tables_found


def process_with_ocr(pdf_bytes, product_name):
    """OCR processing for image-only PDFs."""
    all_chunks = []
    tables_found = 0
    
    try:
        # Convert PDF to images
        images = convert_from_bytes(pdf_bytes, dpi=300)
        
        all_text = []
        for i, img in enumerate(images):
            # OCR each page
            page_text = pytesseract.image_to_string(img, config='--psm 6')
            all_text.append(page_text)
            
            # Try to detect tables from OCR output
            tables = detect_tables_from_text(page_text)
            for table in tables:
                context_chunks = parse_table_with_context(table, product_name)
                all_chunks.extend(context_chunks)
                if context_chunks:
                    tables_found += 1
        
        # Combine and chunk text
        full_text = '\n\n'.join(all_text).replace('\x00', '')
        text_chunks = chunk_with_context(full_text, product_name)
        all_chunks.extend(text_chunks)
        
    except Exception as e:
        print(f"      ⚠️ OCR error: {str(e)[:50]}", flush=True)
    
    return all_chunks, tables_found


# ============================================================================
# CONTEXT INJECTION (God-Tier Logic)
# ============================================================================

def parse_table_with_context(table_data, product_context):
    """Context Injection: Glue Row/Col headers to every cell."""
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


def detect_tables_from_text(text):
    """Detect table structures from OCR text."""
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
        
        # Split by multiple spaces or tabs
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
        if chunk and len(chunk) > 20:
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

print(f"\n📂 Scanning Bremick files...", flush=True)

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

bremick_files = scan_folder('product-library', 'F_Manufacturers/Fasteners/Bremick')
total_files = len(bremick_files)

print(f"   🔩 Found {total_files} Bremick files", flush=True)
print("=" * 80, flush=True)

# ============================================================================
# HYBRID INGESTION LOOP
# ============================================================================

stats = {
    'processed': 0, 
    'chunks': 0, 
    'context_chunks': 0, 
    'tables': 0, 
    'text_layer': 0,
    'ocr_used': 0,
    'errors': 0, 
    'skipped': 0
}
register_entries = []

for i, file_info in enumerate(bremick_files, 1):
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
        full_product = f"Bremick - {product}"
        
        # HYBRID EXTRACTION (Smart Switch)
        chunks, pages, tables, method = extract_hybrid(pdf_data, full_product)
        
        if not chunks:
            print(f"      ⏭️ Skip: No content extracted", flush=True)
            stats['skipped'] += 1
            continue
        
        # Track method used
        if method == "TEXT_LAYER":
            stats['text_layer'] += 1
        elif method == "OCR_TESSERACT":
            stats['ocr_used'] += 1
        
        stats['tables'] += tables
        context_count = len([c for c in chunks if c.startswith('Context:')])
        stats['context_chunks'] += context_count
        
        print(f"      📄 {pages}p | {len(chunks)} chunks | {context_count} ctx | {tables} tbl | [{method}]", flush=True)
        
        # Dedupe
        content_hash = hashlib.sha256(''.join(chunks[:5]).encode()).hexdigest()[:16]
        
        # DB insert
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cur = conn.cursor()
        
        # Check exists
        cur.execute("SELECT 1 FROM documents WHERE page_hash LIKE %s LIMIT 1", (f"{content_hash}%",))
        if cur.fetchone():
            print(f"      ⏭️ Skip: Already exists", flush=True)
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
                    'fasteners', 90, True, 'Technical_Data_Sheet', 4
                ))
                inserted += 1
            except:
                pass
        
        conn.commit()
        conn.close()
        
        if inserted > 0:
            stats['processed'] += 1
            stats['chunks'] += inserted
            print(f"      ✅ Ingested {inserted} chunks", flush=True)
            
            register_entries.append({
                'brand': 'Bremick',
                'product': filename,
                'sector': 'fasteners',
                'status': 'CERTIFIED'
            })
        
    except Exception as e:
        print(f"      ❌ Error: {str(e)[:50]}", flush=True)
        stats['errors'] += 1
    
    # Checkpoint
    if i % 25 == 0:
        print(f"\n📊 CHECKPOINT [{i}/{total_files}]", flush=True)
        print(f"   Processed: {stats['processed']} | Text: {stats['text_layer']} | OCR: {stats['ocr_used']}", flush=True)
        print(f"   Chunks: {stats['chunks']} | Context: {stats['context_chunks']} | Tables: {stats['tables']}", flush=True)

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
print(f"   ⚡ V2.5 HYBRID INGESTION - COMPLETE", flush=True)
print(f"{'='*80}", flush=True)
print(f"   ✅ Files Processed: {stats['processed']}", flush=True)
print(f"   📄 Total Chunks: {stats['chunks']}", flush=True)
print(f"   🎯 Context-Injected: {stats['context_chunks']}", flush=True)
print(f"   📊 Tables Parsed: {stats['tables']}", flush=True)
print(f"   📝 Text Layer: {stats['text_layer']}", flush=True)
print(f"   🔍 OCR Used: {stats['ocr_used']}", flush=True)
print(f"   ⏭️ Skipped: {stats['skipped']}", flush=True)
print(f"   ❌ Errors: {stats['errors']}", flush=True)
print(f"   📋 Register Added: {len(register_entries)}", flush=True)
print(f"\n   Protocol: V2.5 HYBRID OCR", flush=True)
print(f"   Completed: {datetime.now().isoformat()}", flush=True)
print("=" * 80, flush=True)

with open('/app/hybrid_report.json', 'w') as f:
    json.dump({**stats, 'register': len(register_entries), 'completed': datetime.now().isoformat()}, f, indent=2)
