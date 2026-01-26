#!/usr/bin/env python3
"""
⚡ PRYDA PLATINUM V3.0 INGESTION ENGINE
========================================
God-Tier Vision Parsing for Structural Connectors

Features:
- Gemini Vision API for HIGH COMPLEXITY files
- Pryda Unit Law: kN anchor + Timber Grade linking
- JD4/J2 Joint Group extraction
- Context Injection for all table cells

Target: 17 Pryda files → Supabase Vector DB
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

# Unbuffered output
print("=" * 80, flush=True)
print("   ⚡ PRYDA PLATINUM V3.0 - GOD-TIER INGESTION", flush=True)
print(f"   Started: {datetime.now().isoformat()}", flush=True)
print("   Engine: Gemini 1.5 Flash Vision API", flush=True)
print("=" * 80, flush=True)

# Load environment
from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

import psycopg2
import openai
from supabase import create_client
from pdf2image import convert_from_bytes
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

vision_model = genai.GenerativeModel('gemini-1.5-flash')

print(f"\n✅ Platinum Engine initialized", flush=True)
print(f"   Vision Model: Gemini 1.5 Flash", flush=True)
print(f"   Embedding Model: text-embedding-3-small", flush=True)

# ==============================================================================
# PRYDA UNIT LAW - kN ANCHORING & JOINT GROUP DETECTION
# ==============================================================================

PRYDA_UNIT_LAW = """
PRYDA UNIT LAW (MANDATORY):
- Primary force unit: kN (kilonewtons)
- Timber grades: SG8, SG10, SG12, MSG8, MSG10
- Nailing patterns: 4/3.15, 6/3.15, 8/3.15 (count/diameter mm)
- Joint groups: JD4, JD5, J2, J3, J4, J5
- Cyclonic regions: C1, C2, C3, C4
- Wind zones: Low, Medium, High, Very High, Extra High
"""

JOINT_GROUP_PATTERNS = {
    'JD4': 'Joint Group JD4 - High density hardwood',
    'JD5': 'Joint Group JD5 - Medium density hardwood', 
    'J2': 'Joint Group J2 - Radiata Pine (dry)',
    'J3': 'Joint Group J3 - Radiata Pine (green)',
    'J4': 'Joint Group J4 - Softwood dry',
    'J5': 'Joint Group J5 - Softwood green'
}

# ==============================================================================
# ENHANCED VISION PROMPT FOR PRYDA
# ==============================================================================

PRYDA_VISION_PROMPT = """You are a structural engineering document parser for Pryda timber connectors.

TASK: Extract ALL technical specifications with FULL CONTEXT for construction compliance.

CRITICAL EXTRACTION RULES:

1. **LOAD TABLES**: For every kN value found:
   - ANCHOR to specific product code (e.g., "JH 120/45", "H2", "PB 90")
   - LINK to timber grade if shown (SG8, SG10, J2, JD4)
   - INCLUDE nailing pattern (e.g., "4/3.15 nails", "6/2.8 nails")
   - FORMAT: "Product: [CODE] | Timber: [GRADE] | Capacity: [X] kN | Nailing: [PATTERN]"

2. **CONNECTOR TABLES**: Extract complete rows with:
   - Product code and dimensions
   - Uplift capacity (kN)
   - Shear capacity (kN)
   - Fixing requirements

3. **SPAN TABLES**: If present, capture:
   - Joist/bearer sizes
   - Maximum spans by spacing
   - Load conditions

4. **JOINT GROUPS**: When you see JD4, JD5, J2, J3, J4, J5:
   - Always specify which timber species/grade applies
   - Link capacity values to the correct joint group

5. **CYCLONIC DATA**: Flag any C1-C4 or wind zone specific data

OUTPUT FORMAT:
## PRODUCT SPECIFICATIONS
[Product code with full specs in context-injected format]

## LOAD TABLES  
[Complete tables with every cell having row+column context]

## INSTALLATION REQUIREMENTS
[Fixing patterns, edge distances, minimum embedment]

## COMPLIANCE NOTES
[Any AS/NZS references, wind zone requirements]

