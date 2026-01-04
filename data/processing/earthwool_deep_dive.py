#!/usr/bin/env python3
"""
Earthwool Deep Dive - Download and Process Pipeline
Auto-classifies mixed PDFs by doc type and trade
"""

import os
import sys
import json
import time
import re
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

BASE_PATH = 'C_Interiors/Earthwool'
LOCAL_DIR = '/app/data/ingestion/C_Interiors/Earthwool/downloads'
OUTPUT_DIR = '/app/data/processing/earthwool_deep_dive'

# Auto-classification rules for doc_type based on filename
DOC_TYPE_PATTERNS = {
    'Technical_Data_Sheet': ['datasheet', 'data sheet', 'technical', 'specs'],
    'Installation_Guide': ['installation', 'install', 'instructions', 'guide'],
    'BPIR_Declaration': ['bpir', 'building product information'],
    'Certification': ['certificate', 'branz', 'codemark', 'appraisal'],
    'Product_Guide': ['product guide', 'product finder', 'brochure', 'flyer', 'catalogue'],
}

# Trade classification rules for Earthwool
EARTHWOOL_TRADE_RULES = {
    'wall_insulation': {
        'keywords': ['wall', 'wall insulation', 'internal partition', 'stud'],
        'product_family': 'Earthwool Wall'
    },
    'ceiling_insulation': {
        'keywords': ['ceiling', 'skillion', 'roof', 'overhead'],
        'product_family': 'Earthwool Ceiling'
    },
    'underfloor_insulation': {
        'keywords': ['underfloor', 'floor', 'floorshield', 'subfloor'],
        'product_family': 'Earthwool Underfloor'
    },
    'acoustic_insulation': {
        'keywords': ['acoustic', 'sound', 'noise', 'partition'],
        'product_family': 'Earthwool Acoustic'
    },
    'general_insulation': {
        'keywords': ['glasswool', 'glass wool', 'insulation', 'r-value', 'thermal'],
        'product_family': 'Earthwool General'
    },
}


def classify_doc_type(filename: str) -> str:
    """Auto-classify document type from filename"""
    filename_lower = filename.lower()
    
    for doc_type, patterns in DOC_TYPE_PATTERNS.items():
        if any(p in filename_lower for p in patterns):
            return doc_type
    
    return 'Technical_Manual'


def classify_trade(filename: str, content: str = '') -> tuple:
    """Auto-classify trade and product_family from filename and content"""
    text = (filename + ' ' + content[:2000]).lower()
    
    best_trade = 'general_insulation'
    best_family = 'Earthwool General'
    best_score = 0
    
    for trade, rules in EARTHWOOL_TRADE_RULES.items():
        score = sum(1 for kw in rules['keywords'] if kw in text)
        if score > best_score:
            best_score = score
            best_trade = trade
            best_family = rules['product_family']
    
    return best_trade, best_family


def download_files():
    """Download all PDFs from Supabase Storage"""
    print("\n" + "="*60)
    print("📥 DOWNLOADING EARTHWOOL PDFs FROM SUPABASE")
    print("="*60)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    os.makedirs(LOCAL_DIR, exist_ok=True)
    
    # List files directly in Earthwool folder (not in subfolders)
    files = supabase.storage.from_('product-library').list(BASE_PATH)
    pdf_files = [f for f in files if f.get('name', '').endswith('.pdf') and f.get('name') != '_placeholder.pdf']
    
    print(f"\n📂 Found {len(pdf_files)} PDF files")
    
    downloaded = []
    for f in pdf_files:
        filename = f['name']
        remote_path = f"{BASE_PATH}/{filename}"
        local_path = os.path.join(LOCAL_DIR, filename)
        
        if os.path.exists(local_path):
            print(f"   ⏭️ {filename}")
            downloaded.append(local_path)
            continue
        
        try:
            print(f"   ⬇️ {filename}")
            response = supabase.storage.from_('product-library').download(remote_path)
            with open(local_path, 'wb') as file:
                file.write(response)
            downloaded.append(local_path)
            time.sleep(0.2)
        except Exception as e:
            print(f"      ❌ Error: {e}")
    
    print(f"\n✅ Downloaded {len(downloaded)} files")
    return downloaded


