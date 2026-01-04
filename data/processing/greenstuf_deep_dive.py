#!/usr/bin/env python3
"""
GreenStuf Deep Dive - Download and Process Pipeline
Downloads PDFs from Supabase Storage and ingests with trade-aware tagging
"""

import os
import sys
import json
import time
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

BASE_PATH = 'C_Interiors/GreenStuf'
LOCAL_DIR = '/app/data/ingestion/C_Interiors/GreenStuf/downloads'
OUTPUT_DIR = '/app/data/processing/greenstuf_deep_dive'

# Folder to doc_type mapping
FOLDER_DOC_TYPES = {
    '1_Data_Sheets': 'Technical_Data_Sheet',
    '2_Install_Guides': 'Installation_Guide',
    '3_Product_List_Brochures': 'Product_Guide',
    '4_Warranty_Guarantee': 'Warranty',
}

# Trade classification rules for GreenStuf products
GREENSTUF_TRADE_RULES = {
    'wall_insulation': {
        'keywords': ['wall', 'wall section', 'wall insulation', 'interior wall', 'stud', 'bib', 'building blanket'],
        'product_family': 'GreenStuf Wall'
    },
    'ceiling_insulation': {
        'keywords': ['ceiling', 'ceiling blanket', 'ceiling insulation', 'overhead', 'attic'],
        'product_family': 'GreenStuf Ceiling'
    },
    'underfloor_insulation': {
        'keywords': ['underfloor', 'floor', 'subfloor', 'suspended floor'],
        'product_family': 'GreenStuf Underfloor'
    },
    'roof_insulation': {
        'keywords': ['roof', 'skillion', 'rafter', 'pitched roof', 'soffit'],
        'product_family': 'GreenStuf Roof'
    },
    'acoustic_insulation': {
        'keywords': ['acoustic', 'sound', 'noise', 'baffle', 'absorber', 'soundproofing', 'aab', 'asb'],
        'product_family': 'GreenStuf Acoustic'
    },
    'duct_insulation': {
        'keywords': ['duct', 'hvac', 'liner', 'duct liner', 'duct wrap', 'adw', 'ard'],
        'product_family': 'GreenStuf Duct'
    },
    'masonry_insulation': {
        'keywords': ['masonry', 'block', 'concrete block', 'masonry wall'],
        'product_family': 'GreenStuf Masonry'
    },
    'general_insulation': {
        'keywords': ['thermal', 'polyester', 'insulation', 'r-value', 'wool', 'greenstuf'],
        'product_family': 'GreenStuf General'
    },
}


def classify_document(filename: str, folder: str, content: str = '') -> dict:
    """Classify document by trade and doc_type"""
    text = (filename + ' ' + content[:2000]).lower()
    
    doc_type = FOLDER_DOC_TYPES.get(folder, 'Technical_Manual')
    
    trade = 'general_insulation'
    product_family = 'GreenStuf General'
    best_score = 0
    
    for trade_key, rules in GREENSTUF_TRADE_RULES.items():
        score = sum(1 for kw in rules['keywords'] if kw in text)
        if score > best_score:
            best_score = score
            trade = trade_key
            product_family = rules['product_family']
    
    return {
        'trade': trade,
        'product_family': product_family,
        'doc_type': doc_type
    }


def download_files():
    """Download all PDFs from Supabase Storage"""
    print("\n" + "="*60)
    print("📥 DOWNLOADING GREENSTUF PDFs FROM SUPABASE")
    print("="*60)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    os.makedirs(LOCAL_DIR, exist_ok=True)
    
    downloaded = []
    
    for folder in FOLDER_DOC_TYPES.keys():
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
                print(f"   ⏭️ {filename}")
                downloaded.append((local_path, folder))
                continue
            
            try:
                print(f"   ⬇️ {filename}")
                response = supabase.storage.from_('product-library').download(remote_path)
                with open(local_path, 'wb') as file:
                    file.write(response)
                downloaded.append((local_path, folder))
                time.sleep(0.2)
            except Exception as e:
                print(f"      ❌ Error: {e}")
    
    print(f"\n✅ Downloaded {len(downloaded)} files")
    return downloaded


