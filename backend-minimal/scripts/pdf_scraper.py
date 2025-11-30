#!/usr/bin/env python3
"""
STRYDA-v2 PDF Scraper
Downloads PDFs from source URLs and uploads to Supabase Storage
"""

import json
import os
import requests
from datetime import datetime
from pathlib import Path
from supabase import create_client, Client

# Configuration
MANIFEST_PATH = "/app/backend-minimal/training/docs_manifest.jsonl"
LOG_PATH = "/app/backend-minimal/training/logs/pdf_scraper.log"
TEMP_DIR = "/tmp/pdf_downloads"

# Supabase config (extracted from DATABASE_URL)
SUPABASE_URL = "https://qxqisgjhbjwvoxsjibes.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF4cWlzZ2poYmp3dm94c2ppYmVzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczMjM4NDg2OCwiZXhwIjoyMDQ3OTYwODY4fQ.IWxBqO5vSPxBkN-TQnH7yS-j7q1SwY-RvdBzqVmOCMM"

def log(message: str):
    """Write to log file and console"""
    timestamp = datetime.now().isoformat()
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    
    with open(LOG_PATH, 'a') as f:
        f.write(log_line + '\n')

def download_pdf(url: str, output_path: str) -> bool:
    """Download PDF from URL"""
    try:
        response = requests.get(url, timeout=60, stream=True)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = os.path.getsize(output_path)
        if file_size == 0:
            log(f"❌ Downloaded file is empty: {output_path}")
            return False
        
        log(f"✅ Downloaded: {output_path} ({file_size:,} bytes)")
        return True
        
    except Exception as e:
        log(f"❌ Download failed for {url}: {e}")
        return False

def upload_to_supabase(local_path: str, supabase_path: str, bucket: str = "pdfs") -> bool:
    """Upload PDF to Supabase Storage"""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        with open(local_path, 'rb') as f:
            file_data = f.read()
        
        # Upload to bucket
        result = supabase.storage.from_(bucket).upload(
            path=supabase_path,
            file=file_data,
            file_options={"content-type": "application/pdf"}
        )
        
        log(f"✅ Uploaded to Supabase: {bucket}/{supabase_path}")
        return True
        
    except Exception as e:
        log(f"❌ Upload failed for {supabase_path}: {e}")
        return False

def main():
    """Main scraper function"""
    log("="*80)
    log("STRYDA-v2 PDF SCRAPER - START")
    log("="*80)
    
    # Create temp directory
    Path(TEMP_DIR).mkdir(parents=True, exist_ok=True)
    
    # Load manifest
    log(f"\n1. Loading manifest from {MANIFEST_PATH}")
    
    with open(MANIFEST_PATH, 'r') as f:
        entries = [json.loads(line) for line in f if line.strip()]
    
    log(f"   ✅ Loaded {len(entries)} PDF entries")
    
    # Process each entry
    log(f"\n2. Processing PDFs")
    
    stats = {
        "pre_uploaded": 0,
        "downloaded": 0,
        "uploaded": 0,
        "failed": 0,
        "skipped": 0
    }
    
    for idx, entry in enumerate(entries, 1):
        pdf_name = entry["supabase_path"]
        log(f"\n[{idx}/{len(entries)}] Processing: {pdf_name}")
        
        # Check if pre-uploaded
        if entry.get("pre_uploaded", False):
            log(f"   ⏭️  Pre-uploaded, skipping download")
            stats["pre_uploaded"] += 1
            continue
        
        # Check if needs download
        if not entry.get("needs_download", False):
            log(f"   ⏭️  No download needed, skipping")
            stats["skipped"] += 1
            continue
        
        # Download from source_url
        source_url = entry.get("source_url", "")
        if not source_url:
            log(f"   ❌ No source_url provided")
            stats["failed"] += 1
            continue
        
        local_path = os.path.join(TEMP_DIR, pdf_name)
        
        # Download
        if download_pdf(source_url, local_path):
            stats["downloaded"] += 1
            
            # Upload to Supabase
            bucket = entry.get("supabase_bucket", "pdfs")
            if upload_to_supabase(local_path, pdf_name, bucket):
                stats["uploaded"] += 1
            else:
                stats["failed"] += 1
            
            # Clean up temp file
            try:
                os.remove(local_path)
            except:
                pass
        else:
            stats["failed"] += 1
    
    # Summary
    log(f"\n{'='*80}")
    log("SCRAPER COMPLETE")
    log(f"{'='*80}")
    log(f"Pre-uploaded: {stats['pre_uploaded']}")
    log(f"Downloaded: {stats['downloaded']}")
    log(f"Uploaded: {stats['uploaded']}")
    log(f"Failed: {stats['failed']}")
    log(f"Skipped: {stats['skipped']}")
    log(f"Total processed: {len(entries)}")

if __name__ == "__main__":
    main()
