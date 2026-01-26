#!/usr/bin/env python3
"""
Velux Skylights Scraper (Protocol v2.0)
=======================================
Downloads technical PDFs for Velux NZ skylights, flashings, and sun tunnels.

Uses src/ingestion_rules.py for Protocol v2.0 enforcement:
- Rule 1: Context-aware naming
- Rule 6: Flashing docs to /Flashings/ folder
- Rule 8: Monolith detection (>20MB files)

Storage: /B_Enclosure/Velux_Skylights/
- /Pitched_Roof_Skylights/
- /Low_Pitch_Skylights/
- /Sun_Tunnels/
- /Flashings/
- /Blinds_and_Controls/
- /Roof_Windows/
- /00_General_Resources/

Author: STRYDA Data Pipeline
Date: 2025-01
"""

import os
import sys
import re
import time
import requests
from supabase import create_client
from dotenv import load_dotenv

# Add src to path for ingestion_rules
sys.path.insert(0, '/app/src')
from ingestion_rules import (
    PROTOCOL_VERSION,
    is_generic_filename,
    sanitize_filename,
    is_potential_monolith,
    print_protocol_summary
)

load_dotenv("/app/backend-minimal/.env")

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
BUCKET_NAME = "product-library"

print(f"🔗 Supabase URL: {SUPABASE_URL[:30]}..." if SUPABASE_URL else "❌ No SUPABASE_URL")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

STORAGE_PREFIX = "B_Enclosure/Velux_Skylights"

# Stats tracking
stats = {
    "categories_processed": 0,
    "pdfs_found": 0,
    "pdfs_uploaded": 0,
    "pdfs_skipped_duplicate": 0,
    "pdfs_to_general": 0,
    "monoliths_detected": 0,
    "errors": 0,
}

# Track uploaded files for deduplication
uploaded_urls = set()


# =============================================================================
# PITCHED ROOF SKYLIGHTS (15-90°)
# =============================================================================
PITCHED_ROOF_SKYLIGHTS = {
    "VS_Manual_Skylight": [
        ("Installation Instructions", "https://afd-marketing.velux.com/-/media/marketing/nz/installation%20instructions/vs-vse-vss.pdf"),
        ("Product Data Sheet", "https://afd-marketing.velux.com/-/media/marketing/nz/data%20sheets/vs%20product%20data%20sheet%201223.pdf"),
        ("Architectural Drawing", "https://contenthub.velux.com/api/public/content/b37d662467c24d8fa7ad88a998121b1f?v=befe5fd7"),
    ],
    "VSE_Electric_Skylight": [
        ("Product Data Sheet", "https://afd-marketing.velux.com/-/media/marketing/nz/data%20sheets/vse%20product%20data%20sheet%201223.pdf"),
        ("Architectural Drawing", "https://contenthub.velux.com/api/public/content/d00c615b8d364a8b9cd9f1262b844940?v=60658506"),
    ],
    "VSS_Solar_Skylight": [
        ("Product Data Sheet", "https://afd-marketing.velux.com/-/media/marketing/nz/data%20sheets/vss%20product%20data%20sheet%201223.pdf"),
        ("Architectural Drawing", "https://contenthub.velux.com/api/public/content/9f7cc2c6419f4b6c96cb99d5003b8b5e?v=0956e78b"),
    ],
    "FS_Fixed_Skylight": [
        ("Installation Instructions", "https://afd-marketing.velux.com/-/media/marketing/au/downloads/installation%20instructions/6_2_fs_non%20openable_skylight.pdf"),
        ("Product Data Sheet", "https://afd-marketing.velux.com/-/media/marketing/nz/data%20sheets/fs%20product%20data%20sheet%201223.pdf"),
        ("Architectural Drawing", "https://contenthub.velux.com/api/public/content/da47d67d65bf4085a86f571432e25d48?v=87099c22"),
    ],
}

