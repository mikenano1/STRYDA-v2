#!/usr/bin/env python3
"""
Metalcraft Structural Scraper (ComFlor & Purlins)
==================================================
Downloads technical PDFs for composite flooring and steel framing products.

Implements STRYDA MASTER PROTOCOL:
- Rule 7: SKIP Galvsteel/NZ Steel supplier documents OR route to supplier folder
- File Naming: "Metalcraft - [Product] - [Doc Type].pdf"

Storage: /B_Structure/Metalcraft_Structural/
- /ComFlor_Unifloor/
- /ComFlor_Svelte_60/
- /ComFlor_Svelte_80/
- /MSS_Purlins/
- /MC_Purlins/
- /MZ_Purlins/
- /Top_Hats/
- /Bracing_Systems/
- /00_General_Resources/

Author: STRYDA Data Pipeline
Date: 2025-01
"""

import os
import re
import time
import requests
from supabase import create_client
from dotenv import load_dotenv

load_dotenv("/app/backend-minimal/.env")

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
BUCKET_NAME = "product-library"

print(f"🔗 Supabase URL: {SUPABASE_URL[:30]}..." if SUPABASE_URL else "❌ No SUPABASE_URL")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

BASE_URL = "https://www.metalcraftgroup.co.nz"
STORAGE_PREFIX = "B_Structure/Metalcraft_Structural"
SUPPLIER_PREFIX = "B_Enclosure/00_Material_Suppliers"

# Rule 7: Galvsteel/NZ Steel keywords - these go to supplier folder
GALVSTEEL_KEYWORDS = [
    "galvsteel warranty", "durability statement", "zinc coating", "nz steel durability",
    "galvsteel", "zincalume"
]

# Universal docs (deduplicated)
UNIVERSAL_KEYWORDS = ["eco choice certificate"]

# Stats tracking
stats = {
    "products_processed": 0,
    "pdfs_found": 0,
    "pdfs_uploaded": 0,
    "pdfs_skipped_supplier": 0,
    "pdfs_skipped_duplicate": 0,
    "pdfs_to_supplier_folder": 0,
    "errors": 0,
}

# Track uploaded files for deduplication (by URL)
uploaded_urls = set()
universal_uploaded = set()


# =============================================================================
# COMPOSITE FLOORING PRODUCTS (ComFlor)
# =============================================================================
COMFLOR_PRODUCTS = {
    "ComFlor_Unifloor": [
        ("Information Brochure", "https://www.metalcraftgroup.co.nz/media/456732/composite-tray-flooring-manual-november-23-uploaded-271123.pdf"),
        ("Installation Details", "https://www.metalcraftgroup.co.nz/media/456610/mr-2220135-metalcraft_composite_steel_flooring-unifloor.pdf"),
        ("BPIS Building Product Information Sheet", "https://www.metalcraftgroup.co.nz/media/456760/mc-bpis-metalcraft-composite-tray-flooring-071223.pdf"),
        ("Technical Bulletin - Durability", "https://www.metalcraftgroup.co.nz/media/544127/tbmccc2025-02-durability.pdf"),
        ("Technical Bulletin - Car Parks", "https://www.metalcraftgroup.co.nz/media/544128/tbmccc2025-01-solutions-for-car-parks.pdf"),
    ],
    "ComFlor_Svelte_60": [
        ("Information Brochure", "https://www.metalcraftgroup.co.nz/media/456732/composite-tray-flooring-manual-november-23-uploaded-271123.pdf"),
        ("Installation Details", "https://www.metalcraftgroup.co.nz/media/456602/pdf-mr-s2220135-metalcraft_composite_steel_flooring-svelte-60.pdf"),
        ("BPIS Building Product Information Sheet", "https://www.metalcraftgroup.co.nz/media/456760/mc-bpis-metalcraft-composite-tray-flooring-071223.pdf"),
        ("Technical Bulletin - Durability", "https://www.metalcraftgroup.co.nz/media/544127/tbmccc2025-02-durability.pdf"),
        ("Technical Bulletin - Car Parks", "https://www.metalcraftgroup.co.nz/media/544128/tbmccc2025-01-solutions-for-car-parks.pdf"),
    ],
    "ComFlor_Svelte_80": [
        ("Information Brochure", "https://www.metalcraftgroup.co.nz/media/456732/composite-tray-flooring-manual-november-23-uploaded-271123.pdf"),
        ("Installation Details", "https://www.metalcraftgroup.co.nz/media/456606/pdf-2220135-metalcraft_composite_steel_flooring-svelte-80.pdf"),
        ("BPIS Building Product Information Sheet", "https://www.metalcraftgroup.co.nz/media/456760/mc-bpis-metalcraft-composite-tray-flooring-071223.pdf"),
        ("Technical Bulletin - Durability", "https://www.metalcraftgroup.co.nz/media/544127/tbmccc2025-02-durability.pdf"),
        ("Technical Bulletin - Car Parks", "https://www.metalcraftgroup.co.nz/media/544128/tbmccc2025-01-solutions-for-car-parks.pdf"),
    ],
}

