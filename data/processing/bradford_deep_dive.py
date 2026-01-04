#!/usr/bin/env python3
"""
Bradford Deep Dive - Download and Process Pipeline
Auto-categorizes Insulation vs Ventilation products
Handles duplicate detection across document types
"""

import os
import sys
import json
import time
import hashlib
from datetime import datetime

sys.path.insert(0, '/app/backend-minimal')
sys.path.insert(0, '/app/data/processing')

from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

from supabase import create_client
from openai import OpenAI

# Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DATABASE_URL = 'postgresql://postgres.qxqisgjhbjwvoxsjibes:8skmVOJbMyaQHyQl@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres'

BASE_PATH = 'C_Interiors/Bradford'
LOCAL_DIR = '/app/data/ingestion/C_Interiors/Bradford/downloads'
OUTPUT_DIR = '/app/data/processing/bradford_deep_dive'

# Folder to doc_type mapping (priority order - higher = more important)
FOLDER_DOC_TYPES = {
    '1_Product_Technical_Statement': ('Technical_Data_Sheet', 100),
    '2_Warranty': ('Warranty', 40),
    '3_Product_Manual': ('Product_Manual', 80),
    '4_Install_Guide': ('Installation_Guide', 90),
    '5_Product_Information': ('Product_Guide', 60),
    '6_Safety_Data_Sheet': ('Safety_Data_Sheet', 50),
}

# =============================================================================
# PRODUCT TYPE DETECTION: INSULATION vs VENTILATION
# =============================================================================
VENTILATION_KEYWORDS = [
    'ventilation', 'ventilator', 'whirlybird', 'turbine', 'windmaster',
    'hurricane', 'solarxvent', 'ecopower', 'educt', 'iduct', 'static vent',
    'roof vent', 'eave vent', 'subfloor vent', 'soffit vent', 'ridge vent',
    'powered vent', 'solar vent', 'wind vent', 'exhaust', 'airflow',
    'bal vent', 'bal-40', 'bushfire vent', 'cyclonic'
]

INSULATION_KEYWORDS = [
    'insulation', 'batts', 'glasswool', 'glass wool', 'r-value', 'r1.5', 'r2.0',
    'r2.5', 'r3.0', 'r3.5', 'r4.0', 'r5.0', 'r6.0', 'r7.0', 'thermal',
    'acoustic', 'ceiling insulation', 'wall insulation', 'underfloor',
    'gold batts', 'polymax', 'optimo', 'anticon', 'thermoseal', 'quietel',
    'stone wool', 'rockwool', 'soundscreen', 'fireseal', 'ashgrid'
]

def detect_product_type(filename: str, content: str = '') -> str:
    """Detect if product is INSULATION or VENTILATION"""
    text = (filename + ' ' + content[:3000]).lower()
    
    vent_score = sum(1 for kw in VENTILATION_KEYWORDS if kw in text)
    insul_score = sum(1 for kw in INSULATION_KEYWORDS if kw in text)
    
    # Strong ventilation indicators
    if any(kw in text for kw in ['windmaster', 'hurricane', 'solarxvent', 'ecopower', 'whirlybird']):
        vent_score += 5
    
    # Strong insulation indicators
    if any(kw in text for kw in ['batts', 'r-value', 'glasswool', 'thermal insulation']):
        insul_score += 5
    
    if vent_score > insul_score:
        return 'ventilation'
    return 'insulation'

# =============================================================================
# TRADE CLASSIFICATION
# =============================================================================
INSULATION_TRADES = {
    'wall_insulation': ['wall', 'stud', 'internal wall', 'partition'],
    'ceiling_insulation': ['ceiling', 'overhead', 'attic'],
    'underfloor_insulation': ['underfloor', 'floor', 'subfloor', 'suspended'],
    'roof_insulation': ['roof', 'rafter', 'skillion', 'cathedral'],
    'acoustic_insulation': ['acoustic', 'sound', 'noise', 'quietel', 'soundscreen'],
    'general_insulation': ['insulation', 'thermal', 'batts', 'r-value'],
}

VENTILATION_TRADES = {
    'roof_ventilation': ['roof', 'whirlybird', 'turbine', 'windmaster', 'hurricane', 'ridge'],
    'subfloor_ventilation': ['subfloor', 'underfloor vent', 'floor vent'],
    'eave_ventilation': ['eave', 'soffit', 'fascia'],
    'powered_ventilation': ['powered', 'solar', 'ecopower', 'electric', 'hybrid'],
    'general_ventilation': ['ventilation', 'vent', 'airflow'],
}

