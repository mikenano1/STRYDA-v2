#!/usr/bin/env python3
"""
Viblock Masonry Deep Scrape
===========================
Protocol v2.0 Compliant Scraper for Viblock Wall Cladding Products

Discovered Structure:
- VENEER BRICKS (10 Series + 70 Series Kiwibricks) - share universal Veneers PDFs
- STRUCTURAL MASONRY (Textured, Honed, Fluted) - share universal Structural PDFs
- UNIVERSAL RESOURCES - Care, Warranty, Sealing, Sale Conditions

Rules Applied:
- Rule 0: Reconnaissance complete - no product-specific PDFs found (all universal)
- Rule 1: Contextual naming with series identification
- Rule 3: Universal docs to 00_General_Resources
- Rule 7: External Concrete NZ links skipped (supply chain hierarchy)
- Rule 10: Both BPIR documents (Veneers + Structural) are MANDATORY
"""

import os
import sys
import requests
import time

sys.path.insert(0, '/app/backend-minimal')

from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

from supabase import create_client

# Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
BUCKET = 'product-library'
BASE_PATH = 'B_Enclosure/Wall_Cladding/Viblock_Masonry'

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================================
# PDF MANIFEST - Discovered via Reconnaissance
# ============================================================

# PRIORITY 0: BPIR Documents (MANDATORY - Rule 10)
BPIR_DOCS = [
    {
        "url": "https://www.viblock.co.nz/wp-content/uploads/2024/05/Viblock-BPIR-Veneers.pdf",
        "filename": "Viblock - Veneers - BPIR.pdf",
        "folder": "Veneer_Bricks",
        "priority": 0
    },
    {
        "url": "https://www.viblock.co.nz/wp-content/uploads/2024/05/Viblock-BPIR-Structural-Masonry.pdf",
        "filename": "Viblock - Structural - BPIR.pdf",
        "folder": "Structural",
        "priority": 0
    }
]

# PRIORITY 1: System Specifications & Technical Information
SYSTEM_SPECS = [
    {
        "url": "https://www.viblock.co.nz/wp-content/uploads/2023/12/Viblock-Veneers-System-Specification-Oct-2023.pdf",
        "filename": "Viblock - Veneers - System Specification Oct 2023.pdf",
        "folder": "Veneer_Bricks",
        "priority": 1
    },
    {
        "url": "https://www.viblock.co.nz/wp-content/uploads/2024/02/Viblock-Structural-Architectural-Information.pdf",
        "filename": "Viblock - Structural - Architectural Information.pdf",
        "folder": "Structural",
        "priority": 1
    }
]

# PRIORITY 2: Product Brochures & Technical Data
PRODUCT_DOCS = [
    {
        "url": "https://www.viblock.co.nz/wp-content/uploads/2023/12/Viblock-Veneers-Product-Book_compressed.pdf",
        "filename": "Viblock - Veneers - Product Brochure.pdf",
        "folder": "Veneer_Bricks",
        "priority": 2
    },
    {
        "url": "https://www.viblock.co.nz/wp-content/uploads/2025/05/2025-Viblock-Block-Chart-A4.pdf",
        "filename": "Viblock - Block Chart 2025.pdf",
        "folder": "Structural",
        "priority": 2
    },
    {
        "url": "https://www.viblock.co.nz/wp-content/uploads/2019/12/MSDS-Viblock-Masonry.pdf",
        "filename": "Viblock - MSDS Safety Data Sheet.pdf",
        "folder": "00_General_Resources",
        "priority": 2
    }
]

# PRIORITY 3: Universal / General Resources (Rule 3)
UNIVERSAL_DOCS = [
    {
        "url": "https://www.viblock.co.nz/wp-content/uploads/2023/12/Guidelines-for-care-of-Architectural-Concrete-Masonry.pdf",
        "filename": "Viblock - Care and Maintenance Guide.pdf",
        "folder": "00_General_Resources",
        "priority": 3
    },
    {
        "url": "https://www.viblock.co.nz/wp-content/uploads/2023/12/Product-Warranties-2023.pdf",
        "filename": "Viblock - Product Warranty 2023.pdf",
        "folder": "00_General_Resources",
        "priority": 3
    },
    {
        "url": "https://www.viblock.co.nz/wp-content/uploads/2024/07/Viblock-Sealer-Information.pdf",
        "filename": "Viblock - Sealer Information.pdf",
        "folder": "00_General_Resources",
        "priority": 3
    },
    {
        "url": "https://www.viblock.co.nz/wp-content/uploads/2025/05/Viblock-Sale-Conditions.pdf",
        "filename": "Viblock - Conditions of Sale 2025.pdf",
        "folder": "00_General_Resources",
        "priority": 3
    },
    {
        "url": "https://www.viblock.co.nz/wp-content/uploads/2019/12/Viblock-StoClear-Coatings-Brochure.pdf",
        "filename": "Viblock - StoClear Coatings Brochure.pdf",
        "folder": "00_General_Resources",
        "priority": 3
    },
    {
        "url": "https://www.viblock.co.nz/wp-content/uploads/2019/12/Viblock-10-Series-Architectural-Veneers-Information.doc",
        "filename": None,  # Skip - .doc not PDF
        "folder": None,
        "priority": 99,
        "skip_reason": "Rule 4: .doc extension not supported"
    },
    {
        "url": "https://www.viblock.co.nz/wp-content/uploads/2019/12/NZCMA-MM-5.5-Veneer-Stack-Bond.pdf",
        "filename": "Viblock - NZCMA Veneer Stack Bond Guide.pdf",
        "folder": "00_General_Resources",
        "priority": 3
    }
]