# =============================================================================
# LOW PITCH SKYLIGHTS (0-60°)
# =============================================================================
LOW_PITCH_SKYLIGHTS = {
    "VCM_Manual_Skylight": [
        ("Installation Instructions", "https://afd-marketing.velux.com/-/media/marketing/nz/installation%20instructions/vcm-vce-vcs%20454442-2018-10.pdf"),
        ("Product Data Sheet", "https://afd-marketing.velux.com/-/media/marketing/nz/data%20sheets/vcm%20product%20data%20sheet%201223.pdf"),
        ("Architectural Drawing", "https://contenthub.velux.com/api/public/content/cc757dc027bc4846844151ddbc847714?v=9275b8cb"),
    ],
    "VCS_Solar_Skylight": [
        ("Product Data Sheet", "https://afd-marketing.velux.com/-/media/marketing/nz/data%20sheets/vcs%20product%20data%20sheet%201223.pdf"),
        ("Architectural Drawing", "https://contenthub.velux.com/api/public/content/c8c3c6fd0f6a4daa81f668d9438056d7?v=7458d6c4"),
    ],
    "FCM_Fixed_Skylight": [
        ("Installation Instructions", "https://afd-marketing.velux.com/-/media/marketing/nz/installation%20instructions/fcm%20452195-2022-10.pdf"),
        ("Product Data Sheet", "https://afd-marketing.velux.com/-/media/marketing/nz/data%20sheets/fcm%20product%20data%20sheet%201223.pdf"),
        ("Architectural Drawing", "https://contenthub.velux.com/api/public/content/ad5ec70c5c584cba8abeca755d7c6b79?v=09afa3bf"),
    ],
}

# =============================================================================
# ROOF WINDOWS
# =============================================================================
ROOF_WINDOWS = {
    "GGU_Roof_Window": [
        ("Installation Instructions", "https://afd-marketing.velux.com/-/media/marketing/nz/installation%20instructions/ggu%20-%20ggl%20452953-2013-03.pdf"),
        ("Product Data Sheet", "https://afd-marketing.velux.com/-/media/marketing/nz/data%20sheets/ggu%20product%20data%20sheet%201223.pdf"),
        ("Architectural Drawing", "https://contenthub.velux.com/api/public/content/50c25322b6e745439609a924f9f5ad59?v=282b5821"),
        ("Decra Tile Supplementary", "https://afd-marketing.velux.com/-/media/marketing/nz/installation%20instructions/ggu%20supplementary%20for%20decra%20roofing%20451463-0111.pdf"),
    ],
}

# =============================================================================
# SUN TUNNELS
# =============================================================================
SUN_TUNNELS = {
    "TWR_TLR_Rigid_Sun_Tunnel": [
        ("Installation Instructions", "https://afd-marketing.velux.com/-/media/marketing/nz/installation%20instructions/twr%20tlr%20453834-2020-09.pdf"),
    ],
    "TWF_TLF_Flexible_Sun_Tunnel": [
        ("Installation Instructions", "https://afd-marketing.velux.com/-/media/marketing/nz/installation%20instructions/twf%20tlf%20453842-2020-09.pdf"),
    ],
    "TCR_Low_Pitch_Sun_Tunnel": [
        ("Installation Instructions", "https://afd-marketing.velux.com/-/media/marketing/nz/installation%20instructions/tcr%20014%200000usg%20454063-2019-12.pdf"),
    ],
    "Sun_Tunnels_General": [
        ("Product Data Sheet", "https://afd-marketing.velux.com/-/media/marketing/nz/data%20sheets/sun%20tunnel%20product%20data%20sheet%201223.pdf"),
        ("Architectural Drawing Pitched", "https://contenthub.velux.com/api/public/content/b37d662467c24d8fa7ad88a998121b1f?v=befe5fd7"),
        ("Architectural Drawing Flat", "https://contenthub.velux.com/api/public/content/a8f0f0283fc943a299239133dd005c79?v=fb0e1097"),
    ],
}

# =============================================================================
# FLASHINGS (Critical for Weathertightness - Rule 6)
# =============================================================================
FLASHINGS = {
    "EDW_Metal_Tile_Flashing": [
        ("Installation Instructions Skylights", "https://afd-marketing.velux.com/-/media/marketing/au/downloads/installation%20instructions/edw_452259_0509.pdf"),
        ("Installation Instructions Roof Windows", "https://afd-marketing.velux.com/-/media/marketing/au/downloads/installation%20instructions/edw%20v22%20%20%20453578%202013%2010.pdf"),
    ],
    "EDL_Shingle_Slate_Flashing": [
        ("Installation Instructions Skylights", "https://afd-marketing.velux.com/-/media/marketing/au/downloads/installation%20instructions/edl%20a21%20452264201109.pdf"),
        ("Installation Instructions Roof Windows", "https://afd-marketing.velux.com/-/media/marketing/au/downloads/installation%20instructions/edl%20v22%20453496%202014%2004.pdf"),
    ],
    "EKW_Combination_Flashing": [
        ("Installation Instructions Skylights", "https://afd-marketing.velux.com/-/media/marketing/au/downloads/installation%20instructions/ekw%20a21%204506421110.pdf"),
        ("Installation Instructions Roof Windows", "https://afd-marketing.velux.com/-/media/marketing/au/downloads/installation%20instructions/ekw%20v22%20%20%20452853%202012%2001.pdf"),
        ("Architectural Drawing", "https://contenthub.velux.com/api/public/content/5f8685e8bbcd4f498b46ba4125d429e1?v=a2e13dec"),
    ],
    "Custom_Flashing": [
        ("Custom Flashing Guide", "https://afd-marketing.velux.com/-/media/marketing/nz/installation%20instructions/custom%20flashing%20guide%20nz.pdf"),
        ("Rooflink Warranty Article", "https://afd-marketing.velux.com/-/media/marketing/nz/flashings/rl79_p29.pdf"),
    ],
}

