#!/usr/bin/env python3
"""
Smart Ingestion - High-Value Missing PDFs Only
==============================================
Filters and ingests ~50 high-value PDFs from the 139 missing:
1. Asona: Latest versions only (v8, v22, etc.)
2. Pink Batts, GIB, Firth: All 2024-2025 docs
3. Kingspan: All GreenTag certs
4. ECKO: High-value installation guides
"""

import os
import sys
import re
import time
import csv
import tempfile
from collections import defaultdict

sys.path.insert(0, '/app/backend-minimal')

from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

from supabase import create_client
from openai import OpenAI
import psycopg2

# Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DATABASE_URL = 'postgresql://postgres.qxqisgjhbjwvoxsjibes:8skmVOJbMyaQHyQl@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres'

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# =============================================================================
# SMART FILTERING LOGIC
# =============================================================================

def get_not_ingested_files():
    """Parse CSVs to get all not-ingested files with metadata"""
    files = []
    csv_paths = [
        '/app/data/STRYDA_02_A_Structure.csv',
        '/app/data/STRYDA_03_B_Enclosure.csv',
        '/app/data/STRYDA_04_C_Interiors.csv',
        '/app/data/STRYDA_05_F_Manufacturers.csv',
        '/app/data/STRYDA_06_Kingspan_K12.csv',
    ]
    
    for csv_path in csv_paths:
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['ingest_status'] == 'Not Ingested':
                    files.append({
                        'filename': row['filename'],
                        'brand': row['brand'],
                        'storage_path': row['storage_path'],
                        'category': row['category'],
                    })
    
    return files


def filter_asona_latest_versions(files):
    """Keep only latest version of Asona versioned files"""
    asona_files = [f for f in files if f['brand'] == 'Asona']
    other_files = [f for f in files if f['brand'] != 'Asona']
    
    # Group versioned files
    versioned = defaultdict(list)
    non_versioned = []
    
    for f in asona_files:
        filename = f['filename']
        match = re.search(r'(.+?)-v(\d+)\.pdf$', filename, re.IGNORECASE)
        if match:
            base = match.group(1)
            version = int(match.group(2))
            versioned[base].append((version, f))
        else:
            non_versioned.append(f)
    
    # Keep only latest versions
    latest = []
    for base, versions in versioned.items():
        versions.sort(key=lambda x: -x[0])  # Sort by version desc
        latest.append(versions[0][1])  # Keep highest version
    
    return other_files + latest + non_versioned


def filter_high_value_only(files):
    """Apply smart filtering rules"""
    high_value = []
    skipped = []
    
    for f in files:
        filename = f['filename']
        brand = f['brand']
        
        # Rule 1: Skip old versions (already handled for Asona)
        # Rule 2: Keep all Pink Batts, GIB, Firth 2024-2025 docs
        if brand in ['Pink Batts', 'GIB', 'Firth']:
            high_value.append(f)
            continue
        
        # Rule 3: Keep all Kingspan GreenTag certs
        if brand in ['Kingspan', 'Kingspan Insulation'] and 'greentag' in filename.lower():
            high_value.append(f)
            continue
        
        # Rule 4: Keep Asona (already filtered to latest versions)
        if brand == 'Asona':
            high_value.append(f)
            continue
        
        # Rule 5: Keep ECKO installation guides
        if brand == 'Fasteners' and 'ECKO' in filename:
            high_value.append(f)
            continue
        
        # Rule 6: Keep other important docs
        if brand in ['Autex', 'Bradford', 'Earthwool', 'Mammoth']:
            high_value.append(f)
            continue
        
        # Rule 7: Keep Abodo and Red Stag
        if brand in ['Abodo Wood', 'Red Stag']:
            high_value.append(f)
            continue
        
        # Skip the rest (duplicates, old versions, etc.)
        skipped.append(f)
    
    return high_value, skipped


# =============================================================================
# PDF PROCESSING
# =============================================================================

def extract_text_from_pdf(pdf_content):
    """Extract text from PDF using PyMuPDF"""
    import fitz  # PyMuPDF
    
    chunks = []
    try:
        with fitz.open(stream=pdf_content, filetype="pdf") as doc:
            for page_num, page in enumerate(doc, 1):
                text = page.get_text()
                if text and len(text.strip()) > 50:
                    # Split into reasonable chunks (~1000 chars)
                    words = text.split()
                    current_chunk = []
                    current_len = 0
                    
                    for word in words:
                        current_chunk.append(word)
                        current_len += len(word) + 1
                        
                        if current_len >= 1000:
                            chunk_text = ' '.join(current_chunk)
                            chunks.append({
                                'content': chunk_text,
                                'page': page_num,
                            })
                            current_chunk = []
                            current_len = 0
                    
                    # Don't forget remaining text
                    if current_chunk:
                        chunk_text = ' '.join(current_chunk)
                        if len(chunk_text) > 50:
                            chunks.append({
                                'content': chunk_text,
                                'page': page_num,
                            })
    except Exception as e:
        print(f"      ❌ PDF error: {e}")
    
    return chunks


