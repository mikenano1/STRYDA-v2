#!/usr/bin/env python3
"""
Building Compliance Deep Dive - Vision Re-Ingestion
Re-processes all NZ Building Code documents with Vision pipeline
to capture diagrams, tables, and technical drawings.

Run with batch number: python3 compliance_vision_reingest.py [1-4]
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

BUCKET = 'pdfs'
LOCAL_DIR = '/app/data/ingestion/Compliance/downloads'
OUTPUT_DIR = '/app/data/processing/compliance_vision'

# Compliance document classification
DOC_CLASSIFICATION = {
    # NZ Standards
    'NZS-36042011.pdf': {'category': 'Z_Compliance', 'trade': 'nz_standard', 'family': 'NZS 3604:2011 Timber-framed Buildings'},
    'NZS-42292013.pdf': {'category': 'Z_Compliance', 'trade': 'nz_standard', 'family': 'NZS 4229:2013 Concrete Masonry'},
    'SNZ-HB-3604-2011-Selected-Extracts.pdf': {'category': 'Z_Compliance', 'trade': 'nz_standard', 'family': 'NZS 3604:2011 Handbook'},
    
    # Building Code
    'building-code.pdf': {'category': 'Z_Compliance', 'trade': 'building_code', 'family': 'NZ Building Code'},
    
    # Structure (B1)
    'B1-Structure-Amendment13.pdf': {'category': 'Z_Compliance', 'trade': 'acceptable_solution', 'family': 'B1 Structure AS1'},
    'b1-structure-as1-second-edition.pdf': {'category': 'Z_Compliance', 'trade': 'acceptable_solution', 'family': 'B1 Structure AS1'},
    
    # External Moisture (E2)
    'E2-AS1_4th-Edition-2025.pdf': {'category': 'Z_Compliance', 'trade': 'acceptable_solution', 'family': 'E2 External Moisture AS1'},
    'e2-external-moisture-as1-fourth-edition.pdf': {'category': 'Z_Compliance', 'trade': 'acceptable_solution', 'family': 'E2 External Moisture AS1'},
    'WGANZ-Guide-to-E2-AS1-Amd-10-V1.7-November-2022.pdf': {'category': 'Z_Compliance', 'trade': 'industry_guide', 'family': 'WGANZ E2 Guide'},
    
    # Surface Water (E1)
    'E1-AS1_1st-Edition-Amd12-2024.pdf': {'category': 'Z_Compliance', 'trade': 'acceptable_solution', 'family': 'E1 Surface Water AS1'},
    
    # Internal Moisture (E3)
    'E3-AS1_2nd-Edition-Amd7-2020.pdf': {'category': 'Z_Compliance', 'trade': 'acceptable_solution', 'family': 'E3 Internal Moisture AS1'},
    
    # Fire (C)
    'C-AS1_2nd-Edition_2023.pdf': {'category': 'Z_Compliance', 'trade': 'acceptable_solution', 'family': 'C Fire Safety AS1'},
    'C-AS2_2nd-Edition_2025.pdf': {'category': 'Z_Compliance', 'trade': 'acceptable_solution', 'family': 'C Fire Safety AS2'},
    'C-AS3_Amendment-4_2019-EXPIRED.pdf': {'category': 'Z_Compliance', 'trade': 'acceptable_solution', 'family': 'C Fire Safety AS3'},
    'CAS3-Amendment4-2019-EXPIRED.pdf': {'category': 'Z_Compliance', 'trade': 'acceptable_solution', 'family': 'C Fire Safety AS3'},
    'C-AS4_Amendment-4_2019-EXPIRED.pdf': {'category': 'Z_Compliance', 'trade': 'acceptable_solution', 'family': 'C Fire Safety AS4'},
    'C-AS5_Amendment-4_2019-EXPIRED.pdf': {'category': 'Z_Compliance', 'trade': 'acceptable_solution', 'family': 'C Fire Safety AS5'},
    'C-AS6_Amendment-4_2019-EXPIRED.pdf': {'category': 'Z_Compliance', 'trade': 'acceptable_solution', 'family': 'C Fire Safety AS6'},
    'C-AS7_Amendment-4_2019-EXPIRED.pdf': {'category': 'Z_Compliance', 'trade': 'acceptable_solution', 'family': 'C Fire Safety AS7'},
    'C-VM2_Amendment-6_2020.pdf': {'category': 'Z_Compliance', 'trade': 'verification_method', 'family': 'C Fire Safety VM2'},
    
    # Energy (H1)
    'H1-AS1_6th-Edition.pdf': {'category': 'Z_Compliance', 'trade': 'acceptable_solution', 'family': 'H1 Energy Efficiency AS1'},
    'H1-VM1_6th-Edition-2025.pdf': {'category': 'Z_Compliance', 'trade': 'verification_method', 'family': 'H1 Energy Efficiency VM1'},
    
    # Water/Plumbing (G12/G13)
    'G12-AS1_3rd-Edition-Amd14-2024.pdf': {'category': 'Z_Compliance', 'trade': 'acceptable_solution', 'family': 'G12 Water Supplies AS1'},
    'G13-AS1_3rd-Edition-Amd14-2024.pdf': {'category': 'Z_Compliance', 'trade': 'acceptable_solution', 'family': 'G13 Foul Water AS1'},
    
    # Safety (F)
    'F4-AS1_Amendment-6-2021.pdf': {'category': 'Z_Compliance', 'trade': 'acceptable_solution', 'family': 'F4 Safety from Falling AS1'},
    'F6-AS1_Amendment-3-2021.pdf': {'category': 'Z_Compliance', 'trade': 'acceptable_solution', 'family': 'F6 Visibility in Escape AS1'},
    'F7-AS1_5th-Edition-2023.pdf': {'category': 'Z_Compliance', 'trade': 'acceptable_solution', 'family': 'F7 Warning Systems AS1'},
    
    # Industry Codes & Manuals
    'nz_metal_roofing.pdf': {'category': 'Z_Compliance', 'trade': 'industry_code', 'family': 'NZ Metal Roofing Code of Practice'},
    'Ardex-Waterproofing-Manual.pdf': {'category': 'Z_Compliance', 'trade': 'technical_manual', 'family': 'Ardex Waterproofing Manual'},
    'Internal-WetArea-Membrane-CodeOfPractice_4th-Edition-2020.pdf': {'category': 'Z_Compliance', 'trade': 'industry_code', 'family': 'Wet Area Membrane Code of Practice'},
    
    # GIB Fire/Bracing
    'GIB-Fire-Systems-Manual.pdf': {'category': 'Z_Compliance', 'trade': 'technical_manual', 'family': 'GIB Fire Systems Manual'},
    'GIB-Bracing-Supplement-2016.pdf': {'category': 'Z_Compliance', 'trade': 'technical_manual', 'family': 'GIB Bracing Supplement'},
    'GIB-EzyBrace-Systems-2016.pdf': {'category': 'Z_Compliance', 'trade': 'technical_manual', 'family': 'GIB EzyBrace Systems'},
}

# Batch definitions (split 33 docs into 4 batches)
BATCHES = {
    1: ['NZS-36042011.pdf', 'NZS-42292013.pdf', 'SNZ-HB-3604-2011-Selected-Extracts.pdf', 
        'building-code.pdf', 'B1-Structure-Amendment13.pdf', 'b1-structure-as1-second-edition.pdf',
        'E2-AS1_4th-Edition-2025.pdf', 'e2-external-moisture-as1-fourth-edition.pdf'],
    2: ['C-AS1_2nd-Edition_2023.pdf', 'C-AS2_2nd-Edition_2025.pdf', 'C-AS3_Amendment-4_2019-EXPIRED.pdf',
        'CAS3-Amendment4-2019-EXPIRED.pdf', 'C-AS4_Amendment-4_2019-EXPIRED.pdf', 
        'C-AS5_Amendment-4_2019-EXPIRED.pdf', 'C-AS6_Amendment-4_2019-EXPIRED.pdf',
        'C-AS7_Amendment-4_2019-EXPIRED.pdf', 'C-VM2_Amendment-6_2020.pdf'],
    3: ['H1-AS1_6th-Edition.pdf', 'H1-VM1_6th-Edition-2025.pdf', 'G12-AS1_3rd-Edition-Amd14-2024.pdf',
        'G13-AS1_3rd-Edition-Amd14-2024.pdf', 'F4-AS1_Amendment-6-2021.pdf', 'F6-AS1_Amendment-3-2021.pdf',
        'F7-AS1_5th-Edition-2023.pdf', 'E1-AS1_1st-Edition-Amd12-2024.pdf', 'E3-AS1_2nd-Edition-Amd7-2020.pdf',
        'WGANZ-Guide-to-E2-AS1-Amd-10-V1.7-November-2022.pdf'],
    4: ['nz_metal_roofing.pdf', 'Ardex-Waterproofing-Manual.pdf', 
        'Internal-WetArea-Membrane-CodeOfPractice_4th-Edition-2020.pdf',
        'GIB-Fire-Systems-Manual.pdf', 'GIB-Bracing-Supplement-2016.pdf', 'GIB-EzyBrace-Systems-2016.pdf'],
}

seen_hashes = set()

def get_hash(content):
    if isinstance(content, bytes):
        return hashlib.md5(content).hexdigest()
    return hashlib.md5(content.encode()[:2000]).hexdigest()

def process_batch(batch_num):
    from pdf_chunker_v2 import VisionPDFChunker
    
    print(f"\n{'='*60}")
    print(f"📜 COMPLIANCE BATCH {batch_num} - VISION ENABLED")
    print(f"{'='*60}")
    
    batch_files = BATCHES.get(batch_num, [])
    if not batch_files:
        print(f"❌ Invalid batch number: {batch_num}")
        return 0
    
    print(f"   Processing {len(batch_files)} documents")
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    client = OpenAI(api_key=OPENAI_API_KEY)
    conn = psycopg2.connect(DATABASE_URL)
    
    os.makedirs(LOCAL_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    chunker = VisionPDFChunker(output_dir=OUTPUT_DIR, enable_vision=True)
    
    total_chunks = 0
    total_tables = 0
    total_diagrams = 0
    
    for i, filename in enumerate(batch_files, 1):
        local_path = os.path.join(LOCAL_DIR, filename)
        
        classification = DOC_CLASSIFICATION.get(filename, {
            'category': 'Z_Compliance',
            'trade': 'compliance_general',
            'family': filename.replace('.pdf', '').replace('-', ' ').replace('_', ' ')
        })
        
        print(f"\n   [{i}/{len(batch_files)}] 📄 {filename}")
        print(f"      🏷️ {classification['trade']} | {classification['family']}")
        
        try:
            # Download from Supabase
            print(f"      ⬇️ Downloading...")
            response = supabase.storage.from_(BUCKET).download(filename)
            
            file_hash = get_hash(response)
            if file_hash in seen_hashes:
                print(f"      ⏭️ Duplicate file - skipping")
                continue
            seen_hashes.add(file_hash)
            
            with open(local_path, 'wb') as f:
                f.write(response)
            
            file_size_mb = len(response) / (1024 * 1024)
            print(f"      📦 {file_size_mb:.1f} MB")
            
            # Process with Vision
            print(f"      🔬 Processing with Vision pipeline...")
            chunks = chunker.process_pdf(local_path)
            
            if not chunks:
                print(f"      ⚠️ No chunks extracted")
                continue
            
            # Count tables and diagrams
            doc_tables = sum(1 for c in chunks if (c.to_dict() if hasattr(c, 'to_dict') else c).get('has_table'))
            doc_diagrams = sum(1 for c in chunks if (c.to_dict() if hasattr(c, 'to_dict') else c).get('has_diagram'))
            total_tables += doc_tables
            total_diagrams += doc_diagrams
            
            # Filter duplicates and prepare chunks
            new_chunks = []
            for chunk in chunks:
                chunk_dict = chunk.to_dict() if hasattr(chunk, 'to_dict') else chunk
                content = chunk_dict.get('content', '')
                content_hash = get_hash(content)
                
                if content_hash not in seen_hashes:
                    seen_hashes.add(content_hash)
                    chunk_dict['category_code'] = classification['category']
                    chunk_dict['trade'] = classification['trade']
                    chunk_dict['product_family'] = classification['family']
                    chunk_dict['brand_name'] = 'NZ Building Code'
                    chunk_dict['source'] = filename.replace('.pdf', '')
                    new_chunks.append(chunk_dict)
            
            if not new_chunks:
                print(f"      ⏭️ All chunks duplicates")
                continue
            
            # Embed and insert in batches
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
                                'Compliance_Document',
                                chunk.get('trade'),
                                'NZ Building Code',
                                chunk.get('product_family'),
                                chunk.get('category_code'),
                                95,  # High priority for compliance docs
                                embeddings[k],
                                'compliance_vision_reingest'
                            ))
                            inserted += 1
                    conn.commit()
                except Exception as e:
                    print(f"      ❌ DB error: {e}")
                    conn.rollback()
                
                time.sleep(0.1)
            
            print(f"      ✅ {inserted} chunks ({doc_tables} tables, {doc_diagrams} diagrams)")
            total_chunks += inserted
            
            # Memory cleanup
            gc.collect()
            
            # Clean up local file to save space
            os.remove(local_path)
            
        except Exception as e:
            print(f"      ❌ Error: {e}")
    
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"✅ BATCH {batch_num} COMPLETE")
    print(f"   Chunks: {total_chunks} | Tables: {total_tables} | Diagrams: {total_diagrams}")
    print(f"{'='*60}")
    
    return total_chunks

def main():
    batch_num = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    
    if batch_num == 0:
        # Run all batches
        print("Running all 4 batches...")
        grand_total = 0
        for b in [1, 2, 3, 4]:
            chunks = process_batch(b)
            grand_total += chunks
            gc.collect()
            time.sleep(5)
        print(f"\n🎉 ALL BATCHES COMPLETE: {grand_total} total chunks")
    else:
        process_batch(batch_num)

if __name__ == "__main__":
    main()
