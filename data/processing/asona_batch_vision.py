#!/usr/bin/env python3
"""
Asona Acoustics Deep Dive - BATCHED VISION VERSION
Processes in smaller batches to avoid memory issues
Run with: python3 asona_batch_vision.py [batch_number]
  Batch 1: Folders 01-15 (Asona Core + Triton start)
  Batch 2: Folders 16-30 (Triton continued)
  Batch 3: Folders 31-45 (Triton end + Sub-brands)
  Batch 4: Folders 46-55 (OWA, Rondo, Sona, Techsound)
"""

import os
import sys
import json
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

BASE_PATH = 'C_Interiors/Asona_Acoustics'
LOCAL_DIR = '/app/data/ingestion/Asona_Acoustics/downloads'
OUTPUT_DIR = '/app/data/processing/asona_deep_dive'

# Batch definitions
BATCHES = {
    1: ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15'],
    2: ['16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30'],
    3: ['31', '32', '33', '34', '35', '36', '37', '38', '39', '40', '41', '42', '43', '44', '45'],
    4: ['46', '47', '48', '49', '50', '51', '52', '53', '54', '55'],
}

PRODUCT_CLASSIFICATION = {
    '01_Asona_Origami': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Origami'},
    '02_Asona_Diffuzion': {'trade': 'acoustic_diffuser', 'product_family': 'Asona Diffuzion'},
    '03_Asona_Gypclean': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Gypclean'},
    '04_Asona_Polyfon_40': {'trade': 'acoustic_panel', 'product_family': 'Asona Polyfon 40'},
    '05_Asona_Polyfon_F_Mesh': {'trade': 'acoustic_panel', 'product_family': 'Asona Polyfon F-Mesh'},
    '06_Asona_Pyramid_3D': {'trade': 'acoustic_panel', 'product_family': 'Asona Pyramid 3D'},
    '07_Asona_Quicklock': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Quicklock'},
    '08_Asona_Renew': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Renew'},
    '09_Asona_Snaptex': {'trade': 'acoustic_wall', 'product_family': 'Asona Snaptex'},
    '10_Asona_Snaptex_Laminate_Finishes': {'trade': 'acoustic_wall', 'product_family': 'Asona Snaptex Laminate'},
    '11_Asona_SonaWood_Ceiling_Tiles': {'trade': 'acoustic_ceiling', 'product_family': 'Asona SonaWood Ceiling'},
    '12_Asona_SonaWood_Panels': {'trade': 'acoustic_wall', 'product_family': 'Asona SonaWood Panels'},
    '13_Asona_Triton_4': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton 4'},
    '14_Asona_Triton_15': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton 15'},
    '15_Asona_Triton_25': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton 25'},
    '16_Asona_Triton_25_Woodlock': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton 25 Woodlock'},
    '17_Asona_Triton_30HD': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton 30HD'},
    '18_Asona_Triton_50': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton 50'},
    '19_Asona_Triton_50HD': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton 50HD'},
    '20_Asona_Triton_75': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton 75'},
    '21_Asona_Triton_100': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton 100'},
    '22_Asona_Triton_Avant_15': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton Avant 15'},
    '23_Asona_Triton_Baffle_Beam': {'trade': 'acoustic_baffle', 'product_family': 'Asona Triton Baffle Beam'},
    '24_Asona_Triton_Cloud': {'trade': 'acoustic_cloud', 'product_family': 'Asona Triton Cloud'},
    '25_Asona_Triton_Cloud_Hygiene': {'trade': 'acoustic_cloud', 'product_family': 'Asona Triton Cloud Hygiene'},
    '26_Asona_Triton_Defender_50': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton Defender 50'},
    '27_Asona_Triton_Duo_35': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton Duo 35'},
    '28_Asona_Triton_Duo_60': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton Duo 60'},
    '29_Asona_Triton_Fabwool': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton Fabwool'},
    '30_Asona_Triton_Hygiene': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton Hygiene'},
    '31_Asona_Triton_Pull_Panel': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton Pull Panel'},
    '32_Asona_Triton_Saab_VF103': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton Saab VF103'},
    '33_Asona_Triton_Sports_40': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton Sports 40'},
    '34_Asona_Triton_Trio_85': {'trade': 'acoustic_ceiling', 'product_family': 'Asona Triton Trio 85'},
    '35_Asona_Ultrasound_Perforated_Plasterboard': {'trade': 'perforated_panel', 'product_family': 'Asona Ultrasound'},
    '36_Sonaris_Perforated_Laminates': {'trade': 'perforated_panel', 'product_family': 'Sonaris Perforated'},
    '37_Knauf_Danoline_Solar_Panel': {'trade': 'acoustic_ceiling', 'product_family': 'Knauf Danoline Solar'},
    '38_Knauf_Danoline_Strat_O_Panel': {'trade': 'acoustic_ceiling', 'product_family': 'Knauf Danoline Strat-O'},
    '39_Metapan_C_Series': {'trade': 'metal_ceiling', 'product_family': 'Metapan C Series'},
    '40_Metapan_P': {'trade': 'metal_ceiling', 'product_family': 'Metapan P'},
    '41_Metapan_UL_Series': {'trade': 'metal_ceiling', 'product_family': 'Metapan UL Series'},
    '42_OWA_Humancare': {'trade': 'acoustic_ceiling', 'product_family': 'OWA Humancare'},
    '43_OWA_Symphonia': {'trade': 'acoustic_ceiling', 'product_family': 'OWA Symphonia'},
    '44_OWA_Symphonia_Balance': {'trade': 'acoustic_ceiling', 'product_family': 'OWA Symphonia Balance'},
    '45_OWA_Symphonia_C': {'trade': 'acoustic_ceiling', 'product_family': 'OWA Symphonia C'},
    '46_OWA_Symphonia_Privacy_High_CAC': {'trade': 'acoustic_ceiling', 'product_family': 'OWA Symphonia Privacy'},
    '47_Rondo_Don': {'trade': 'ceiling_grid', 'product_family': 'Rondo Don'},
    '48_Rondo_Don_DXW': {'trade': 'ceiling_grid', 'product_family': 'Rondo Don DXW'},
    '49_Rondo_Keylock': {'trade': 'ceiling_grid', 'product_family': 'Rondo Keylock'},
    '50_Rondo_Xpress': {'trade': 'ceiling_grid', 'product_family': 'Rondo Xpress'},
    '51_Sona_Acoustic': {'trade': 'acoustic_panel', 'product_family': 'Sona Acoustic'},
    '52_Sona_Spray': {'trade': 'acoustic_spray', 'product_family': 'Sona Spray'},
    '53_Techsound_FT55': {'trade': 'acoustic_underlay', 'product_family': 'Techsound FT55'},
    '54_Techsound_SY50': {'trade': 'acoustic_underlay', 'product_family': 'Techsound SY50'},
    '55_Techsound_Tube_S': {'trade': 'acoustic_underlay', 'product_family': 'Techsound Tube S'},
    '00_Brand_Wide': {'trade': 'asona_general', 'product_family': 'Asona Brand-Wide'},
}

