#!/usr/bin/env python3
"""
Viblock Manual Upload Processor
===============================
Processes manually-uploaded Viblock PDFs from temporary bucket
Applies STRYDA Master Protocol naming and folder allocation

Protocol Rules Applied:
- Rule 1: Contextual naming [Manufacturer] - [Category] - [Document Type].pdf
- Rule 2: Sanitization - clean filenames
- Rule 3: Universal docs to 00_General_Resources
- Rule 10: BPIR documents are mandatory
"""

import os
import sys
import time

sys.path.insert(0, '/app/backend-minimal')

from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

from supabase import create_client

# Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
BUCKET_SOURCE = 'temporary'
BUCKET_DEST = 'product-library'
BASE_PATH = 'B_Enclosure/Wall_Cladding/Viblock_Masonry'

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================================
# FILE MAPPING: Original filename -> (New filename, Folder)
# ============================================================

VIBLOCK_FILE_MAPPING = {
    # PRIORITY 0: BPIR Documents (MANDATORY)
    "Viblock-BPIR-Veneers.pdf": (
        "Viblock - Veneers - BPIR.pdf",
        "Veneer_Bricks"
    ),
    "Viblock-BPIR-Structural-Masonry.pdf": (
        "Viblock - Structural - BPIR.pdf",
        "Structural"
    ),
    
    # PRIORITY 1: System Specifications
    "Viblock-Veneers-System-Specification-Oct-2023.pdf": (
        "Viblock - Veneers - System Specification Oct 2023.pdf",
        "Veneer_Bricks"
    ),
    "Viblock-Structural-Architectural-Information.pdf": (
        "Viblock - Structural - Architectural Information.pdf",
        "Structural"
    ),
    
    # PRIORITY 2: Technical Data
    "Viblock-Veneers-Product-Book_compressed.pdf": (
        "Viblock - Veneers - Product Brochure.pdf",
        "Veneer_Bricks"
    ),
    "2025-Viblock-Block-Chart-A4.pdf": (
        "Viblock - Block Chart 2025.pdf",
        "Structural"
    ),
    "Viblock-Block-Chart-A4.pdf": (
        "Viblock - Block Chart.pdf",
        "Structural"
    ),
    "Viblock-Block-Chart-A4-1.pdf": (
        None,  # Duplicate - skip
        None
    ),
    "MSDS-Viblock-Masonry.pdf": (
        "Viblock - MSDS Safety Data Sheet.pdf",
        "00_General_Resources"
    ),
    
    # PRIORITY 3: General Resources
    "Guidelines-for-care-of-Architectural-Concrete-Masonry.pdf": (
        "Viblock - Care of Architectural Concrete Masonry Guide.pdf",
        "00_General_Resources"
    ),
    "Care-Maintenance-Guide.pdf": (
        "Viblock - Care and Maintenance Guide.pdf",
        "00_General_Resources"
    ),
    "Product-Warranties-2023.pdf": (
        "Viblock - Product Warranty 2023.pdf",
        "00_General_Resources"
    ),
    "Viblock-Product-Warranty.pdf": (
        "Viblock - Product Warranty.pdf",
        "00_General_Resources"
    ),
    "Viblock-Sealer-Information.pdf": (
        "Viblock - Sealer Information.pdf",
        "00_General_Resources"
    ),
    "Viblock-Sale-Conditions.pdf": (
        "Viblock - Conditions of Sale.pdf",
        "00_General_Resources"
    ),
    "Viblock-StoClear-Coatings-Brochure.pdf": (
        "Viblock - StoClear Coatings Brochure.pdf",
        "00_General_Resources"
    ),
    "NZCMA-MM-5.5-Veneer-Stack-Bond.pdf": (
        "Viblock - NZCMA Veneer Stack Bond Guide.pdf",
        "00_General_Resources"
    ),
    
    # Additional Viblock products found (BONUS!)
    "Viblock-BPIR-Pavers.pdf": (
        "Viblock - Pavers - BPIR.pdf",
        "00_General_Resources"  # Or could go to separate Pavers folder
    ),
    "Viblock-BPIR-Retaining-Wall-Systems.pdf": (
        "Viblock - Retaining Walls - BPIR.pdf",
        "00_General_Resources"
    ),
    "Viblock-Product-Book-2023.pdf": (
        "Viblock - Full Product Catalogue 2023.pdf",
        "00_General_Resources"
    ),
    "Viblock-Retaining-Wall-Information.pdf": (
        "Viblock - Retaining Wall Information.pdf",
        "00_General_Resources"
    ),
    "Paving-Product-Book_v1.pdf": (
        "Viblock - Paving Product Book.pdf",
        "00_General_Resources"
    ),
    "Tactile-Paver-Installation-Specification.pdf": (
        "Viblock - Tactile Paver Installation Specification.pdf",
        "00_General_Resources"
    ),
    
    # External/Third-party resources (Rule 7 - but user uploaded them)
    "m_work_guide_jul_20.pdf": (
        "Concrete NZ - Masonry Workmanship Guide Jul 2020.pdf",
        "00_General_Resources"
    ),
    "Concrete Masonry - Site Practice & workmanshop Guide.pdf": (
        "Concrete NZ - Site Practice and Workmanship Guide.pdf",
        "00_General_Resources"
    ),
    "New Zealand Concrete Masonry Manual.pdf": (
        "Concrete NZ - NZ Concrete Masonry Manual.pdf",
        "00_General_Resources"
    ),
    "MBBBrickVeneerBestPracticeGuideMay25.pdf": (
        "Master Brick and Block - Veneer Best Practice Guide May 2025.pdf",
        "00_General_Resources"
    ),
    
    # Non-Viblock files to SKIP
    "PREMIER-BRICK-MAINTENANCE-INFORMATION.pdf": (None, None),
    "4211-Report-Summary.pdf": (None, None),
    "Product-Technical-Statement.pdf": (None, None),
}


