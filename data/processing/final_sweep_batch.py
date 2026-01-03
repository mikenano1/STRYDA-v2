#!/usr/bin/env python3
"""
STRYDA Big Brain - FINAL SWEEP BATCH PROCESSOR
Processes all Final Sweep PDFs through Vision Pipeline and ingests into DB
"""

import os
import sys
import json
import subprocess
import time
from datetime import datetime
from glob import glob

sys.path.insert(0, '/app/backend-minimal')
from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

# Configuration
BASE_INPUT_DIR = "/app/data/ingestion/F_Manufacturers/Fasteners"
OUTPUT_DIR = "/app/data/processing/final_sweep"
MANIFEST_PATH = os.path.join(BASE_INPUT_DIR, "manifest_final_sweep.json")

# Brand metadata for ingestion
BRAND_CONFIG = {
    "Delfast": {"category": "F_Manufacturers", "product_family": "Collated Nails", "trade": "fasteners"},
    "Blacks": {"category": "F_Manufacturers", "product_family": "Industrial Fasteners", "trade": "fasteners"},
    "Mainland_Fasteners": {"category": "F_Manufacturers", "product_family": "South Island Fasteners", "trade": "fasteners"},
    "Ecko": {"category": "F_Manufacturers", "product_family": "T-Rex Screws", "trade": "fasteners"},
    "Pryda": {"category": "F_Manufacturers", "product_family": "Brackets Bracing", "trade": "fasteners"},
    "Bremick": {"category": "F_Manufacturers", "product_family": "Anchors Industrial", "trade": "fasteners"},
    "Zenith": {"category": "F_Manufacturers", "product_family": "Hardware Fasteners", "trade": "fasteners"},
    "Titan": {"category": "F_Manufacturers", "product_family": "Framing Nails", "trade": "fasteners"},
    "NZ_Nails": {"category": "F_Manufacturers", "product_family": "Loose Nails", "trade": "fasteners"},
    "MacSim": {"category": "F_Manufacturers", "product_family": "Anchors Packers", "trade": "fasteners"},
    "SPAX": {"category": "F_Manufacturers", "product_family": "Premium Screws", "trade": "fasteners"},
    "PlaceMakers": {"category": "F_Manufacturers", "product_family": "Master Catalogue", "trade": "fasteners"},
}


def run_command(cmd: str, description: str, timeout: int = 600) -> bool:
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if result.stdout:
            # Print last part of output
            lines = result.stdout.strip().split('\n')
            print('\n'.join(lines[-50:]))
        
        if result.returncode != 0:
            print(f"⚠️ Warning - exit code {result.returncode}")
            if result.stderr:
                print(f"Stderr: {result.stderr[-1000:]}")
            return False
        
        return True
        
    except subprocess.TimeoutExpired:
        print(f"⏰ Command timed out after {timeout}s")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def process_brand(brand_dir: str, brand_name: str) -> dict:
    """Process a single brand's PDFs"""
    result = {
        "brand": brand_name,
        "pdf_count": 0,
        "chunk_count": 0,
        "ingested": 0,
        "success": False,
        "errors": []
    }
    
    # Find PDFs
    pdf_files = glob(os.path.join(brand_dir, "*.pdf"))
    result["pdf_count"] = len(pdf_files)
    
    if not pdf_files:
        print(f"   ⚠️ No PDFs found for {brand_name}")
        return result
    
    print(f"\n📁 Processing {brand_name}: {len(pdf_files)} PDFs")
    
    # Create output directory for this brand
    brand_output = os.path.join(OUTPUT_DIR, brand_name)
    os.makedirs(brand_output, exist_ok=True)
    
    # Get brand config
    config = BRAND_CONFIG.get(brand_name, {
        "category": "F_Manufacturers",
        "product_family": "General",
        "trade": "fasteners"
    })
    
    # Step 1: Run Vision Pipeline (pdf_chunker_v2.py)
    chunks_file = os.path.join(brand_output, "chunks.json")
    
    # Build command for chunker
    cmd = f"""cd /app/data/processing && python3 pdf_chunker_v2.py \
        --input "{brand_dir}" \
        --output "{brand_output}" """
    
    success = run_command(cmd, f"Vision processing {brand_name}...", timeout=900)
    
    if not success or not os.path.exists(chunks_file):
        result["errors"].append("Vision processing failed or no chunks generated")
        return result
    
    # Load and count chunks
    with open(chunks_file) as f:
        chunks = json.load(f)
    result["chunk_count"] = len(chunks)
    
    if not chunks:
        result["errors"].append("No chunks extracted")
        return result
    
    print(f"   ✅ Extracted {len(chunks)} chunks")
    
    # Step 2: Ingest chunks
    ingest_cmd = f"""cd /app/data/processing && python3 ingestor.py \
        --chunks "{chunks_file}" \
        --brand "{brand_name.replace('_', ' ')}" \
        --category "{config['category']}" \
        --doc-type "Product_Catalog" \
        --product-family "{config['product_family']}" \
        --trade "{config['trade']}" \
        --source "Final Sweep - {brand_name}" \
        --priority 80"""
    
    success = run_command(ingest_cmd, f"Ingesting {brand_name} chunks...", timeout=600)
    
    if success:
        result["ingested"] = len(chunks)
        result["success"] = True
    else:
        result["errors"].append("Ingestion failed")
    
    return result


