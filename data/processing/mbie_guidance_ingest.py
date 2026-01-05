#!/usr/bin/env python3
"""
MBIE Guidance Documents - Vision-Enabled Ingestion
Processes 3 key MBIE compliance guidance documents:
1. Minor Variation Guidance
2. Schedule 1 Exemptions (Building Work Not Requiring Consent)
3. Tolerances, Materials & Workmanship Guide

Run: python3 mbie_guidance_ingest.py
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
LOCAL_DIR = '/app/data/ingestion/MBIE_Guidance/downloads'
OUTPUT_DIR = '/app/data/processing/mbie_guidance_vision'

# Document classification with proper metadata
# Maps filename patterns to metadata
DOC_CLASSIFICATION = {
    # Minor Variations Guidance
    'minor-variation': {
        'category': 'Z_Compliance',
        'trade': 'mbie_guidance',
        'family': 'MBIE Minor Variations Guidance',
        'brand': 'MBIE',
        'priority': 98  # Very high - authoritative for consent process questions
    },
    'variation': {
        'category': 'Z_Compliance',
        'trade': 'mbie_guidance',
        'family': 'MBIE Minor Variations Guidance',
        'brand': 'MBIE',
        'priority': 98
    },
    
    # Schedule 1 Exemptions (Building Work Not Requiring Consent)
    'schedule-1': {
        'category': 'Z_Compliance',
        'trade': 'mbie_guidance',
        'family': 'MBIE Schedule 1 Exemptions Guide',
        'brand': 'MBIE',
        'priority': 98
    },
    'exemption': {
        'category': 'Z_Compliance',
        'trade': 'mbie_guidance',
        'family': 'MBIE Schedule 1 Exemptions Guide',
        'brand': 'MBIE',
        'priority': 98
    },
    'consent-not-required': {
        'category': 'Z_Compliance',
        'trade': 'mbie_guidance',
        'family': 'MBIE Schedule 1 Exemptions Guide',
        'brand': 'MBIE',
        'priority': 98
    },
    
    # Tolerances Guide
    'tolerance': {
        'category': 'Z_Compliance',
        'trade': 'mbie_guidance',
        'family': 'MBIE Tolerances Materials Workmanship Guide',
        'brand': 'MBIE',
        'priority': 95
    },
    'workmanship': {
        'category': 'Z_Compliance',
        'trade': 'mbie_guidance',
        'family': 'MBIE Tolerances Materials Workmanship Guide',
        'brand': 'MBIE',
        'priority': 95
    },
}

seen_hashes = set()

def get_hash(content):
    if isinstance(content, bytes):
        return hashlib.md5(content).hexdigest()
    return hashlib.md5(content.encode()[:2000]).hexdigest()

def classify_document(filename):
    """Determine document classification based on filename"""
    filename_lower = filename.lower()
    
    for pattern, metadata in DOC_CLASSIFICATION.items():
        if pattern in filename_lower:
            return metadata
    
    # Default classification for unrecognized MBIE docs
    return {
        'category': 'Z_Compliance',
        'trade': 'mbie_guidance',
        'family': filename.replace('.pdf', '').replace('-', ' ').replace('_', ' '),
        'brand': 'MBIE',
        'priority': 90
    }

def main():
    from pdf_chunker_v2 import VisionPDFChunker
    
    print("=" * 70)
    print("📜 MBIE GUIDANCE DOCUMENTS - VISION INGESTION")
    print("=" * 70)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    client = OpenAI(api_key=OPENAI_API_KEY)
    conn = psycopg2.connect(DATABASE_URL)
    
    os.makedirs(LOCAL_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # List files in pdfs bucket that match MBIE guidance patterns
    print("\n🔍 Scanning 'pdfs' bucket for MBIE guidance documents...")
    
    all_files = supabase.storage.from_(BUCKET).list()
    pdf_files = [f['name'] for f in all_files if f['name'].endswith('.pdf')]
    
    # Filter for MBIE guidance docs (look for keywords)
    mbie_keywords = ['mbie', 'minor-variation', 'variation', 'schedule-1', 'exemption', 
                     'tolerance', 'workmanship', 'consent-not-required']
    
    target_files = []
    for f in pdf_files:
        f_lower = f.lower()
        if any(kw in f_lower for kw in mbie_keywords):
            target_files.append(f)
    
    if not target_files:
        print("\n⚠️  No MBIE guidance documents found in bucket.")
        print("   Please upload the PDFs with names containing:")
        print("   • 'minor-variation' or 'variation'")
        print("   • 'schedule-1' or 'exemption' or 'consent-not-required'")
        print("   • 'tolerance' or 'workmanship'")
        
        # Show all available PDFs for reference
        print("\n📁 Available PDFs in bucket:")
        for f in sorted(pdf_files)[:15]:
            print(f"   • {f}")
        if len(pdf_files) > 15:
            print(f"   ... and {len(pdf_files) - 15} more")
        return
    
    print(f"\n📄 Found {len(target_files)} MBIE guidance documents:")
    for f in target_files:
        print(f"   • {f}")
    
    # Initialize Vision chunker
    chunker = VisionPDFChunker(output_dir=OUTPUT_DIR, enable_vision=True)
    
    total_chunks = 0
    total_tables = 0
    total_diagrams = 0
    
    for i, filename in enumerate(target_files, 1):
        local_path = os.path.join(LOCAL_DIR, filename)
        classification = classify_document(filename)
        
        print(f"\n{'='*60}")
        print(f"[{i}/{len(target_files)}] 📄 {filename}")
        print(f"   🏷️  Trade: {classification['trade']}")
        print(f"   📁 Family: {classification['family']}")
        print(f"   ⭐ Priority: {classification['priority']}")
        print("=" * 60)
        
        try:
            # Download from Supabase
            print(f"   ⬇️  Downloading...")
            response = supabase.storage.from_(BUCKET).download(filename)
            
            file_hash = get_hash(response)
            if file_hash in seen_hashes:
                print(f"   ⏭️  Duplicate file - skipping")
                continue
            seen_hashes.add(file_hash)
            
            with open(local_path, 'wb') as f:
                f.write(response)
            
            file_size_mb = len(response) / (1024 * 1024)
            print(f"   📦 Size: {file_size_mb:.1f} MB")
            
            # Process with Vision pipeline
            print(f"   🔬 Processing with Vision AI pipeline...")
            chunks = chunker.process_pdf(local_path)
            
            if not chunks:
                print(f"   ⚠️  No chunks extracted")
                continue
            
            # Count tables and diagrams
            doc_tables = sum(1 for c in chunks if (c.to_dict() if hasattr(c, 'to_dict') else c).get('has_table'))
            doc_diagrams = sum(1 for c in chunks if (c.to_dict() if hasattr(c, 'to_dict') else c).get('has_diagram'))
            total_tables += doc_tables
            total_diagrams += doc_diagrams
            
            print(f"   📊 Extracted: {len(chunks)} chunks ({doc_tables} tables, {doc_diagrams} diagrams)")
            
            # Filter duplicates and prepare chunks
            new_chunks = []
            for chunk in chunks:
                chunk_dict = chunk.to_dict() if hasattr(chunk, 'to_dict') else chunk
                content = chunk_dict.get('content', '')
                content_hash = get_hash(content)
                
                if content_hash not in seen_hashes and len(content.strip()) > 50:
                    seen_hashes.add(content_hash)
                    chunk_dict['category_code'] = classification['category']
                    chunk_dict['trade'] = classification['trade']
                    chunk_dict['product_family'] = classification['family']
                    chunk_dict['brand_name'] = classification['brand']
                    chunk_dict['source'] = filename.replace('.pdf', '')
                    chunk_dict['priority'] = classification['priority']
                    new_chunks.append(chunk_dict)
            
            if not new_chunks:
                print(f"   ⏭️  All chunks were duplicates or too short")
                continue
            
            print(f"   ✅ {len(new_chunks)} unique chunks to insert")
            
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
                                'MBIE_Guidance',
                                chunk.get('trade'),
                                chunk.get('brand_name'),
                                chunk.get('product_family'),
                                chunk.get('category_code'),
                                chunk.get('priority', 95),
                                embeddings[k],
                                'mbie_guidance_vision'
                            ))
                            inserted += 1
                    conn.commit()
                    print(f"   💾 Batch {j//batch_size + 1}: {len(batch)} chunks inserted")
                    
                except Exception as e:
                    print(f"   ❌ DB error: {e}")
                    conn.rollback()
                
                time.sleep(0.1)
            
            print(f"   ✅ Total inserted: {inserted} chunks")
            total_chunks += inserted
            
            # Memory cleanup
            gc.collect()
            
            # Clean up local file
            os.remove(local_path)
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("🎉 MBIE GUIDANCE INGESTION COMPLETE")
    print("=" * 70)
    print(f"   📄 Documents processed: {len(target_files)}")
    print(f"   📊 Total chunks: {total_chunks}")
    print(f"   📋 Tables captured: {total_tables}")
    print(f"   🖼️  Diagrams captured: {total_diagrams}")
    print("=" * 70)
    
    # Reminder to update retrieval logic
    print("\n⚠️  NEXT STEP: Run auto_config_generator.py to update retrieval rules")
    print("   python3 /app/data/processing/auto_config_generator.py")

if __name__ == "__main__":
    main()
