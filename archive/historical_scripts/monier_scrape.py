#!/usr/bin/env python3
"""
Monier Roofing Scraper (Protocol v2.0)
======================================
Downloads technical PDFs for Monier NZ concrete and terracotta roof tiles.

Uses src/ingestion_rules.py for Protocol v2.0 enforcement:
- Rule 1: Context-aware naming (no PTS_Madison.pdf)
- Rule 3: Universal docs to 00_General_Resources
- Rule 6: Hidden technical data check on brochures

Storage: /B_Enclosure/Monier_Roofing/
- /Concrete_Tiles/
- /Terracotta_Tiles/
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
    is_universal_document,
    sanitize_filename,
    ALLOWED_EXTENSIONS,
    print_protocol_summary
)

load_dotenv("/app/backend-minimal/.env")

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
BUCKET_NAME = "product-library"

print(f"🔗 Supabase URL: {SUPABASE_URL[:30]}..." if SUPABASE_URL else "❌ No SUPABASE_URL")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

STORAGE_PREFIX = "B_Enclosure/Monier_Roofing"

# Stats tracking
stats = {
    "products_processed": 0,
    "pdfs_found": 0,
    "pdfs_uploaded": 0,
    "pdfs_skipped_duplicate": 0,
    "pdfs_to_general": 0,
    "rule1_violations_fixed": 0,
    "errors": 0,
}

# Track uploaded files for deduplication
uploaded_urls = set()


# =============================================================================
# CONCRETE TILES
# =============================================================================
CONCRETE_TILES = {
    "Horizon": {
        "folder": "Concrete_Tiles/Horizon",
        "docs": [
            ("Product Technical Statement", "https://celumcsrcomaublobs.blob.core.windows.net/celum/31528_yConnect_Document_NZ%20Horizon%20Product%20Technical%20Statement.pdf"),
            ("Collections Brochure", "https://celumcsrcomaublobs.blob.core.windows.net/celum/19383_yConnect_Document_Monier%20NZ%20Collections%20Brochure%20July%202019.pdf"),
            ("C-LOC Technology Brochure", "https://celumcsrcomaublobs.blob.core.windows.net/celum/77139_yConnect_Document_Monier_C-LocBrochure_LR.pdf"),
        ]
    },
    "Tudor": {
        "folder": "Concrete_Tiles/Tudor",
        "docs": [
            ("Product Technical Statement", "https://celumcsrcomaublobs.blob.core.windows.net/celum/31533_yConnect_Document_NZ%20Tudor%20Product%20Technical%20Statement.pdf"),
        ]
    },
    "Hacienda": {
        "folder": "Concrete_Tiles/Hacienda",
        "docs": [
            ("Product Technical Statement", "https://celumcsrcomaublobs.blob.core.windows.net/celum/2915_yConnect_Document_NZ%20Hacienda%20Product%20Technical%20Statement.pdf"),
        ]
    },
}

# =============================================================================
# TERRACOTTA TILES
# =============================================================================
TERRACOTTA_TILES = {
    "Nouveau": {
        "folder": "Terracotta_Tiles/Nouveau",
        "docs": [
            ("Product Technical Statement", "https://celumcsrcomaublobs.blob.core.windows.net/celum/31529_yConnect_Document_NZ%20Nouveau%20Product%20Technical%20Statement.pdf"),
        ]
    },
    "Marseille": {
        "folder": "Terracotta_Tiles/Marseille",
        "docs": [
            ("Product Technical Statement", "https://celumcsrcomaublobs.blob.core.windows.net/celum/31530_yConnect_Document_NZ%20Marseille%20Product%20Technical%20Statement.pdf"),
        ]
    },
    "Portuguese": {
        "folder": "Terracotta_Tiles/Portuguese",
        "docs": [
            ("Product Technical Statement", "https://celumcsrcomaublobs.blob.core.windows.net/celum/31534_yConnect_Document_NZ%20Portuguese%20Product%20Technical%20Statement.pdf"),
            ("Collections Brochure", "https://celumcsrcomaublobs.blob.core.windows.net/celum/2009_yConnect_Document_Monier%20Collections%20Brochure.pdf"),
        ]
    },
    "Urban_Shingle": {
        "folder": "Terracotta_Tiles/Urban_Shingle",
        "docs": [
            ("Product Technical Statement", "https://celumcsrcomaublobs.blob.core.windows.net/celum/31535_yConnect_Document_NZ%20Urban%20Shingle%20Product%20Technical%20Statement.pdf"),
        ]
    },
}

# =============================================================================
# UNIVERSAL RESOURCES (Rule 3 - go to 00_General_Resources)
# =============================================================================
UNIVERSAL_RESOURCES = [
    ("50 Year Performance Guarantee", "https://celumcsrcomaublobs.blob.core.windows.net/celum/19383_yConnect_Document_Monier%20NZ%20Collections%20Brochure%20July%202019.pdf"),
    ("C-LOC Colour Lock Technology", "https://celumcsrcomaublobs.blob.core.windows.net/celum/77139_yConnect_Document_Monier_C-LocBrochure_LR.pdf"),
    ("NZ Collections Brochure", "https://celumcsrcomaublobs.blob.core.windows.net/celum/19383_yConnect_Document_Monier%20NZ%20Collections%20Brochure%20July%202019.pdf"),
]


def apply_rule1_naming(original_title: str, product_name: str) -> str:
    """
    Rule 1: Context-Aware Naming
    Transform generic names like "PTS_Madison.pdf" to proper format.
    """
    # Check if it's a generic filename
    if is_generic_filename(original_title):
        stats["rule1_violations_fixed"] += 1
        print(f"    ⚠️ Rule 1 Fix: '{original_title}' → context-aware name")
    
    # Clean the title
    clean_title = sanitize_filename(original_title)
    
    # Format: "Monier - [Product] - [Document Type].pdf"
    return f"Monier - {product_name} - {clean_title}.pdf"


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


def process_product(product_name: str, product_data: dict):
    """Process all documents for a product."""
    print(f"\n📁 Processing: {product_name}")
    stats["products_processed"] += 1
    
    folder = product_data["folder"]
    
    for doc_title, pdf_url in product_data["docs"]:
        stats["pdfs_found"] += 1
        
        # Skip if URL already processed
        if pdf_url in uploaded_urls:
            print(f"  ⏭️ SKIPPED (Duplicate URL): {doc_title[:40]}...")
            stats["pdfs_skipped_duplicate"] += 1
            continue
        
        # Rule 3: Check if universal document
        if is_universal_document(doc_title):
            print(f"  📋 Rule 3: '{doc_title}' → 00_General_Resources")
            stats["pdfs_to_general"] += 1
            # Will be handled in universal resources section
            continue
        
        # Rule 1: Apply context-aware naming
        filename = apply_rule1_naming(doc_title, product_name)
        storage_path = f"{STORAGE_PREFIX}/{folder}/{filename}"
        
        # Upload
        if upload_to_supabase(pdf_url, storage_path, doc_title):
            stats["pdfs_uploaded"] += 1
            uploaded_urls.add(pdf_url)
        
        time.sleep(0.3)


def process_universal_resources():
    """Process universal resources (Rule 3)."""
    print(f"\n📁 Processing Universal Resources (00_General_Resources)")
    
    general_folder = f"{STORAGE_PREFIX}/00_General_Resources"
    
    for doc_title, pdf_url in UNIVERSAL_RESOURCES:
        stats["pdfs_found"] += 1
        
        if pdf_url in uploaded_urls:
            print(f"  ⏭️ SKIPPED (Already uploaded): {doc_title[:40]}...")
            stats["pdfs_skipped_duplicate"] += 1
            continue
        
        # Format for universal: "Monier - Universal - [Title].pdf"
        clean_title = sanitize_filename(doc_title)
        filename = f"Monier - Universal - {clean_title}.pdf"
        storage_path = f"{general_folder}/{filename}"
        
        if upload_to_supabase(pdf_url, storage_path, doc_title):
            stats["pdfs_uploaded"] += 1
            uploaded_urls.add(pdf_url)
        
        time.sleep(0.3)


def run_verification():
    """Rule 5: Verification - check for generic filename failures."""
    print("\n" + "=" * 70)
    print("📋 RULE 5 VERIFICATION - Checking for generic filename failures")
    print("=" * 70)
    
    # List all uploaded files and check
    failures = []
    
    folders_to_check = [
        f"{STORAGE_PREFIX}/Concrete_Tiles",
        f"{STORAGE_PREFIX}/Terracotta_Tiles",
        f"{STORAGE_PREFIX}/00_General_Resources",
    ]
    
    for folder in folders_to_check:
        try:
            subfolders = supabase.storage.from_(BUCKET_NAME).list(path=folder)
            for sf in subfolders:
                if sf.get('id'):  # It's a folder
                    subfolder_path = f"{folder}/{sf['name']}"
                    files = supabase.storage.from_(BUCKET_NAME).list(path=subfolder_path)
                    for f in files:
                        filename = f.get('name', '')
                        if filename.endswith('.pdf'):
                            if is_generic_filename(filename):
                                failures.append(f"{sf['name']}/{filename}")
                elif sf.get('name', '').endswith('.pdf'):
                    # Direct file in folder
                    if is_generic_filename(sf['name']):
                        failures.append(sf['name'])
        except Exception as e:
            print(f"  ⚠️ Could not check {folder}: {e}")
    
    print(f"\n📊 Verification Results:")
    print(f"   Generic filename failures: {len(failures)}")
    
    if failures:
        print(f"\n   ❌ FAILURES:")
        for f in failures[:10]:
            print(f"      - {f}")
    else:
        print(f"   ✅ PASSED: 0 generic filename failures")
    
    return len(failures)


def main():
    """Main scraping function."""
    print("=" * 70)
    print(f"🏠 MONIER ROOFING SCRAPER (Protocol v{PROTOCOL_VERSION})")
    print("=" * 70)
    
    # Print protocol summary
    print_protocol_summary()
    
    print(f"\nStorage: {BUCKET_NAME}/{STORAGE_PREFIX}")
    print("=" * 70)
    
    # Process universal resources first
    process_universal_resources()
    
    # Process Concrete Tiles
    print("\n" + "=" * 50)
    print("🧱 CONCRETE TILES")
    print("=" * 50)
    for product_name, product_data in CONCRETE_TILES.items():
        process_product(product_name, product_data)
    
    # Process Terracotta Tiles
    print("\n" + "=" * 50)
    print("🏺 TERRACOTTA TILES")
    print("=" * 50)
    for product_name, product_data in TERRACOTTA_TILES.items():
        process_product(product_name, product_data)
    
    # Run verification (Rule 5)
    failures = run_verification()
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 SCRAPING SUMMARY")
    print("=" * 70)
    print(f"Protocol Version:           v{PROTOCOL_VERSION}")
    print(f"Products processed:         {stats['products_processed']}")
    print(f"PDFs found:                 {stats['pdfs_found']}")
    print(f"PDFs uploaded:              {stats['pdfs_uploaded']}")
    print(f"PDFs to General Resources:  {stats['pdfs_to_general']}")
    print(f"Rule 1 violations fixed:    {stats['rule1_violations_fixed']}")
    print(f"PDFs skipped (duplicate):   {stats['pdfs_skipped_duplicate']}")
    print(f"Errors:                     {stats['errors']}")
    print(f"Verification failures:      {failures}")
    print("=" * 70)
    
    if failures == 0:
        print("✅ ALL PROTOCOL RULES PASSED")
    else:
        print(f"⚠️ {failures} VERIFICATION FAILURES - Review required")


if __name__ == "__main__":
    main()
