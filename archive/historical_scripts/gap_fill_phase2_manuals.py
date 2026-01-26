#!/usr/bin/env python3
"""
Gap Fill Phase 2 - Targeted Manuals Scraper (Protocol v2.0)
===========================================================
Ingests specific high-value installation manuals identified during Deep Recon.

Target Manufacturers:
- Viking Roofspec (Membranes, Tanking, Applicator Handbooks)
- Nuralite (3PM Installation, CodeMark)
- Gerard (Master Manual, CF Shingle/Shake)
- Solerati (La Escandella Manual)

Rule 8: These are all "Monoliths" - Named clearly as Master Manuals

Author: STRYDA Data Pipeline
Date: 2025-01
"""

import os
import sys
import time
import requests
from supabase import create_client
from dotenv import load_dotenv

sys.path.insert(0, '/app/src')
from ingestion_rules import (
    PROTOCOL_VERSION,
    sanitize_filename,
    is_potential_monolith,
    print_protocol_summary
)

load_dotenv("/app/backend-minimal/.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
BUCKET_NAME = "product-library"

print(f"🔗 Supabase URL: {SUPABASE_URL[:30]}..." if SUPABASE_URL else "❌ No SUPABASE_URL")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

stats = {
    "pdfs_found": 0,
    "pdfs_uploaded": 0,
    "pdfs_skipped_duplicate": 0,
    "monoliths_detected": 0,
    "errors": 0,
}

uploaded_urls = set()


# =============================================================================
# TARGETED MANUALS - DIRECT URLs FROM DEEP RECON
# =============================================================================

VIKING_ROOFSPEC = {
    "prefix": "B_Enclosure/Viking_Roofspec",
    "docs": [
        # Applicator Handbooks (Rule 8 - Monolith)
        {
            "folder": "00_General_Resources",
            "filename": "Viking - Master Rubber Applicator Training Handbook 2021.pdf",
            "url": "https://www.vikingroofspec.co.nz/media/lecmyptv/vk_rubber_training_handbook_2021-final.pdf",
            "title": "Rubber Applicator Training Handbook"
        },
        # Tanking
        {
            "folder": "Tanking",
            "filename": "Viking - Below Ground Tanking Methodology v1.2.pdf",
            "url": "https://www.vikingroofspec.co.nz/media/k4douviw/viking-below-ground-tanking-methodology-v1-2.pdf",
            "title": "Below Ground Tanking Methodology"
        },
    ]
}

NURALITE_MEMBRANES = {
    "prefix": "B_Enclosure/Nuralite_Membranes",
    "docs": [
        # Installation Manual
        {
            "folder": "Nuraply_3PM",
            "filename": "Nuralite - Nuraply 3PM Installation Checksheet.pdf",
            "url": "https://www.flatroof.co.nz/pdf/Nuralite/Nuraply_3PM_Installation_Checksheet.pdf",
            "title": "Nuraply 3PM Installation Checksheet"
        },
        # CodeMark Certificate
        {
            "folder": "Nuraply_3PM",
            "filename": "Nuralite - Nuraply 3PM CodeMark Certificate CM70032.pdf",
            "url": "https://codehub.building.govt.nz/assets/_generated_pdfs/cm70032-8788.pdf",
            "title": "CodeMark Certificate CM70032"
        },
    ]
}

GERARD_ROOFING = {
    "prefix": "B_Enclosure/Gerard_Roofing",
    "docs": [
        # Master Installation Manual (Rule 8 - Monolith)
        {
            "folder": "00_General_Resources",
            "filename": "Gerard - Master NZ Installation Manual v2.3 (Jul 2024).pdf",
            "url": "https://www.gerardroofs.co.nz/media/fsdmzlqc/man0003-gerard-new-zealand-installation-manual-0724-v2-3.pdf",
            "title": "Master NZ Installation Manual"
        },
        # CF Shake/Shingle Manual
        {
            "folder": "Installation_Manuals",
            "filename": "Gerard - CF Shake Shingle Installation Manual v32 (Nov 2025).pdf",
            "url": "https://www.gerardroofs.co.nz/media/lxxpmbso/man0019-gerard-cf-shake-shingle-installation-manual-battens-v32-1125-lr.pdf",
            "title": "CF Shake/Shingle Installation Manual"
        },
    ]
}

SOLERATI_TILES = {
    "prefix": "B_Enclosure/Solerati_Tiles",
    "docs": [
        # La Escandella Installation Manual
        {
            "folder": "Installation_Manuals",
            "filename": "Solerati - La Escandella Master Installation Manual.pdf",
            "url": "https://www.solerati.co.nz/wp-content/uploads/2017/04/la-escandella-installation-manual.pdf",
            "title": "La Escandella Installation Manual"
        },
    ]
}


def upload_to_supabase(pdf_url: str, storage_path: str, doc_title: str) -> bool:
    """Download PDF and upload to Supabase storage."""
    try:
        print(f"  📥 Downloading: {doc_title[:50]}...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(pdf_url, timeout=120, allow_redirects=True, headers=headers)
        
        if response.status_code != 200:
            print(f"  ❌ Failed (HTTP {response.status_code})")
            stats["errors"] += 1
            return False
        
        pdf_content = response.content
        
        # Check if valid PDF
        if not pdf_content[:4] == b'%PDF':
            print(f"  ⚠️ Not a valid PDF (got {pdf_content[:20]}...)")
            stats["errors"] += 1
            return False
        
        # Rule 8: Monolith detection
        file_size_mb = len(pdf_content) / (1024 * 1024)
        if is_potential_monolith(file_size_mb=file_size_mb):
            stats["monoliths_detected"] += 1
            print(f"  📚 Rule 8: Monolith detected ({file_size_mb:.1f}MB)")
        else:
            print(f"  📄 File size: {file_size_mb:.1f}MB")
        
        try:
            supabase.storage.from_(BUCKET_NAME).upload(
                storage_path,
                pdf_content,
                {"content-type": "application/pdf"}
            )
            print(f"  ✅ Uploaded: {storage_path.split('/')[-1]}")
            return True
        except Exception as e:
            if "Duplicate" in str(e) or "already exists" in str(e).lower():
                print(f"  ⏭️ Already exists")
                stats["pdfs_skipped_duplicate"] += 1
                return False
            else:
                print(f"  ❌ Upload error: {e}")
                stats["errors"] += 1
                return False
                
    except requests.exceptions.Timeout:
        print(f"  ❌ Timeout (file may be too large)")
        stats["errors"] += 1
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        stats["errors"] += 1
        return False


def process_manufacturer(name: str, config: dict):
    """Process all docs for a manufacturer."""
    print(f"\n{'=' * 60}")
    print(f"🏭 {name}")
    print(f"{'=' * 60}")
    
    prefix = config["prefix"]
    
    for doc in config["docs"]:
        stats["pdfs_found"] += 1
        
        url = doc["url"]
        if url in uploaded_urls:
            print(f"  ⏭️ SKIPPED (Duplicate URL): {doc['title']}")
            stats["pdfs_skipped_duplicate"] += 1
            continue
        
        storage_path = f"{prefix}/{doc['folder']}/{doc['filename']}"
        
        if upload_to_supabase(url, storage_path, doc["title"]):
            stats["pdfs_uploaded"] += 1
            uploaded_urls.add(url)
        
        time.sleep(0.5)


def main():
    """Main scraping function."""
    print("=" * 70)
    print(f"📚 GAP FILL PHASE 2 - TARGETED MANUALS (Protocol v{PROTOCOL_VERSION})")
    print("=" * 70)
    
    print_protocol_summary()
    
    print("\n⚠️  Rule 8 ACTIVE: These are high-value MONOLITH documents")
    print("   Named clearly as Master Manuals for easy discovery")
    print("=" * 70)
    
    # Process each manufacturer
    process_manufacturer("VIKING ROOFSPEC (Membranes & Tanking)", VIKING_ROOFSPEC)
    process_manufacturer("NURALITE MEMBRANES (3PM Installation)", NURALITE_MEMBRANES)
    process_manufacturer("GERARD ROOFING (Metal Tiles)", GERARD_ROOFING)
    process_manufacturer("SOLERATI TILES (Clay)", SOLERATI_TILES)
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 SCRAPING SUMMARY")
    print("=" * 70)
    print(f"Protocol Version:           v{PROTOCOL_VERSION}")
    print(f"PDFs found:                 {stats['pdfs_found']}")
    print(f"PDFs uploaded:              {stats['pdfs_uploaded']}")
    print(f"PDFs skipped (duplicate):   {stats['pdfs_skipped_duplicate']}")
    print(f"Monoliths detected:         {stats['monoliths_detected']}")
    print(f"Errors:                     {stats['errors']}")
    print("=" * 70)
    
    if stats['errors'] > 0:
        print("\n⚠️ Some downloads failed. These URLs may require:")
        print("   - Manual download from manufacturer website")
        print("   - VPN/different network (geo-blocked)")
        print("   - Direct contact with manufacturer")


if __name__ == "__main__":
    main()