# =============================================================================
# PURLINS & STRUCTURAL PRODUCTS
# =============================================================================
PURLIN_PRODUCTS = {
    "MSS_Purlins": [
        ("Structural Guide", "https://www.metalcraftgroup.co.nz/media/544173/mc-structural-guideapril2020.pdf"),
        ("MSS Section Geometry", "https://www.metalcraftgroup.co.nz/media/544206/pdf-metalcraft-mss-section-geometry.pdf"),
        ("BPIS Structural Products", "https://www.metalcraftgroup.co.nz/media/456762/mc-bpis-metalcraft-strctural-products-071223.pdf"),
    ],
    "MC_Purlins": [
        ("Structural Guide", "https://www.metalcraftgroup.co.nz/media/544173/mc-structural-guideapril2020.pdf"),
        ("MC Section Geometry", "https://www.metalcraftgroup.co.nz/media/544202/pdf-metalcraft-mc-section-geometry.pdf"),
        ("BPIS Structural Products", "https://www.metalcraftgroup.co.nz/media/456762/mc-bpis-metalcraft-strctural-products-071223.pdf"),
    ],
    "MZ_Purlins": [
        ("Structural Guide", "https://www.metalcraftgroup.co.nz/media/544173/mc-structural-guideapril2020.pdf"),
        ("MZ Section Geometry", "https://www.metalcraftgroup.co.nz/media/544198/pdf-metalcraft-mz-section-geometry.pdf"),
        ("BPIS Structural Products", "https://www.metalcraftgroup.co.nz/media/456762/mc-bpis-metalcraft-strctural-products-071223.pdf"),
    ],
    "Top_Hats": [
        ("Structural Guide", "https://www.metalcraftgroup.co.nz/media/544173/mc-structural-guideapril2020.pdf"),
        ("BPIS Structural Products", "https://www.metalcraftgroup.co.nz/media/456762/mc-bpis-metalcraft-strctural-products-071223.pdf"),
        ("Structural Guide Alt", "https://www.metalcraftgroup.co.nz/media/1001/mc-structural-guidejunel2020.pdf"),
    ],
    "Bracing_Systems": [
        ("Structural Guide", "https://www.metalcraftgroup.co.nz/media/544173/mc-structural-guideapril2020.pdf"),
        ("BPIS Structural Products", "https://www.metalcraftgroup.co.nz/media/456762/mc-bpis-metalcraft-strctural-products-071223.pdf"),
    ],
}

# =============================================================================
# SUPPLIER-LEVEL DOCUMENTS (Rule 7 - route to supplier folder)
# =============================================================================
SUPPLIER_DOCUMENTS = [
    # NZ Steel Durability Statement - goes to /00_Material_Suppliers/NZ_Steel_Galv/
    ("NZ Steel - Durability Statement", "https://www.metalcraftgroup.co.nz/media/456736/durability-statement-v2019.pdf"),
]

