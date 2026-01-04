#!/usr/bin/env python3
"""
Timber Suppliers Deep Dive - CHH Woodproducts & Red Stag
Vision-enabled processing with auto-detection of timber product types
"""

import os
import sys
import time
import hashlib
import gc

sys.path.insert(0, '/app/backend-minimal')
sys.path.insert(0, '/app/data/processing')

from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

from supabase import create_client
from openai import OpenAI
import psycopg2

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')

LOCAL_DIR = '/app/data/ingestion/Timber_Suppliers/downloads'
OUTPUT_DIR = '/app/data/processing/timber_deep_dive'

# Brand configurations
BRANDS = {
    'CHH_Woodproducts': {
        'path': 'A_Structure/CHH_Woodproducts',
        'brand_name': 'CHH Woodproducts',
        'default_trade': 'structural_timber',
    },
    'Red_Stag': {
        'path': 'A_Structure/Red_Stag',
        'brand_name': 'Red Stag',
        'default_trade': 'structural_timber',
    },
}

# Auto-detect trade from filename/content
TRADE_KEYWORDS = {
    'framing': ['framing', 'laserframe', 'frame', 'stud', 'dwang', 'nog'],
    'treated_timber': ['treated', 'cca', 'losp', 'boron', 'h1', 'h3', 'h4', 'h5', 'azole', 'antisapstain'],
    'structural_timber': ['structural', 'graded', 'sg8', 'sg10', 'sg12', 'msg'],
    'piles': ['pile', 'anchor pile', 'house pile', 'foundation'],
    'posts_rails': ['post', 'rail', 'paling', 'fence', 'landscaping'],
    'plywood': ['plywood', 'ply', 'panel'],
    'lvl': ['lvl', 'laminated veneer', 'hyspan', 'hyjoist'],
    'particle_board': ['particle', 'mdf', 'chipboard'],
    'timber_general': ['specification', 'guide', 'technical', 'mould', 'substitute'],
}

def detect_trade(filename: str, content: str = '') -> str:
    """Auto-detect trade from filename and content"""
    text = (filename + ' ' + content[:2000]).lower()
    
    for trade, keywords in TRADE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return trade
    
    return 'structural_timber'

def detect_product_family(filename: str, brand_name: str) -> str:
    """Extract product family from filename"""
    filename_lower = filename.lower()
    
    # CHH specific products
    if 'laserframe' in filename_lower:
        return f'{brand_name} Laserframe'
    elif 'pinex' in filename_lower:
        return f'{brand_name} Pinex'
    elif 'cca' in filename_lower:
        return f'{brand_name} CCA Treated'
    elif 'losp' in filename_lower or 'azole' in filename_lower:
        return f'{brand_name} LOSP Treated'
    elif 'boron' in filename_lower or 'h1' in filename_lower:
        return f'{brand_name} Boron Treated'
    elif 'antisapstain' in filename_lower:
        return f'{brand_name} Antisapstain'
    
    # Red Stag specific
    elif 'framepro' in filename_lower:
        return f'{brand_name} FramePro'
    elif 'landscaping' in filename_lower:
        return f'{brand_name} Landscaping'
    elif 'structural' in filename_lower:
        return f'{brand_name} Structural'
    
    # Generic
    elif 'sds' in filename_lower or 'msds' in filename_lower:
        return f'{brand_name} Safety Data'
    else:
        return f'{brand_name} General'

def detect_doc_type(filename: str) -> str:
    """Detect document type"""
    filename_lower = filename.lower()
    
    if 'sds' in filename_lower or 'msds' in filename_lower or 'safety' in filename_lower:
        return 'Safety_Data_Sheet'
    elif 'install' in filename_lower or 'specification' in filename_lower:
        return 'Installation_Guide'
    elif 'technical' in filename_lower or 'note' in filename_lower:
        return 'Technical_Note'
    elif 'producer' in filename_lower or 'statement' in filename_lower:
        return 'Certification'
    elif 'guide' in filename_lower:
        return 'Product_Guide'
    else:
        return 'Technical_Data_Sheet'

seen_hashes = set()

def get_hash(content):
    if isinstance(content, bytes):
        return hashlib.md5(content).hexdigest()
    return hashlib.md5(content.encode()[:2000]).hexdigest()