def detect_doc_type(filename):
    """Detect document type from filename"""
    fl = filename.lower()
    if any(k in fl for k in ['datasheet', 'data sheet', 'technical']):
        return 'Technical_Data_Sheet'
    elif any(k in fl for k in ['install', 'installation', 'guide']):
        return 'Installation_Guide'
    elif any(k in fl for k in ['brochure', 'flyer', 'catalogue', 'catalog']):
        return 'Product_Guide'
    elif any(k in fl for k in ['certificate', 'greentag', 'declare', 'epd']):
        return 'Certification'
    elif any(k in fl for k in ['warranty']):
        return 'Warranty'
    elif any(k in fl for k in ['sds', 'safety']):
        return 'Safety_Data_Sheet'
    else:
        return 'Technical_Manual'


def detect_trade(category, brand):
    """Detect trade classification"""
    if category == 'C_Interiors':
        if brand == 'Asona':
            return 'acoustic_ceiling'
        elif brand in ['GIB', 'Pink Batts']:
            return 'interior_lining'
        elif brand in ['Autex', 'Mammoth']:
            return 'acoustic_insulation'
        return 'interior_general'
    elif category == 'B_Enclosure':
        return 'thermal_insulation'
    elif category == 'A_Structure':
        if brand == 'Firth':
            return 'concrete_masonry'
        return 'structural_timber'
    elif category == 'F_Manufacturers':
        return 'fasteners'
    return 'general'


# =============================================================================
# INGESTION
# =============================================================================

def ingest_file(file_info, conn):
    """Download, process, and ingest a single file"""
    filename = file_info['filename']
    storage_path = file_info['storage_path']
    brand = file_info['brand']
    category = file_info['category']
    
    # Determine bucket from path
    if storage_path.startswith('03_Kooltherm'):
        bucket = 'product-library'
    elif '/' in storage_path:
        bucket = 'product-library'
    else:
        bucket = 'pdfs'
    
    # Download PDF
    try:
        pdf_content = supabase.storage.from_(bucket).download(storage_path)
    except Exception as e:
        print(f"   ❌ Download failed: {e}")
        return 0
    
    # Extract text
    chunks = extract_text_from_pdf(pdf_content)
    if not chunks:
        print(f"   ⚠️ No text extracted")
        return 0
    
    # Prepare metadata
    source_name = f"{brand} Deep Dive - {filename}" if brand not in ['Fasteners', 'Unknown'] else filename.replace('.pdf', '')
    doc_type = detect_doc_type(filename)
    trade = detect_trade(category, brand)
    
    # Embed and insert
    inserted = 0
    batch_size = 20
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        texts = [c['content'][:8000] for c in batch]
        
        try:
            response = openai_client.embeddings.create(
                model='text-embedding-3-small',
                input=texts
            )
            embeddings = [e.embedding for e in response.data]
        except Exception as e:
            print(f"   ❌ Embedding error: {e}")
            continue
        
        with conn.cursor() as cur:
            for j, chunk in enumerate(batch):
                try:
                    cur.execute('''
                        INSERT INTO documents (
                            source, content, page, doc_type, trade, brand_name,
                            product_family, category_code, priority, embedding, ingestion_source
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ''', (
                        source_name,
                        chunk['content'],
                        chunk['page'],
                        doc_type,
                        trade,
                        brand if brand != 'Fasteners' else 'ECKO',
                        f"{brand} Products",
                        category,
                        85,
                        embeddings[j],
                        'smart_ingest_v1'
                    ))
                    inserted += 1
                except Exception as e:
                    conn.rollback()
                    print(f"   ❌ Insert error: {e}")
        
        conn.commit()
        time.sleep(0.1)  # Rate limiting
    
    return inserted


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("🚀 SMART INGESTION - HIGH-VALUE PDFs ONLY")
    print("=" * 60)
    
    # Step 1: Get all not-ingested files
    print("\n📋 Loading not-ingested files from CSVs...")
    all_files = get_not_ingested_files()
    print(f"   Found {len(all_files)} not-ingested files")
    
    # Step 2: Apply Asona version filter
    print("\n🔍 Filtering Asona to latest versions only...")
    files = filter_asona_latest_versions(all_files)
    print(f"   After Asona filter: {len(files)} files")
    
    # Step 3: Apply high-value filter
    print("\n⭐ Filtering to high-value docs only...")
    high_value, skipped = filter_high_value_only(files)
    print(f"   High-value: {len(high_value)} files")
    print(f"   Skipped (noise): {len(skipped)} files")
    
    # Show what we're ingesting
    print("\n📦 FILES TO INGEST:")
    by_brand = defaultdict(list)
    for f in high_value:
        by_brand[f['brand']].append(f['filename'])
    
    for brand, filenames in sorted(by_brand.items()):
        print(f"   {brand}: {len(filenames)} files")
    
    # Step 4: Connect to database
    print("\n💾 Connecting to database...")
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    
    # Step 5: Ingest files
    print("\n🔄 INGESTING FILES...")
    total_chunks = 0
    successful = 0
    failed = 0
    
    for i, f in enumerate(high_value, 1):
        print(f"\n[{i}/{len(high_value)}] {f['brand']} / {f['filename'][:50]}...")
        chunks = ingest_file(f, conn)
        if chunks > 0:
            print(f"   ✅ {chunks} chunks")
            total_chunks += chunks
            successful += 1
        else:
            failed += 1
    
    conn.close()
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ INGESTION COMPLETE")
    print("=" * 60)
    print(f"   Files processed: {successful}/{len(high_value)}")
    print(f"   Failed: {failed}")
    print(f"   Total chunks added: {total_chunks}")
    
    return successful, total_chunks


if __name__ == '__main__':
    main()
