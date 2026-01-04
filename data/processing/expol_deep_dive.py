#!/usr/bin/env python3
"""
EXPOL Deep Dive - Download and Process Pipeline
Handles multi-category products (Structure, Enclosure, Interiors)
with Vision-enabled processing, duplicate detection, and proper categorization
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

BASE_PATH = 'C_Interiors/Expol'
LOCAL_DIR = '/app/data/ingestion/C_Interiors/Expol/downloads'
OUTPUT_DIR = '/app/data/processing/expol_deep_dive'

# =============================================================================
# PRODUCT CLASSIFICATION - Multi-Category Mapping
# =============================================================================
# EXPOL spans 3 categories: Structure (foundation), Enclosure (drainage), Interiors (insulation)

PRODUCT_CLASSIFICATION = {
    # FOUNDATION/SLAB INSULATION → A_Structure
    '01_Thermoslab_Edge': {
        'category_code': 'A_Structure',
        'trade': 'slab_insulation',
        'product_family': 'Expol Thermoslab Edge',
        'description': 'Slab edge insulation for concrete foundations'
    },
    '02_Slab_X200': {
        'category_code': 'A_Structure',
        'trade': 'slab_insulation',
        'product_family': 'Expol Slab X200',
        'description': 'Under-slab insulation system'
    },
    '03_Thermoslab': {
        'category_code': 'A_Structure',
        'trade': 'slab_insulation',
        'product_family': 'Expol Thermoslab',
        'description': 'Complete slab insulation system'
    },
    '06_Max_Edge': {
        'category_code': 'A_Structure',
        'trade': 'slab_insulation',
        'product_family': 'Expol Max Edge',
        'description': 'Maximum performance slab edge insulation'
    },
    
    # STRUCTURAL FILL → A_Structure
    '11_Tuff_Pods': {
        'category_code': 'A_Structure',
        'trade': 'structural_fill',
        'product_family': 'Expol Tuff Pods',
        'description': 'Void formers for ribraft foundations'
    },
    '12_Geoform_Lightweight_Fill': {
        'category_code': 'A_Structure',
        'trade': 'structural_fill',
        'product_family': 'Expol Geoform',
        'description': 'Lightweight structural fill material'
    },
    
    # DRAINAGE → B_Enclosure
    '09_StyroDrain': {
        'category_code': 'B_Enclosure',
        'trade': 'drainage',
        'product_family': 'Expol StyroDrain',
        'description': 'Drainage board system'
    },
    
    # BOARD INSULATION → C_Interiors
    '04_Platinum_Board': {
        'category_code': 'C_Interiors',
        'trade': 'board_insulation',
        'product_family': 'Expol Platinum Board',
        'description': 'Premium insulation board'
    },
    '05_Extruded_Polystyrene': {
        'category_code': 'C_Interiors',
        'trade': 'board_insulation',
        'product_family': 'Expol XPS',
        'description': 'Extruded polystyrene insulation'
    },
    '07_FastLine': {
        'category_code': 'C_Interiors',
        'trade': 'board_insulation',
        'product_family': 'Expol FastLine',
        'description': 'Fast-install insulation system'
    },
    '08_Imperia_Panel': {
        'category_code': 'C_Interiors',
        'trade': 'board_insulation',
        'product_family': 'Expol Imperia Panel',
        'description': 'High-performance insulation panel'
    },
    
    # UNDERFLOOR/GARAGE → C_Interiors
    '13_Underfloor_Insulation': {
        'category_code': 'C_Interiors',
        'trade': 'underfloor_insulation',
        'product_family': 'Expol Underfloor',
        'description': 'Suspended floor insulation'
    },
    '14_Garage_Door_Insulation': {
        'category_code': 'C_Interiors',
        'trade': 'garage_insulation',
        'product_family': 'Expol Garage Door',
        'description': 'Garage door insulation kit'
    },
    
    # BRAND-WIDE DOCS
    '00_Brand_Wide': {
        'category_code': 'C_Interiors',  # Default category
        'trade': 'expol_general',
        'product_family': 'Expol Brand-Wide',
        'description': 'General EXPOL documentation (Tech Guide 2025)'
    },
}

# =============================================================================
# BRAND-WIDE DOCUMENT DETECTION
# =============================================================================
BRAND_WIDE_KEYWORDS = [
    'tech guide', 'technical guide', 'product guide', 'catalogue', 'catalog',
    'brochure', 'general', 'overview', 'range', 'all products',
    'sustainability', 'environmental', 'warranty', 'terms'
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
    
    if any(k in filename_lower for k in ['datasheet', 'data sheet', 'technical data', 'tds']):
        return 'Technical_Data_Sheet'
    elif any(k in filename_lower for k in ['install', 'installation', 'fixing', 'laying']):
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
    elif any(k in filename_lower for k in ['tech guide', 'technical guide']):
        return 'Technical_Manual'
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
    print("📥 DOWNLOADING EXPOL PDFs FROM SUPABASE")
    print("="*60)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    os.makedirs(LOCAL_DIR, exist_ok=True)
    
    downloaded = []
    duplicates_skipped = 0
    
    # Get list of product folders
    folders = supabase.storage.from_('product-library').list(BASE_PATH)
    product_folders = [f['name'] for f in folders if f.get('name', '').startswith(('0', '1'))]
    
    print(f"\n📂 Found {len(product_folders)} product folders")
    
    for folder in sorted(product_folders):
        folder_path = f"{BASE_PATH}/{folder}"
        local_folder = os.path.join(LOCAL_DIR, folder)
        os.makedirs(local_folder, exist_ok=True)
        
        # Get classification for this folder
        classification = PRODUCT_CLASSIFICATION.get(folder, {
            'category_code': 'C_Interiors',
            'trade': 'expol_general',
            'product_family': 'Expol General'
        })
        
        files = supabase.storage.from_('product-library').list(folder_path)
        pdf_files = [f for f in files if f.get('name', '').endswith('.pdf') and f.get('name') != '_placeholder.pdf']
        
        print(f"\n📂 {folder}: {len(pdf_files)} PDFs → {classification['category_code']}/{classification['trade']}")
        
        for f in pdf_files:
            filename = f['name']
            remote_path = f"{folder_path}/{filename}"
            local_path = os.path.join(local_folder, filename)
            
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
                is_brand_wide = is_brand_wide_doc(filename) or folder == '00_Brand_Wide'
                
                # Save file
                with open(local_path, 'wb') as file:
                    file.write(response)
                
                # Track this file
                seen_file_hashes[file_hash] = {
                    'folder': folder,
                    'filename': filename,
                }
                
                if is_brand_wide:
                    print(f"   🌐 BRAND-WIDE: {filename[:45]}")
                else:
                    print(f"   ⬇️ {filename[:50]}")
                
                downloaded.append({
                    'local_path': local_path,
                    'folder': folder,
                    'classification': classification,
                    'is_brand_wide': is_brand_wide,
                })
                time.sleep(0.1)
                
            except Exception as e:
                print(f"   ❌ Error downloading {filename}: {e}")
    
    print(f"\n{'='*60}")
    print(f"📊 DOWNLOAD SUMMARY")
    print(f"{'='*60}")
    print(f"   Total files downloaded: {len(downloaded)}")
    print(f"   Duplicate files skipped: {duplicates_skipped}")
    
    return downloaded


def process_pdfs(pdf_files: list):
    """Process PDFs with Vision-enabled chunking and duplicate detection"""
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
        'by_category': {},
        'by_trade': {},
    }
    
    for i, pdf_info in enumerate(pdf_files, 1):
        pdf_path = pdf_info['local_path']
        folder = pdf_info['folder']
        classification = pdf_info['classification']
        is_brand_wide = pdf_info['is_brand_wide']
        
        filename = os.path.basename(pdf_path)
        
        # Use brand-wide classification if detected
        if is_brand_wide:
            category_code = 'C_Interiors'
            trade = 'expol_general'
            product_family = 'Expol Brand-Wide'
        else:
            category_code = classification['category_code']
            trade = classification['trade']
            product_family = classification['product_family']
        
        print(f"\n[{i}/{len(pdf_files)}] 📄 {filename[:50]}")
        print(f"    🏷️ {category_code}/{trade} | {product_family}")
        
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
                
                # Check for duplicate content
                content_hash = get_content_hash(content)
                if content_hash in seen_content_hashes:
                    dupe_count += 1
                    continue
                seen_content_hashes.add(content_hash)
                
                # Track diagrams and tables
                if chunk_dict.get('has_diagram'):
                    diagrams += 1
                if chunk_dict.get('has_table'):
                    tables += 1
                
                # Set metadata
                chunk_dict['category_code'] = category_code
                chunk_dict['trade'] = trade
                chunk_dict['product_family'] = product_family
                chunk_dict['doc_type'] = doc_type
                chunk_dict['brand_name'] = 'Expol'
                chunk_dict['source'] = f"Expol Deep Dive - {filename}"
                chunk_dict['is_brand_wide'] = is_brand_wide
                
                all_chunks.append(chunk_dict)
                chunk_count += 1
                
                # Track stats
                stats['by_category'][category_code] = stats['by_category'].get(category_code, 0) + 1
                stats['by_trade'][trade] = stats['by_trade'].get(trade, 0) + 1
            
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
    print(f"   Diagrams extracted: {stats['diagrams_found']}")
    print(f"   Tables extracted: {stats['tables_found']}")
    print(f"\n   By Category:")
    for cat, count in sorted(stats['by_category'].items()):
        print(f"      • {cat}: {count}")
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
                        chunk.get('source', 'Expol Deep Dive'),
                        chunk.get('content', ''),
                        chunk.get('page', 1),
                        chunk.get('doc_type', 'Technical_Manual'),
                        chunk.get('trade', 'expol_general'),
                        'Expol',
                        chunk.get('product_family', 'Expol General'),
                        chunk.get('category_code', 'C_Interiors'),
                        85,  # Priority for manufacturer docs
                        embeddings[j],
                        'expol_deep_dive'
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
    print("🧱 EXPOL DEEP DIVE")
    print("   Multi-Category: Structure | Enclosure | Interiors")
    print("   Vision Pipeline | Duplicate Detection | Trade Classification")
    print("="*70)
    
    # Download with file-level duplicate detection
    pdf_files = download_files()
    if not pdf_files:
        print("❌ No PDF files found")
        return
    
    # Process with Vision pipeline and chunk-level duplicate detection
    chunks, stats = process_pdfs(pdf_files)
    
    # Ingest to database
    if chunks:
        ingest_to_database(chunks)
    
    print("\n" + "="*70)
    print("✅ EXPOL DEEP DIVE COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()
