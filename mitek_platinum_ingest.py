#!/usr/bin/env python3
"""
PLATINUM MITEK INGESTION ENGINE (V3.0)
======================================
Protocol: PLATINUM V3.0 + BIBLE PRIORITY + kN LOCK

Directives:
1. BIBLE PRIORITY: Residential Manual first (weight 1.5x)
2. kN REGEX LOCK: Extract kN as engineering units
3. GIB-HANDIBRAC PROTOCOL: Dual-brand tagging
4. Full Context Injection for tables
"""
import os
import sys
import json
import hashlib
import re
from datetime import datetime
from pathlib import Path
from io import BytesIO

# Load env
env_file = Path('/app/backend-minimal/.env')
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            key, val = line.split('=', 1)
            os.environ[key.strip()] = val.strip()

import psycopg2
import openai
from supabase import create_client
import fitz  # PyMuPDF

# Config
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
OPENAI_KEY = os.getenv('OPENAI_API_KEY')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = openai.OpenAI(api_key=OPENAI_KEY)

print("=" * 80)
print("⚡ PLATINUM MITEK INGESTION ENGINE (V3.0)")
print(f"   Started: {datetime.now().isoformat()}")
print("=" * 80)

# ============================================================================
# DIRECTIVE 1: BIBLE PRIORITY WEIGHTING
# ============================================================================

BIBLE_MULTIPLIER = 1.5  # 50% weight boost for authoritative manuals
BIBLE_PATTERNS = ['Residential-Manual', 'PosiStrut-Manual', 'FLITCH-BEAM-Manual', 'Characteristic_Loadings']

def get_document_weight(filename):
    """Assign weight based on document authority level"""
    for pattern in BIBLE_PATTERNS:
        if pattern.lower() in filename.lower():
            return BIBLE_MULTIPLIER
    if 'BPIR' in filename.upper():
        return 1.3  # Compliance docs get 30% boost
    return 1.0

# ============================================================================
# DIRECTIVE 2: kN REGEX LOCK - Engineering Unit Extraction
# ============================================================================

KN_PATTERN = re.compile(r'(\d+(?:\.\d+)?)\s*kN', re.IGNORECASE)
FORCE_PATTERNS = {
    'kN': re.compile(r'(\d+(?:\.\d+)?)\s*kN', re.IGNORECASE),
    'N': re.compile(r'(\d+(?:\.\d+)?)\s*N\b', re.IGNORECASE),
    'kgf': re.compile(r'(\d+(?:\.\d+)?)\s*kgf', re.IGNORECASE),
}

def extract_kn_values(text):
    """Extract all kN values and normalize them"""
    values = []
    for match in KN_PATTERN.finditer(text):
        val = float(match.group(1))
        values.append({
            'value': val,
            'unit': 'kN',
            'raw': match.group(0),
            'position': match.start()
        })
    return values

def enhance_kn_context(text):
    """
    kN REGEX LOCK: Wrap kN values with engineering context markers
    "12kN" becomes "[FORCE: 12kN]" for better semantic matching
    """
    def replace_kn(match):
        return f"[FORCE: {match.group(0)}]"
    
    enhanced = KN_PATTERN.sub(replace_kn, text)
    return enhanced

# ============================================================================
# DIRECTIVE 3: GIB-HANDIBRAC CROSS-BRAND PROTOCOL
# ============================================================================

CROSS_BRAND_PRODUCTS = {
    'GIB-HandiBrac': ['MiTek', 'GIB', 'Winstone'],
    'GIB-Quiet-Tie': ['MiTek', 'GIB', 'Winstone'],
}

def get_brand_tags(filename):
    """Return all applicable brand tags for cross-brand products"""
    tags = ['MiTek']  # Base tag for all MiTek products
    
    for product, brands in CROSS_BRAND_PRODUCTS.items():
        if product.lower().replace('-', '') in filename.lower().replace('-', ''):
            tags.extend(brands)
    
    # Also check for sub-brands
    if 'lumberlok' in filename.lower():
        tags.append('Lumberlok')
    if 'bowmac' in filename.lower():
        tags.append('Bowmac')
    if 'gang-nail' in filename.lower() or 'gangnail' in filename.lower():
        tags.append('Gang-Nail')
    if 'posistrut' in filename.lower():
        tags.append('PosiStrut')
    if 'stud-lok' in filename.lower() or 'studlok' in filename.lower():
        tags.append('Stud-Lok')
    
    return list(set(tags))  # Remove duplicates

# ============================================================================
# TEXT EXTRACTION WITH CONTEXT INJECTION
# ============================================================================