def main():
    print("="*70)
    print("🧠 STRYDA Big Brain - FINAL SWEEP BATCH PROCESSOR")
    print("="*70)
    print(f"⏰ Started: {datetime.now().isoformat()}")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    results = {
        "started_at": datetime.now().isoformat(),
        "brands": []
    }
    
    # Get all brand directories
    brand_dirs = [d for d in os.listdir(BASE_INPUT_DIR) 
                  if os.path.isdir(os.path.join(BASE_INPUT_DIR, d))]
    
    print(f"\n📚 Found {len(brand_dirs)} brand directories to process")
    
    total_pdfs = 0
    total_chunks = 0
    total_ingested = 0
    
    for brand_name in sorted(brand_dirs):
        brand_dir = os.path.join(BASE_INPUT_DIR, brand_name)
        
        # Check if there are actually PDFs in this directory
        pdf_files = glob(os.path.join(brand_dir, "*.pdf"))
        if not pdf_files:
            print(f"   ⏭️ Skipping {brand_name} (no PDFs)")
            continue
        
        brand_result = process_brand(brand_dir, brand_name)
        results["brands"].append(brand_result)
        
        total_pdfs += brand_result["pdf_count"]
        total_chunks += brand_result["chunk_count"]
        total_ingested += brand_result["ingested"]
        
        # Small delay between brands to avoid rate limits
        time.sleep(1)
    
    # Summary
    results["completed_at"] = datetime.now().isoformat()
    results["summary"] = {
        "total_brands": len(results["brands"]),
        "total_pdfs": total_pdfs,
        "total_chunks": total_chunks,
        "total_ingested": total_ingested
    }
    
    print("\n\n" + "="*70)
    print("📊 FINAL SWEEP BATCH PROCESSING SUMMARY")
    print("="*70)
    
    print(f"\n📋 By Brand:")
    for br in results["brands"]:
        status = "✅" if br["success"] else "❌"
        print(f"   {status} {br['brand']}: {br['pdf_count']} PDFs → {br['chunk_count']} chunks → {br['ingested']} ingested")
        if br["errors"]:
            for err in br["errors"]:
                print(f"      ⚠️ {err}")
    
    print(f"\n📊 Totals:")
    print(f"   📄 PDFs processed: {total_pdfs}")
    print(f"   📝 Chunks extracted: {total_chunks}")
    print(f"   💾 Chunks ingested: {total_ingested}")
    
    # Save results
    results_file = os.path.join(OUTPUT_DIR, "batch_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📋 Results saved to: {results_file}")
    print(f"⏰ Completed: {datetime.now().isoformat()}")
    
    return all(br["success"] for br in results["brands"])


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
