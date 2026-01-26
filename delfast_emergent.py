#!/usr/bin/env python3
"""
STRYDA DELFAST EXPANSION - EMERGENT INTEGRATION VERSION
=========================================================
Uses emergentintegrations library for Gemini Vision API
Protocol: /protocols/INGESTION_V3_PLATINUM.md
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

# Unbuffered logging
log_file = open('/app/delfast_ingestion.log', 'w', buffering=1)
sys.stdout = log_file
sys.stderr = log_file

print("=" * 80, flush=True)
print("   🔩 STRYDA DELFAST EXPANSION - EMERGENT VISION", flush=True)
print(f"   Started: {datetime.now().isoformat()}", flush=True)
print("   Engine: Gemini 2.5 Flash (via emergentintegrations)", flush=True)
print("=" * 80, flush=True)

# Load environment
from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

import psycopg2
import openai
from supabase import create_client
from pdf2image import convert_from_bytes
from PIL import Image
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

# Config
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
OPENAI_KEY = os.getenv('OPENAI_API_KEY')
EMERGENT_KEY = os.getenv('EMERGENT_LLM_KEY')

# Initialize clients
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = openai.OpenAI(api_key=OPENAI_KEY)

print(f"\n✅ Delfast Expansion Engine initialized", flush=True)
print(f"   Vision Model: Gemini 2.5 Flash (emergent)", flush=True)
print(f"   Embedding Model: text-embedding-3-small", flush=True)

# ============================================================================
# DELFAST DOC TYPE CLASSIFIER
# ============================================================================

def classify_doc_type(filename: str) -> str:
    fname_lower = filename.lower()
    if 'branz' in fname_lower or 'appraisal' in fname_lower or '1154' in fname_lower or '619' in fname_lower:
        return 'Appraisal'
    elif 'sds' in fname_lower or 'safety' in fname_lower or 'msds' in fname_lower:
        return 'Safety_Data'
    elif 'bpir' in fname_lower:
        return 'BPIR_Certificate'
    elif 'catalogue' in fname_lower or 'catalog' in fname_lower:
        return 'Product_Catalogue'
    elif 'specs' in fname_lower or 'technical' in fname_lower:
        return 'Technical_Manual'
    else:
        return 'Technical_Data_Sheet'

# ============================================================================
# ENHANCED VISION PROMPT FOR DELFAST
# ============================================================================

DELFAST_VISION_PROMPT = """You are a technical document parser for DELFAST construction fastener data sheets.

TASK: Analyze this page image and extract ALL content with FULL CONTEXT.

CRITICAL EXTRACTION RULES:

1. **TABLES**: Convert to Markdown format. For EVERY numeric value, include:
   - The ROW header (e.g., nail size "3.15 x 90mm", product code "JDN-65")
   - The COLUMN header (e.g., "Proof Load", "Zone B", "Zone C", "Zone D", "Sea Spray")
   - Format: "Product: [row] | Property: [column] | Value: [value]"

2. **CORROSION/DURABILITY TABLES**: PAY SPECIAL ATTENTION to tables showing:
   - Galvanised vs Mechanical Galv vs Stainless 304/316
   - Zone classifications (Zone B, Zone C, Zone D, Sea Spray Zone)
   - Extract EACH cell with full context: "Finish: Galvanised | Zone: C | Rating: Suitable"

3. **CAPACITY TABLES**: For nail/staple capacity tables:
   - Include timber grade (SG8, SG10, MSG6, MSG8)
   - Include load type (Shear, Withdrawal, Lateral)
   - Format: "Nail: D-Head 90mm | Timber: SG8 | Load: Lateral | Capacity: 1.2kN"

4. **DIAGRAMS**: Describe technical drawings, installation details, fixing patterns.

5. **TEXT**: Transcribe all text content verbatim, especially:
   - BRANZ Appraisal numbers
   - Product codes (JDN, RX40A, CN Series, T-Nail, C-Nail)
   - Compliance statements

OUTPUT FORMAT:
## TABLES
[For each table, output both the markdown table AND individual cell context lines]

## DIAGRAMS
[Descriptions of any figures/drawings found]

## TEXT
[All other text content]

