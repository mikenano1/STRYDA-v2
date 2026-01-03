#!/usr/bin/env python3
"""
Pink Batts Deep Dive - Download and Process Pipeline
Downloads PDFs from Supabase Storage and processes through Vision-enabled chunker
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

# Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
STORAGE_PATH = 'C_Interiors/Pink_Batts'
LOCAL_DIR = '/app/data/ingestion/C_Interiors/Pink_Batts/downloads'
OUTPUT_DIR = '/app/data/processing/pink_batts_deep_dive'

# Trade classification rules for Pink Batts
PINK_BATTS_TRADE_RULES = {
    'wall_insulation': {
        'keywords': ['wall', 'stud', 'r2.2', 'r2.4', 'r2.6', 'r2.8', 'r3.2', 'narrow wall', 
                     'wall product', 'wall installation', 'wall insulation'],
        'product_family': 'Pink Batts Wall'
    },
    'ceiling_insulation': {
        'keywords': ['ceiling', 'r3.2', 'r3.6', 'r4.0', 'r4.3', 'r5.0', 'r6.0', 'r7.0',
                     'ceiling product', 'ceiling installation', 'ceiling insulation'],
        'product_family': 'Pink Batts Ceiling'
    },
    'underfloor_insulation': {
        'keywords': ['underfloor', 'floor', 'snug', 'polyester', 'suspended floor',
                     'underfloor product', 'underfloor installation'],
        'product_family': 'Pink Batts Underfloor'
    },
    'roof_insulation': {
        'keywords': ['roof', 'skillion', 'pitched', 'rafter', 'roof blanket',
                     'skillion roof', 'roof insulation'],
        'product_family': 'Pink Batts Roof'
    },
    'acoustic_insulation': {
        'keywords': ['acoustic', 'sound', 'noise', 'silencer', 'soundproofing',
                     'acoustic insulation', 'noise control'],
        'product_family': 'Pink Batts Acoustic'
    },
    'general_insulation': {
        'keywords': ['thermal', 'r-value', 'glass wool', 'insulation', 'batts'],
        'product_family': 'Pink Batts General'
    },
}

# Document type classification
DOC_TYPE_RULES = {
    'Installation_Guide': ['installation', 'guide', 'install', 'how to'],
    'Technical_Data_Sheet': ['data sheet', 'technical', 'specifications', 'tds'],
    'BPIR_Declaration': ['bpir', 'building product information'],
    'BRANZ_Appraisal': ['branz', 'appraisal', '238', '767', '632'],
    'EPD_Declaration': ['epd', 'environmental product declaration'],
    'Safety_Data_Sheet': ['safety', 'sds', 'msds', 'ingredient', 'fibre dust'],
    'Product_Guide': ['product guide', 'brochure', 'catalogue'],
    'Warranty': ['warranty', 'certificate'],
    'Certification': ['certification', 'iso', 'greenguard', 'ems', 'qa'],
}


def classify_document(filename: str, content: str = '') -> dict:
    """Classify document by trade and doc_type based on filename and content"""
    text = (filename + ' ' + content[:2000]).lower()
    
    # Detect trade
    trade = 'general_insulation'
    product_family = 'Pink Batts General'
    best_score = 0
    
    for trade_key, rules in PINK_BATTS_TRADE_RULES.items():
        score = sum(1 for kw in rules['keywords'] if kw in text)
        if score > best_score:
            best_score = score
            trade = trade_key
            product_family = rules['product_family']
    
    # Detect doc_type
    doc_type = 'Technical_Manual'
    for dtype, keywords in DOC_TYPE_RULES.items():
        if any(kw in text for kw in keywords):
            doc_type = dtype
            break
    
    return {
        'trade': trade,
        'product_family': product_family,
        'doc_type': doc_type
    }


def download_files():
    """Download all PDFs from Supabase Storage"""
    print("\n" + "="*60)
    print("📥 DOWNLOADING PINK BATTS PDFs FROM SUPABASE")
    print("="*60)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    os.makedirs(LOCAL_DIR, exist_ok=True)
    
    # List files
    files = supabase.storage.from_('product-library').list(STORAGE_PATH)
    pdf_files = [f for f in files if f.get('name', '').endswith('.pdf') and f.get('name') != '_placeholder.pdf']
    
    print(f"   Found {len(pdf_files)} PDF files to download")
    
    downloaded = []
    for i, f in enumerate(pdf_files, 1):
        filename = f['name']
        remote_path = f"{STORAGE_PATH}/{filename}"
        local_path = os.path.join(LOCAL_DIR, filename)
        
        # Skip if already downloaded
        if os.path.exists(local_path):
            print(f"   [{i}/{len(pdf_files)}] ⏭️ Already exists: {filename}")
            downloaded.append(local_path)
            continue
        
        try:
            print(f"   [{i}/{len(pdf_files)}] ⬇️ Downloading: {filename}")
            response = supabase.storage.from_('product-library').download(remote_path)
            
            with open(local_path, 'wb') as file:
                file.write(response)
            
            downloaded.append(local_path)
            time.sleep(0.2)  # Rate limiting
            
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
    
    for i, pdf_path in enumerate(pdf_files, 1):
        filename = os.path.basename(pdf_path)
        print(f"\n[{i}/{len(pdf_files)}] 📄 Processing: {filename}")
        
        try:
            # Process PDF
            chunks = chunker.process_pdf(pdf_path)
            
            # Classify each chunk
            classification = classify_document(filename)
            
            for chunk in chunks:
                chunk_dict = chunk.to_dict() if hasattr(chunk, 'to_dict') else chunk
                chunk_dict['trade'] = classification['trade']
                chunk_dict['product_family'] = classification['product_family']
                chunk_dict['doc_type'] = classification['doc_type']
                chunk_dict['brand_name'] = 'Pink Batts'
                chunk_dict['category_code'] = 'C_Interiors'
                all_chunks.append(chunk_dict)
            
            file_stats.append({
                'filename': filename,
                'chunks': len(chunks),
                'trade': classification['trade'],
                'doc_type': classification['doc_type']
            })
            
            print(f"      ✅ {len(chunks)} chunks | trade={classification['trade']} | doc_type={classification['doc_type']}")
            
        except Exception as e:
            print(f"      ❌ Error: {e}")
            file_stats.append({
                'filename': filename,
                'chunks': 0,
                'error': str(e)
            })
    
    # Save all chunks
    chunks_file = os.path.join(OUTPUT_DIR, 'all_chunks.json')
    with open(chunks_file, 'w') as f:
        json.dump(all_chunks, f, indent=2, default=str)
    
    # Save stats
    stats_file = os.path.join(OUTPUT_DIR, 'processing_stats.json')
    stats = {
        'timestamp': datetime.now().isoformat(),
        'total_files': len(pdf_files),
        'total_chunks': len(all_chunks),
        'chunker_stats': chunker.stats,
        'file_stats': file_stats,
        'trade_distribution': {}
    }
    
    # Calculate trade distribution
    for chunk in all_chunks:
        trade = chunk.get('trade', 'unknown')
        stats['trade_distribution'][trade] = stats['trade_distribution'].get(trade, 0) + 1
    
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    print(f"\n{'='*60}")
    print("📊 PROCESSING SUMMARY")
    print(f"{'='*60}")
    print(f"   Total files processed: {len(pdf_files)}")
    print(f"   Total chunks created: {len(all_chunks)}")
    print(f"   Images found: {chunker.stats.get('images_found', 0)}")
    print(f"   Images captioned: {chunker.stats.get('images_captioned', 0)}")
    print(f"   Tables extracted: {chunker.stats.get('tables_extracted', 0)}")
    print(f"\n   Trade Distribution:")
    for trade, count in sorted(stats['trade_distribution'].items(), key=lambda x: -x[1]):
        print(f"      • {trade}: {count}")
    
    print(f"\n   📁 Output saved to: {OUTPUT_DIR}")
    
    return all_chunks, stats


def main():
    print("\n" + "="*70)
    print("🎯 PINK BATTS DEEP DIVE - INGESTION PIPELINE")
    print("="*70)
    
    # Step 1: Download files
    pdf_files = download_files()
    
    if not pdf_files:
        print("❌ No PDF files found to process")
        return
    
    # Step 2: Process through Vision pipeline
    chunks, stats = process_pdfs(pdf_files)
    
    print("\n" + "="*70)
    print("✅ PINK BATTS PROCESSING COMPLETE")
    print("="*70)
    print(f"\nNext step: Run ingestor to add {len(chunks)} chunks to database")
    print(f"   python3 /app/data/processing/ingestor_v2.py \\")
    print(f"      --chunks {OUTPUT_DIR}/all_chunks.json \\")
    print(f"      --brand 'Pink Batts' \\")
    print(f"      --source 'Pink Batts Deep Dive'")


if __name__ == "__main__":
    main()