# =============================================================================
# BLINDS AND CONTROLS
# =============================================================================
BLINDS_CONTROLS = {
    "DSD_DSH_DSC_Solar_Blackout_Blind": [
        ("Installation Instructions", "https://afd-marketing.velux.com/-/media/marketing/au/downloads/installation%20instructions/dsc-dsd-dsh%20slimline%20454286-2019-02.pdf"),
    ],
    "DKL_Manual_Blackout_Blind": [
        ("Installation Instructions", "https://afd-marketing.velux.com/-/media/marketing/au/downloads/installation%20instructions/dkl%20slimline.pdf"),
    ],
    "FSCH_FSCD_Solar_Honeycomb_Blind": [
        ("Installation Instructions", "https://afd-marketing.velux.com/-/media/marketing/nz/installation%20instructions/fscdfsch%20453786201407.pdf"),
    ],
    "FHCD_Manual_Honeycomb_Blind": [
        ("Installation Instructions", "https://afd-marketing.velux.com/-/media/marketing/nz/installation%20instructions/fhcd%20453787201504.pdf"),
    ],
    "KLF_200_Smart_System": [
        ("User Manual", "https://afd-marketing.velux.com/-/media/marketing/nz/installation%20instructions/klf200_instructions%20for%20use.pdf"),
    ],
    "KLI_310_Remote_Control": [
        ("User Manual", "https://afd-marketing.velux.com/-/media/marketing/nz/installation%20instructions/kli-310-sky%20-%20454332-2018-min.pdf"),
    ],
    "KLR_200_Remote_Control": [
        ("User Manual", "https://afd-marketing.velux.com/-/media/marketing/au/downloads/installation%20instructions/klr_200_controller_instruction_booklet.pdf"),
    ],
    "KLC_500_Control_Unit": [
        ("Installation Instructions", "https://afd-marketing.velux.com/-/media/marketing/nz/installation%20instructions/klc%20500%20452420201309.pdf"),
    ],
    "KLR_100_Remote_Control": [
        ("User Manual", "https://afd-marketing.velux.com/-/media/marketing/nz/installation%20instructions/klr%20100%20452672-2011-06.pdf"),
    ],
}


def upload_to_supabase(pdf_url: str, storage_path: str, doc_title: str) -> bool:
    """Download PDF and upload to Supabase storage."""
    try:
        print(f"  📥 Downloading: {doc_title[:50]}...")
        response = requests.get(pdf_url, timeout=60)
        if response.status_code != 200:
            print(f"  ❌ Failed to download (HTTP {response.status_code})")
            stats["errors"] += 1
            return False
        
        pdf_content = response.content
        
        # Verify PDF
        if not pdf_content[:4] == b'%PDF':
            print(f"  ⚠️ Not a valid PDF file")
            stats["errors"] += 1
            return False
        
        # Rule 8: Check for monolith (>20MB)
        file_size_mb = len(pdf_content) / (1024 * 1024)
        if is_potential_monolith(file_size_mb=file_size_mb):
            stats["monoliths_detected"] += 1
            print(f"  ⚠️ Rule 8: Large file detected ({file_size_mb:.1f}MB)")
        
        # Upload
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
                
    except Exception as e:
        print(f"  ❌ Error: {e}")
        stats["errors"] += 1
        return False


def process_category(category_name: str, folder: str, products: dict):
    """Process all products in a category."""
    print(f"\n{'=' * 50}")
    print(f"📁 {category_name}")
    print(f"{'=' * 50}")
    stats["categories_processed"] += 1
    
    for product_name, docs in products.items():
        print(f"\n  📦 {product_name.replace('_', ' ')}")
        
        for doc_title, pdf_url in docs:
            stats["pdfs_found"] += 1
            
            # Skip if URL already processed
            if pdf_url in uploaded_urls:
                print(f"    ⏭️ SKIPPED (Duplicate URL): {doc_title[:35]}...")
                stats["pdfs_skipped_duplicate"] += 1
                continue
            
            # Rule 1: Context-aware naming
            # Format: "Velux - [Product] - [Document Type].pdf"
            clean_product = product_name.replace('_', ' ')
            clean_title = sanitize_filename(doc_title)
            filename = f"Velux - {clean_product} - {clean_title}.pdf"
            storage_path = f"{STORAGE_PREFIX}/{folder}/{filename}"
            
            # Upload
            if upload_to_supabase(pdf_url, storage_path, doc_title):
                stats["pdfs_uploaded"] += 1
                uploaded_urls.add(pdf_url)
            
            time.sleep(0.3)


