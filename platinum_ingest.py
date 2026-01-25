#!/usr/bin/env python3
"""
STRYDA V3.0 PLATINUM INGESTION ENGINE
Cloud Vision API using Gemini Flash

Protocol: /protocols/INGESTION_V3_PLATINUM.md
Engine: Gemini 1.5 Flash Vision API
"""
import os
import sys
import json
import hashlib
import base64
import re
from datetime import datetime
from pathlib import Path
from io import BytesIO

# Unbuffered logging
sys.stdout = open('/app/platinum_ingestion.log', 'w', buffering=1)
sys.stderr = sys.stdout

print("=" * 80, flush=True)
print("   ⚡ STRYDA V3.0 PLATINUM - CLOUD VISION INGESTION", flush=True)
print(f"   Started: {datetime.now().isoformat()}", flush=True)
print("   Engine: Gemini 1.5 Flash Vision API", flush=True)
print("=" * 80, flush=True)

# Load environment
env_file = Path('/app/backend-minimal/.env')
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            key, val = line.split('=', 1)
            os.environ[key.strip()] = val.strip()

import psycopg2
import openai
from supabase import create_client
from pdf2image import convert_from_bytes
from PIL import Image
import google.generativeai as genai

# Config
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
OPENAI_KEY = os.getenv('OPENAI_API_KEY')
GEMINI_KEY = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')

# Initialize clients
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = openai.OpenAI(api_key=OPENAI_KEY)
genai.configure(api_key=GEMINI_KEY)

# Vision model
vision_model = genai.GenerativeModel('gemini-1.5-flash')

print(f"\n✅ Platinum Engine initialized", flush=True)
print(f"   Vision Model: Gemini 1.5 Flash", flush=True)
print(f"   Embedding Model: text-embedding-3-small", flush=True)

# ============================================================================
# PLATINUM VISION PROMPT
# ============================================================================

VISION_PROMPT = """You are a technical document parser for construction product data sheets.

TASK: Analyze this page image and extract ALL content with FULL CONTEXT.

INSTRUCTIONS:
1. **TABLES**: Convert to Markdown format. CRITICAL: For every numeric value, include:
   - The ROW header (e.g., size "1/2 inch", "M10", etc.)
   - The COLUMN header (e.g., "Proof Load", "Tensile Strength", etc.)
   - Format each cell as: "Size: [row] | Property: [column] | Value: [value]"

2. **DIAGRAMS**: If you see any technical drawings or figures, describe them:
   - What type of diagram (cross-section, installation detail, connection diagram)
   - Key components shown
   - Any dimensions or specifications visible

3. **TEXT**: Transcribe all text content verbatim, maintaining section headers.

OUTPUT FORMAT:
## TABLES
[For each table, output both the markdown table AND individual cell context lines]

## DIAGRAMS
[Descriptions of any figures/drawings found]

## TEXT
[All other text content]

Be thorough - every specification matters for construction compliance."""

# ============================================================================
# VISION API EXTRACTION
# ============================================================================

def extract_with_vision(pdf_bytes, product_name):
    """
    Use Gemini Vision API to parse PDF pages as images.
    Returns structured content with context injection.
    """
    all_content = []
    tables_found = 0
    diagrams_found = 0
    
    try:
        # Convert PDF to images (300 DPI for clarity)
        images = convert_from_bytes(pdf_bytes, dpi=200, fmt='JPEG')
        print(f"      📄 Converted {len(images)} pages to images", flush=True)
        
        for page_num, img in enumerate(images, 1):
            # Convert PIL image to bytes for API
            img_buffer = BytesIO()
            img.save(img_buffer, format='JPEG', quality=85)
            img_bytes = img_buffer.getvalue()
            
            # Create image part for Gemini
            image_part = {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(img_bytes).decode('utf-8')
            }
            
            try:
                # Call Gemini Vision API
                response = vision_model.generate_content([
                    VISION_PROMPT,
                    {"mime_type": "image/jpeg", "data": base64.b64encode(img_bytes).decode('utf-8')}
                ])
                
                page_content = response.text
                
                # Count tables and diagrams
                if '## TABLES' in page_content and '|' in page_content:
                    tables_found += page_content.count('|---')
                if '## DIAGRAMS' in page_content:
                    diagrams_found += 1
                
                # Add product context prefix
                contextualized = f"[Document: {product_name} | Page: {page_num}]\n\n{page_content}"
                all_content.append(contextualized)
                
            except Exception as e:
                print(f"      ⚠️ Vision API error page {page_num}: {str(e)[:40]}", flush=True)
                continue
        
        return all_content, len(images), tables_found, diagrams_found
        
    except Exception as e:
        print(f"      ❌ PDF conversion error: {str(e)[:50]}", flush=True)
        return [], 0, 0, 0


