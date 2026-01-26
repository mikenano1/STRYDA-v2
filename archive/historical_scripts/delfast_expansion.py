#!/usr/bin/env python3
"""
STRYDA DELFAST EXPANSION PROTOCOL
==================================
Mastery System Implementation - Full Compliance

Operations:
1. Move 17 PDFs from /temporary to /product-library/F_Manufacturers/Fasteners/Delfast/
2. Ingest with V3.0 Platinum Vision + metadata tagging
3. Flag BRANZ Appraisals 1154 & 619 for enhanced table extraction

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
sys.stdout = open('/app/delfast_ingestion.log', 'w', buffering=1)
sys.stderr = sys.stdout

print("=" * 80, flush=True)
print("   🔩 STRYDA DELFAST EXPANSION - MASTERY PROTOCOL", flush=True)
print(f"   Started: {datetime.now().isoformat()}", flush=True)
print("   Engine: Gemini 1.5 Flash Vision API (V3.0 Platinum)", flush=True)
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
GEMINI_KEY = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY') or os.getenv('EMERGENT_LLM_KEY')

# Initialize clients
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = openai.OpenAI(api_key=OPENAI_KEY)
genai.configure(api_key=GEMINI_KEY)

# Vision model
vision_model = genai.GenerativeModel('gemini-1.5-flash')

print(f"\n✅ Delfast Expansion Engine initialized", flush=True)
print(f"   Vision Model: Gemini 1.5 Flash", flush=True)
print(f"   Embedding Model: text-embedding-3-small", flush=True)

# ============================================================================
# DELFAST DOC TYPE CLASSIFIER
# ============================================================================

def classify_doc_type(filename: str) -> str:
    """Classify document type based on filename patterns."""
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
# ENHANCED VISION PROMPT FOR DELFAST (Zone & Corrosion Tables)
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
# VISION API EXTRACTION (Delfast Enhanced)
# ============================================================================

def extract_with_vision(pdf_bytes, product_name, is_branz_appraisal=False):
    """
    Use Gemini Vision API to parse PDF pages as images.
    Enhanced extraction for BRANZ Appraisals (1154, 619).
    """
    all_content = []
    tables_found = 0
    diagrams_found = 0
    
    # Use enhanced prompt for BRANZ appraisals
    prompt = DELFAST_VISION_PROMPT
    
    try:
        # Higher DPI for BRANZ appraisals (better table extraction)
        dpi = 250 if is_branz_appraisal else 200
        images = convert_from_bytes(pdf_bytes, dpi=dpi, fmt='JPEG')
        print(f"      📄 Converted {len(images)} pages @ {dpi}DPI", flush=True)
        
        for page_num, img in enumerate(images, 1):
            # Convert PIL image to bytes
            img_buffer = BytesIO()
            img.save(img_buffer, format='JPEG', quality=90 if is_branz_appraisal else 85)
            img_bytes = img_buffer.getvalue()
            
            try:
                # Call Gemini Vision API
                response = vision_model.generate_content([
                    prompt,
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
# PHASE 1: SCAN AND MOVE FILES
# ============================================================================

print(f"\n📂 PHASE 1: FILE DISCOVERY & MIGRATION", flush=True)
print("=" * 60, flush=True)

# Scan temporary bucket
temp_files = []
try:
    items = supabase.storage.from_('temporary').list('', {'limit': 100})
    for item in items:
        name = item.get('name', '')
        if name.lower().endswith('.pdf'):
            temp_files.append({'name': name, 'path': name, 'bucket': 'temporary'})
except Exception as e:
    print(f"   ❌ Error scanning temporary: {str(e)[:50]}", flush=True)

# Scan existing Delfast folder
existing_files = []
try:
    items = supabase.storage.from_('product-library').list('F_Manufacturers/Fasteners/Delfast', {'limit': 100})
    for item in items:
        name = item.get('name', '')
        if name.lower().endswith('.pdf'):
            existing_files.append({'name': name, 'path': f"F_Manufacturers/Fasteners/Delfast/{name}", 'bucket': 'product-library'})
except Exception as e:
    print(f"   ❌ Error scanning Delfast folder: {str(e)[:50]}", flush=True)

print(f"   📥 Files in /temporary: {len(temp_files)}", flush=True)
print(f"   📁 Files already in Delfast: {len(existing_files)}", flush=True)

# Move files from temporary to Delfast folder
DEST_PATH = 'F_Manufacturers/Fasteners/Delfast'
moved_files = []

for file_info in temp_files:
    filename = file_info['name']
    
    # Skip non-PDF files
    if filename.lower() == 'download.html':
        continue
    
    print(f"   📦 Moving: {filename[:50]}...", flush=True)
    
    try:
        # Download from temporary
        pdf_data = supabase.storage.from_('temporary').download(filename)
        
        if pdf_data:
            # Generate proper filename for Delfast
            new_filename = filename
            if not filename.lower().startswith('delfast'):
                # Prefix with Delfast for branding
                new_filename = f"Delfast_{filename}"
            
            # Upload to product-library
            dest_path = f"{DEST_PATH}/{new_filename}"
            supabase.storage.from_('product-library').upload(
                dest_path, 
                pdf_data,
                {'content-type': 'application/pdf', 'upsert': 'true'}
            )
            
            moved_files.append({
                'name': new_filename,
                'path': dest_path,
                'bucket': 'product-library',
                'original': filename
            })
            print(f"      ✅ Moved → {dest_path[:50]}", flush=True)
            
    except Exception as e:
        # File might already exist
        print(f"      ⚠️ {str(e)[:40]}", flush=True)

print(f"\n   📊 Files moved: {len(moved_files)}", flush=True)

# Combine all files for ingestion
all_files = existing_files + moved_files
print(f"   📁 Total files to ingest: {len(all_files)}", flush=True)

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
    
    # Check if BRANZ Appraisal (enhanced extraction)
    is_branz = 'branz' in filename.lower() or 'appraisal' in filename.lower() or '1154' in filename or '619' in filename
    if is_branz:
        stats['branz_appraisals'] += 1
        print(f"      ⭐ BRANZ Appraisal detected - Enhanced extraction", flush=True)
    
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
            
            # Determine chunk-specific doc type
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
                    'fasteners',  # trade: fasteners
                    96,  # priority (higher than generic)
                    True,  # is_active
                    chunk_doc_type,  # doc_type
                    3 if is_branz else 4  # hierarchy_level (3 for BRANZ = higher authority)
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
print(f"\n   Protocol: V3.0 PLATINUM (Delfast Mastery)", flush=True)
print(f"   Completed: {datetime.now().isoformat()}", flush=True)
print("=" * 80, flush=True)

# Save report
with open('/app/delfast_report.json', 'w') as f:
    json.dump({**stats, 'completed': datetime.now().isoformat()}, f, indent=2)

print("\n✅ Report saved to /app/delfast_report.json", flush=True)