def process_pdfs(pdf_files: list):
    """Process PDFs through Vision-enabled chunker with auto-classification"""
    print("\n" + "="*60)
    print("🔬 PROCESSING PDFs WITH AUTO-CLASSIFICATION")
    print("="*60)
    
    from pdf_chunker_v2 import VisionPDFChunker
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    chunker = VisionPDFChunker(output_dir=OUTPUT_DIR, enable_vision=True)
    
    all_chunks = []
    file_stats = []
    
    for i, pdf_path in enumerate(pdf_files, 1):
        filename = os.path.basename(pdf_path)
        print(f"\n[{i}/{len(pdf_files)}] 📄 {filename}")
        
        # Auto-classify from filename
        doc_type = classify_doc_type(filename)
        trade, product_family = classify_trade(filename)
        
        print(f"    📋 Auto-classified: doc_type={doc_type}, trade={trade}")
        
        try:
            chunks = chunker.process_pdf(pdf_path)
            
            for chunk in chunks:
                chunk_dict = chunk.to_dict() if hasattr(chunk, 'to_dict') else chunk
                
                # Refine trade based on content if generic
                if trade == 'general_insulation':
                    content_trade, content_family = classify_trade(filename, chunk_dict.get('content', ''))
                    if content_trade != 'general_insulation':
                        trade = content_trade
                        product_family = content_family
                
                chunk_dict['trade'] = trade
                chunk_dict['product_family'] = product_family
                chunk_dict['doc_type'] = doc_type
                chunk_dict['brand_name'] = 'Earthwool'
                chunk_dict['category_code'] = 'C_Interiors'
                chunk_dict['source'] = f"Earthwool Deep Dive - {filename}"
                all_chunks.append(chunk_dict)
            
            file_stats.append({
                'filename': filename,
                'chunks': len(chunks),
                'doc_type': doc_type,
                'trade': trade
            })
            
            print(f"    ✅ {len(chunks)} chunks")
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
            file_stats.append({'filename': filename, 'error': str(e)})
    
    # Save chunks
    chunks_file = os.path.join(OUTPUT_DIR, 'all_chunks.json')
    with open(chunks_file, 'w') as f:
        json.dump(all_chunks, f, indent=2, default=str)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 PROCESSING SUMMARY")
    print(f"{'='*60}")
    print(f"   Files processed: {len(pdf_files)}")
    print(f"   Chunks created: {len(all_chunks)}")
    print(f"   Tables: {chunker.stats.get('tables_extracted', 0)}")
    
    # Doc type distribution
    doc_types = {}
    trades = {}
    for chunk in all_chunks:
        dt = chunk.get('doc_type', 'Unknown')
        tr = chunk.get('trade', 'Unknown')
        doc_types[dt] = doc_types.get(dt, 0) + 1
        trades[tr] = trades.get(tr, 0) + 1
    
    print(f"\n   Doc Type Distribution:")
    for dt, count in sorted(doc_types.items(), key=lambda x: -x[1]):
        print(f"      • {dt}: {count}")
    
    print(f"\n   Trade Distribution:")
    for tr, count in sorted(trades.items(), key=lambda x: -x[1]):
        print(f"      • {tr}: {count}")
    
    return all_chunks


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
                        chunk.get('source', 'Earthwool Deep Dive'),
                        chunk.get('content', ''),
                        chunk.get('page', 1),
                        chunk.get('doc_type', 'Technical_Manual'),
                        chunk.get('trade', 'general_insulation'),
                        'Earthwool',
                        chunk.get('product_family', 'Earthwool General'),
                        'C_Interiors',
                        85,
                        embeddings[j],
                        'earthwool_deep_dive'
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
    print("🐑 EARTHWOOL DEEP DIVE - AUTO-CLASSIFICATION PIPELINE")
    print("="*70)
    
    pdf_files = download_files()
    if not pdf_files:
        print("❌ No PDF files found")
        return
    
    chunks = process_pdfs(pdf_files)
    
    if chunks:
        ingest_to_database(chunks)
    
    print("\n" + "="*70)
    print("✅ EARTHWOOL DEEP DIVE COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()
