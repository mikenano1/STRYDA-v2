#!/usr/bin/env python3
"""
STRYDA V3.0 PLATINUM INGESTION ENGINE
Cloud Vision API using Emergent Integrations for Gemini Flash

Protocol: /protocols/INGESTION_V3_PLATINUM.md
Engine: Gemini 2.5 Flash Vision API via Emergent Integrations
"""
import os
import sys
import json
import hashlib
import base64
import re
import asyncio
from datetime import datetime
from pathlib import Path
from io import BytesIO

# Unbuffered logging to file
log_file = open('/app/platinum_ingestion.log', 'w', buffering=1)

def log(msg):
    """Log to both file and print"""
    print(msg, file=log_file, flush=True)
    print(msg, flush=True)

log("=" * 80)
log("   ⚡ STRYDA V3.0 PLATINUM - CLOUD VISION INGESTION")
log(f"   Started: {datetime.now().isoformat()}")
log("   Engine: Gemini 2.5 Flash Vision API (Emergent Integration)")
log("=" * 80)

# Load environment
from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

import psycopg2
import openai
from supabase import create_client
from pdf2image import convert_from_bytes
from PIL import Image
from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContent

# Config
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
OPENAI_KEY = os.getenv('OPENAI_API_KEY')
EMERGENT_KEY = os.getenv('EMERGENT_LLM_KEY')

# Initialize clients
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = openai.OpenAI(api_key=OPENAI_KEY)

log(f"\n✅ Platinum Engine initialized")
log(f"   Vision Model: Gemini 2.5 Flash (Emergent)")
log(f"   Embedding Model: text-embedding-3-small")

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
# VISION API EXTRACTION USING EMERGENT INTEGRATIONS
# ============================================================================

async def extract_page_with_vision(img_base64: str, product_name: str, page_num: int) -> str:
    """
    Use Emergent Integrations to call Gemini Vision API.
    """
    try:
        # Create a new chat instance for this page
        chat = LlmChat(
            api_key=EMERGENT_KEY,
            session_id=f"platinum-{hashlib.md5(product_name.encode()).hexdigest()[:8]}-p{page_num}",
            system_message="You are a technical document parser. Extract all content accurately."
        ).with_model("gemini", "gemini-2.5-flash")
        
        # Create file content with image
        file_content = FileContent(content_type="image/jpeg", file_content_base64=img_base64)
        
        # Create message with image
        user_message = UserMessage(
            text=VISION_PROMPT,
            file_contents=[file_content]
        )
        
        # Send and get response
        response = await chat.send_message(user_message)
        return response
        
    except Exception as e:
        log(f"      ⚠️ Vision API error page {page_num}: {str(e)[:60]}")
        return ""


def extract_with_vision(pdf_bytes, product_name):
    """
    Use Gemini Vision API to parse PDF pages as images.
    Returns structured content with context injection.
    """
    all_content = []
    tables_found = 0
    diagrams_found = 0
    
    try:
        # Convert PDF to images (150 DPI for balance of quality and speed)
        images = convert_from_bytes(pdf_bytes, dpi=150, fmt='JPEG')
        log(f"      📄 Converted {len(images)} pages to images")
        
        for page_num, img in enumerate(images, 1):
            # Convert PIL image to base64
            img_buffer = BytesIO()
            img.save(img_buffer, format='JPEG', quality=85)
            img_bytes = img_buffer.getvalue()
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            # Call Vision API asynchronously
            page_content = asyncio.run(extract_page_with_vision(img_base64, product_name, page_num))
            
            if not page_content:
                continue
            
            # Count tables and diagrams
            if '## TABLES' in page_content and '|' in page_content:
                tables_found += page_content.count('|---')
            if '## DIAGRAMS' in page_content:
                diagrams_found += 1
            
            # Add product context prefix
            contextualized = f"[Document: {product_name} | Page: {page_num}]\n\n{page_content}"
            all_content.append(contextualized)
        
        return all_content, len(images), tables_found, diagrams_found
        
    except Exception as e:
        log(f"      ❌ PDF conversion error: {str(e)[:50]}")
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
        
        for part in sections:
            part = part.strip()
            if not part:
                continue
            
            if part in ['## TABLES', '## DIAGRAMS', '## TEXT']:
                current_section = part
                continue
            
            # For tables, try to keep them intact
            if current_section == '## TABLES':
                table_blocks = re.split(r'\n\n+', part)
                for block in table_blocks:
                    if '|' in block:
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
        log(f"      ⚠️ Embedding error: {str(e)[:30]}")
        return None


# ============================================================================
# SCAN FILES
# ============================================================================

log(f"\n📂 Scanning Bremick files...")