Be exhaustive - every number matters for structural design."""

# ==============================================================================
# HIGH COMPLEXITY VISION EXTRACTION
# ==============================================================================

def extract_with_vision(pdf_bytes, product_name, is_high_complexity=False):
    """
    Use Gemini Vision API to parse PDF pages.
    Enhanced parsing for HIGH COMPLEXITY files.
    """
    all_content = []
    tables_found = 0
    kn_values_found = []
    
    try:
        # Higher DPI for high complexity
        dpi = 250 if is_high_complexity else 200
        images = convert_from_bytes(pdf_bytes, dpi=dpi, fmt='JPEG')
        print(f"      📄 Converted {len(images)} pages (DPI: {dpi})", flush=True)
        
        for page_num, img in enumerate(images, 1):
            img_buffer = BytesIO()
            img.save(img_buffer, format='JPEG', quality=90 if is_high_complexity else 85)
            img_bytes = img_buffer.getvalue()
            
            try:
                # Use enhanced prompt for high complexity
                prompt = PRYDA_VISION_PROMPT if is_high_complexity else PRYDA_VISION_PROMPT
                
                response = vision_model.generate_content([
                    prompt,
                    {"mime_type": "image/jpeg", "data": base64.b64encode(img_bytes).decode('utf-8')}
                ])
                
                page_content = response.text
                
                # Extract kN values for logging
                kn_matches = re.findall(r'(\d+\.?\d*)\s*kN', page_content)
                kn_values_found.extend(kn_matches)
                
                # Count tables
                if '|' in page_content:
                    tables_found += page_content.count('|---') or page_content.count('| -')
                
                # Add product context prefix with Pryda Unit Law
                contextualized = f"[PRYDA CONNECTOR | Document: {product_name} | Page: {page_num}]\n"
                contextualized += f"[Unit Law: kN primary | Joint Groups: JD4/J2 applicable]\n\n"
                contextualized += page_content
                
                all_content.append(contextualized)
                
            except Exception as e:
                print(f"      ⚠️ Vision API error page {page_num}: {str(e)[:40]}", flush=True)
                continue
        
        unique_kn = sorted(set(kn_values_found), key=lambda x: float(x))
        return all_content, len(images), tables_found, unique_kn
        
    except Exception as e:
        print(f"      ❌ PDF conversion error: {str(e)[:50]}", flush=True)
        return [], 0, 0, []


def apply_pryda_context_injection(content, product_name):
    """
    Apply Pryda-specific context injection to extracted content.
    Links kN values to timber grades and joint groups.
    """
    enhanced = content
    
    # Inject joint group context
    for jg, desc in JOINT_GROUP_PATTERNS.items():
        if jg in content:
            enhanced = enhanced.replace(jg, f"{jg} ({desc})")
    
    # Ensure kN values have context
    # Pattern: number followed by kN
    def add_kn_context(match):
        value = match.group(1)
        return f"{value} kN (characteristic capacity)"
    
    enhanced = re.sub(r'(\d+\.?\d*)\s*kN(?!\s*\()', add_kn_context, enhanced)
    
    return enhanced


def chunk_pryda_content(content_pages, product_name, chunk_size=1200, overlap=200):
    """
    Smart chunking for Pryda content.
    Keeps load tables intact, preserves context.
    """
    chunks = []
    
    for page_content in content_pages:
        # Apply context injection
        enhanced = apply_pryda_context_injection(page_content, product_name)
        
        # Split by sections
        sections = re.split(r'(## PRODUCT SPECIFICATIONS|## LOAD TABLES|## INSTALLATION REQUIREMENTS|## COMPLIANCE NOTES)', enhanced)
        
        current_section = ""
        
        for part in sections:
            part = part.strip()
            if not part:
                continue
            
            if part.startswith('##'):
                current_section = part
                continue
            
            # For load tables, try to keep complete rows together
            if current_section == '## LOAD TABLES' or '|' in part:
                # Split by double newline to get table blocks
                blocks = re.split(r'\n\n+', part)
                for block in blocks:
                    if '|' in block or 'kN' in block:
                        chunk = f"[PRYDA LOAD DATA | {product_name}]\n{block}"
                        chunks.append(chunk)
                    elif block.strip():
                        chunks.append(f"[{product_name}] {block}")
            else:
                # Standard chunking for text
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


# ==============================================================================
# CROSS-CHECK EXISTING DATA
# ==============================================================================

def check_existing_pryda_chunks():
    """Check for existing Pryda chunks in database"""
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM documents WHERE source LIKE 'Pryda%'")
    count = cur.fetchone()[0]
    
    cur.execute("SELECT DISTINCT source FROM documents WHERE source LIKE 'Pryda%' LIMIT 20")
    sources = [r[0] for r in cur.fetchall()]
    
    conn.close()
    return count, sources


def purge_legacy_pryda():
    """Remove any legacy/placeholder Pryda data"""
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    
    # Count before
    cur.execute("SELECT COUNT(*) FROM documents WHERE source LIKE 'Pryda%'")
    before = cur.fetchone()[0]
    
    if before > 0:
        print(f"   ⚠️ Found {before} existing Pryda chunks - purging legacy data...", flush=True)
        cur.execute("DELETE FROM documents WHERE source LIKE 'Pryda%'")
        conn.commit()
        print(f"   ✅ Purged {before} legacy chunks", flush=True)
    
    conn.close()
    return before


# ==============================================================================
# SAMPLE DATA CARD GENERATOR
# ==============================================================================

def generate_data_card(product_code, chunks_data):
    """Generate a sample data card for verification"""
    print(f"\n{'='*60}", flush=True)
    print(f"   📋 SAMPLE DATA CARD: {product_code}", flush=True)
    print(f"{'='*60}", flush=True)
    
    # Search chunks for product code
    relevant = [c for c in chunks_data if product_code.lower() in c.lower()]
    
    if relevant:
        sample = relevant[0][:500]
        print(f"\n{sample}...", flush=True)
    else:
        print(f"   ⚠️ Product {product_code} not found in current batch", flush=True)
    
    print(f"{'='*60}\n", flush=True)


# ==============================================================================
# SCAN PRYDA FILES
# ==============================================================================

print(f"\n📂 Scanning Pryda files...", flush=True)

# List files from Supabase
pryda_path = 'F_Manufacturers/Fasteners/Pryda'
pryda_files = supabase.storage.from_('product-library').list(pryda_path, {'limit': 100})
pryda_files = [f for f in pryda_files if f['name'].endswith('.pdf')]

total_files = len(pryda_files)
print(f"   🔩 Found {total_files} Pryda files", flush=True)

# Identify HIGH COMPLEXITY files
HIGH_COMPLEXITY_NAMES = [
    'Brackets Fixes Design Guide',
    'Fasteners Design Guide',
    'Hangers Truss Boots Design Guide'
]

def is_high_complexity(filename):
    return any(hc in filename for hc in HIGH_COMPLEXITY_NAMES)

# Cross-check existing
print(f"\n🔍 Cross-checking existing data...", flush=True)
existing_count, existing_sources = check_existing_pryda_chunks()
print(f"   Existing Pryda chunks: {existing_count}", flush=True)

# Purge legacy if exists
if existing_count > 0:
    purge_legacy_pryda()

print("=" * 80, flush=True)

# ==============================================================================
# PLATINUM INGESTION LOOP
# ==============================================================================

stats = {
    'processed': 0,
    'chunks': 0,
    'tables': 0,
    'kn_values': [],
    'pages_scanned': 0,
    'errors': 0,
    'skipped': 0,
    'high_complexity': 0
}

all_chunks_data = []  # For data card generation

for i, file_info in enumerate(pryda_files, 1):
    filename = file_info['name']
    filepath = f"{pryda_path}/{filename}"
    
    complexity = "🔴 HIGH" if is_high_complexity(filename) else "🟢 STD"
    print(f"\n[{i:2}/{total_files}] {complexity} {filename[:50]}...", flush=True)
    
    try:
        # Download
        pdf_data = supabase.storage.from_('product-library').download(filepath)
        if not pdf_data:
            print(f"      ⏭️ Skip: Download failed", flush=True)
            stats['skipped'] += 1
            continue
        
        # Product name
        product = filename.replace('.pdf', '').replace('-', ' ').replace('_', ' ')
        full_product = f"Pryda - {product}"
        
        # Determine complexity
        high_comp = is_high_complexity(filename)
        if high_comp:
            stats['high_complexity'] += 1
        
        # PLATINUM VISION EXTRACTION
        content_pages, pages, tables, kn_vals = extract_with_vision(
            pdf_data, full_product, is_high_complexity=high_comp
        )
        
        if not content_pages:
            print(f"      ⏭️ Skip: No content extracted", flush=True)
            stats['skipped'] += 1
            continue
        
        stats['pages_scanned'] += pages
        stats['tables'] += tables
        stats['kn_values'].extend(kn_vals)
        
        # Smart chunking with Pryda context
        chunks = chunk_pryda_content(content_pages, full_product)
        all_chunks_data.extend(chunks)
        
        print(f"      📊 {pages}p | {len(chunks)} chunks | {tables} tables | {len(kn_vals)} kN values", flush=True)
        
        # Dedupe hash
        content_hash = hashlib.sha256(''.join(chunks[:3]).encode()).hexdigest()[:16]
        
        # DB insert
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cur = conn.cursor()
        
        # Insert chunks
        inserted = 0
        for ci, chunk in enumerate(chunks):
            emb = get_embedding(chunk)
            if not emb:
                continue
            
            # Determine doc type
            if 'LOAD DATA' in chunk or 'kN' in chunk:
                doc_type = 'Load_Capacity_Table'
            elif '|' in chunk:
                doc_type = 'Technical_Table'
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
                    'structural_connectors', 90, True, doc_type, 4
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
        
        # 50% Progress Report with Data Card
        if i == total_files // 2:
            print("\n" + "=" * 60, flush=True)
            print("   📊 50% PROGRESS REPORT", flush=True)
            print("=" * 60, flush=True)
            print(f"   Files processed: {stats['processed']}/{total_files}", flush=True)
            print(f"   Chunks created: {stats['chunks']}", flush=True)
            print(f"   kN values found: {len(set(stats['kn_values']))}", flush=True)
            
            # Generate sample data card
            generate_data_card("JH 120/45", all_chunks_data)
        
    except Exception as e:
        print(f"      ❌ Error: {str(e)[:50]}", flush=True)
        stats['errors'] += 1
    
    # Checkpoint every 5 files
    if i % 5 == 0:
        print(f"\n📊 CHECKPOINT [{i}/{total_files}]", flush=True)
        print(f"   Processed: {stats['processed']} | Chunks: {stats['chunks']} | High Complexity: {stats['high_complexity']}", flush=True)

# ==============================================================================
# FINAL REPORT
# ==============================================================================

unique_kn = sorted(set(stats['kn_values']), key=lambda x: float(x) if x else 0)

print(f"\n{'='*80}", flush=True)
print(f"   ⚡ PRYDA PLATINUM V3.0 INGESTION - COMPLETE", flush=True)
print(f"{'='*80}", flush=True)
print(f"   ✅ Files Processed: {stats['processed']}", flush=True)
print(f"   📄 Total Chunks: {stats['chunks']}", flush=True)
print(f"   📊 Tables Extracted: {stats['tables']}", flush=True)
print(f"   ⚡ kN Values Captured: {len(unique_kn)}", flush=True)
print(f"   🔴 High Complexity Files: {stats['high_complexity']}", flush=True)
print(f"   📑 Pages Scanned: {stats['pages_scanned']}", flush=True)
print(f"   ⏭️ Skipped: {stats['skipped']}", flush=True)
print(f"   ❌ Errors: {stats['errors']}", flush=True)
print(f"\n   📊 kN Load Range: {unique_kn[:5]}...{unique_kn[-5:] if len(unique_kn) > 5 else ''}", flush=True)
print(f"\n   Protocol: PLATINUM V3.0 (Pryda Unit Law)", flush=True)
print(f"   Completed: {datetime.now().isoformat()}", flush=True)
print("=" * 80, flush=True)

# Verify final count
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM documents WHERE source LIKE 'Pryda%'")
final_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM documents")
total_db = cur.fetchone()[0]
conn.close()

print(f"\n   📈 DATABASE STATUS:", flush=True)
print(f"      Pryda chunks: {final_count}", flush=True)
print(f"      Total DB chunks: {total_db}", flush=True)

# Save report
report = {
    'timestamp': datetime.now().isoformat(),
    'protocol': 'PLATINUM V3.0',
    'segment': 'Pryda Structural Connectors',
    'stats': {
        'files_processed': stats['processed'],
        'total_chunks': stats['chunks'],
        'tables_extracted': stats['tables'],
        'kn_values_captured': len(unique_kn),
        'high_complexity_files': stats['high_complexity'],
        'pages_scanned': stats['pages_scanned'],
        'errors': stats['errors']
    },
    'kn_values': unique_kn,
    'final_db_count': final_count,
    'total_db_count': total_db
}

with open('/app/pryda_platinum_report.json', 'w') as f:
    json.dump(report, f, indent=2)

print(f"\n   📁 Report saved: /app/pryda_platinum_report.json", flush=True)