def process_pdfs(pdf_files: list):
    """Process PDFs through Vision-enabled chunker"""
    print("\n" + "="*60)
    print("🔬 PROCESSING PDFs WITH VISION PIPELINE")
    print("="*60)
    
    from pdf_chunker_v2 import VisionPDFChunker
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    chunker = VisionPDFChunker(output_dir=OUTPUT_DIR, enable_vision=True)
    
    all_chunks = []
    file_stats = []
    
    for i, (pdf_path, folder) in enumerate(pdf_files, 1):
        filename = os.path.basename(pdf_path)
        print(f"\n[{i}/{len(pdf_files)}] 📄 {filename}")
        
        try:
            chunks = chunker.process_pdf(pdf_path)
            classification = classify_document(filename, folder)
            
            for chunk in chunks:
                chunk_dict = chunk.to_dict() if hasattr(chunk, 'to_dict') else chunk
                chunk_dict['trade'] = classification['trade']
                chunk_dict['product_family'] = classification['product_family']
                chunk_dict['doc_type'] = classification['doc_type']
                chunk_dict['brand_name'] = 'GreenStuf'
                chunk_dict['category_code'] = 'C_Interiors'
                chunk_dict['source'] = f"GreenStuf Deep Dive - {filename}"
                all_chunks.append(chunk_dict)
            
            file_stats.append({
                'filename': filename,
                'folder': folder,
                'chunks': len(chunks),
                'trade': classification['trade'],
                'doc_type': classification['doc_type']
            })
            
            print(f"    ✅ {len(chunks)} chunks | trade={classification['trade']}")
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
            file_stats.append({'filename': filename, 'error': str(e)})
    
    # Save chunks
    chunks_file = os.path.join(OUTPUT_DIR, 'all_chunks.json')
    with open(chunks_file, 'w') as f:
        json.dump(all_chunks, f, indent=2, default=str)
    
    print(f"\n{'='*60}")
    print(f"📊 PROCESSING SUMMARY")
    print(f"{'='*60}")
    print(f"   Files processed: {len(pdf_files)}")
    print(f"   Chunks created: {len(all_chunks)}")
    print(f"   Tables: {chunker.stats.get('tables_extracted', 0)}")
    print(f"   Images captioned: {chunker.stats.get('images_captioned', 0)}")
    
    return all_chunks


def ingest_to_database(chunks: list):
    """Ingest chunks to database with embeddings"""
    print("\n" + "="*60)
    print("💾 INGESTING TO DATABASE")
    print("="*60)
    
    import psycopg2
    import psycopg2.extras
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    
    batch_size = 20
    total_inserted = 0
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        print(f"   Batch {i//batch_size + 1}/{(len(chunks) + batch_size - 1)//batch_size}...")
        
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
                        chunk.get('source', 'GreenStuf Deep Dive'),
                        chunk.get('content', ''),
                        chunk.get('page', 1),
                        chunk.get('doc_type', 'Technical_Manual'),
                        chunk.get('trade', 'general_insulation'),
                        'GreenStuf',
                        chunk.get('product_family', 'GreenStuf General'),
                        'C_Interiors',
                        85,
                        embeddings[j],
                        'greenstuf_deep_dive'
                    ))
                    total_inserted += 1
                except Exception as e:
                    conn.rollback()
                    print(f"      ❌ Insert error: {e}")
        
        conn.commit()
        time.sleep(0.3)
    
    conn.close()
    print(f"\n✅ Inserted {total_inserted} chunks")
    return total_inserted


def main():
    print("\n" + "="*70)
    print("🌿 GREENSTUF DEEP DIVE - INGESTION PIPELINE")
    print("="*70)
    
    pdf_files = download_files()
    if not pdf_files:
        print("❌ No PDF files found")
        return
    
    chunks = process_pdfs(pdf_files)
    
    if chunks:
        ingest_to_database(chunks)
    
    print("\n" + "="*70)
    print("✅ GREENSTUF DEEP DIVE COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()
