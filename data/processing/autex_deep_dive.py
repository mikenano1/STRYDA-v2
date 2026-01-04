#!/usr/bin/env python3
"""
Autex Acoustics Deep Dive - Download and Process Pipeline
Handles 22 product folders with intelligent duplicate detection
and application-based trade classification
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

BASE_PATH = 'C_Interiors/Autex'
LOCAL_DIR = '/app/data/ingestion/C_Interiors/Autex/downloads'
OUTPUT_DIR = '/app/data/processing/autex_deep_dive'

# =============================================================================
# PRODUCT TO TRADE MAPPING
# =============================================================================
PRODUCT_CLASSIFICATION = {
    '01_3D_Acoustic_Ceiling_Tiles': ('acoustic_ceiling', 'Autex 3D Ceiling'),
    '02_3D_Acoustic_Wall_Tiles': ('acoustic_wall', 'Autex 3D Wall'),
    '03_Accent_Ceiling_Tiles': ('acoustic_ceiling', 'Autex Accent'),
    '04_Acoustic_Timber': ('acoustic_timber', 'Autex Timber'),
    '05_Cascade_Screens': ('acoustic_screens', 'Autex Cascade'),
    '06_Composition': ('acoustic_wall', 'Autex Composition'),
    '07_Composition_Peel_n_Stick_Tiles': ('acoustic_wall', 'Autex Composition Tiles'),
    '08_Cove': ('acoustic_ceiling', 'Autex Cove'),
    '09_Cube_Acoustic_Panel': ('acoustic_wall', 'Autex Cube'),
    '10_Embrace_Wall_System': ('acoustic_wall', 'Autex Embrace'),
    '11_Frontier': ('acoustic_screens', 'Autex Frontier'),
    '12_Grid_Ceiling_Tiles': ('acoustic_ceiling', 'Autex Grid'),
    '13_Groove_Duet': ('acoustic_wall', 'Autex Groove Duet'),
    '14_Groove_Panel': ('acoustic_wall', 'Autex Groove Panel'),
    '15_Horizon': ('acoustic_ceiling', 'Autex Horizon'),
    '16_Lanes': ('acoustic_wall', 'Autex Lanes'),
    '17_Lattice': ('acoustic_ceiling', 'Autex Lattice'),
    '18_Mirage_Textured_Panel': ('acoustic_wall', 'Autex Mirage'),
    '19_Quietspace_Panel': ('acoustic_wall', 'Autex Quietspace'),
    '20_ReForm': ('acoustic_wall', 'Autex ReForm'),
    '21_Vertiface': ('acoustic_wall', 'Autex Vertiface'),
    '22_Vicinity_Workstation_Screens': ('acoustic_screens', 'Autex Vicinity'),
}

# =============================================================================
# BRAND-WIDE DOCUMENT DETECTION (Duplicates to keep once)
# =============================================================================
BRAND_WIDE_KEYWORDS = [
    'colour', 'color', 'colour range', 'color chart', 'colour chart',
    'care and maintenance', 'care & maintenance', 'cleaning',
    'sustainability', 'environmental', 'ecospecifier', 'greenguard',
    'warranty', 'general brochure', 'brand brochure',
    'acoustic basics', 'acoustic guide', 'nrc guide',
]

def is_brand_wide_doc(filename: str, content: str = '') -> bool:
    """Detect if document is brand-wide (not product-specific)"""
    text = (filename + ' ' + content[:1000]).lower()
    return any(kw in text for kw in BRAND_WIDE_KEYWORDS)

# =============================================================================
# DOC TYPE DETECTION
# =============================================================================
def detect_doc_type(filename: str) -> str:
    """Detect document type from filename"""
    filename_lower = filename.lower()
    
    if any(k in filename_lower for k in ['datasheet', 'data sheet', 'technical']):
        return 'Technical_Data_Sheet'
    elif any(k in filename_lower for k in ['install', 'installation', 'guide']):
        return 'Installation_Guide'
    elif any(k in filename_lower for k in ['brochure', 'flyer', 'catalogue']):
        return 'Product_Guide'
    elif any(k in filename_lower for k in ['colour', 'color']):
        return 'Color_Chart'
    elif any(k in filename_lower for k in ['care', 'maintenance', 'clean']):
        return 'Care_Guide'
    elif any(k in filename_lower for k in ['warranty']):
        return 'Warranty'
    elif any(k in filename_lower for k in ['certificate', 'greenguard', 'declare']):
        return 'Certification'
    elif any(k in filename_lower for k in ['cad', 'dwg', 'revit', 'bim']):
        return 'CAD_Files'
    else:
        return 'Technical_Manual'

# =============================================================================
# DUPLICATE DETECTION
# =============================================================================
seen_file_hashes = {}  # filename_hash -> (trade, product_family, first_folder)
seen_content_hashes = set()

def get_file_hash(content: bytes) -> str:
    """Hash file content for duplicate detection"""
    return hashlib.md5(content).hexdigest()

def get_content_hash(text: str) -> str:
    """Hash text content for chunk duplicate detection"""
    normalized = ' '.join(text.lower().split())
    return hashlib.md5(normalized[:1000].encode()).hexdigest()

# =============================================================================
# MAIN PIPELINE
# =============================================================================
def download_files():
    """Download all PDFs from Supabase Storage with duplicate detection"""
    print("\n" + "="*60)
    print("📥 DOWNLOADING AUTEX PDFs FROM SUPABASE")
    print("="*60)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    os.makedirs(LOCAL_DIR, exist_ok=True)
    
    downloaded = []
    duplicates_skipped = 0
    brand_wide_docs = []
    
    # Get list of product folders
    folders = supabase.storage.from_('product-library').list(BASE_PATH)
    product_folders = [f['name'] for f in folders if f.get('name', '').startswith(('0', '1', '2'))]
    
    print(f"\n📂 Found {len(product_folders)} product folders")
    
    for folder in sorted(product_folders):
        folder_path = f"{BASE_PATH}/{folder}"
        local_folder = os.path.join(LOCAL_DIR, folder)
        os.makedirs(local_folder, exist_ok=True)
        
        # Get trade/product_family for this folder
        trade, product_family = PRODUCT_CLASSIFICATION.get(folder, ('acoustic_general', 'Autex General'))
        
        files = supabase.storage.from_('product-library').list(folder_path)
        pdf_files = [f for f in files if f.get('name', '').endswith('.pdf') and f.get('name') != '_placeholder.pdf']
        
        print(f"\n📂 {folder}: {len(pdf_files)} files")
        
        for f in pdf_files:
            filename = f['name']
            remote_path = f"{folder_path}/{filename}"
            local_path = os.path.join(local_folder, filename)
            
            # Download file
            try:
                response = supabase.storage.from_('product-library').download(remote_path)
                file_hash = get_file_hash(response)
                
                # Check for duplicate file across folders
                if file_hash in seen_file_hashes:
                    prev_folder = seen_file_hashes[file_hash]['folder']
                    print(f"   ⏭️ DUPE: {filename[:40]}... (same as in {prev_folder})")
                    duplicates_skipped += 1
                    continue
                
                # Check if brand-wide doc
                is_brand_wide = is_brand_wide_doc(filename)
                
                # Save file
                with open(local_path, 'wb') as file:
                    file.write(response)
                
                # Track this file
                seen_file_hashes[file_hash] = {
                    'folder': folder,
                    'filename': filename,
                    'trade': trade if not is_brand_wide else 'acoustic_general',
                    'product_family': product_family if not is_brand_wide else 'Autex Brand-Wide',
                }
                
                if is_brand_wide:
                    brand_wide_docs.append(filename)
                    print(f"   🌐 BRAND-WIDE: {filename[:45]}")
                else:
                    print(f"   ⬇️ {filename[:50]}")
                
                downloaded.append((local_path, folder, trade, product_family, is_brand_wide))
                time.sleep(0.1)
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    print(f"\n{'='*60}")
    print(f"📊 DOWNLOAD SUMMARY")
    print(f"{'='*60}")
    print(f"   Total files downloaded: {len(downloaded)}")
    print(f"   Duplicate files skipped: {duplicates_skipped}")
    print(f"   Brand-wide docs found: {len(brand_wide_docs)}")
    
    return downloaded


def process_pdfs(pdf_files: list):
    """Process PDFs with chunk-level duplicate detection"""
    print("\n" + "="*60)
    print("🔬 PROCESSING PDFs WITH DUPLICATE FILTERING")
    print("="*60)
    
    from pdf_chunker_v2 import VisionPDFChunker
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    chunker = VisionPDFChunker(output_dir=OUTPUT_DIR, enable_vision=True)
    
    all_chunks = []
    stats = {
        'files_processed': 0,
        'chunks_created': 0,
        'chunks_skipped_dupe': 0,
        'by_trade': {},
    }
    
    for i, (pdf_path, folder, trade, product_family, is_brand_wide) in enumerate(pdf_files, 1):
        filename = os.path.basename(pdf_path)
        
        # Override trade/family for brand-wide docs
        if is_brand_wide:
            trade = 'acoustic_general'
            product_family = 'Autex Brand-Wide'
        
        print(f"\n[{i}/{len(pdf_files)}] 📄 {filename[:50]}")
        print(f"    🏷️ {trade} | {product_family}")
        
        try:
            chunks = chunker.process_pdf(pdf_path)
            doc_type = detect_doc_type(filename)
            
            chunk_count = 0
            dupe_count = 0
            
            for chunk in chunks:
                chunk_dict = chunk.to_dict() if hasattr(chunk, 'to_dict') else chunk
                content = chunk_dict.get('content', '')
                
                # Check for duplicate content
                content_hash = get_content_hash(content)
                if content_hash in seen_content_hashes:
                    dupe_count += 1
                    continue
                seen_content_hashes.add(content_hash)
                
                # Set metadata
                chunk_dict['trade'] = trade
                chunk_dict['product_family'] = product_family
                chunk_dict['doc_type'] = doc_type
                chunk_dict['brand_name'] = 'Autex'
                chunk_dict['category_code'] = 'C_Interiors'
                chunk_dict['source'] = f"Autex Deep Dive - {filename}"
                chunk_dict['is_brand_wide'] = is_brand_wide
                
                all_chunks.append(chunk_dict)
                chunk_count += 1
                
                # Track by trade
                stats['by_trade'][trade] = stats['by_trade'].get(trade, 0) + 1
            
            stats['files_processed'] += 1
            stats['chunks_created'] += chunk_count
            stats['chunks_skipped_dupe'] += dupe_count
            
            print(f"    ✅ {chunk_count} chunks (skipped {dupe_count} dupes)")
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    # Save chunks
    chunks_file = os.path.join(OUTPUT_DIR, 'all_chunks.json')
    with open(chunks_file, 'w') as f:
        json.dump(all_chunks, f, indent=2, default=str)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 PROCESSING SUMMARY")
    print(f"{'='*60}")
    print(f"   Files processed: {stats['files_processed']}")
    print(f"   Chunks created: {stats['chunks_created']}")
    print(f"   Duplicate chunks skipped: {stats['chunks_skipped_dupe']}")
    print(f"\n   By Trade:")
    for trade, count in sorted(stats['by_trade'].items(), key=lambda x: -x[1]):
        print(f"      • {trade}: {count}")
    
    return all_chunks, stats


def ingest_to_database(chunks: list):
    """Ingest chunks to database with embeddings"""
    print("\n" + "="*60)
    print("💾 INGESTING TO DATABASE")
    print("="*60)
    
    import psycopg2
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    
    batch_size = 20
    total_inserted = 0
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        batch_num = i//batch_size + 1
        total_batches = (len(chunks) + batch_size - 1)//batch_size
        
        if batch_num % 10 == 1 or batch_num == total_batches:
            print(f"   Batch {batch_num}/{total_batches}...")
        
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
                        chunk.get('source', 'Autex Deep Dive'),
                        chunk.get('content', ''),
                        chunk.get('page', 1),
                        chunk.get('doc_type', 'Technical_Manual'),
                        chunk.get('trade', 'acoustic_general'),
                        'Autex',
                        chunk.get('product_family', 'Autex General'),
                        'C_Interiors',
                        85,
                        embeddings[j],
                        'autex_deep_dive'
                    ))
                    total_inserted += 1
                except Exception as e:
                    conn.rollback()
                    print(f"      ❌ Insert error: {e}")
        
        conn.commit()
        time.sleep(0.2)
    
    conn.close()
    print(f"\n   ✅ Inserted {total_inserted} chunks")
    return total_inserted


def main():
    print("\n" + "="*70)
    print("🎵 AUTEX ACOUSTICS DEEP DIVE")
    print("   22 Products | Duplicate Detection | Trade Classification")
    print("="*70)
    
    # Download with file-level duplicate detection
    pdf_files = download_files()
    if not pdf_files:
        print("❌ No PDF files found")
        return
    
    # Process with chunk-level duplicate detection
    chunks, stats = process_pdfs(pdf_files)
    
    # Ingest to database
    if chunks:
        ingest_to_database(chunks)
    
    print("\n" + "="*70)
    print("✅ AUTEX DEEP DIVE COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()