def extract_text_with_context(pdf_bytes, product_name):
    """
    Extract text from PDF with full context injection for tables.
    """
    all_content = []
    tables_found = 0
    kn_values = []
    total_pages = 0
    
    try:
        # PyMuPDF needs bytes, not memoryview
        if isinstance(pdf_bytes, memoryview):
            pdf_bytes = bytes(pdf_bytes)
        
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(doc)
        
        for page_num in range(total_pages):
            page = doc[page_num]
            text = page.get_text()
            
            if not text.strip():
                continue
            
            # Extract kN values from this page
            page_kn = extract_kn_values(text)
            kn_values.extend(page_kn)
            
            # Enhance kN values with context markers
            enhanced_text = enhance_kn_context(text)
            
            # Count table markers (pipes in text)
            if '|' in text or '\t' in text:
                tables_found += 1
            
            # Add document and page context
            contextualized = f"[Document: {product_name} | Page: {page_num + 1}]\n\n{enhanced_text}"
            all_content.append(contextualized)
        
        doc.close()
        return all_content, total_pages, tables_found, kn_values
        
    except Exception as e:
        print(f"      ❌ PDF extraction error: {str(e)[:50]}")
        return [], 0, 0, []


def smart_chunk(content_pages, product_name, chunk_size=1200, overlap=200):
    """Smart chunking that preserves context"""
    chunks = []
    
    for page_content in content_pages:
        text = page_content
        
        # If content is small enough, keep as one chunk
        if len(text) <= chunk_size:
            chunks.append(text)
            continue
        
        # Split by paragraphs first
        paragraphs = re.split(r'\n\n+', text)
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) <= chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
    
    return chunks


def get_embedding(text):
    """Get embedding from OpenAI"""
    try:
        r = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text[:8000],
            dimensions=1536
        )
        return r.data[0].embedding
    except Exception as e:
        print(f"      ⚠️ Embedding error: {str(e)[:30]}")
        return None


# ============================================================================
# LOAD MITEK FILES FROM MANIFEST
# ============================================================================

print("\n📂 LOADING MITEK MANIFEST...")

manifest_path = '/app/mitek_manifest.json'
with open(manifest_path, 'r') as f:
    manifest = json.load(f)

files_to_process = manifest['processed']
total_files = len(files_to_process)

print(f"   Found {total_files} files in manifest")

# ============================================================================
# DIRECTIVE 1: SORT BY BIBLE PRIORITY
# ============================================================================

print("\n📖 APPLYING BIBLE PRIORITY SORT...")

def get_sort_priority(file_info):
    """Bible documents first, then compliance, then others"""
    name = file_info['original']
    if any(p.lower() in name.lower() for p in BIBLE_PATTERNS):
        return 0  # Highest priority
    if 'BPIR' in name.upper():
        return 1
    return 2

files_to_process.sort(key=get_sort_priority)

print("   ✅ Bibles and Compliance docs prioritized")
for i, f in enumerate(files_to_process[:5]):
    weight = get_document_weight(f['original'])
    print(f"      [{i+1}] {f['original'][:45]}... (weight: {weight}x)")

# ============================================================================
# PLATINUM INGESTION LOOP
# ============================================================================

TARGET_BUCKET = 'product-library'
TARGET_PATH = 'F_Manufacturers/Structural/MiTek'

stats = {
    'processed': 0,
    'chunks': 0,
    'pages': 0,
    'tables': 0,
    'kn_values_found': 0,
    'cross_brand_tagged': 0,
    'bible_docs': 0,
    'errors': 0,
    'skipped': 0
}

print(f"\n🔄 INGESTING {total_files} MITEK FILES...")
print("=" * 80)