def classify_trade(filename: str, content: str, product_type: str) -> tuple:
    """Classify trade based on product type"""
    text = (filename + ' ' + content[:2000]).lower()
    
    trades = INSULATION_TRADES if product_type == 'insulation' else VENTILATION_TRADES
    default_trade = 'general_insulation' if product_type == 'insulation' else 'general_ventilation'
    default_family = f'Bradford {product_type.title()}'
    
    best_trade = default_trade
    best_score = 0
    
    for trade, keywords in trades.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > best_score:
            best_score = score
            best_trade = trade
    
    # Product family based on trade
    family_map = {
        'wall_insulation': 'Bradford Wall Batts',
        'ceiling_insulation': 'Bradford Ceiling Batts',
        'underfloor_insulation': 'Bradford Underfloor',
        'roof_insulation': 'Bradford Roof Batts',
        'acoustic_insulation': 'Bradford Acoustic',
        'roof_ventilation': 'Bradford Windmaster/Hurricane',
        'subfloor_ventilation': 'Bradford Subfloor Vents',
        'eave_ventilation': 'Bradford Eave Vents',
        'powered_ventilation': 'Bradford Ecopower/Solar',
    }
    
    product_family = family_map.get(best_trade, default_family)
    return best_trade, product_family

# =============================================================================
# DUPLICATE DETECTION
# =============================================================================
seen_content_hashes = set()

def get_content_hash(content: str) -> str:
    """Generate hash of content for duplicate detection"""
    # Normalize: lowercase, remove extra whitespace
    normalized = ' '.join(content.lower().split())
    return hashlib.md5(normalized[:1000].encode()).hexdigest()

def is_duplicate(content: str) -> bool:
    """Check if content is duplicate of already processed chunk"""
    content_hash = get_content_hash(content)
    if content_hash in seen_content_hashes:
        return True
    seen_content_hashes.add(content_hash)
    return False

# =============================================================================
# MAIN PIPELINE
# =============================================================================
def download_files():
    """Download all PDFs from Supabase Storage"""
    print("\n" + "="*60)
    print("📥 DOWNLOADING BRADFORD PDFs FROM SUPABASE")
    print("="*60)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    os.makedirs(LOCAL_DIR, exist_ok=True)
    
    downloaded = []
    
    for folder, (doc_type, priority) in FOLDER_DOC_TYPES.items():
        folder_path = f"{BASE_PATH}/{folder}"
        local_folder = os.path.join(LOCAL_DIR, folder)
        os.makedirs(local_folder, exist_ok=True)
        
        files = supabase.storage.from_('product-library').list(folder_path)
        pdf_files = [f for f in files if f.get('name', '').endswith('.pdf') and f.get('name') != '_placeholder.pdf']
        
        print(f"\n📂 {folder}: {len(pdf_files)} files")
        
        for f in pdf_files:
            filename = f['name']
            remote_path = f"{folder_path}/{filename}"
            local_path = os.path.join(local_folder, filename)
            
            if os.path.exists(local_path):
                print(f"   ⏭️ {filename[:50]}")
                downloaded.append((local_path, folder, doc_type, priority))
                continue
            
            try:
                print(f"   ⬇️ {filename[:50]}")
                response = supabase.storage.from_('product-library').download(remote_path)
                with open(local_path, 'wb') as file:
                    file.write(response)
                downloaded.append((local_path, folder, doc_type, priority))
                time.sleep(0.2)
            except Exception as e:
                print(f"      ❌ Error: {e}")
    
    print(f"\n✅ Downloaded {len(downloaded)} files")
    return downloaded