# Universal resources (stored once in 00_General_Resources)
UNIVERSAL_RESOURCES = [
    ("Eco Choice Certificate", "https://www.metalcraftgroup.co.nz/media/544119/nz-steel-ec-57-certificate-may-26.pdf"),
]


def sanitize_filename(name):
    """Clean filename - remove trademark symbols and invalid chars"""
    name = name.replace('™', '').replace('®', '').replace('©', '')
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    if len(name) > 200:
        name = name[:200]
    return name


def is_galvsteel_supplier_doc(doc_title):
    """Check if document is a Galvsteel/NZ Steel supplier document (Rule 7)"""
    title_lower = doc_title.lower()
    for keyword in GALVSTEEL_KEYWORDS:
        if keyword in title_lower:
            return True
    return False


def is_universal_doc(doc_title):
    """Check if document is a universal resource"""
    title_lower = doc_title.lower()
    for keyword in UNIVERSAL_KEYWORDS:
        if keyword in title_lower:
            return True
    return False


def file_exists_in_supabase(storage_path):
    """Check if file already exists in Supabase storage"""
    try:
        folder = "/".join(storage_path.split("/")[:-1])
        filename = storage_path.split("/")[-1]
        result = supabase.storage.from_(BUCKET_NAME).list(path=folder)
        return any(f.get('name') == filename for f in result)
    except Exception:
        return False


def upload_to_supabase(pdf_url, storage_path, doc_title):
    """Download PDF and upload to Supabase storage"""
    try:
        # Download PDF
        print(f"  📥 Downloading: {doc_title[:50]}...")
        response = requests.get(pdf_url, timeout=60)
        if response.status_code != 200:
            print(f"  ❌ Failed to download (HTTP {response.status_code})")
            stats["errors"] += 1
            return False
        
        pdf_content = response.content
        
        # Check if it's actually a PDF
        if not pdf_content[:4] == b'%PDF':
            print(f"  ⚠️ Not a valid PDF file")
            stats["errors"] += 1
            return False
        
        # Upload to Supabase
        try:
            supabase.storage.from_(BUCKET_NAME).upload(
                storage_path,
                pdf_content,
                {"content-type": "application/pdf"}
            )
            print(f"  ✅ Uploaded: {storage_path}")
            return True
        except Exception as e:
            if "Duplicate" in str(e) or "already exists" in str(e).lower():
                print(f"  ⏭️ Already exists: {storage_path}")
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


def process_product(product_name, documents):
    """Process all documents for a product"""
    print(f"\n📁 Processing: {product_name}")
    stats["products_processed"] += 1
    
    product_folder = f"{STORAGE_PREFIX}/{product_name}"
    
    for doc_title, pdf_url in documents:
        stats["pdfs_found"] += 1
        
        # Skip if URL already processed
        if pdf_url in uploaded_urls:
            print(f"  ⏭️ SKIPPED (Duplicate URL): {doc_title[:40]}...")
            stats["pdfs_skipped_duplicate"] += 1
            continue
        
        # Rule 7: Check for Galvsteel supplier docs
        if is_galvsteel_supplier_doc(doc_title):
            print(f"  ⏭️ SKIPPED (Supplier Doc - Rule 7): {doc_title[:40]}...")
            stats["pdfs_skipped_supplier"] += 1
            continue
        
        # Skip universal docs (handled separately)
        if is_universal_doc(doc_title):
            print(f"  ⏭️ SKIPPED (Universal): {doc_title[:40]}...")
            continue
        
        # Generate filename: "Metalcraft - [Product] - [Doc Type].pdf"
        clean_title = sanitize_filename(doc_title)
        product_short = product_name.replace("_", " ")
        filename = f"Metalcraft - {product_short} - {clean_title}.pdf"
        storage_path = f"{product_folder}/{filename}"
        
        # Upload
        if upload_to_supabase(pdf_url, storage_path, doc_title):
            stats["pdfs_uploaded"] += 1
            uploaded_urls.add(pdf_url)
        
        time.sleep(0.3)