def run_verification():
    """Rule 5: Verification - check for generic filename failures and cross-folder issues."""
    print("\n" + "=" * 70)
    print("📋 VERIFICATION")
    print("=" * 70)
    
    failures = []
    cross_folder_issues = []
    
    # Check all folders
    folders_to_check = [
        ("Pitched_Roof_Skylights", ["VS", "VSE", "VSS", "FS"]),
        ("Low_Pitch_Skylights", ["VCM", "VCS", "FCM"]),
        ("Sun_Tunnels", ["TWR", "TLR", "TWF", "TCR"]),
        ("Flashings", ["EDW", "EDL", "EKW"]),
        ("Roof_Windows", ["GGU"]),
        ("Blinds_and_Controls", []),
    ]
    
    for folder, expected_prefixes in folders_to_check:
        folder_path = f"{STORAGE_PREFIX}/{folder}"
        try:
            files = supabase.storage.from_(BUCKET_NAME).list(path=folder_path)
            for f in files:
                filename = f.get('name', '')
                if filename.endswith('.pdf'):
                    # Check for generic filenames
                    if is_generic_filename(filename):
                        failures.append(f"{folder}/{filename}")
                    
                    # Cross-folder check: VS files should NOT be in Low_Pitch
                    if folder == "Low_Pitch_Skylights":
                        for pitched_prefix in ["VS ", "VSE ", "VSS ", "FS "]:
                            if pitched_prefix in filename:
                                cross_folder_issues.append(f"❌ {filename} found in {folder} (should be Pitched)")
        except Exception as e:
            print(f"  ⚠️ Could not check {folder}: {e}")
    
    print(f"\n📊 Verification Results:")
    print(f"   Generic filename failures: {len(failures)}")
    print(f"   Cross-folder issues: {len(cross_folder_issues)}")
    
    if failures:
        print(f"\n   ❌ Generic Filename FAILURES:")
        for f in failures[:5]:
            print(f"      - {f}")
    
    if cross_folder_issues:
        print(f"\n   ❌ Cross-folder ISSUES:")
        for issue in cross_folder_issues[:5]:
            print(f"      {issue}")
    
    if not failures and not cross_folder_issues:
        print(f"   ✅ ALL CHECKS PASSED")
    
    return len(failures) + len(cross_folder_issues)


def main():
    """Main scraping function."""
    print("=" * 70)
    print(f"🪟 VELUX SKYLIGHTS SCRAPER (Protocol v{PROTOCOL_VERSION})")
    print("=" * 70)
    
    print_protocol_summary()
    
    print(f"\nStorage: {BUCKET_NAME}/{STORAGE_PREFIX}")
    print("=" * 70)
    
    # Process each category
    process_category("PITCHED ROOF SKYLIGHTS (15-90°)", "Pitched_Roof_Skylights", PITCHED_ROOF_SKYLIGHTS)
    process_category("LOW PITCH SKYLIGHTS (0-60°)", "Low_Pitch_Skylights", LOW_PITCH_SKYLIGHTS)
    process_category("ROOF WINDOWS", "Roof_Windows", ROOF_WINDOWS)
    process_category("SUN TUNNELS", "Sun_Tunnels", SUN_TUNNELS)
    process_category("FLASHINGS (Critical - Weathertightness)", "Flashings", FLASHINGS)
    process_category("BLINDS AND CONTROLS", "Blinds_and_Controls", BLINDS_CONTROLS)
    
    # Run verification
    failures = run_verification()
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 SCRAPING SUMMARY")
    print("=" * 70)
    print(f"Protocol Version:           v{PROTOCOL_VERSION}")
    print(f"Categories processed:       {stats['categories_processed']}")
    print(f"PDFs found:                 {stats['pdfs_found']}")
    print(f"PDFs uploaded:              {stats['pdfs_uploaded']}")
    print(f"PDFs skipped (duplicate):   {stats['pdfs_skipped_duplicate']}")
    print(f"Monoliths detected (Rule 8): {stats['monoliths_detected']}")
    print(f"Errors:                     {stats['errors']}")
    print(f"Verification failures:      {failures}")
    print("=" * 70)
    
    if failures == 0:
        print("✅ ALL PROTOCOL RULES PASSED")
    else:
        print(f"⚠️ {failures} VERIFICATION FAILURES - Review required")


if __name__ == "__main__":
    main()