def scan_folder(bucket, path):
    files = []
    try:
        items = supabase.storage.from_(bucket).list(path, {'limit': 500})
        for item in items:
            name = item['name']
            if name.lower().endswith('.pdf'):
                files.append({'name': name, 'path': f"{path}/{name}", 'bucket': bucket})
            elif item.get('id') is None:  # It's a folder
                files.extend(scan_folder(bucket, f"{path}/{name}"))
    except Exception as e:
        log(f"   Error scanning {path}: {e}")
    return files

bremick_files = scan_folder('product-library', 'F_Manufacturers/Fasteners/Bremick')
total_files = len(bremick_files)

log(f"   🔩 Found {total_files} Bremick files")
log("=" * 80)

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
    
    log(f"\n[{i:3}/{total_files}] {filename[:55]}...")
    
    try:
        # Download
        pdf_data = supabase.storage.from_(bucket).download(filepath)
        if not pdf_data:
            log(f"      ⏭️ Skip: Download failed")
            stats['skipped'] += 1
            continue
        
        # Product name
        product = filename.replace('.pdf', '').replace('-', ' ').replace('_', ' ').title()[:60]
        full_product = f"Bremick - {product}"
        
        # PLATINUM VISION EXTRACTION
        content_pages, pages, tables, diagrams = extract_with_vision(pdf_data, full_product)
        
        if not content_pages:
            log(f"      ⏭️ Skip: No content extracted")
            stats['skipped'] += 1
            continue
        
        stats['pages_scanned'] += pages
        stats['tables'] += tables
        stats['diagrams'] += diagrams
        
        # Smart chunking
        chunks = chunk_vision_output(content_pages, full_product)
        
        log(f"      📊 {pages}p | {len(chunks)} chunks | {tables} tables | {diagrams} diagrams")
        
        # Dedupe
        content_hash = hashlib.sha256(''.join(chunks[:3]).encode()).hexdigest()[:16]
        
        # DB insert
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cur = conn.cursor()
        
        # Check exists
        cur.execute("SELECT 1 FROM documents WHERE page_hash LIKE %s LIMIT 1", (f"{content_hash}%",))
        if cur.fetchone():
            log(f"      ⏭️ Skip: Already exists")
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
                        content, source, page, embedding, page_hash,
                        trade, priority, is_active, doc_type, hierarchy_level,
                        has_table, has_diagram, brand_name
                    ) VALUES (%s, %s, %s, %s::vector, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    chunk, full_product, ci + 1, emb,
                    f"{content_hash}_{ci}",
                    'fasteners', 95, True, doc_type, 4,
                    '[TABLE' in chunk, '[DIAGRAM' in chunk, 'Bremick'
                ))
                inserted += 1
            except Exception as e:
                log(f"      ⚠️ DB insert error: {str(e)[:40]}")
        
        conn.commit()
        conn.close()
        
        if inserted > 0:
            stats['processed'] += 1
            stats['chunks'] += inserted
            log(f"      ✅ Ingested {inserted} chunks [PLATINUM]")
            
            register_entries.append({
                'brand': 'Bremick',
                'product': filename,
                'sector': 'fasteners',
                'status': 'CERTIFIED'
            })
        
    except Exception as e:
        log(f"      ❌ Error: {str(e)[:50]}")
        stats['errors'] += 1
    
    # Checkpoint every 10 files
    if i % 10 == 0:
        log(f"\n📊 CHECKPOINT [{i}/{total_files}]")
        log(f"   Processed: {stats['processed']} | Pages: {stats['pages_scanned']} | Chunks: {stats['chunks']}")
        log(f"   Tables: {stats['tables']} | Diagrams: {stats['diagrams']} | Errors: {stats['errors']}")

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
log(f"\n{'='*80}")
log(f"   ⚡ V3.0 PLATINUM INGESTION - COMPLETE")
log(f"{'='*80}")
log(f"   ✅ Files Processed: {stats['processed']}")
log(f"   📄 Total Chunks: {stats['chunks']}")
log(f"   📊 Tables Extracted: {stats['tables']}")
log(f"   🖼️ Diagrams Captured: {stats['diagrams']}")
log(f"   📑 Pages Scanned: {stats['pages_scanned']}")
log(f"   ⏭️ Skipped: {stats['skipped']}")
log(f"   ❌ Errors: {stats['errors']}")
log(f"   📋 Register Added: {len(register_entries)}")
log(f"\n   Protocol: V3.0 PLATINUM (Cloud Vision)")
log(f"   Completed: {datetime.now().isoformat()}")
log("=" * 80)

with open('/app/platinum_report.json', 'w') as f:
    json.dump({**stats, 'register': len(register_entries), 'completed': datetime.now().isoformat()}, f, indent=2)

log_file.close()