for i, file_info in enumerate(files_to_process, 1):
    original = file_info['original']
    sanitized = file_info['sanitized']
    file_path = file_info['path']
    
    print(f"\n[{i:2}/{total_files}] {original[:55]}...")
    
    # Get document weight
    weight = get_document_weight(original)
    if weight > 1.0:
        print(f"      📖 BIBLE PRIORITY: {weight}x weight multiplier")
        stats['bible_docs'] += 1
    
    # Get brand tags
    brand_tags = get_brand_tags(original)
    if len(brand_tags) > 1:
        print(f"      🏷️ CROSS-BRAND: {', '.join(brand_tags)}")
        stats['cross_brand_tagged'] += 1
    
    try:
        # Download PDF
        pdf_data = supabase.storage.from_(TARGET_BUCKET).download(file_path)
        
        if not pdf_data:
            print(f"      ⚠️ Download failed - skipping")
            stats['skipped'] += 1
            continue
        
        # Extract text with context
        product_name = f"MiTek - {sanitized.replace('.pdf', '').replace('MiTek - ', '')}"
        content_pages, pages, tables, kn_values = extract_text_with_context(pdf_data, product_name)
        
        if not content_pages:
            print(f"      ⏭️ No content extracted - skipping")
            stats['skipped'] += 1
            continue
        
        stats['pages'] += pages
        stats['tables'] += tables
        stats['kn_values_found'] += len(kn_values)
        
        if kn_values:
            print(f"      ⚡ kN VALUES: {', '.join([v['raw'] for v in kn_values[:5]])}{'...' if len(kn_values) > 5 else ''}")
        
        # Smart chunking
        chunks = smart_chunk(content_pages, product_name)
        print(f"      📊 {pages}p | {len(chunks)} chunks | {tables} tables | {len(kn_values)} kN values")
        
        # Dedupe hash
        content_hash = hashlib.sha256(''.join(chunks[:3]).encode()).hexdigest()[:16]
        
        # DB connection
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cur = conn.cursor()
        
        # Check if exists
        cur.execute("SELECT 1 FROM documents WHERE page_hash LIKE %s LIMIT 1", (f"{content_hash}%",))
        if cur.fetchone():
            print(f"      ⏭️ Already exists in DB - skipping")
            stats['skipped'] += 1
            conn.close()
            continue
        
        # Insert chunks
        inserted = 0
        for ci, chunk in enumerate(chunks):
            emb = get_embedding(chunk)
            if not emb:
                continue
            
            # Determine doc type
            if 'Manual' in original or 'Characteristic' in original:
                doc_type = 'Technical_Manual'
            elif 'BPIR' in original:
                doc_type = 'Compliance_Certificate'
            elif 'Test' in original:
                doc_type = 'Test_Data'
            elif 'Span' in original:
                doc_type = 'Span_Table'
            else:
                doc_type = 'Technical_Data_Sheet'
            
            # Calculate priority with weight multiplier
            base_priority = 90
            weighted_priority = int(base_priority * weight)
            
            # Add brand tags to content for cross-brand retrieval
            brand_suffix = f"\n[Brand Tags: {', '.join(brand_tags)}]" if len(brand_tags) > 1 else ""
            chunk_with_tags = chunk + brand_suffix
            
            try:
                cur.execute("""
                    INSERT INTO documents (
                        content, source, page, embedding, page_hash,
                        trade, priority, is_active, doc_type, hierarchy_level
                    ) VALUES (%s, %s, %s, %s::vector, %s, %s, %s, %s, %s, %s)
                """, (
                    chunk_with_tags, 
                    product_name, 
                    ci + 1, 
                    emb,
                    f"{content_hash}_{ci}",
                    'structural',  # Trade category
                    weighted_priority,
                    True,
                    doc_type,
                    3 if weight > 1.0 else 4  # Bibles get higher hierarchy
                ))
                inserted += 1
            except Exception as e:
                pass
        
        conn.commit()
        conn.close()
        
        if inserted > 0:
            stats['processed'] += 1
            stats['chunks'] += inserted
            print(f"      ✅ Ingested {inserted} chunks (priority: {weighted_priority})")
        
    except Exception as e:
        print(f"      ❌ Error: {str(e)[:50]}")
        stats['errors'] += 1

# ============================================================================
# FINAL REPORT
# ============================================================================

print("\n" + "=" * 80)
print("⚡ PLATINUM MITEK INGESTION - COMPLETE")
print("=" * 80)
print(f"\n✅ Files Processed: {stats['processed']}")
print(f"📄 Total Chunks: {stats['chunks']}")
print(f"📑 Pages Scanned: {stats['pages']}")
print(f"📊 Tables Found: {stats['tables']}")
print(f"⚡ kN Values Extracted: {stats['kn_values_found']}")
print(f"📖 Bible Docs (1.5x weight): {stats['bible_docs']}")
print(f"🏷️ Cross-Brand Tagged: {stats['cross_brand_tagged']}")
print(f"⏭️ Skipped: {stats['skipped']}")
print(f"❌ Errors: {stats['errors']}")
print(f"\n   Protocol: PLATINUM V3.0 + BIBLE PRIORITY")
print(f"   Completed: {datetime.now().isoformat()}")
print("=" * 80)

# Save report
report = {
    **stats,
    'completed': datetime.now().isoformat(),
    'protocol': 'PLATINUM_V3.0_MITEK'
}
with open('/app/mitek_ingestion_report.json', 'w') as f:
    json.dump(report, f, indent=2)

print(f"\n💾 Report saved to: /app/mitek_ingestion_report.json")