# Global duplicate tracking (persisted between batches)
HASH_FILE = '/app/data/processing/asona_seen_hashes.json'

def load_seen_hashes():
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_seen_hashes(hashes):
    with open(HASH_FILE, 'w') as f:
        json.dump(list(hashes), f)

def get_hash(content):
    if isinstance(content, bytes):
        return hashlib.md5(content).hexdigest()
    return hashlib.md5(content.encode()[:2000]).hexdigest()

def process_batch(batch_num):
    from pdf_chunker_v2 import VisionPDFChunker
    
    print(f"\n{'='*60}")
    print(f"🎵 ASONA BATCH {batch_num} - VISION ENABLED")
    print(f"{'='*60}")
    
    batch_prefixes = BATCHES.get(batch_num, [])
    if not batch_prefixes:
        print(f"❌ Invalid batch number: {batch_num}")
        return
    
    print(f"   Processing folders starting with: {batch_prefixes}")
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    client = OpenAI(api_key=OPENAI_API_KEY)
    conn = psycopg2.connect(DATABASE_URL)
    
    os.makedirs(LOCAL_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    chunker = VisionPDFChunker(output_dir=OUTPUT_DIR, enable_vision=True)
    seen_hashes = load_seen_hashes()
    
    # Get matching folders
    all_folders = supabase.storage.from_('product-library').list(BASE_PATH)
    folders = [f['name'] for f in all_folders 
               if any(f.get('name', '').startswith(p) for p in batch_prefixes)]
    
    print(f"   Found {len(folders)} folders for this batch")
    
    total_chunks = 0
    total_files = 0
    
    for folder in sorted(folders):
        folder_path = f"{BASE_PATH}/{folder}"
        local_folder = os.path.join(LOCAL_DIR, folder)
        os.makedirs(local_folder, exist_ok=True)
        
        classification = PRODUCT_CLASSIFICATION.get(folder, {
            'trade': 'asona_general', 'product_family': 'Asona General'
        })
        
        files = supabase.storage.from_('product-library').list(folder_path)
        pdf_files = [f for f in files if f.get('name', '').endswith('.pdf') 
                     and f.get('name') != '_placeholder.pdf']
        
        if not pdf_files:
            continue
        
        print(f"\n📁 {folder}: {len(pdf_files)} PDFs → {classification['trade']}")
        
        for f in pdf_files:
            filename = f['name']
            remote_path = f"{folder_path}/{filename}"
            local_path = os.path.join(local_folder, filename)
            
            try:
                # Download
                response = supabase.storage.from_('product-library').download(remote_path)
                file_hash = get_hash(response)
                
                if file_hash in seen_hashes:
                    print(f"   ⏭️ DUPE: {filename[:40]}")
                    continue
                seen_hashes.add(file_hash)
                
                with open(local_path, 'wb') as file:
                    file.write(response)
                
                # Process with Vision
                print(f"   📄 Processing: {filename[:45]}")
                chunks = chunker.process_pdf(local_path)
                
                if not chunks:
                    print(f"      ⚠️ No chunks extracted")
                    continue
                
                # Filter and prepare chunks
                new_chunks = []
                for chunk in chunks:
                    chunk_dict = chunk.to_dict() if hasattr(chunk, 'to_dict') else chunk
                    content = chunk_dict.get('content', '')
                    content_hash = get_hash(content)
                    
                    if content_hash not in seen_hashes:
                        seen_hashes.add(content_hash)
                        chunk_dict['trade'] = classification['trade']
                        chunk_dict['product_family'] = classification['product_family']
                        chunk_dict['brand_name'] = 'Asona'
                        chunk_dict['category_code'] = 'C_Interiors'
                        chunk_dict['source'] = f"Asona Deep Dive - {filename}"
                        new_chunks.append(chunk_dict)
                
                if not new_chunks:
                    print(f"      ⏭️ All chunks were duplicates")
                    continue
                
                # Embed and insert
                batch_size = 15
                inserted = 0
                
                for i in range(0, len(new_chunks), batch_size):
                    batch = new_chunks[i:i+batch_size]
                    texts = [c.get('content', '')[:8000] for c in batch]
                    
                    try:
                        emb_response = client.embeddings.create(
                            model='text-embedding-3-small', input=texts
                        )
                        embeddings = [e.embedding for e in emb_response.data]
                        
                        with conn.cursor() as cur:
                            for j, chunk in enumerate(batch):
                                cur.execute('''
                                    INSERT INTO documents (
                                        source, content, page, doc_type, trade, brand_name,
                                        product_family, category_code, priority, embedding, 
                                        ingestion_source
                                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ''', (
                                    chunk.get('source'),
                                    chunk.get('content', ''),
                                    chunk.get('page', 1),
                                    chunk.get('doc_type', 'Technical_Manual'),
                                    chunk.get('trade'),
                                    'Asona',
                                    chunk.get('product_family'),
                                    'C_Interiors',
                                    85,
                                    embeddings[j],
                                    'asona_deep_dive_vision'
                                ))
                                inserted += 1
                        conn.commit()
                    except Exception as e:
                        print(f"      ❌ DB error: {e}")
                        conn.rollback()
                    
                    time.sleep(0.1)
                
                print(f"      ✅ {inserted} chunks inserted")
                total_chunks += inserted
                total_files += 1
                
                # Memory cleanup after each file
                gc.collect()
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        # Save hashes after each folder
        save_seen_hashes(seen_hashes)
    
    conn.close()
    save_seen_hashes(seen_hashes)
    
    print(f"\n{'='*60}")
    print(f"✅ BATCH {batch_num} COMPLETE")
    print(f"   Files: {total_files} | Chunks: {total_chunks}")
    print(f"{'='*60}")
    
    return total_chunks

def main():
    batch_num = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    
    if batch_num == 0:
        # Run all batches
        print("Running all 4 batches...")
        total = 0
        for b in [1, 2, 3, 4]:
            total += process_batch(b) or 0
            gc.collect()
            time.sleep(5)
        print(f"\n🎉 ALL BATCHES COMPLETE: {total} total chunks")
    else:
        process_batch(batch_num)

if __name__ == "__main__":
    main()
