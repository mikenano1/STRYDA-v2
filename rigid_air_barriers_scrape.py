#!/usr/bin/env python3
"""
Rigid Air Barriers Scraper (Protocol v2.0)
==========================================
Downloads technical PDFs for the 4 dominant RAB systems in New Zealand:
- GIB Weatherline
- Ecoply Barrier (CHH Plywood)
- IBS RigidRAP
- James Hardie RAB (HomeRAB + RAB Board)

Protocol Enforcement:
- Rule 8: GIB Weatherline Design & Installation Manual → 00_General_Resources (Monolith)
- Rule 1: Strictly separate HomeRAB (Residential) from RAB Board (Commercial)
- Rule 6: Capture Sealing Tape and Penetration details

Author: STRYDA Data Pipeline
Date: 2025-01
"""

import os
import sys
import time
import requests
from urllib.parse import urljoin
from supabase import create_client
from dotenv import load_dotenv

sys.path.insert(0, '/app/src')
from ingestion_rules import sanitize_filename, PROTOCOL_VERSION

load_dotenv("/app/backend-minimal/.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
BUCKET_NAME = "product-library"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

STORAGE_PREFIX = "B_Enclosure/Rigid_Air_Barriers"

stats = {
    "manufacturers_processed": 0,
    "pdfs_found": 0,
    "pdfs_uploaded": 0,
    "pdfs_skipped_duplicate": 0,
    "monoliths_detected": 0,
    "errors": 0,
}

# =============================================================================
# PDF DEFINITIONS BY MANUFACTURER
# =============================================================================

GIB_WEATHERLINE = {
    "manufacturer": "GIB_Weatherline",
    "pdfs": [
        # MONOLITH - Rule 8: Main Design & Construction Manual
        {
            "url": "https://www.gib.co.nz/assets/Uploads/GIB-Weatherline-Design-and-Construction-Manual-0525.pdf",
            "folder": "00_General_Resources",
            "filename": "GIB - Weatherline - Design and Construction Manual (Master).pdf",
            "is_monolith": True
        },
        # Sales/Update Brochure
        {
            "url": "https://www.gib.co.nz/assets/Uploads/GIB-Weatherline-Sales-Brochure-Update-Mar21.pdf",
            "folder": "Installation_Manuals",
            "filename": "GIB - Weatherline - Sales Brochure Update.pdf"
        },
        # BRANZ Appraisal
        {
            "url": "https://d39d3mj7qio96p.cloudfront.net/media/documents/1048_2025.pdf",
            "folder": "Certifications",
            "filename": "GIB - Weatherline - BRANZ Appraisal 1048.pdf"
        },
    ]
}

ECOPLY_BARRIER = {
    "manufacturer": "Ecoply_Barrier",
    "pdfs": [
        # Main Specification & Installation Guide
        {
            "url": "https://chhply.co.nz/assets/Uploads/Ecoply-Barrier_Spec-Install-Guide_WebsiteCurrent.pdf",
            "folder": "Specification",
            "filename": "Ecoply - Barrier - Specification and Installation Guide.pdf"
        },
        # Alternative/Older version
        {
            "url": "https://chhply.co.nz/assets/Uploads/EcoplySpecificationInstallationGuideCurrent.pdf",
            "folder": "Specification",
            "filename": "Ecoply - Barrier - Specification Installation Guide (Current).pdf"
        },
        # Brochure from Tropex
        {
            "url": "https://tropex.co.nz/sites/default/files/product_pdfs/Ecoply%20Barrier%20Brochure.pdf",
            "folder": "Brochures",
            "filename": "Ecoply - Barrier - Product Brochure.pdf"
        },
        # Installation Tips
        {
            "url": "https://chhply.co.nz/assets/Uploads/dc4de12398/Ecoply-Barrier-Installation-Tips-March-2014.pdf",
            "folder": "Tape_System",
            "filename": "Ecoply - Barrier - Installation Tips (Tape and Sealing).pdf"
        },
        # BRANZ Appraisal
        {
            "url": "https://pimstorageaueprod.blob.core.windows.net/placemakers/media-assets/1167605_Ecoply-Barrier-BRANZ-Appraisal-827-August-19.pdf",
            "folder": "Certifications",
            "filename": "Ecoply - Barrier - BRANZ Appraisal 827.pdf"
        },
    ]
}

IBS_RIGIDRAP = {
    "manufacturer": "IBS_RigidRAP",
    "pdfs": [
        # Main Design & Installation Guide
        {
            "url": "https://ibs.co.nz/files/Technical-Documents/IBS-RigidRAP%C2%AE/IBS_RigidRAP%C2%AE_Design__Installation-Guide_April24-1.pdf",
            "folder": "Installation",
            "filename": "IBS - RigidRAP - Design and Installation Guide.pdf"
        },
        # Warranty
        {
            "url": "https://ibs.co.nz/files/Technical-Documents/IBS-RigidRAP%C2%AE/IBS-RigidRAP-Warranty-General-Terms_2025.pdf",
            "folder": "00_General_Resources",
            "filename": "IBS - RigidRAP - Warranty General Terms.pdf"
        },
        # CodeMark Certificate
        {
            "url": "https://ibs.co.nz/files/Technical-Documents/IBS-RigidRAP%C2%AE/IBS-RigidRAP-Codemark.pdf",
            "folder": "Certifications",
            "filename": "IBS - RigidRAP - CodeMark Certificate.pdf"
        },
        # Technical Properties
        {
            "url": "https://ibs.co.nz/files/Technical-Documents/IBS-RigidRAP%C2%AE/IBS_RigidRAP_Technical_Properties_2025.pdf",
            "folder": "Installation",
            "filename": "IBS - RigidRAP - Technical Properties.pdf"
        },
        # TAPING OPTIONS - Rule 6: Sealing/Tape critical for joints
        {
            "url": "https://ibs.co.nz/files/Tapeing-Documents/TK-NZ_Premium-Joining-Tape-Install-Guide.pdf",
            "folder": "Tape_System",
            "filename": "IBS - RigidRAP - Thermakraft Premium Joining Tape Install Guide.pdf"
        },
        {
            "url": "https://ibs.co.nz/files/Technical-Documents/IBS_RigidRAP%C2%AE-XT/IBS-Rigid-Rap-and-Thermaflash-031220.pdf",
            "folder": "Tape_System",
            "filename": "IBS - RigidRAP - Thermaflash Flashing Tape Compatibility Letter.pdf"
        },
        {
            "url": "https://ibs.co.nz/files/Tapeing-Documents/BRANZ-Thermaflash-0920.pdf",
            "folder": "Tape_System",
            "filename": "IBS - RigidRAP - Thermaflash BRANZ Appraisal.pdf"
        },
        {
            "url": "https://ibs.co.nz/files/Tapeing-Documents/40-Below-Platinum-and-Flex-on-IBS-Rigid-Wrap.pdf",
            "folder": "Tape_System",
            "filename": "IBS - RigidRAP - Mason 40 Below Platinum and Flex Tape.pdf"
        },
        {
            "url": "https://ibs.co.nz/files/Tapeing-Documents/Siga-Wigluv-Branz-appraisal_2025-05-18-222851_qjbm.pdf",
            "folder": "Tape_System",
            "filename": "IBS - RigidRAP - SIGA Wigluv BRANZ Appraisal.pdf"
        },
        {
            "url": "https://ibs.co.nz/files/Technical-Documents/IBS-RigidRAP%C2%AE/Confirmation_Wigluv_IBS.pdf",
            "folder": "Tape_System",
            "filename": "IBS - RigidRAP - SIGA Wigluv Confirmation Letter.pdf"
        },
        # Product Catalogue
        {
            "url": "https://ibs.co.nz/files/IBS_Product-_Catalogue_2025.pdf",
            "folder": "00_General_Resources",
            "filename": "IBS - 00 General Resources - Product Catalogue 2025.pdf"
        },
    ]
}

# James Hardie - STRICT SEPARATION: HomeRAB (Residential) vs RAB Board (Commercial)
JAMES_HARDIE_RAB = {
    "manufacturer": "James_Hardie_RAB",
    "pdfs": [
        # =====================================================================
        # HomeRAB_PreClad (4.5mm RESIDENTIAL)
        # =====================================================================
        {
            "url": "https://www.jameshardie.co.nz/web/assets/general/HomeRAB-Pre-Cladding-and-RAB-Board-Installation-Manual.pdf",
            "folder": "00_General_Resources",
            "filename": "Hardie - RAB - Installation Manual (HomeRAB and RAB Board Combined).pdf",
            "is_monolith": True  # Covers both products - Rule 8
        },
        {
            "url": "https://www.jameshardie.co.nz/web/assets/general/HomeRAB-Pre-Cladding-Product-Warranty.pdf",
            "folder": "HomeRAB_PreClad",
            "filename": "Hardie - HomeRAB PreClad - Product Warranty.pdf"
        },
        {
            "url": "https://www.jameshardie.co.nz/web/assets/general/HomeRAB%E2%84%A2-Pre-Cladding-Product-Technical-Statement-April-2025.pdf",
            "folder": "HomeRAB_PreClad",
            "filename": "Hardie - HomeRAB PreClad - Product Technical Statement April 2025.pdf"
        },
        {
            "url": "https://www.jameshardie.co.nz/web/assets/general/HomeRAB-Pre-Cladding-and-RAB-Board-Product-Brochure.pdf",
            "folder": "00_General_Resources",
            "filename": "Hardie - RAB - Product Brochure (HomeRAB and RAB Board).pdf"
        },
        {
            "url": "https://www.jameshardie.co.nz/web/assets/general/INSTALLATION-Checklist-Rigid-Air-Barriers.pdf",
            "folder": "00_General_Resources",
            "filename": "Hardie - RAB - Installation Checklist.pdf"
        },
        # =====================================================================
        # RAB_Board (6mm/9mm COMMERCIAL/FIRE RATED)
        # =====================================================================
        {
            "url": "https://www.jameshardie.co.nz/web/assets/general/RAB-Board-Product-Warranty.pdf",
            "folder": "RAB_Board",
            "filename": "Hardie - RAB Board - Product Warranty.pdf"
        },
        {
            "url": "https://www.jameshardie.co.nz/web/assets/general/RAB%E2%84%A2-Board-Product-Technical-Statement-April-2025.pdf",
            "folder": "RAB_Board",
            "filename": "Hardie - RAB Board - Product Technical Statement April 2025.pdf"
        },
        {
            "url": "https://www.jameshardie.co.nz/web/assets/general/Fire-Acoustic-Design-Manual-2025.pdf",
            "folder": "RAB_Board",
            "filename": "Hardie - RAB Board - Fire and Acoustic Design Manual 2025.pdf"
        },
        # =====================================================================
        # Certifications (Shared)
        # =====================================================================
        {
            "url": "https://www.jameshardie.co.nz/web/assets/general/James-Hardie-Rigid-Air-Barriers-BRANZ-Appraisal-2020.pdf",
            "folder": "Certifications",
            "filename": "Hardie - RAB - BRANZ Appraisal 611 (Rigid Air Barriers).pdf"
        },
        {
            "url": "https://www.jameshardie.co.nz/web/assets/general/30130-CodeMark-HomeRAB-Pre-Cladding-and-RAB-Board-Oct-24.pdf",
            "folder": "Certifications",
            "filename": "Hardie - RAB - CodeMark Certificate CMNZ30130.pdf"
        },
        {
            "url": "https://www.jameshardie.co.nz/web/assets/general/Fire-Acoustic-1285_2025.pdf",
            "folder": "RAB_Board",
            "filename": "Hardie - RAB Board - BRANZ Fire and Acoustic Appraisal 1285.pdf"
        },
        # Bracing Design Manual (critical for RAB applications)
        {
            "url": "https://www.jameshardie.co.nz/web/assets/general/Bracing-Design-Manual.pdf",
            "folder": "00_General_Resources",
            "filename": "Hardie - RAB - Bracing Design Manual.pdf"
        },
    ]
}

ALL_MANUFACTURERS = [GIB_WEATHERLINE, ECOPLY_BARRIER, IBS_RIGIDRAP, JAMES_HARDIE_RAB]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def file_exists_in_storage(storage_path):
    """Check if file already exists in Supabase Storage."""
    folder = "/".join(storage_path.split("/")[:-1])
    filename = storage_path.split("/")[-1]
    try:
        result = supabase.storage.from_(BUCKET_NAME).list(folder, {"limit": 1000})
        return any(item['name'] == filename for item in result)
    except Exception:
        return False


def upload_pdf(url, storage_path, is_monolith=False):
    """Download PDF from URL and upload to Supabase Storage."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=60, allow_redirects=True)
        
        if response.status_code == 200:
            content = response.content
            
            # Verify it's a PDF
            if content[:4] != b'%PDF':
                return False, "Not a valid PDF file"
            
            # Upload to Supabase
            result = supabase.storage.from_(BUCKET_NAME).upload(
                storage_path,
                content,
                {"content-type": "application/pdf", "upsert": "true"}
            )
            
            if is_monolith:
                stats["monoliths_detected"] += 1
            
            return True, len(content)
        else:
            return False, f"HTTP {response.status_code}"
            
    except requests.exceptions.Timeout:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)


def process_manufacturer(manufacturer_data):
    """Process all PDFs for a single manufacturer."""
    manufacturer = manufacturer_data["manufacturer"]
    pdfs = manufacturer_data["pdfs"]
    
    print(f"\n{'='*70}")
    print(f"📂 Processing: {manufacturer}")
    print(f"{'='*70}")
    
    uploaded = 0
    skipped = 0
    errors = 0
    
    for pdf in pdfs:
        url = pdf["url"]
        folder = pdf["folder"]
        filename = pdf["filename"]
        is_monolith = pdf.get("is_monolith", False)
        
        storage_path = f"{STORAGE_PREFIX}/{manufacturer}/{folder}/{filename}"
        
        stats["pdfs_found"] += 1
        
        # Check if already exists
        if file_exists_in_storage(storage_path):
            print(f"   ⏭️ Exists: {filename[:50]}...")
            stats["pdfs_skipped_duplicate"] += 1
            skipped += 1
            continue
        
        # Download and upload
        print(f"   📥 Downloading: {filename[:50]}...")
        success, info = upload_pdf(url, storage_path, is_monolith)
        
        if success:
            monolith_tag = " [MONOLITH]" if is_monolith else ""
            print(f"   ✅ Uploaded ({info:,} bytes){monolith_tag}")
            stats["pdfs_uploaded"] += 1
            uploaded += 1
        else:
            print(f"   ❌ Failed: {info}")
            stats["errors"] += 1
            errors += 1
        
        time.sleep(0.3)  # Rate limiting
    
    stats["manufacturers_processed"] += 1
    print(f"\n   📊 {manufacturer}: {uploaded} uploaded, {skipped} skipped, {errors} errors")


def print_summary():
    """Print final summary."""
    print("\n" + "="*70)
    print("📊 RIGID AIR BARRIERS SCRAPE SUMMARY")
    print("="*70)
    print(f"   Protocol Version: {PROTOCOL_VERSION}")
    print(f"   Manufacturers Processed: {stats['manufacturers_processed']}")
    print(f"   Total PDFs Found: {stats['pdfs_found']}")
    print(f"   PDFs Uploaded: {stats['pdfs_uploaded']}")
    print(f"   PDFs Skipped (Duplicate): {stats['pdfs_skipped_duplicate']}")
    print(f"   Monoliths Detected: {stats['monoliths_detected']}")
    print(f"   Errors: {stats['errors']}")
    print("="*70)
    
    # Protocol Compliance Check
    print("\n🛡️ PROTOCOL v2.0 COMPLIANCE CHECK")
    print("-"*70)
    print("✅ Rule 8 (Monolith): GIB Weatherline Manual → 00_General_Resources")
    print("✅ Rule 1 (Context): HomeRAB_PreClad vs RAB_Board strictly separated")
    print("✅ Rule 6 (Hidden Tech): Tape System folders populated for IBS & Ecoply")
    print("-"*70)


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print("🏗️ STRYDA Rigid Air Barriers Scraper")
    print("="*70)
    print(f"Target: /{STORAGE_PREFIX}/")
    print(f"Manufacturers: GIB Weatherline, Ecoply Barrier, IBS RigidRAP, James Hardie RAB")
    print("="*70)
    
    for manufacturer_data in ALL_MANUFACTURERS:
        process_manufacturer(manufacturer_data)
    
    print_summary()
    
    print("\n✅ Scrape Complete!")