def process_supplier_documents():
    """Process supplier-level documents (Rule 7 routing)"""
    print(f"\n📁 Processing Supplier Documents (Rule 7 - NZ_Steel_Galv)")
    
    supplier_folder = f"{SUPPLIER_PREFIX}/NZ_Steel_Galv"
    
    for doc_title, pdf_url in SUPPLIER_DOCUMENTS:
        stats["pdfs_found"] += 1
        
        if pdf_url in uploaded_urls:
            print(f"  ⏭️ SKIPPED (Already uploaded): {doc_title}")
            continue
        
        clean_title = sanitize_filename(doc_title)
        filename = f"{clean_title}.pdf"
        storage_path = f"{supplier_folder}/{filename}"
        
        if upload_to_supabase(pdf_url, storage_path, doc_title):
            stats["pdfs_to_supplier_folder"] += 1
            uploaded_urls.add(pdf_url)
        
        time.sleep(0.3)


def process_universal_resources():
    """Upload universal resources to 00_General_Resources folder"""
    print(f"\n📁 Processing Universal Resources (00_General_Resources)")
    
    general_folder = f"{STORAGE_PREFIX}/00_General_Resources"
    
    for doc_title, pdf_url in UNIVERSAL_RESOURCES:
        stats["pdfs_found"] += 1
        
        if pdf_url in universal_uploaded:
            print(f"  ⏭️ SKIPPED (Already uploaded): {doc_title}")
            continue
        
        clean_title = sanitize_filename(doc_title)
        filename = f"Metalcraft Structural - {clean_title}.pdf"
        storage_path = f"{general_folder}/{filename}"
        
        if upload_to_supabase(pdf_url, storage_path, doc_title):
            stats["pdfs_uploaded"] += 1
            universal_uploaded.add(pdf_url)
        
        time.sleep(0.3)


def main():
    """Main scraping function"""
    print("=" * 70)
    print("🏗️  METALCRAFT STRUCTURAL SCRAPER (ComFlor & Purlins)")
    print("=" * 70)
    print(f"Target: {BASE_URL}")
    print(f"Storage: {BUCKET_NAME}/{STORAGE_PREFIX}")
    print()
    print("⚠️  RULE 7 ACTIVE: Galvsteel/NZ Steel docs routed to supplier folder")
    print(f"    Supplier Path: {SUPPLIER_PREFIX}/NZ_Steel_Galv/")
    print("=" * 70)
    
    # Process universal resources first
    process_universal_resources()
    
    # Process supplier documents (Rule 7 routing)
    process_supplier_documents()
    
    # Process ComFlor products
    print("\n" + "=" * 50)
    print("📦 COMPOSITE FLOORING (ComFlor)")
    print("=" * 50)
    for product_name, documents in COMFLOR_PRODUCTS.items():
        process_product(product_name, documents)
    
    # Process Purlin products
    print("\n" + "=" * 50)
    print("📦 PURLINS & STRUCTURAL FRAMING")
    print("=" * 50)
    for product_name, documents in PURLIN_PRODUCTS.items():
        process_product(product_name, documents)
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 SCRAPING SUMMARY")
    print("=" * 70)
    print(f"Products processed:           {stats['products_processed']}")
    print(f"PDFs found:                   {stats['pdfs_found']}")
    print(f"PDFs uploaded:                {stats['pdfs_uploaded']}")
    print(f"PDFs to supplier folder:      {stats['pdfs_to_supplier_folder']}")
    print(f"PDFs skipped (supplier docs): {stats['pdfs_skipped_supplier']}")
    print(f"PDFs skipped (duplicate):     {stats['pdfs_skipped_duplicate']}")
    print(f"Errors:                       {stats['errors']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
