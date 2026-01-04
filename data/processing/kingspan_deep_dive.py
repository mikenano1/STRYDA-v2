#!/usr/bin/env python3
"""
Kingspan Deep Dive - Download and Process Pipeline
Handles TWO product categories:
  1. B_Enclosure/Kingspan - Insulated Panels (wall/roof panels)
  2. C_Interiors/Kingspan_Insulation - Insulation Boards (Kooltherm, Therma, Steico, etc.)

With Vision-enabled processing, duplicate detection, and proper categorization
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

LOCAL_DIR = '/app/data/ingestion/Kingspan/downloads'
OUTPUT_DIR = '/app/data/processing/kingspan_deep_dive'

# =============================================================================
# TWO PRODUCT CATEGORIES
# =============================================================================

# Category 1: Insulated Panels (B_Enclosure)
PANELS_BASE_PATH = 'B_Enclosure/Kingspan'
PANEL_CLASSIFICATION = {
    '01_Architectural_Wall_Panel': {
        'category_code': 'B_Enclosure',
        'trade': 'wall_panel',
        'product_family': 'Kingspan Architectural Wall Panel',
    },
    '02_KRock_Rockspan_Wall_Panel': {
        'category_code': 'B_Enclosure',
        'trade': 'wall_panel',
        'product_family': 'Kingspan K-Rock Rockspan',
    },
    '03_KRock_Firemaster_Wall_Panel': {
        'category_code': 'B_Enclosure',
        'trade': 'fire_rated_panel',
        'product_family': 'Kingspan K-Rock Firemaster',
    },
    '04_Trapezoidal_Wall_Panel': {
        'category_code': 'B_Enclosure',
        'trade': 'wall_panel',
        'product_family': 'Kingspan Trapezoidal Wall',
    },
    '05_Trapezoidal_Roof_Panel': {
        'category_code': 'B_Enclosure',
        'trade': 'roof_panel',
        'product_family': 'Kingspan Trapezoidal Roof',
    },
    '06_Coldstore_Panel': {
        'category_code': 'B_Enclosure',
        'trade': 'coldstore_panel',
        'product_family': 'Kingspan Coldstore',
    },
    '07_Evolution_Panelised_Facade': {
        'category_code': 'B_Enclosure',
        'trade': 'facade_panel',
        'product_family': 'Kingspan Evolution Facade',
    },
    '08_Fivecrown_Roof_Wall_Panel': {
        'category_code': 'B_Enclosure',
        'trade': 'roof_panel',
        'product_family': 'Kingspan Fivecrown',
    },
    '00_Brand_Wide': {
        'category_code': 'B_Enclosure',
        'trade': 'kingspan_panels_general',
        'product_family': 'Kingspan Panels Brand-Wide',
    },
}

# Category 2: Insulation Boards (C_Interiors)
BOARDS_BASE_PATH = 'C_Interiors/Kingspan_Insulation'
BOARD_CLASSIFICATION = {
    # Kooltherm Range
    '01_Kooltherm_K10_G2_Soffit_Board': {
        'category_code': 'C_Interiors',
        'trade': 'soffit_insulation',
        'product_family': 'Kingspan Kooltherm K10 G2',
    },
    '02_Kooltherm_K10_G2W_White_Soffit_Board': {
        'category_code': 'C_Interiors',
        'trade': 'soffit_insulation',
        'product_family': 'Kingspan Kooltherm K10 G2W',
    },
    '03_Kooltherm_K12_Framing_Board': {
        'category_code': 'C_Interiors',
        'trade': 'wall_insulation',
        'product_family': 'Kingspan Kooltherm K12',
    },
    '04_Kooltherm_K17_Insulated_Plasterboard': {
        'category_code': 'C_Interiors',
        'trade': 'wall_insulation',
        'product_family': 'Kingspan Kooltherm K17',
    },
    '05_Kooltherm_K7_Roof_Board': {
        'category_code': 'C_Interiors',
        'trade': 'roof_insulation',
        'product_family': 'Kingspan Kooltherm K7',
    },
    '06_Kooltherm_K5_External_Wall_Board': {
        'category_code': 'C_Interiors',
        'trade': 'wall_insulation',
        'product_family': 'Kingspan Kooltherm K5',
    },
    '07_Kooltherm_K3_Floorboard': {
        'category_code': 'C_Interiors',
        'trade': 'floor_insulation',
        'product_family': 'Kingspan Kooltherm K3',
    },
    '08_Kooltherm_K20_Concrete_Sandwich_Board': {
        'category_code': 'C_Interiors',
        'trade': 'wall_insulation',
        'product_family': 'Kingspan Kooltherm K20',
    },
    # Therma Range
    '09_Therma_TR26_Roof_Insulation': {
        'category_code': 'C_Interiors',
        'trade': 'roof_insulation',
        'product_family': 'Kingspan Therma TR26',
    },
    '10_Therma_TR27_Roof_Insulation': {
        'category_code': 'C_Interiors',
        'trade': 'roof_insulation',
        'product_family': 'Kingspan Therma TR27',
    },
    '11_Therma_TR28_Roof_Insulation': {
        'category_code': 'C_Interiors',
        'trade': 'roof_insulation',
        'product_family': 'Kingspan Therma TR28',
    },
    '12_Therma_TT47_Roof_Insulation': {
        'category_code': 'C_Interiors',
        'trade': 'roof_insulation',
        'product_family': 'Kingspan Therma TT47',
    },
    # Steico Range (Wood Fibre)
    '13_Steico_Universal_Wall_Insulation': {
        'category_code': 'C_Interiors',
        'trade': 'wall_insulation',
        'product_family': 'Kingspan Steico Wall',
    },
    '14_Steico_Universal_Roof_Insulation': {
        'category_code': 'C_Interiors',
        'trade': 'roof_insulation',
        'product_family': 'Kingspan Steico Roof',
    },
    # GreenGuard (Below Grade)
    '15_GreenGuard_G300': {
        'category_code': 'C_Interiors',
        'trade': 'below_grade_insulation',
        'product_family': 'Kingspan GreenGuard G300',
    },
    # Air Cell
    '16_AirCell_Insulated_Tape': {
        'category_code': 'C_Interiors',
        'trade': 'insulation_accessories',
        'product_family': 'Kingspan Air-Cell Tape',
    },
    '17_AirCell_Vapor_Barrier': {
        'category_code': 'C_Interiors',
        'trade': 'insulation_accessories',
        'product_family': 'Kingspan Air-Cell Vapor Barrier',
    },
    '00_Brand_Wide': {
        'category_code': 'C_Interiors',
        'trade': 'kingspan_boards_general',
        'product_family': 'Kingspan Insulation Brand-Wide',
    },
}

# =============================================================================
# BRAND-WIDE DOCUMENT DETECTION
# =============================================================================
BRAND_WIDE_KEYWORDS = [
    'tech guide', 'technical guide', 'product guide', 'catalogue', 'catalog',
    'brochure', 'general', 'overview', 'range', 'all products', 'full range',
    'sustainability', 'environmental', 'warranty', 'terms', 'brand'
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
    
    if any(k in filename_lower for k in ['datasheet', 'data sheet', 'technical data', 'tds', 'pds']):
        return 'Technical_Data_Sheet'
    elif any(k in filename_lower for k in ['install', 'installation', 'fixing', 'laying', 'guide']):
        return 'Installation_Guide'
    elif any(k in filename_lower for k in ['brochure', 'flyer', 'catalogue', 'catalog']):
        return 'Product_Guide'
    elif any(k in filename_lower for k in ['spec', 'specification']):
        return 'Specification'
    elif any(k in filename_lower for k in ['cad', 'dwg', 'detail', 'drawing']):
        return 'CAD_Detail'
    elif any(k in filename_lower for k in ['certificate', 'branz', 'appraisal', 'codemark', 'greentag']):
        return 'Certification'
    elif any(k in filename_lower for k in ['safety', 'sds', 'msds']):
        return 'Safety_Data_Sheet'
    elif any(k in filename_lower for k in ['epd', 'environmental product']):
        return 'EPD'
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
# DOWNLOAD FUNCTION
# =============================================================================
def download_from_path(supabase, base_path: str, classification: dict, category_name: str):
    """Download PDFs from a specific Supabase path"""
    downloaded = []
    duplicates_skipped = 0
    
    print(f"\n📂 Scanning {category_name}: {base_path}")
    
    try:
        folders = supabase.storage.from_('product-library').list(base_path)
        product_folders = [f['name'] for f in folders if f.get('name', '').startswith(('0', '1'))]
    except Exception as e:
        print(f"   ❌ Error listing folders: {e}")
        return [], 0
    
    print(f"   Found {len(product_folders)} product folders")
    
    for folder in sorted(product_folders):
        folder_path = f"{base_path}/{folder}"
        local_folder = os.path.join(LOCAL_DIR, category_name, folder)
        os.makedirs(local_folder, exist_ok=True)
        
        # Get classification
        class_info = classification.get(folder, {
            'category_code': 'C_Interiors',
            'trade': 'kingspan_general',
            'product_family': 'Kingspan General'
        })
        
        try:
            files = supabase.storage.from_('product-library').list(folder_path)
            pdf_files = [f for f in files if f.get('name', '').endswith('.pdf') and f.get('name') != '_placeholder.pdf']
        except Exception as e:
            print(f"   ❌ Error listing {folder}: {e}")
            continue
        
        if not pdf_files:
            continue
            
        print(f"\n   📁 {folder}: {len(pdf_files)} PDFs → {class_info['trade']}")
        
        for f in pdf_files:
            filename = f['name']
            remote_path = f"{folder_path}/{filename}"
            local_path = os.path.join(local_folder, filename)
            
            try:
                response = supabase.storage.from_('product-library').download(remote_path)
                file_hash = get_file_hash(response)
                
                # Check for duplicate
                if file_hash in seen_file_hashes:
                    prev = seen_file_hashes[file_hash]
                    print(f"      ⏭️ DUPE: {filename[:35]}... (same as {prev['folder']})")
                    duplicates_skipped += 1
                    continue
                
                # Check if brand-wide
                is_brand_wide = is_brand_wide_doc(filename) or folder == '00_Brand_Wide'
                
                # Save file
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
                    'classification': class_info,
                    'is_brand_wide': is_brand_wide,
                    'category_name': category_name,
                })
                time.sleep(0.1)
                
            except Exception as e:
                print(f"      ❌ Error: {e}")
    
    return downloaded, duplicates_skipped


def download_files():
    """Download all Kingspan PDFs from both categories"""
    print("\n" + "="*60)
    print("📥 DOWNLOADING KINGSPAN PDFs FROM SUPABASE")
    print("="*60)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    os.makedirs(LOCAL_DIR, exist_ok=True)
    
    all_downloaded = []
    total_dupes = 0
    
    # Download Insulated Panels (B_Enclosure)
    panels, panel_dupes = download_from_path(
        supabase, PANELS_BASE_PATH, PANEL_CLASSIFICATION, 'Panels'
    )
    all_downloaded.extend(panels)
    total_dupes += panel_dupes
    
    # Download Insulation Boards (C_Interiors)
    boards, board_dupes = download_from_path(
        supabase, BOARDS_BASE_PATH, BOARD_CLASSIFICATION, 'Boards'
    )
    all_downloaded.extend(boards)
    total_dupes += board_dupes
    
    print(f"\n{'='*60}")
    print(f"📊 DOWNLOAD SUMMARY")
    print(f"{'='*60}")
    print(f"   Insulated Panels: {len(panels)} files")
    print(f"   Insulation Boards: {len(boards)} files")
    print(f"   Total downloaded: {len(all_downloaded)}")
    print(f"   Duplicates skipped: {total_dupes}")
    
    return all_downloaded


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
        category_name = pdf_info['category_name']
        
        filename = os.path.basename(pdf_path)
        
        # Use brand-wide classification if detected
        if is_brand_wide:
            if category_name == 'Panels':
                category_code = 'B_Enclosure'
                trade = 'kingspan_panels_general'
                product_family = 'Kingspan Panels Brand-Wide'
            else:
                category_code = 'C_Interiors'
                trade = 'kingspan_boards_general'
                product_family = 'Kingspan Insulation Brand-Wide'
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
                chunk_dict['brand_name'] = 'Kingspan'
                chunk_dict['source'] = f"Kingspan Deep Dive - {filename}"
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
                        chunk.get('source', 'Kingspan Deep Dive'),
                        chunk.get('content', ''),
                        chunk.get('page', 1),
                        chunk.get('doc_type', 'Technical_Manual'),
                        chunk.get('trade', 'kingspan_general'),
                        'Kingspan',
                        chunk.get('product_family', 'Kingspan General'),
                        chunk.get('category_code', 'C_Interiors'),
                        85,
                        embeddings[j],
                        'kingspan_deep_dive'
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
    print("🏗️ KINGSPAN DEEP DIVE")
    print("   Insulated Panels (B_Enclosure) + Insulation Boards (C_Interiors)")
    print("   Vision Pipeline | Duplicate Detection | Trade Classification")
    print("="*70)
    
    # Download from both categories
    pdf_files = download_files()
    if not pdf_files:
        print("❌ No PDF files found")
        return
    
    # Process with Vision pipeline
    chunks, stats = process_pdfs(pdf_files)
    
    # Ingest to database
    if chunks:
        ingest_to_database(chunks)
    
    print("\n" + "="*70)
    print("✅ KINGSPAN DEEP DIVE COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()
