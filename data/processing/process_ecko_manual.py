#!/usr/bin/env python3
"""
STRYDA Big Brain - ECKO MANUAL INGESTION PROCESSOR
Processes manually uploaded Ecko catalogue PDFs

Usage:
    python process_ecko_manual.py

Drop PDFs into: /app/data/ingestion/manual_upload/Ecko/
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from glob import glob

sys.path.insert(0, '/app/backend-minimal')
from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

# Configuration
INPUT_DIR = "/app/data/ingestion/manual_upload/Ecko"
OUTPUT_DIR = "/app/data/processing/ecko_manual"
CHUNKER_SCRIPT = "/app/data/processing/pdf_chunker_v2.py"
INGESTOR_SCRIPT = "/app/data/processing/ingestor.py"

# Ecko metadata
ECKO_CONFIG = {
    "brand": "Ecko",
    "category": "F_Manufacturers",
    "product_family": "T-Rex Screws Fasteners",
    "doc_type": "Product_Catalog",
    "trade": "fasteners",
    "source": "Ecko Master Catalogue (Manual Upload)",
    "priority": 85,  # High priority for PlaceMakers captain brand
    "retailers": ["PlaceMakers", "ITM"]
}


def check_for_pdfs():
    """Check if any PDFs are in the drop zone"""
    pdf_files = glob(os.path.join(INPUT_DIR, "*.pdf"))
    pdf_files += glob(os.path.join(INPUT_DIR, "*.PDF"))
    return pdf_files


def process_ecko_upload():
    """Process all PDFs in the Ecko manual upload folder"""
    
    print("=" * 60)
    print("🦎 ECKO MANUAL INGESTION PROCESSOR")
    print("=" * 60)
    print(f"⏰ Started: {datetime.now().isoformat()}")
    print(f"📂 Drop zone: {INPUT_DIR}")
    
    # Check for PDFs
    pdf_files = check_for_pdfs()
    
    if not pdf_files:
        print("\n⚠️ No PDF files found in drop zone!")
        print(f"   Please upload Ecko catalogue PDFs to:")
        print(f"   {INPUT_DIR}")
        return False
    
    print(f"\n📄 Found {len(pdf_files)} PDF(s) to process:")
    for pdf in pdf_files:
        size_mb = os.path.getsize(pdf) / 1024 / 1024
        print(f"   • {os.path.basename(pdf)} ({size_mb:.1f} MB)")
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Step 1: Run Vision Pipeline
    print("\n" + "=" * 60)
    print("🔬 STEP 1: Vision Pipeline Processing")
    print("=" * 60)
    
    cmd = f'python3 "{CHUNKER_SCRIPT}" --input "{INPUT_DIR}" --output "{OUTPUT_DIR}"'
    print(f"   Running: {cmd}")
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=1800)
    
    if result.returncode != 0:
        print(f"   ❌ Vision pipeline failed!")
        print(f"   Stderr: {result.stderr[-500:]}")
        return False
    
    # Check for chunks file
    chunks_file = os.path.join(OUTPUT_DIR, "chunks.json")
    if not os.path.exists(chunks_file):
        print("   ❌ No chunks.json generated!")
        return False
    
    # Load and count chunks
    with open(chunks_file) as f:
        chunks = json.load(f)
    
    print(f"   ✅ Extracted {len(chunks)} chunks")
    
    # Show chunk type breakdown
    chunk_types = {}
    for chunk in chunks:
        ct = chunk.get('chunk_type', 'unknown')
        chunk_types[ct] = chunk_types.get(ct, 0) + 1
    
    print(f"   📊 Breakdown: {chunk_types}")
    
    # Step 2: Ingest with Ecko metadata
    print("\n" + "=" * 60)
    print("🔬 STEP 2: Ingesting into Database")
    print("=" * 60)
    
    ingest_cmd = f'''python3 "{INGESTOR_SCRIPT}" \
        --chunks "{chunks_file}" \
        --brand "{ECKO_CONFIG['brand']}" \
        --category "{ECKO_CONFIG['category']}" \
        --doc-type "{ECKO_CONFIG['doc_type']}" \
        --product-family "{ECKO_CONFIG['product_family']}" \
        --trade "{ECKO_CONFIG['trade']}" \
        --source "{ECKO_CONFIG['source']}" \
        --priority {ECKO_CONFIG['priority']}'''
    
    print(f"   Brand: {ECKO_CONFIG['brand']}")
    print(f"   Retailers: {ECKO_CONFIG['retailers']}")
    print(f"   Priority: {ECKO_CONFIG['priority']}")
    
    result = subprocess.run(ingest_cmd, shell=True, capture_output=True, text=True, timeout=1200)
    
    # Print output
    if result.stdout:
        print(result.stdout[-1000:])
    
    if result.returncode != 0:
        print(f"   ❌ Ingestion failed!")
        print(f"   Stderr: {result.stderr[-500:]}")
        return False
    
    # Check stats
    stats_file = os.path.join(OUTPUT_DIR, "chunks_ingestion_stats.json")
    if os.path.exists(stats_file):
        with open(stats_file) as f:
            stats = json.load(f)
        print(f"\n   ✅ Ingestion complete!")
        print(f"   📊 Chunks inserted: {stats.get('chunks_inserted', 0)}")
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 ECKO MANUAL INGESTION COMPLETE")
    print("=" * 60)
    print(f"   Brand: {ECKO_CONFIG['brand']}")
    print(f"   Source: {ECKO_CONFIG['source']}")
    print(f"   Chunks: {len(chunks)}")
    print(f"   Retailers: {', '.join(ECKO_CONFIG['retailers'])}")
    print(f"\n   🔍 Test query: 'What Ecko T-Rex screws are available?'")
    print(f"⏰ Completed: {datetime.now().isoformat()}")
    
    return True


if __name__ == "__main__":
    # Check if PDFs exist
    pdfs = check_for_pdfs()
    
    if not pdfs:
        print("=" * 60)
        print("🦎 ECKO MANUAL UPLOAD - READY")
        print("=" * 60)
        print(f"\n📂 Drop zone ready at:")
        print(f"   {INPUT_DIR}")
        print(f"\n📋 Instructions:")
        print(f"   1. Download the Ecko Master Catalogue PDF")
        print(f"   2. Upload it to the drop zone folder above")
        print(f"   3. Run this script again: python process_ecko_manual.py")
        print(f"\n🏷️ Metadata that will be applied:")
        print(f"   • Brand: Ecko")
        print(f"   • Retailers: PlaceMakers, ITM")
        print(f"   • Priority: 85 (High)")
        sys.exit(0)
    
    success = process_ecko_upload()
    sys.exit(0 if success else 1)