# SKIPPED DOCUMENTS (Rule 7 - External Supply Chain)
SKIPPED_EXTERNAL = [
    "https://cdn.ymaws.com/concretenz.org.nz/resource/resmgr/docs/masonry/m_work_guide_jul_20.pdf",  # Concrete NZ
    "https://cdn.ymaws.com/concretenz.org.nz/resource/resmgr/docs/masonry/m_workmanship_guide_jul_20.pdf",  # Concrete NZ
    "https://concretenz.org.nz/page/masonry_manual",  # External link
    "https://www.level.org.nz/passive-design/thermal-mass/thermal-mass-design/",  # External link
    "https://www.masterbrickandblock.co.nz/Public_Resources",  # External link
]

# Combine all documents
ALL_DOCS = BPIR_DOCS + SYSTEM_SPECS + PRODUCT_DOCS + UNIVERSAL_DOCS


def get_existing_files():
    """Get list of existing files in Viblock_Masonry directory"""
    existing = set()
    
    # Check root and subfolders
    folders_to_check = [
        '',
        'Veneer_Bricks',
        'Structural', 
        '00_General_Resources',
        'Masonry_Veneer'  # Legacy folder from previous scrape
    ]
    
    for folder in folders_to_check:
        try:
            path = f"{BASE_PATH}/{folder}" if folder else BASE_PATH
            result = supabase.storage.from_(BUCKET).list(path)
            for item in result:
                if item.get('name') and not item.get('id') is None:
                    existing.add(item['name'].lower())
        except Exception as e:
            pass
    
    return existing


def download_pdf(url):
    """Download PDF content with retry logic"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for attempt in range(3):
        try:
            response = requests.get(url, headers=headers, timeout=60)
            if response.status_code == 200 and len(response.content) > 1000:
                # Verify it's actually a PDF
                if response.content[:4] == b'%PDF':
                    return response.content
                else:
                    print(f"    ⚠️ Not a valid PDF: {url}")
                    return None
            elif response.status_code == 404:
                print(f"    ❌ 404 Not Found: {url}")
                return None
            else:
                print(f"    ⚠️ Attempt {attempt+1}: HTTP {response.status_code}")
        except Exception as e:
            print(f"    ⚠️ Attempt {attempt+1}: {str(e)[:50]}")
        time.sleep(2)
    
    return None


def upload_to_supabase(content, folder, filename):
    """Upload PDF to Supabase Storage"""
    storage_path = f"{BASE_PATH}/{folder}/{filename}"
    
    try:
        supabase.storage.from_(BUCKET).upload(
            storage_path,
            content,
            {"content-type": "application/pdf", "upsert": "true"}
        )
        return True
    except Exception as e:
        if "Duplicate" in str(e) or "already exists" in str(e).lower():
            print(f"    ℹ️ Already exists, skipping")
            return True
        print(f"    ❌ Upload failed: {str(e)[:50]}")
        return False


def main():
    print("=" * 70)
    print("VIBLOCK MASONRY DEEP SCRAPE")
    print("Protocol v2.0 Compliant")
    print("=" * 70)
    
    # Get existing files for deduplication
    existing_files = get_existing_files()
    print(f"\n📂 Found {len(existing_files)} existing files in Viblock_Masonry/")
    
    # Statistics
    stats = {
        "downloaded": 0,
        "skipped_exists": 0,
        "skipped_rule": 0,
        "failed": 0
    }
    
    # Sort by priority
    sorted_docs = sorted([d for d in ALL_DOCS if d.get('filename')], key=lambda x: x['priority'])
    
    print(f"\n📋 Processing {len(sorted_docs)} documents...\n")
    
    for doc in sorted_docs:
        url = doc['url']
        filename = doc['filename']
        folder = doc['folder']
        priority = doc['priority']
        
        if not filename:
            continue
            
        priority_label = {0: "P0-BPIR", 1: "P1-SPEC", 2: "P2-TECH", 3: "P3-GENERAL"}.get(priority, "P?")
        print(f"[{priority_label}] {filename}")
        
        # Check for duplicates (case-insensitive)
        if filename.lower() in existing_files:
            print(f"    ⏭️ Already exists - skipping")
            stats["skipped_exists"] += 1
            continue
        
        # Download
        print(f"    ⬇️ Downloading...")
        content = download_pdf(url)
        
        if not content:
            stats["failed"] += 1
            continue
        
        # Upload
        print(f"    ⬆️ Uploading to {folder}/")
        if upload_to_supabase(content, folder, filename):
            stats["downloaded"] += 1
            existing_files.add(filename.lower())
            print(f"    ✅ Success ({len(content):,} bytes)")
        else:
            stats["failed"] += 1
        
        time.sleep(0.5)  # Rate limiting
    
    # Print summary
    print("\n" + "=" * 70)
    print("SCRAPE SUMMARY")
    print("=" * 70)
    print(f"✅ Downloaded: {stats['downloaded']}")
    print(f"⏭️ Already existed: {stats['skipped_exists']}")
    print(f"🚫 Skipped (rules): {stats['skipped_rule']}")
    print(f"❌ Failed: {stats['failed']}")
    
    print("\n📁 Skipped External Resources (Rule 7):")
    for url in SKIPPED_EXTERNAL:
        print(f"   - {url[:60]}...")
    
    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)
    
    # Verify final structure
    for folder in ['Veneer_Bricks', 'Structural', '00_General_Resources']:
        try:
            result = supabase.storage.from_(BUCKET).list(f"{BASE_PATH}/{folder}")
            files = [f['name'] for f in result if f.get('name')]
            print(f"\n📂 {folder}/ ({len(files)} files)")
            for f in sorted(files):
                print(f"   └─ {f}")
        except Exception as e:
            print(f"   ❌ Error listing {folder}: {e}")
    
    return stats['failed'] == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
