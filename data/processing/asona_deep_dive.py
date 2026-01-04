#!/usr/bin/env python3
"""
Asona Acoustics Deep Dive - Download and Process Pipeline
Handles 55+ acoustic products including sub-brands:
  - Asona (core + Triton range)
  - Sonaris, Knauf Danoline, Metapan, OWA, Rondo, Sona, Techsound

With Vision-enabled processing, duplicate detection, and acoustic trade classification
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
DATABASE_URL = os.getenv('DATABASE_URL')

BASE_PATH = 'C_Interiors/Asona_Acoustics'
LOCAL_DIR = '/app/data/ingestion/Asona_Acoustics/downloads'
OUTPUT_DIR = '/app/data/processing/asona_deep_dive'

# =============================================================================
# PRODUCT CLASSIFICATION
# =============================================================================
# Asona is an acoustic products distributor with multiple sub-brands

PRODUCT_CLASSIFICATION = {
    # Asona Core Products
    '01_Asona_Origami': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Origami', 'sub_brand': 'Asona'},
    '02_Asona_Diffuzion': {'trade': 'acoustic_diffuser', 'product_family': 'Asona Diffuzion', 'sub_brand': 'Asona'},
    '03_Asona_Gypclean': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Gypclean', 'sub_brand': 'Asona'},
    '04_Asona_Polyfon_40': {'trade': 'acoustic_panel', 'product_family': 'Asona Polyfon 40', 'sub_brand': 'Asona'},
    '05_Asona_Polyfon_F_Mesh': {'trade': 'acoustic_panel', 'product_family': 'Asona Polyfon F-Mesh', 'sub_brand': 'Asona'},
    '06_Asona_Pyramid_3D': {'trade': 'acoustic_panel', 'product_family': 'Asona Pyramid 3D', 'sub_brand': 'Asona'},
    '07_Asona_Quicklock': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Quicklock', 'sub_brand': 'Asona'},
    '08_Asona_Renew': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Renew', 'sub_brand': 'Asona'},
    '09_Asona_Snaptex': {'trade': 'acoustic_wall', 'product_family': 'Asona Snaptex', 'sub_brand': 'Asona'},
    '10_Asona_Snaptex_Laminate_Finishes': {'trade': 'acoustic_wall', 'product_family': 'Asona Snaptex Laminate', 'sub_brand': 'Asona'},
    '11_Asona_SonaWood_Ceiling_Tiles': {'trade': 'acoustic_ceiling', 'product_family': 'Asona SonaWood Ceiling', 'sub_brand': 'Asona'},
    '12_Asona_SonaWood_Panels': {'trade': 'acoustic_wall', 'product_family': 'Asona SonaWood Panels', 'sub_brand': 'Asona'},
    
    # Asona Triton Range (Mineral Wool Ceiling Tiles)
    '13_Asona_Triton_4': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton 4', 'sub_brand': 'Asona Triton'},
    '14_Asona_Triton_15': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton 15', 'sub_brand': 'Asona Triton'},
    '15_Asona_Triton_25': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton 25', 'sub_brand': 'Asona Triton'},
    '16_Asona_Triton_25_Woodlock': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton 25 Woodlock', 'sub_brand': 'Asona Triton'},
    '17_Asona_Triton_30HD': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton 30HD', 'sub_brand': 'Asona Triton'},
    '18_Asona_Triton_50': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton 50', 'sub_brand': 'Asona Triton'},
    '19_Asona_Triton_50HD': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton 50HD', 'sub_brand': 'Asona Triton'},
    '20_Asona_Triton_75': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton 75', 'sub_brand': 'Asona Triton'},
    '21_Asona_Triton_100': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton 100', 'sub_brand': 'Asona Triton'},
    '22_Asona_Triton_Avant_15': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton Avant 15', 'sub_brand': 'Asona Triton'},
    '23_Asona_Triton_Baffle_Beam': {'trade': 'acoustic_baffle', 'product_family': 'Asona Triton Baffle Beam', 'sub_brand': 'Asona Triton'},
    '24_Asona_Triton_Cloud': {'trade': 'acoustic_cloud', 'product_family': 'Asona Triton Cloud', 'sub_brand': 'Asona Triton'},
    '25_Asona_Triton_Cloud_Hygiene': {'trade': 'acoustic_cloud', 'product_family': 'Asona Triton Cloud Hygiene', 'sub_brand': 'Asona Triton'},
    '26_Asona_Triton_Defender_50': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton Defender 50', 'sub_brand': 'Asona Triton'},
    '27_Asona_Triton_Duo_35': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton Duo 35', 'sub_brand': 'Asona Triton'},
    '28_Asona_Triton_Duo_60': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton Duo 60', 'sub_brand': 'Asona Triton'},
    '29_Asona_Triton_Fabwool': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton Fabwool', 'sub_brand': 'Asona Triton'},
    '30_Asona_Triton_Hygiene': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton Hygiene', 'sub_brand': 'Asona Triton'},
    '31_Asona_Triton_Pull_Panel': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton Pull Panel', 'sub_brand': 'Asona Triton'},
    '32_Asona_Triton_Saab_VF103': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton Saab VF103', 'sub_brand': 'Asona Triton'},
    '33_Asona_Triton_Sports_40': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton Sports 40', 'sub_brand': 'Asona Triton'},
    '34_Asona_Triton_Trio_85': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton Trio 85', 'sub_brand': 'Asona Triton'},
    
    # Asona Other
    '35_Asona_Ultrasound_Perforated_Plasterboard': {'trade': 'perforated_panel', 'product_family': 'Asona Ultrasound', 'sub_brand': 'Asona'},
    
    # Sonaris
    '36_Sonaris_Perforated_Laminates': {'trade': 'perforated_panel', 'product_family': 'Sonaris Perforated Laminates', 'sub_brand': 'Sonaris'},
    
    # Knauf Danoline
    '37_Knauf_Danoline_Solar_Panel': {'trade': 'acoustic_ceiling', 'product_family': 'Knauf Danoline Solar', 'sub_brand': 'Knauf Danoline'},
    '38_Knauf_Danoline_Strat_O_Panel': {'trade': 'acoustic_ceiling', 'product_family': 'Knauf Danoline Strat-O', 'sub_brand': 'Knauf Danoline'},
    
    # Metapan
    '39_Metapan_C_Series': {'trade': 'metal_ceiling', 'product_family': 'Metapan C Series', 'sub_brand': 'Metapan'},
    '40_Metapan_P': {'trade': 'metal_ceiling', 'product_family': 'Metapan P', 'sub_brand': 'Metapan'},
    '41_Metapan_UL_Series': {'trade': 'metal_ceiling', 'product_family': 'Metapan UL Series', 'sub_brand': 'Metapan'},
    
    # OWA
    '42_OWA_Humancare': {'trade': 'acoustic_ceiling', 'product_family': 'OWA Humancare', 'sub_brand': 'OWA'},
    '43_OWA_Symphonia': {'trade': 'acoustic_ceiling', 'product_family': 'OWA Symphonia', 'sub_brand': 'OWA'},
    '44_OWA_Symphonia_Balance': {'trade': 'acoustic_ceiling', 'product_family': 'OWA Symphonia Balance', 'sub_brand': 'OWA'},
    '45_OWA_Symphonia_C': {'trade': 'acoustic_ceiling', 'product_family': 'OWA Symphonia C', 'sub_brand': 'OWA'},
    '46_OWA_Symphonia_Privacy_High_CAC': {'trade': 'acoustic_ceiling', 'product_family': 'OWA Symphonia Privacy', 'sub_brand': 'OWA'},
    
    # Rondo
    '47_Rondo_Don': {'trade': 'ceiling_grid', 'product_family': 'Rondo Don', 'sub_brand': 'Rondo'},
    '48_Rondo_Don_DXW': {'trade': 'ceiling_grid', 'product_family': 'Rondo Don DXW', 'sub_brand': 'Rondo'},
    '49_Rondo_Keylock': {'trade': 'ceiling_grid', 'product_family': 'Rondo Keylock', 'sub_brand': 'Rondo'},
    '50_Rondo_Xpress': {'trade': 'ceiling_grid', 'product_family': 'Rondo Xpress', 'sub_brand': 'Rondo'},
    
    # Sona
    '51_Sona_Acoustic': {'trade': 'acoustic_panel', 'product_family': 'Sona Acoustic', 'sub_brand': 'Sona'},
    '52_Sona_Spray': {'trade': 'acoustic_spray', 'product_family': 'Sona Spray', 'sub_brand': 'Sona'},
    
    # Techsound
    '53_Techsound_FT55': {'trade': 'acoustic_underlay', 'product_family': 'Techsound FT55', 'sub_brand': 'Techsound'},
    '54_Techsound_SY50': {'trade': 'acoustic_underlay', 'product_family': 'Techsound SY50', 'sub_brand': 'Techsound'},
    '55_Techsound_Tube_S': {'trade': 'acoustic_underlay', 'product_family': 'Techsound Tube S', 'sub_brand': 'Techsound'},
    
    # Brand-Wide
    '00_Brand_Wide': {'trade': 'asona_general', 'product_family': 'Asona Brand-Wide', 'sub_brand': 'Asona'},
}

# =============================================================================
# BRAND-WIDE DOCUMENT DETECTION
# =============================================================================
BRAND_WIDE_KEYWORDS = [
    'catalogue', 'catalog', 'brochure', 'general', 'overview', 'range',
    'product guide', 'full range', 'sustainability', 'warranty', 'terms',
    'specification guide', 'all products'
]

def is_brand_wide_doc(filename: str, content: str = '') -> bool:
    text = (filename + ' ' + content[:1000]).lower()
    return any(kw in text for kw in BRAND_WIDE_KEYWORDS)

# =============================================================================
# DOC TYPE DETECTION
# =============================================================================
def detect_doc_type(filename: str) -> str:
    filename_lower = filename.lower()
    
    if any(k in filename_lower for k in ['datasheet', 'data sheet', 'technical data', 'tds', 'pds']):
        return 'Technical_Data_Sheet'
    elif any(k in filename_lower for k in ['install', 'installation', 'fixing', 'guide']):
        return 'Installation_Guide'
    elif any(k in filename_lower for k in ['brochure', 'flyer', 'catalogue', 'catalog']):
        return 'Product_Guide'
    elif any(k in filename_lower for k in ['spec', 'specification']):
        return 'Specification'
    elif any(k in filename_lower for k in ['cad', 'dwg', 'detail', 'drawing']):
        return 'CAD_Detail'
    elif any(k in filename_lower for k in ['certificate', 'branz', 'appraisal', 'codemark']):
        return 'Certification'
    elif any(k in filename_lower for k in ['safety', 'sds', 'msds']):
        return 'Safety_Data_Sheet'
    elif any(k in filename_lower for k in ['nrc', 'acoustic', 'performance']):
        return 'Acoustic_Data'
    elif any(k in filename_lower for k in ['warranty']):
        return 'Warranty'
    else:
        return 'Technical_Manual'

# =============================================================================
# DUPLICATE DETECTION
# =============================================================================
seen_file_hashes = {}
seen_content_hashes = set()

def get_file_hash(content: bytes) -> str:
    return hashlib.md5(content).hexdigest()

def get_content_hash(text: str) -> str:
    normalized = ' '.join(text.lower().split())
    return hashlib.md5(normalized[:1000].encode()).hexdigest()

# =============================================================================
# DOWNLOAD FUNCTION
# =============================================================================
def download_files():
    print("\n" + "="*60)
    print("📥 DOWNLOADING ASONA ACOUSTICS PDFs FROM SUPABASE")
    print("="*60)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    os.makedirs(LOCAL_DIR, exist_ok=True)
    
    downloaded = []
    duplicates_skipped = 0
    
    try:
        folders = supabase.storage.from_('product-library').list(BASE_PATH)
        product_folders = [f['name'] for f in folders if f.get('name', '').startswith(('0', '1', '2', '3', '4', '5'))]
    except Exception as e:
        print(f"   ❌ Error listing folders: {e}")
        return []
    
    print(f"\n📂 Found {len(product_folders)} product folders")
    
    for folder in sorted(product_folders):
        folder_path = f"{BASE_PATH}/{folder}"
        local_folder = os.path.join(LOCAL_DIR, folder)
        os.makedirs(local_folder, exist_ok=True)
        
        classification = PRODUCT_CLASSIFICATION.get(folder, {
            'trade': 'asona_general',
            'product_family': 'Asona General',
            'sub_brand': 'Asona'
        })
        
        try:
            files = supabase.storage.from_('product-library').list(folder_path)
            pdf_files = [f for f in files if f.get('name', '').endswith('.pdf') and f.get('name') != '_placeholder.pdf']
        except Exception as e:
            print(f"   ❌ Error listing {folder}: {e}")
            continue
        
        if not pdf_files:
            continue
            
        print(f"\n   📁 {folder}: {len(pdf_files)} PDFs → {classification['trade']}")
        
        for f in pdf_files:
            filename = f['name']
            remote_path = f"{folder_path}/{filename}"
            local_path = os.path.join(local_folder, filename)
            
            try:
                response = supabase.storage.from_('product-library').download(remote_path)
                file_hash = get_file_hash(response)
                
                if file_hash in seen_file_hashes:
                    prev = seen_file_hashes[file_hash]
                    print(f"      ⏭️ DUPE: {filename[:35]}... (same as {prev['folder']})")
                    duplicates_skipped += 1
                    continue
                
                is_brand_wide = is_brand_wide_doc(filename) or folder == '00_Brand_Wide'
                
                with open(local_path, 'wb') as file:
                    file.write(response)
                
                seen_file_hashes[file_hash] = {'folder': folder, 'filename': filename}
                
                if is_brand_wide:
                    print(f"      🌐 BRAND-WIDE: {filename[:40]}")
                else:
                    print(f"      ⬇️ {filename[:45]}")
                
                downloaded.append({
                    'local_path': local_path,
                    'folder': folder,
                    'classification': classification,
                    'is_brand_wide': is_brand_wide,
                })
                time.sleep(0.1)
                
            except Exception as e:
                print(f"      ❌ Error: {e}")
    
    print(f"\n{'='*60}")
    print(f"📊 DOWNLOAD SUMMARY")
    print(f"{'='*60}")
    print(f"   Total files downloaded: {len(downloaded)}")
    print(f"   Duplicate files skipped: {duplicates_skipped}")
    
    return downloaded


def process_pdfs(pdf_files: list):
    print("\n" + "="*60)
    print("🔬 PROCESSING PDFs WITH VISION PIPELINE")
    print("="*60)
    
    from pdf_chunker_v2 import VisionPDFChunker
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    chunker = VisionPDFChunker(output_dir=OUTPUT_DIR, enable_vision=True)
    
    all_chunks = []
    stats = {
        'files_processed': 0,
        'chunks_created': 0,
        'chunks_skipped_dupe': 0,
        'diagrams_found': 0,
        'tables_found': 0,
        'by_trade': {},
        'by_sub_brand': {},
    }
    
    for i, pdf_info in enumerate(pdf_files, 1):
        pdf_path = pdf_info['local_path']
        folder = pdf_info['folder']
        classification = pdf_info['classification']
        is_brand_wide = pdf_info['is_brand_wide']
        
        filename = os.path.basename(pdf_path)
        
        if is_brand_wide:
            trade = 'asona_general'
            product_family = 'Asona Brand-Wide'
            sub_brand = 'Asona'
        else:
            trade = classification.get('trade', 'asona_general')
            product_family = classification.get('product_family', 'Asona General')
            sub_brand = classification.get('sub_brand', 'Asona')
        
        print(f"\n[{i}/{len(pdf_files)}] 📄 {filename[:50]}")
        print(f"    🏷️ {sub_brand}/{trade} | {product_family}")
        
        try:
            chunks = chunker.process_pdf(pdf_path)
            doc_type = detect_doc_type(filename)
            
            chunk_count = 0
            dupe_count = 0
            diagrams = 0
            tables = 0
            
            for chunk in chunks:
                chunk_dict = chunk.to_dict() if hasattr(chunk, 'to_dict') else chunk
                content = chunk_dict.get('content', '')
                
                content_hash = get_content_hash(content)
                if content_hash in seen_content_hashes:
                    dupe_count += 1
                    continue
                seen_content_hashes.add(content_hash)
                
                if chunk_dict.get('has_diagram'):
                    diagrams += 1
                if chunk_dict.get('has_table'):
                    tables += 1
                
                chunk_dict['category_code'] = 'C_Interiors'
                chunk_dict['trade'] = trade
                chunk_dict['product_family'] = product_family
                chunk_dict['doc_type'] = doc_type
                chunk_dict['brand_name'] = 'Asona'  # Master brand
                chunk_dict['sub_brand'] = sub_brand
                chunk_dict['source'] = f"Asona Deep Dive - {filename}"
                chunk_dict['is_brand_wide'] = is_brand_wide
                
                all_chunks.append(chunk_dict)
                chunk_count += 1
                
                stats['by_trade'][trade] = stats['by_trade'].get(trade, 0) + 1
                stats['by_sub_brand'][sub_brand] = stats['by_sub_brand'].get(sub_brand, 0) + 1
            
            stats['files_processed'] += 1
            stats['chunks_created'] += chunk_count
            stats['chunks_skipped_dupe'] += dupe_count
            stats['diagrams_found'] += diagrams
            stats['tables_found'] += tables
            
            print(f"    ✅ {chunk_count} chunks (skipped {dupe_count} dupes)")
            if diagrams or tables:
                print(f"    📊 Found {diagrams} diagrams, {tables} tables")
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    chunks_file = os.path.join(OUTPUT_DIR, 'all_chunks.json')
    with open(chunks_file, 'w') as f:
        json.dump(all_chunks, f, indent=2, default=str)
    
    print(f"\n{'='*60}")
    print(f"📊 PROCESSING SUMMARY")
    print(f"{'='*60}")
    print(f"   Files processed: {stats['files_processed']}")
    print(f"   Chunks created: {stats['chunks_created']}")
    print(f"   Duplicate chunks skipped: {stats['chunks_skipped_dupe']}")
    print(f"   Diagrams extracted: {stats['diagrams_found']}")
    print(f"   Tables extracted: {stats['tables_found']}")
    print(f"\n   By Trade:")
    for trade, count in sorted(stats['by_trade'].items(), key=lambda x: -x[1]):
        print(f"      • {trade}: {count}")
    print(f"\n   By Sub-Brand:")
    for brand, count in sorted(stats['by_sub_brand'].items(), key=lambda x: -x[1]):
        print(f"      • {brand}: {count}")
    
    return all_chunks, stats


def ingest_to_database(chunks: list):
    print("\n" + "="*60)
    print("💾 INGESTING TO DATABASE")
    print("="*60)
    
    import psycopg2
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    conn = psycopg2.connect(DATABASE_URL)
    
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
                        chunk.get('source', 'Asona Deep Dive'),
                        chunk.get('content', ''),
                        chunk.get('page', 1),
                        chunk.get('doc_type', 'Technical_Manual'),
                        chunk.get('trade', 'asona_general'),
                        'Asona',
                        chunk.get('product_family', 'Asona General'),
                        'C_Interiors',
                        85,
                        embeddings[j],
                        'asona_deep_dive'
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
    print("🎵 ASONA ACOUSTICS DEEP DIVE")
    print("   55+ Products | Multi-Brand | Acoustic Ceiling/Wall/Baffle")
    print("   Vision Pipeline | Duplicate Detection | Trade Classification")
    print("="*70)
    
    pdf_files = download_files()
    if not pdf_files:
        print("❌ No PDF files found")
        return
    
    chunks, stats = process_pdfs(pdf_files)
    
    if chunks:
        ingest_to_database(chunks)
    
    print("\n" + "="*70)
    print("✅ ASONA ACOUSTICS DEEP DIVE COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()