def process_pdfs(pdf_files: list):
    """Process PDFs with product type detection and duplicate filtering"""
    print("\n" + "="*60)
    print("🔬 PROCESSING PDFs - INSULATION vs VENTILATION")
    print("="*60)
    
    from pdf_chunker_v2 import VisionPDFChunker
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    chunker = VisionPDFChunker(output_dir=OUTPUT_DIR, enable_vision=True)
    
    insulation_chunks = []
    ventilation_chunks = []
    duplicates_skipped = 0
    
    stats = {
        'insulation_files': 0,
        'ventilation_files': 0,
        'insulation_chunks': 0,
        'ventilation_chunks': 0,
        'duplicates_skipped': 0,
    }
    
    for i, (pdf_path, folder, doc_type, priority) in enumerate(pdf_files, 1):
        filename = os.path.basename(pdf_path)
        print(f"\n[{i}/{len(pdf_files)}] 📄 {filename[:55]}")
        
        # Detect product type from filename first
        product_type = detect_product_type(filename)
        
        try:
            chunks = chunker.process_pdf(pdf_path)
            
            # Refine product type from first chunk content
            if chunks:
                first_content = chunks[0].to_dict().get('content', '') if hasattr(chunks[0], 'to_dict') else chunks[0].get('content', '')
                product_type = detect_product_type(filename, first_content)
            
            print(f"    🏷️ Type: {product_type.upper()} | Doc: {doc_type}")
            
            if product_type == 'ventilation':
                stats['ventilation_files'] += 1
            else:
                stats['insulation_files'] += 1
            
            # Process chunks
            chunk_count = 0
            for chunk in chunks:
                chunk_dict = chunk.to_dict() if hasattr(chunk, 'to_dict') else chunk
                content = chunk_dict.get('content', '')
                
                # Skip duplicates
                if is_duplicate(content):
                    duplicates_skipped += 1
                    continue
                
                # Classify trade
                trade, product_family = classify_trade(filename, content, product_type)
                
                # Set metadata
                chunk_dict['trade'] = trade
                chunk_dict['product_family'] = product_family
                chunk_dict['doc_type'] = doc_type
                chunk_dict['priority'] = priority
                chunk_dict['brand_name'] = 'Bradford'
                chunk_dict['product_type'] = product_type
                chunk_dict['source'] = f"Bradford Deep Dive - {filename}"
                
                # Route to correct category
                if product_type == 'ventilation':
                    chunk_dict['category_code'] = 'B_Enclosure'
                    ventilation_chunks.append(chunk_dict)
                    stats['ventilation_chunks'] += 1
                else:
                    chunk_dict['category_code'] = 'C_Interiors'
                    insulation_chunks.append(chunk_dict)
                    stats['insulation_chunks'] += 1
                
                chunk_count += 1
            
            print(f"    ✅ {chunk_count} chunks (skipped {duplicates_skipped - stats['duplicates_skipped']} dupes)")
            stats['duplicates_skipped'] = duplicates_skipped
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    # Save chunks
    insul_file = os.path.join(OUTPUT_DIR, 'insulation_chunks.json')
    vent_file = os.path.join(OUTPUT_DIR, 'ventilation_chunks.json')
    
    with open(insul_file, 'w') as f:
        json.dump(insulation_chunks, f, indent=2, default=str)
    with open(vent_file, 'w') as f:
        json.dump(ventilation_chunks, f, indent=2, default=str)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 PROCESSING SUMMARY")
    print(f"{'='*60}")
    print(f"   INSULATION: {stats['insulation_files']} files → {stats['insulation_chunks']} chunks")
    print(f"   VENTILATION: {stats['ventilation_files']} files → {stats['ventilation_chunks']} chunks")
    print(f"   Duplicates skipped: {stats['duplicates_skipped']}")
    
    return insulation_chunks, ventilation_chunks, stats


def ingest_to_database(chunks: list, category: str):
    """Ingest chunks to database with embeddings"""
    if not chunks:
        print(f"   No {category} chunks to ingest")
        return 0
    
    print(f"\n   💾 Ingesting {len(chunks)} {category} chunks...")
    
    import psycopg2
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    
    batch_size = 20
    total_inserted = 0
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        
        texts = [c.get('content', '')[:8000] for c in batch]
        
        try:
            response = client.embeddings.create(model='text-embedding-3-small', input=texts)
            embeddings = [e.embedding for e in response.data]
        except Exception as e:
            print(f"      ❌ Embedding error: {e}")
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
                        chunk.get('source', 'Bradford Deep Dive'),
                        chunk.get('content', ''),
                        chunk.get('page', 1),
                        chunk.get('doc_type', 'Technical_Manual'),
                        chunk.get('trade', 'general_insulation'),
                        'Bradford',
                        chunk.get('product_family', 'Bradford General'),
                        chunk.get('category_code', 'C_Interiors'),
                        chunk.get('priority', 85),
                        embeddings[j],
                        'bradford_deep_dive'
                    ))
                    total_inserted += 1
                except Exception as e:
                    conn.rollback()
                    print(f"      ❌ Insert error: {e}")
        
        conn.commit()
        time.sleep(0.3)
    
    conn.close()
    print(f"   ✅ Inserted {total_inserted} {category} chunks")
    return total_inserted


def main():
    print("\n" + "="*70)
    print("🧱 BRADFORD DEEP DIVE - INSULATION & VENTILATION")
    print("="*70)
    
    # Download
    pdf_files = download_files()
    if not pdf_files:
        print("❌ No PDF files found")
        return
    
    # Process with product type detection
    insulation_chunks, ventilation_chunks, stats = process_pdfs(pdf_files)
    
    # Ingest separately
    print("\n" + "="*60)
    print("💾 INGESTING TO DATABASE")
    print("="*60)
    
    insul_count = ingest_to_database(insulation_chunks, "INSULATION (C_Interiors)")
    vent_count = ingest_to_database(ventilation_chunks, "VENTILATION (B_Enclosure)")
    
    print("\n" + "="*70)
    print("✅ BRADFORD DEEP DIVE COMPLETE")
    print("="*70)
    print(f"   🏠 Insulation: {insul_count} chunks → C_Interiors")
    print(f"   🌀 Ventilation: {vent_count} chunks → B_Enclosure")


if __name__ == "__main__":
    main()