Be thorough - every specification matters for NZ Building Code compliance."""

# ============================================================================
# VISION API EXTRACTION (Using emergentintegrations)
# ============================================================================

async def extract_with_vision_async(pdf_bytes, product_name, is_branz_appraisal=False):
    """Use emergentintegrations for Gemini Vision API."""
    all_content = []
    tables_found = 0
    diagrams_found = 0
    
    try:
        dpi = 200 if is_branz_appraisal else 150
        images = convert_from_bytes(pdf_bytes, dpi=dpi, fmt='JPEG')
        print(f"      📄 Converted {len(images)} pages @ {dpi}DPI", flush=True)
        
        for page_num, img in enumerate(images, 1):
            # Convert PIL image to base64
            img_buffer = BytesIO()
            img.save(img_buffer, format='JPEG', quality=80)
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
            
            try:
                # Create chat instance for this page
                chat = LlmChat(
                    api_key=EMERGENT_KEY,
                    session_id=f"delfast_{product_name}_{page_num}_{datetime.now().timestamp()}",
                    system_message="You are a technical document parser for construction product data."
                ).with_model("gemini", "gemini-2.5-flash")
                
                # Create image content
                image_content = ImageContent(image_base64=img_base64)
                
                # Create message with image
                user_message = UserMessage(
                    text=DELFAST_VISION_PROMPT,
                    file_contents=[image_content]
                )
                
                # Send and get response
                response = await chat.send_message(user_message)
                page_content = response
                
                # Count tables and diagrams
                if '## TABLES' in page_content and '|' in page_content:
                    tables_found += page_content.count('|---')
                if '## DIAGRAMS' in page_content:
                    diagrams_found += 1
                
                # Add product context prefix
                contextualized = f"[Document: {product_name} | Page: {page_num}]\n\n{page_content}"
                all_content.append(contextualized)
                
                print(f"      ✓ Page {page_num} extracted", flush=True)
                
            except Exception as e:
                print(f"      ⚠️ Vision API error page {page_num}: {str(e)[:50]}", flush=True)
                continue
        
        return all_content, len(images), tables_found, diagrams_found
        
    except Exception as e:
        print(f"      ❌ PDF conversion error: {str(e)[:50]}", flush=True)
        return [], 0, 0, 0


def extract_with_vision(pdf_bytes, product_name, is_branz_appraisal=False):
    """Sync wrapper for async vision extraction."""
    return asyncio.run(extract_with_vision_async(pdf_bytes, product_name, is_branz_appraisal))


def chunk_vision_output(content_pages, product_name, chunk_size=1200, overlap=200):
    """Smart chunking - keeps tables intact."""
    chunks = []
    
    for page_content in content_pages:
        sections = re.split(r'(## TABLES|## DIAGRAMS|## TEXT)', page_content)
        current_section = ""
        
        for part in sections:
            part = part.strip()
            if not part:
                continue
            
            if part in ['## TABLES', '## DIAGRAMS', '## TEXT']:
                current_section = part
                continue
            
            if current_section == '## TABLES':
                table_blocks = re.split(r'\n\n+', part)
                for block in table_blocks:
                    if '|' in block:
                        chunk = f"[TABLE from {product_name}]\n{block}"
                        chunks.append(chunk)
                    elif block.strip():
                        chunks.append(f"[{product_name}] {block}")
            
            elif current_section == '## DIAGRAMS':
                if part.strip():
                    chunks.append(f"[DIAGRAM from {product_name}]\n{part}")
            
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
# MAIN EXECUTION
# ============================================================================

print(f"\n📂 PHASE 1: FILE DISCOVERY", flush=True)
print("=" * 60, flush=True)

# Scan Delfast folder (files already moved)
all_files = []
try:
    items = supabase.storage.from_('product-library').list('F_Manufacturers/Fasteners/Delfast', {'limit': 100})
    for item in items:
        name = item.get('name', '')
        if name.lower().endswith('.pdf'):
            all_files.append({
                'name': name, 
                'path': f"F_Manufacturers/Fasteners/Delfast/{name}", 
                'bucket': 'product-library'
            })
except Exception as e:
    print(f"   ❌ Error: {str(e)[:50]}", flush=True)

print(f"   📁 Found {len(all_files)} Delfast files", flush=True)

# ============================================================================
# PHASE 2: PLATINUM VISION INGESTION
# ============================================================================

print(f"\n📂 PHASE 2: PLATINUM VISION INGESTION", flush=True)
print("=" * 60, flush=True)

stats = {
    'processed': 0,
    'chunks': 0,
    'tables': 0,
    'diagrams': 0,
    'pages_scanned': 0,
    'errors': 0,
    'skipped': 0,
    'branz_appraisals': 0
}

total_files = len(all_files)

for i, file_info in enumerate(all_files, 1):
    filename = file_info['name']
    filepath = file_info['path']
    bucket = file_info['bucket']
    
    print(f"\n[{i:3}/{total_files}] {filename[:55]}...", flush=True)
    
    # Classify document type
    doc_type = classify_doc_type(filename)
    
    # Check if BRANZ Appraisal
    is_branz = 'branz' in filename.lower() or 'appraisal' in filename.lower() or '1154' in filename or '619' in filename
    if is_branz:
        stats['branz_appraisals'] += 1
        print(f"      ⭐ BRANZ Appraisal - Enhanced extraction", flush=True)
    
    try:
        # Download
        pdf_data = supabase.storage.from_(bucket).download(filepath)
        if not pdf_data:
            print(f"      ⏭️ Skip: Download failed", flush=True)
            stats['skipped'] += 1
            continue
        
        # Product name
        product = filename.replace('.pdf', '').replace('-', ' ').replace('_', ' ').title()[:60]
        full_product = f"Delfast - {product}"
        
        # PLATINUM VISION EXTRACTION
        content_pages, pages, tables, diagrams = extract_with_vision(pdf_data, full_product, is_branz)
        
        if not content_pages:
            print(f"      ⏭️ Skip: No content extracted", flush=True)
            stats['skipped'] += 1
            continue
        
        stats['pages_scanned'] += pages
        stats['tables'] += tables
        stats['diagrams'] += diagrams
        
        # Smart chunking
        chunks = chunk_vision_output(content_pages, full_product)
        
        print(f"      📊 {pages}p | {len(chunks)} chunks | {tables} tables | doc_type: {doc_type}", flush=True)
        
        # Dedupe hash
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
        
        # Insert with Delfast metadata
        inserted = 0
        for ci, chunk in enumerate(chunks):
            emb = get_embedding(chunk)
            if not emb:
                continue
            
            chunk_doc_type = doc_type
            if '[TABLE' in chunk:
                chunk_doc_type = 'Technical_Table'
            elif '[DIAGRAM' in chunk:
                chunk_doc_type = 'Technical_Diagram'
            
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
                    'fasteners',
                    96,
                    True,
                    chunk_doc_type,
                    3 if is_branz else 4
                ))
                inserted += 1
            except Exception as e:
                pass
        
        conn.commit()
        conn.close()
        
        if inserted > 0:
            stats['processed'] += 1
            stats['chunks'] += inserted
            print(f"      ✅ Ingested {inserted} chunks [DELFAST PLATINUM]", flush=True)
        
    except Exception as e:
        print(f"      ❌ Error: {str(e)[:50]}", flush=True)
        stats['errors'] += 1
    
    # Checkpoint
    if i % 5 == 0:
        print(f"\n📊 CHECKPOINT [{i}/{total_files}]", flush=True)
        print(f"   Processed: {stats['processed']} | Chunks: {stats['chunks']} | BRANZ: {stats['branz_appraisals']}", flush=True)

# ============================================================================
# FINAL REPORT
# ============================================================================

print(f"\n{'='*80}", flush=True)
print(f"   🔩 DELFAST EXPANSION - COMPLETE", flush=True)
print(f"{'='*80}", flush=True)
print(f"   ✅ Files Processed: {stats['processed']}", flush=True)
print(f"   📄 Total Chunks: {stats['chunks']}", flush=True)
print(f"   📊 Tables Extracted: {stats['tables']}", flush=True)
print(f"   🖼️ Diagrams Captured: {stats['diagrams']}", flush=True)
print(f"   📑 Pages Scanned: {stats['pages_scanned']}", flush=True)
print(f"   ⭐ BRANZ Appraisals: {stats['branz_appraisals']}", flush=True)
print(f"   ⏭️ Skipped: {stats['skipped']}", flush=True)
print(f"   ❌ Errors: {stats['errors']}", flush=True)
print(f"\n   Protocol: V3.0 PLATINUM (Emergent Vision)", flush=True)
print(f"   Completed: {datetime.now().isoformat()}", flush=True)
print("=" * 80, flush=True)

# Save report
with open('/app/delfast_report.json', 'w') as f:
    json.dump({**stats, 'completed': datetime.now().isoformat()}, f, indent=2)

print("\n✅ Report saved to /app/delfast_report.json", flush=True)
log_file.close()