def chunk_vision_output(content_pages, product_name, chunk_size=1200, overlap=200):
    """
    Smart chunking of vision output.
    Keeps tables intact, splits text appropriately.
    """
    chunks = []
    
    for page_content in content_pages:
        # Split by major sections
        sections = re.split(r'(## TABLES|## DIAGRAMS|## TEXT)', page_content)
        
        current_section = ""
        current_chunk = ""
        
        for part in sections:
            part = part.strip()
            if not part:
                continue
            
            if part in ['## TABLES', '## DIAGRAMS', '## TEXT']:
                current_section = part
                continue
            
            # For tables, try to keep them intact
            if current_section == '## TABLES':
                # Split by table markers
                table_blocks = re.split(r'\n\n+', part)
                for block in table_blocks:
                    if '|' in block:  # It's a table
                        chunk = f"[TABLE from {product_name}]\n{block}"
                        chunks.append(chunk)
                    elif block.strip():
                        chunks.append(f"[{product_name}] {block}")
            
            # For diagrams, keep descriptions together
            elif current_section == '## DIAGRAMS':
                if part.strip():
                    chunks.append(f"[DIAGRAM from {product_name}]\n{part}")
            
            # For text, chunk normally
            else:
                text = part
                start = 0
                while start < len(text):
                    end = start + chunk_size
                    chunk = text[start:end].strip()
                    if chunk:
                        chunks.append(f"[{product_name}]\n{chunk}")
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
    except Exception as e:
        print(f"      ⚠️ Embedding error: {str(e)[:30]}", flush=True)
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
# PLATINUM INGESTION LOOP
# ============================================================================

stats = {
    'processed': 0, 
    'chunks': 0, 
    'tables': 0,
    'diagrams': 0,
    'pages_scanned': 0,
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
        
        # PLATINUM VISION EXTRACTION
        content_pages, pages, tables, diagrams = extract_with_vision(pdf_data, full_product)
        
        if not content_pages:
            print(f"      ⏭️ Skip: No content extracted", flush=True)
            stats['skipped'] += 1
            continue
        
        stats['pages_scanned'] += pages
        stats['tables'] += tables
        stats['diagrams'] += diagrams
        
        # Smart chunking
        chunks = chunk_vision_output(content_pages, full_product)
        
        print(f"      📊 {pages}p | {len(chunks)} chunks | {tables} tables | {diagrams} diagrams", flush=True)
        
        # Dedupe
        content_hash = hashlib.sha256(''.join(chunks[:3]).encode()).hexdigest()[:16]
        
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
            
            # Determine doc type based on chunk content
            if '[TABLE' in chunk:
                doc_type = 'Technical_Table'
            elif '[DIAGRAM' in chunk:
                doc_type = 'Technical_Diagram'
            else:
                doc_type = 'Technical_Data_Sheet'
            
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
                    'fasteners', 95, True, doc_type, 4
                ))
                inserted += 1
            except Exception as e:
                pass
        
        conn.commit()
        conn.close()
        
        if inserted > 0:
            stats['processed'] += 1
            stats['chunks'] += inserted
            print(f"      ✅ Ingested {inserted} chunks [PLATINUM]", flush=True)
            
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
    if i % 10 == 0:
        print(f"\n📊 CHECKPOINT [{i}/{total_files}]", flush=True)
        print(f"   Processed: {stats['processed']} | Pages: {stats['pages_scanned']} | Chunks: {stats['chunks']}", flush=True)
        print(f"   Tables: {stats['tables']} | Diagrams: {stats['diagrams']} | Errors: {stats['errors']}", flush=True)

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
print(f"   ⚡ V3.0 PLATINUM INGESTION - COMPLETE", flush=True)
print(f"{'='*80}", flush=True)
print(f"   ✅ Files Processed: {stats['processed']}", flush=True)
print(f"   📄 Total Chunks: {stats['chunks']}", flush=True)
print(f"   📊 Tables Extracted: {stats['tables']}", flush=True)
print(f"   🖼️ Diagrams Captured: {stats['diagrams']}", flush=True)
print(f"   📑 Pages Scanned: {stats['pages_scanned']}", flush=True)
print(f"   ⏭️ Skipped: {stats['skipped']}", flush=True)
print(f"   ❌ Errors: {stats['errors']}", flush=True)
print(f"   📋 Register Added: {len(register_entries)}", flush=True)
print(f"\n   Protocol: V3.0 PLATINUM (Cloud Vision)", flush=True)
print(f"   Completed: {datetime.now().isoformat()}", flush=True)
print("=" * 80, flush=True)

with open('/app/platinum_report.json', 'w') as f:
    json.dump({**stats, 'register': len(register_entries), 'completed': datetime.now().isoformat()}, f, indent=2)
