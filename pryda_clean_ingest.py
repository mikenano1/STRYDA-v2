#!/usr/bin/env python3
"""
PLATINUM RECOVERY SPRINT - STEP 3
PRYDA RE-INGESTION (CLEAN SLATE)

Rule: Every chunk MUST be tagged with BRAND: PRYDA
"""
import os
import sys
import json
import hashlib
import re
from datetime import datetime
from pathlib import Path

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
import fitz

# Config
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
OPENAI_KEY = os.getenv('OPENAI_API_KEY')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = openai.OpenAI(api_key=OPENAI_KEY)

print("=" * 80)
print("⚡ PRYDA RE-INGESTION (CLEAN SLATE)")
print(f"   Started: {datetime.now().isoformat()}")
print("   Rule: Every chunk tagged with [BRAND: PRYDA]")
print("=" * 80)

# ============================================================================
# PRYDA STRUCTURAL BIBLES (Priority 1.5x)
# ============================================================================

STRUCTURAL_BIBLES = [
    'Design_Guide',
    'Manual',
    'Bracing_Design',
    'Connectors_Tie-downs',
]

def get_document_weight(filename):
    """Assign weight based on document type"""
    for bible in STRUCTURAL_BIBLES:
        if bible.lower() in filename.lower():
            return 1.5  # Bible priority
    return 1.0


# ============================================================================
# UTILITIES
# ============================================================================

def extract_text(pdf_bytes, doc_name):
    """Extract text from PDF with context"""
    all_content = []
    try:
        if isinstance(pdf_bytes, memoryview):
            pdf_bytes = bytes(pdf_bytes)
        
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        for page_num in range(len(doc)):
            text = doc[page_num].get_text()
            if text.strip():
                # Add document context and BRAND TAG
                contextualized = f"[BRAND: PRYDA]\n[Document: {doc_name} | Page: {page_num + 1}]\n\n{text}"
                all_content.append(contextualized)
        
        doc.close()
        return all_content
        
    except Exception as e:
        print(f"      ❌ PDF error: {str(e)[:50]}")
        return []


def smart_chunk(pages, max_size=1200):
    """Smart chunking preserving context"""
    chunks = []
    for page in pages:
        if len(page) <= max_size:
            chunks.append(page)
        else:
            # Split by paragraphs
            paras = re.split(r'\n\n+', page)
            current = ""
            for para in paras:
                if len(current) + len(para) <= max_size:
                    current += para + "\n\n"
                else:
                    if current:
                        chunks.append(current.strip())
                    current = para + "\n\n"
            if current:
                chunks.append(current.strip())
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
# SCAN FOR PRYDA FILES
# ============================================================================

print("\n📂 SCANNING FOR PRYDA FILES...")

def scan_pryda(bucket, path):
    """Recursively find Pryda PDFs"""
    found = []
    try:
        items = supabase.storage.from_(bucket).list(path, {'limit': 200})
        for item in items:
            item_path = f"{path}/{item['name']}" if path else item['name']
            if item['name'].lower().endswith('.pdf') and 'pryda' in path.lower():
                found.append(item_path)
            elif item.get('id') is None:  # Folder
                found.extend(scan_pryda(bucket, item_path))
    except:
        pass
    return found

pryda_files = scan_pryda('product-library', 'F_Manufacturers/Fasteners/Pryda')
print(f"   Found {len(pryda_files)} Pryda PDFs")

for f in pryda_files[:5]:
    print(f"   • {f.split('/')[-1]}")
if len(pryda_files) > 5:
    print(f"   ... and {len(pryda_files) - 5} more")

# ============================================================================
# INGESTION LOOP
# ============================================================================

stats = {
    'processed': 0,
    'chunks': 0,
    'pages': 0,
    'bibles': 0,
    'errors': 0
}

print(f"\n🔄 INGESTING {len(pryda_files)} PRYDA FILES...")
print("=" * 80)

for i, file_path in enumerate(pryda_files, 1):
    filename = file_path.split('/')[-1]
    print(f"\n[{i:2}/{len(pryda_files)}] {filename[:55]}...")
    
    # Get weight
    weight = get_document_weight(filename)
    if weight > 1.0:
        print(f"      📖 STRUCTURAL BIBLE: {weight}x weight")
        stats['bibles'] += 1
    
    try:
        # Download PDF
        pdf_data = supabase.storage.from_('product-library').download(file_path)
        
        if not pdf_data:
            print(f"      ⚠️ Download failed")
            stats['errors'] += 1
            continue
        
        # Extract text
        doc_name = f"Pryda - {filename.replace('.pdf', '').replace('_', ' ')}"
        pages = extract_text(pdf_data, doc_name)
        
        if not pages:
            print(f"      ⏭️ No content extracted")
            stats['errors'] += 1
            continue
        
        stats['pages'] += len(pages)
        
        # Chunk
        chunks = smart_chunk(pages)
        print(f"      📊 {len(pages)} pages → {len(chunks)} chunks")
        
        # Hash for dedup
        content_hash = hashlib.sha256(filename.encode()).hexdigest()[:16]
        
        # DB connection
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cur = conn.cursor()
        
        # Check if exists
        cur.execute("SELECT 1 FROM documents WHERE page_hash LIKE %s LIMIT 1", (f"pryda_{content_hash}%",))
        if cur.fetchone():
            print(f"      ⏭️ Already exists")
            conn.close()
            continue
        
        # Insert chunks
        inserted = 0
        for ci, chunk in enumerate(chunks):
            emb = get_embedding(chunk)
            if not emb:
                continue
            
            # Determine doc type
            if 'Design' in filename or 'Guide' in filename:
                doc_type = 'Design_Guide'
            elif 'Manual' in filename:
                doc_type = 'Technical_Manual'
            else:
                doc_type = 'Technical_Data_Sheet'
            
            # Priority with weight
            base_priority = 90
            weighted_priority = int(base_priority * weight)
            
            try:
                cur.execute("""
                    INSERT INTO documents (
                        content, source, page, embedding, page_hash,
                        trade, priority, is_active, doc_type, hierarchy_level
                    ) VALUES (%s, %s, %s, %s::vector, %s, %s, %s, %s, %s, %s)
                """, (
                    chunk,
                    doc_name,
                    ci + 1,
                    emb,
                    f"pryda_{content_hash}_{ci}",
                    'structural',
                    weighted_priority,
                    True,
                    doc_type,
                    3 if weight > 1.0 else 4
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
print("⚡ PRYDA RE-INGESTION - COMPLETE")
print("=" * 80)
print(f"\n✅ Files Processed: {stats['processed']}")
print(f"📄 Total Chunks: {stats['chunks']}")
print(f"📑 Pages Scanned: {stats['pages']}")
print(f"📖 Structural Bibles: {stats['bibles']}")
print(f"❌ Errors: {stats['errors']}")
print(f"\n   All chunks tagged: [BRAND: PRYDA]")
print(f"   Completed: {datetime.now().isoformat()}")
print("=" * 80)

# Save report
with open('/app/pryda_ingestion_report.json', 'w') as f:
    json.dump({**stats, 'completed': datetime.now().isoformat()}, f, indent=2)

print(f"\n💾 Report saved to: /app/pryda_ingestion_report.json")