def download_from_temp(filename):
    """Download file from temporary bucket"""
    try:
        # Get signed URL for download
        signed_url = supabase.storage.from_(BUCKET_SOURCE).create_signed_url(filename, 60)
        
        if signed_url and signed_url.get('signedURL'):
            import requests
            response = requests.get(signed_url['signedURL'], timeout=60)
            if response.status_code == 200:
                return response.content
        return None
    except Exception as e:
        print(f"    ❌ Download error: {str(e)[:50]}")
        return None


def upload_to_destination(content, folder, filename):
    """Upload to product-library bucket"""
    storage_path = f"{BASE_PATH}/{folder}/{filename}"
    
    try:
        supabase.storage.from_(BUCKET_DEST).upload(
            storage_path,
            content,
            {"content-type": "application/pdf", "upsert": "true"}
        )
        return True
    except Exception as e:
        if "Duplicate" in str(e) or "already exists" in str(e).lower():
            return True
        print(f"    ❌ Upload error: {str(e)[:50]}")
        return False


def delete_from_temp(filename):
    """Delete processed file from temporary bucket"""
    try:
        supabase.storage.from_(BUCKET_SOURCE).remove([filename])
        return True
    except:
        return False


def main():
    print("=" * 70)
    print("VIBLOCK MANUAL UPLOAD PROCESSOR")
    print("STRYDA Master Protocol v2.0")
    print("=" * 70)
    
    # Get files from temporary bucket
    try:
        temp_files = supabase.storage.from_(BUCKET_SOURCE).list('')
        temp_filenames = [f['name'] for f in temp_files if f.get('name')]
    except Exception as e:
        print(f"❌ Failed to list temporary bucket: {e}")
        return False
    
    print(f"\n📂 Found {len(temp_filenames)} files in temporary bucket")
    
    stats = {
        "processed": 0,
        "skipped_not_viblock": 0,
        "skipped_duplicate": 0,
        "failed": 0
    }
    
    processed_files = []
    
    # Process each file
    print("\n" + "-" * 70)
    print("PROCESSING FILES")
    print("-" * 70)
    
    for orig_filename in sorted(temp_filenames):
        # Check if we have a mapping for this file
        if orig_filename not in VIBLOCK_FILE_MAPPING:
            print(f"\n⏭️ {orig_filename}")
            print(f"   └─ Not in mapping, skipping")
            stats["skipped_not_viblock"] += 1
            continue
        
        new_filename, folder = VIBLOCK_FILE_MAPPING[orig_filename]
        
        if new_filename is None:
            print(f"\n🚫 {orig_filename}")
            print(f"   └─ Marked for skip (duplicate or non-Viblock)")
            stats["skipped_duplicate"] += 1
            continue
        
        print(f"\n📄 {orig_filename}")
        print(f"   └─ → {new_filename}")
        print(f"   └─ → {folder}/")
        
        # Download
        content = download_from_temp(orig_filename)
        if not content:
            print(f"   ❌ Failed to download")
            stats["failed"] += 1
            continue
        
        # Upload with new name
        if upload_to_destination(content, folder, new_filename):
            print(f"   ✅ Uploaded ({len(content):,} bytes)")
            stats["processed"] += 1
            processed_files.append(orig_filename)
        else:
            stats["failed"] += 1
        
        time.sleep(0.3)
    
    # Summary
    print("\n" + "=" * 70)
    print("PROCESSING SUMMARY")
    print("=" * 70)
    print(f"✅ Processed & uploaded: {stats['processed']}")
    print(f"⏭️ Skipped (not Viblock): {stats['skipped_not_viblock']}")
    print(f"🚫 Skipped (duplicate): {stats['skipped_duplicate']}")
    print(f"❌ Failed: {stats['failed']}")
    
    # Clean up processed files from temporary
    if processed_files:
        print(f"\n🧹 Cleaning up {len(processed_files)} processed files from temporary...")
        for filename in processed_files:
            if delete_from_temp(filename):
                print(f"   ✓ Deleted: {filename}")
    
    # Verification
    print("\n" + "=" * 70)
    print("FINAL DIRECTORY STRUCTURE")
    print("=" * 70)
    
    for folder in ['Veneer_Bricks', 'Structural', '00_General_Resources']:
        try:
            result = supabase.storage.from_(BUCKET_DEST).list(f"{BASE_PATH}/{folder}")
            files = [f['name'] for f in result if f.get('name')]
            print(f"\n📂 {folder}/ ({len(files)} files)")
            for f in sorted(files):
                print(f"   └─ {f}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return stats['failed'] == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