def process_brand(brand_key: str, config: dict):
    """Process a single brand"""
    from pdf_chunker_v2 import VisionPDFChunker
    
    print(f"\n{'='*60}")
    print(f"🌲 Processing: {config['brand_name']}")
    print(f"{'='*60}")
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    client = OpenAI(api_key=OPENAI_API_KEY)
    conn = psycopg2.connect(DATABASE_URL)
    
    local_dir = os.path.join(LOCAL_DIR, brand_key)
    os.makedirs(local_dir, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    chunker = VisionPDFChunker(output_dir=OUTPUT_DIR, enable_vision=True)
    
    # Get PDFs
    files = supabase.storage.from_('product-library').list(config['path'])
    pdf_files = [f for f in files if f.get('name', '').endswith('.pdf') and f['name'] != '_placeholder.pdf']
    
    print(f"   Found {len(pdf_files)} PDFs")
    
    total_chunks = 0
    
    for i, f in enumerate(pdf_files, 1):
        filename = f['name']
        remote_path = f"{config['path']}/{filename}"
        local_path = os.path.join(local_dir, filename)
        
        print(f"\n   [{i}/{len(pdf_files)}] 📄 {filename[:50]}")
        
        try:
            # Download
            response = supabase.storage.from_('product-library').download(remote_path)
            file_hash = get_hash(response)
            
            if file_hash in seen_hashes:
                print(f"      ⏭️ Duplicate file")
                continue
            seen_hashes.add(file_hash)
            
            with open(local_path, 'wb') as file:
                file.write(response)
            
            # Process with Vision
            chunks = chunker.process_pdf(local_path)
            
            if not chunks:
                print(f"      ⚠️ No chunks")
                continue
            
            # Detect metadata
            first_content = chunks[0].to_dict().get('content', '') if hasattr(chunks[0], 'to_dict') else chunks[0].get('content', '')
            trade = detect_trade(filename, first_content)
            product_family = detect_product_family(filename, config['brand_name'])
            doc_type = detect_doc_type(filename)
            
            print(f"      🏷️ {trade} | {product_family}")
            
            # Filter duplicates
            new_chunks = []
            for chunk in chunks:
                chunk_dict = chunk.to_dict() if hasattr(chunk, 'to_dict') else chunk
                content = chunk_dict.get('content', '')
                content_hash = get_hash(content)
                
                if content_hash not in seen_hashes:
                    seen_hashes.add(content_hash)
                    chunk_dict['trade'] = trade
                    chunk_dict['product_family'] = product_family
                    chunk_dict['brand_name'] = config['brand_name']
                    chunk_dict['category_code'] = 'A_Structure'
                    chunk_dict['doc_type'] = doc_type
                    chunk_dict['source'] = f"{config['brand_name']} - {filename}"
                    new_chunks.append(chunk_dict)
            
            if not new_chunks:
                print(f"      ⏭️ All chunks duplicates")
                continue
            
            # Embed and insert
            batch_size = 15
            inserted = 0
            
            for j in range(0, len(new_chunks), batch_size):
                batch = new_chunks[j:j+batch_size]
                texts = [c.get('content', '')[:8000] for c in batch]
                
                try:
                    emb_response = client.embeddings.create(model='text-embedding-3-small', input=texts)
                    embeddings = [e.embedding for e in emb_response.data]
                    
                    with conn.cursor() as cur:
                        for k, chunk in enumerate(batch):
                            cur.execute('''
                                INSERT INTO documents (
                                    source, content, page, doc_type, trade, brand_name,
                                    product_family, category_code, priority, embedding, ingestion_source
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ''', (
                                chunk.get('source'),
                                chunk.get('content', ''),
                                chunk.get('page', 1),
                                chunk.get('doc_type'),
                                chunk.get('trade'),
                                chunk.get('brand_name'),
                                chunk.get('product_family'),
                                'A_Structure',
                                85,
                                embeddings[k],
                                'timber_deep_dive'
                            ))
                            inserted += 1
                    conn.commit()
                except Exception as e:
                    print(f"      ❌ DB error: {e}")
                    conn.rollback()
                
                time.sleep(0.1)
            
            print(f"      ✅ {inserted} chunks")
            total_chunks += inserted
            gc.collect()
            
        except Exception as e:
            print(f"      ❌ Error: {e}")
    
    conn.close()
    print(f"\n   📊 {config['brand_name']} Total: {total_chunks} chunks")
    return total_chunks

def main():
    print("="*60)
    print("🌲 TIMBER SUPPLIERS DEEP DIVE")
    print("   CHH Woodproducts & Red Stag")
    print("   Vision Pipeline | Auto-Detection | NZ Timber Focus")
    print("="*60)
    
    grand_total = 0
    
    for brand_key, config in BRANDS.items():
        chunks = process_brand(brand_key, config)
        grand_total += chunks
        gc.collect()
        time.sleep(2)
    
    print(f"\n{'='*60}")
    print(f"✅ TIMBER SUPPLIERS DEEP DIVE COMPLETE")
    print(f"   Total chunks ingested: {grand_total}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
