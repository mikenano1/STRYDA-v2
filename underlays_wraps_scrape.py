#!/usr/bin/env python3
"""
Underlays & Wraps Scraper (Thermakraft & DriStud) - Protocol v2.0
=================================================================
Downloads technical PDFs for wall/roof underlays, wraps, and tapes.

CRITICAL: Strictly separates Wall vs Roof applications to prevent compliance errors.

Uses src/ingestion_rules.py for Protocol v2.0 enforcement:
- Rule 1: Context-aware naming (no generic "Product Technical Statement.pdf")
- Rule 6: Tapes/Flashings to dedicated folders
- Rule 8: Monolith detection for master guides

Storage: /B_Enclosure/Underlays_and_Wraps/
- /Kingspan_Thermakraft/
- /DriStud/

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

STORAGE_PREFIX = "B_Enclosure/Underlays_and_Wraps"

# Stats tracking
stats = {
    "brands_processed": 0,
    "categories_processed": 0,
    "pdfs_found": 0,
    "pdfs_uploaded": 0,
    "pdfs_skipped_duplicate": 0,
    "monoliths_detected": 0,
    "errors": 0,
}

# Track uploaded files for deduplication
uploaded_urls = set()


# =============================================================================
# KINGSPAN THERMAKRAFT PRODUCTS
# =============================================================================

# WALL UNDERLAY (NOT for roof use without mesh)
THERMAKRAFT_WALL_UNDERLAY = {
    "Watergate_Plus": [
        ("Data Sheet", "https://irp.cdn-website.com/e5e43e78/files/uploaded/KINZ-TK_Watergate+Plus+Data+Sheet+v12.0.pdf"),
        ("Installation Guide", "https://irp.cdn-website.com/e5e43e78/files/uploaded/KINZ-TK_Watergate+Plus+Install+Guide+v7.0.pdf"),
        ("BRANZ Appraisal", "https://irp.cdn-website.com/e5e43e78/files/uploaded/BRANZ+WG+2025.pdf"),
    ],
    "Thermakraft_220": [
        ("Data Sheet", "https://irp.cdn-website.com/e5e43e78/files/uploaded/KINZ-TK_Thermakraft+220+Data+Sheet+v8.0.pdf"),
        ("Installation Guide", "https://irp.cdn-website.com/e5e43e78/files/uploaded/KINZ_TK+Thermakraft+220+Install+Guide+v5.0.pdf"),
        ("BRANZ Appraisal", "https://irp.cdn-website.com/e5e43e78/files/uploaded/BRANZ+220+2025.pdf"),
    ],
    "Covertek_403_Wall": [
        ("Data Sheet", "https://irp.cdn-website.com/e5e43e78/files/uploaded/KINZ-TK_Covertek+403+Data+Sheet+v8.0.pdf"),
        ("Installation Guide", "https://irp.cdn-website.com/e5e43e78/files/uploaded/KINZ-TK_Covertek+403+Install+Guide+v5.0.pdf"),
        ("BRANZ Appraisal", "https://irp.cdn-website.com/e5e43e78/files/uploaded/BRANZ+403+7-2025.pdf"),
        ("CodeMark Certificate", "https://irp.cdn-website.com/e5e43e78/files/uploaded/CodeMark+403+7-25.pdf"),
    ],
    "Covertek_401_Wall": [
        ("Data Sheet", "https://irp.cdn-website.com/e5e43e78/files/uploaded/KINZ-TK_Covertek+401+Data+Sheet+v9.0.pdf"),
        ("Installation Guide", "https://irp.cdn-website.com/e5e43e78/files/uploaded/KINZ-TK_Covertek+401+Install+Guide+v6.0.pdf"),
        ("BRANZ Appraisal", "https://irp.cdn-website.com/e5e43e78/files/uploaded/BRANZ+401+7-2025.pdf"),
    ],
    "Covertek_215_Wall": [
        ("Data Sheet", "https://irp.cdn-website.com/e5e43e78/files/uploaded/KINZ-TK_Covertek+215+Data+Sheet+v3.0.pdf"),
        ("Installation Guide", "https://irp.cdn-website.com/e5e43e78/files/uploaded/KINZ-TK_Covertek+215+Install+Guide+v3.0.pdf"),
        ("BRANZ Appraisal", "https://irp.cdn-website.com/e5e43e78/files/uploaded/BRANZ+CT215.pdf"),
    ],
    "RainArmor_SA": [
        ("Data Sheet", "https://irp.cdn-website.com/e5e43e78/files/uploaded/kinz-tk_rainarmor_sa_data_sheet_v1.0_1124_%28003%29.pdf"),
        ("Installation Guide", "https://irp.cdn-website.com/e5e43e78/files/uploaded/kinz-tk_rainarmor_sa_install_guide_v1.0_1124%28003%29.pdf"),
    ],
}

# ROOF UNDERLAY (Self-supporting or with mesh)
THERMAKRAFT_ROOF_UNDERLAY = {
    "Covertek_407": [
        ("Data Sheet", "https://irp.cdn-website.com/e5e43e78/files/uploaded/KINZ-TK_Covertek+407+Data+Sheet+v9.0.pdf"),
        ("Installation Guide", "https://irp.cdn-website.com/e5e43e78/files/uploaded/KINZ-TK_Covertek+407+Install+Guide+v5.0.pdf"),
        ("BRANZ Appraisal", "https://irp.cdn-website.com/e5e43e78/files/uploaded/BRANZ+407+2025.pdf"),
        ("CodeMark Certificate", "https://irp.cdn-website.com/e5e43e78/files/uploaded/CodeMark+407+7-25.pdf"),
    ],
    "Covertek_405": [
        ("Data Sheet", "https://irp.cdn-website.com/e5e43e78/files/uploaded/KINZ-TK_Covertek+405+Data+Sheet+v8.0.pdf"),
        ("Installation Guide", "https://irp.cdn-website.com/e5e43e78/files/uploaded/KINZ-TK_Covertek+405+Install+Guide+v5.0.pdf"),
        ("BRANZ Appraisal", "https://irp.cdn-website.com/e5e43e78/files/uploaded/BRANZ+405+2024.pdf"),
        ("CodeMark Certificate", "https://irp.cdn-website.com/e5e43e78/files/uploaded/CodeMark+405+7-25.pdf"),
    ],
    "Covertek_403_Roof": [
        ("Data Sheet", "https://irp.cdn-website.com/e5e43e78/files/uploaded/KINZ-TK_Covertek+403+Data+Sheet+v8.0.pdf"),
        ("Installation Guide", "https://irp.cdn-website.com/e5e43e78/files/uploaded/KINZ-TK_Covertek+403+Install+Guide+v5.0.pdf"),
        ("BRANZ Appraisal", "https://irp.cdn-website.com/e5e43e78/files/uploaded/Covertek_403_917_2020_-_A1.pdf"),
        ("CodeMark Certificate", "https://irp.cdn-website.com/e5e43e78/files/uploaded/CodeMark+403+7-25-b96e6258.pdf"),
    ],
    "Covertek_401_Roof": [
        ("Data Sheet", "https://irp.cdn-website.com/e5e43e78/files/uploaded/KINZ-TK_Covertek+401+Data+Sheet+v9.0.pdf"),
        ("Installation Guide", "https://irp.cdn-website.com/e5e43e78/files/uploaded/KINZ-TK_Covertek+401+Install+Guide+v6.0.pdf"),
    ],
    "Vapour_Shield": [
        ("Data Sheet", "https://irp.cdn-website.com/e5e43e78/files/uploaded/KINZ-TK_Vapour+Shield+Data+Sheet.pdf"),
    ],
}

# FOILS AND MESH
THERMAKRAFT_FOILS_MESH = {
    "Thermabar_397": [
        ("Data Sheet", "https://irp.cdn-website.com/e5e43e78/files/uploaded/KINZ-TK_Thermabar+397+Data+Sheet+v9.0.pdf"),
        ("Installation Guide", "https://irp.cdn-website.com/e5e43e78/files/uploaded/KINZ-TK_Thermabar+397+Install+Guide+v5.0.pdf"),
        ("BRANZ Appraisal", "https://irp.cdn-website.com/e5e43e78/files/uploaded/BRANZ+TB397+2025.pdf"),
    ],
    "Thermabar_344": [
        ("Data Sheet", "https://irp.cdn-website.com/e5e43e78/files/uploaded/KINZ-TK_Thermabar+344+Data+Sheet+v5.0.pdf"),
        ("Installation Guide", "https://irp.cdn-website.com/e5e43e78/files/uploaded/KINZ-TK_Thermabar+344+Install+Guide+v4.0.pdf"),
    ],
}

# TAPES AND FLASHINGS (Critical for weathertightness - Rule 6)
THERMAKRAFT_TAPES_FLASHINGS = {
    "Thermaflash": [
        ("Data Sheet", "https://irp.cdn-website.com/e5e43e78/files/uploaded/KINZ-TK_Thermaflash+Data+Sheet.pdf"),
        ("BRANZ Appraisal", "https://irp.cdn-website.com/e5e43e78/files/uploaded/Thermaflash_1122_2020_-_A1.pdf"),
    ],
    "Aluband_Window_Flashing_Tape": [
        ("Data Sheet", "https://irp.cdn-website.com/e5e43e78/files/uploaded/KINZ-TK_Aluband+Data+Sheet.pdf"),
        ("BRANZ Appraisal", "https://irp.cdn-website.com/e5e43e78/files/uploaded/Aluband_878_2024.pdf"),
    ],
    "OneSeal_Penetration_Seals": [
        ("BRANZ Appraisal", "https://irp.cdn-website.com/e5e43e78/files/uploaded/Oneseal_Multifit_Pipe_and_Cable_Penetration_Seals_942_2022_-_A1.pdf"),
    ],
}

# BITUMINOUS PAPERS
THERMAKRAFT_BITUMINOUS = {
    "Thermakraft_215_Bitumen": [
        ("Data Sheet", "https://irp.cdn-website.com/e5e43e78/files/uploaded/KINZ-TK_Thermakraft+215+Bitumen+Data+Sheet.pdf"),
    ],
    "Thermakraft_213_Bitumen": [
        ("Data Sheet", "https://irp.cdn-website.com/e5e43e78/files/uploaded/KINZ-TK_Thermakraft+213+Bitumen+Data+Sheet.pdf"),
    ],
}

# DAMP PROOF MEMBRANES
THERMAKRAFT_DPM = {
    "Thermathene_Black_250": [
        ("Data Sheet", "https://irp.cdn-website.com/e5e43e78/files/uploaded/KINZ-TK_Thermathene+Black+Data+Sheet.pdf"),
    ],
    "Thermathene_Orange_300": [
        ("Data Sheet", "https://irp.cdn-website.com/e5e43e78/files/uploaded/KINZ-TK_Thermathene+Orange+Data+Sheet.pdf"),
        ("BRANZ Appraisal", "https://irp.cdn-website.com/e5e43e78/files/uploaded/Thermathene_Orange_1104_2020_-_A1-09cd4da3.pdf"),
    ],
    "Supercourse_500_DPC": [
        ("Data Sheet", "https://irp.cdn-website.com/e5e43e78/files/uploaded/KINZ-TK_Supercourse+500+Data+Sheet.pdf"),
    ],
}


# =============================================================================
# DRISTUD PRODUCTS
# =============================================================================

# WALL WRAP
DRISTUD_WALL = {
    "DriStud_Wall_Wrap": [
        ("Installation Guide", "https://www.drispace.co.nz/download/93/dristud-wall-wrap/3963/dristud-wall-wrap-install-guide.pdf"),
        ("CodeMark Certificate", "https://www.drispace.co.nz/download/72/all-documents/3021/codemark-certificate-dristud-wall-wrap-2.pdf"),
    ],
    "DriStud_EcoWall_Wrap": [
        ("Installation Guide", "https://www.drispace.co.nz/download/234/dristud-ecowall-wrap/7412/dristud-ecowall-wrap-install-guide.pdf"),
    ],
    "DriStud_Repel": [
        ("Installation Guide", "https://www.drispace.co.nz/download/133/dristud-repel/5616/dristud-repel-install-guide.pdf"),
        ("CodeMark Certificate", "https://www.drispace.co.nz/download/72/all-documents/5563/codemark-certificate-dristud-repel.pdf"),
    ],
}

# ROOF UNDERLAY
DRISTUD_ROOF = {
    "DriStud_FRU38_Underlay": [
        ("Installation Guide", "https://www.drispace.co.nz/download/74/dristud-roof/7067/dristud-fru38-install-guide.pdf"),
        ("CodeMark Certificate", "https://www.drispace.co.nz/download/101/dristud-fru36-roof-underlay/3416/codemark-certificate-ecodri-fr-ru22-ru24-fru36-fru38-roof-underlay.pdf"),
    ],
    "DriStud_FRU36_Underlay": [
        ("Installation Guide", "https://www.drispace.co.nz/download/72/all-documents/7068/dristud-fru36-install-guide.pdf"),
        ("CodeMark Certificate", "https://www.drispace.co.nz/download/101/dristud-fru36-roof-underlay/3416/codemark-certificate-ecodri-fr-ru22-ru24-fru36-fru38-roof-underlay.pdf"),
    ],
    "DriStud_RU24_Underlay": [
        ("Installation Guide", "https://www.drispace.co.nz/download/74/dristud-roof/7066/dristud-ru24-install-guide.pdf"),
    ],
    "DriStud_RU22_Underlay": [
        ("Installation Guide", "https://www.drispace.co.nz/download/157/dristud-ru22-roof-underlay/7219/dristud-ru22-install-guide.pdf"),
    ],
    "DriStud_EcoDri_FR_Underlay": [
        ("Installation Guide", "https://www.drispace.co.nz/download/230/dristud-ecodri-fr/7227/dristud-ecodri-fr-install-guide.pdf"),
    ],
}

# TAPES
DRISTUD_TAPES = {
    "DriStud_Cool_Window_Flashing_Tape": [
        ("Installation Guide Flexible", "https://www.drispace.co.nz/download/97/dristud-cool-window-flashing-tape/4345/dristud-cool-tape-flexible-wall-wrap-install-guide.pdf"),
        ("Installation Guide Rigid", "https://www.drispace.co.nz/download/97/dristud-cool-window-flashing-tape/3017/dristud-cool-tape-rigid-air-barrier-install-guide.pdf"),
        ("CodeMark Certificate", "https://www.drispace.co.nz/download/72/all-documents/3018/codemark-certificate-dristud-cool-window-flashing-tape-2.pdf"),
    ],
}

# FOILS
DRISTUD_FOILS = {
    "DriStud_W11_White_Faced_Foil": [
        ("CodeMark Certificate", "https://www.drispace.co.nz/download/72/all-documents/3075/codemark-certificate-dristud-w11-white-faced-foil.pdf"),
    ],
}

# PROCTORPASSIVE (Airtight membranes)
DRISTUD_PROCTORPASSIVE = {
    "Wraptite_SA": [
        ("System Guide", "https://www.drispace.co.nz/download/72/all-documents/6113/wraptite-sa-uv-sa-system-guide-2024.pdf"),
        ("CodeMark Certificate", "https://www.drispace.co.nz/download/72/all-documents/5793/codemark-certificate-proctorpassive-wraptite-sa.pdf"),
    ],
    "Wraptite_UV_SA": [
        ("System Guide", "https://www.drispace.co.nz/download/72/all-documents/6113/wraptite-sa-uv-sa-system-guide-2024.pdf"),
        ("CodeMark Certificate", "https://www.drispace.co.nz/download/72/all-documents/5794/codemark-certificate-proctorpassive-wraptite-uv-sa.pdf"),
    ],
    "SmartVap": [
        ("Product Technical Statement", "https://www.drispace.co.nz/download/178/private-docs/3440/proctorpassive-smartvap-product-technical-statement.pdf"),
    ],
    "GeoVap_120": [
        ("Product Technical Statement", "https://www.drispace.co.nz/download/72/all-documents/3438/proctorpassive-geovap-120-product-technical-statement.pdf"),
    ],
    "DriFlash_Tape": [
        ("Product Technical Statement", "https://www.drispace.co.nz/download/72/all-documents/5639/proctorpassive-driflash-product-technical-statement.pdf"),
    ],
}

# VENT PRODUCTS (Passive ventilation)
DRISTUD_VENT = {
    "RV10P_Ridge_Vent": [
        ("Product Technical Statement", "https://www.drispace.co.nz/download/72/all-documents/3934/vent-rv10p-product-technical-statement.pdf"),
        ("BRANZ Appraisal", "https://www.drispace.co.nz/download/72/all-documents/4454/vent-rv10-branz-appraisal-979.pdf"),
    ],
    "VB20_Roof_Vented_Batten": [
        ("Product Technical Statement", "https://www.drispace.co.nz/download/72/all-documents/3936/vent-vb20-roof-product-technical-statement.pdf"),
        ("BRANZ Appraisal", "https://www.drispace.co.nz/download/72/all-documents/4674/vent-vb20-roof-branz-appraisal-979.pdf"),
    ],
    "VB20_Wall_Vented_Batten": [
        ("Product Technical Statement", "https://www.drispace.co.nz/download/72/all-documents/3932/vent-vb20-wall-product-technical-statement.pdf"),
        ("BRANZ Appraisal", "https://www.drispace.co.nz/download/72/all-documents/3098/vent-vb20-wall-branz-appraisal-1099.pdf"),
    ],
    "G1200N_Over_Fascia_Vent": [
        ("Product Technical Statement", "https://www.drispace.co.nz/download/112/g1200n-over-fascia-vent/4428/vent-g1200n-product-technical-statement-2.pdf"),
    ],
}

# DESIGN GUIDES (Rule 8 - Monoliths to General Resources)
DRISTUD_GENERAL = [
    ("DriSpace Product Range Guide 2025", "https://www.drispace.co.nz/wp-content/uploads/2026/01/Product-Range-2025.pdf"),
    ("Moisture Management Design Guide", "https://www.drispace.co.nz/wp-content/uploads/2025/08/Moisture-Management-Design-Guide-250825.pdf"),
    ("Wraptite SA Systems Guide", "https://www.drispace.co.nz/wp-content/uploads/2025/11/Wraptite-SA-System-Guide-FINAL.pdf"),
    ("Underlay and Foil Applications Guide", "https://www.drispace.co.nz/wp-content/uploads/2025/11/DriSpace-Underlay-and-Foil-Applications-Final-Nov25.pdf"),
    ("Education Systems Condensation Guide", "https://www.drispace.co.nz/wp-content/uploads/2025/09/DriSpace-Education-Systems-2024.pdf"),
]


def upload_to_supabase(pdf_url: str, storage_path: str, doc_title: str) -> bool:
    """Download PDF and upload to Supabase storage."""
    try:
        print(f"    📥 Downloading: {doc_title[:45]}...")
        response = requests.get(pdf_url, timeout=60, allow_redirects=True)
        if response.status_code != 200:
            print(f"    ❌ Failed to download (HTTP {response.status_code})")
            stats["errors"] += 1
            return False
        
        pdf_content = response.content
        
        # Verify PDF
        if not pdf_content[:4] == b'%PDF':
            print(f"    ⚠️ Not a valid PDF file")
            stats["errors"] += 1
            return False
        
        # Rule 8: Check for monolith (>20MB)
        file_size_mb = len(pdf_content) / (1024 * 1024)
        if is_potential_monolith(file_size_mb=file_size_mb):
            stats["monoliths_detected"] += 1
            print(f"    ⚠️ Rule 8: Monolith detected ({file_size_mb:.1f}MB)")
        
        # Upload
        try:
            supabase.storage.from_(BUCKET_NAME).upload(
                storage_path,
                pdf_content,
                {"content-type": "application/pdf"}
            )
            print(f"    ✅ Uploaded: {storage_path.split('/')[-1][:50]}...")
            return True
        except Exception as e:
            if "Duplicate" in str(e) or "already exists" in str(e).lower():
                print(f"    ⏭️ Already exists")
                stats["pdfs_skipped_duplicate"] += 1
                return False
            else:
                print(f"    ❌ Upload error: {e}")
                stats["errors"] += 1
                return False
                
    except Exception as e:
        print(f"    ❌ Error: {e}")
        stats["errors"] += 1
        return False


def process_products(brand: str, category: str, folder: str, products: dict):
    """Process all products in a category."""
    print(f"\n  📁 {category}")
    stats["categories_processed"] += 1
    
    for product_name, docs in products.items():
        clean_product = product_name.replace('_', ' ')
        
        for doc_title, pdf_url in docs:
            stats["pdfs_found"] += 1
            
            # Skip if URL already processed
            if pdf_url in uploaded_urls:
                stats["pdfs_skipped_duplicate"] += 1
                continue
            
            # Rule 1: Context-aware naming
            # Format: "[Brand] - [Product] - [Document Type].pdf"
            clean_title = sanitize_filename(doc_title)
            filename = f"{brand} - {clean_product} - {clean_title}.pdf"
            storage_path = f"{STORAGE_PREFIX}/{folder}/{filename}"
            
            if upload_to_supabase(pdf_url, storage_path, doc_title):
                stats["pdfs_uploaded"] += 1
                uploaded_urls.add(pdf_url)
            
            time.sleep(0.2)


def process_general_resources(brand: str, folder: str, docs: list):
    """Process general/monolith resources (Rule 8)."""
    print(f"\n  📁 00_General_Resources (Rule 8 - Monoliths)")
    
    for doc_title, pdf_url in docs:
        stats["pdfs_found"] += 1
        
        if pdf_url in uploaded_urls:
            stats["pdfs_skipped_duplicate"] += 1
            continue
        
        clean_title = sanitize_filename(doc_title)
        filename = f"{brand} - Master - {clean_title}.pdf"
        storage_path = f"{STORAGE_PREFIX}/{folder}/00_General_Resources/{filename}"
        
        if upload_to_supabase(pdf_url, storage_path, doc_title):
            stats["pdfs_uploaded"] += 1
            uploaded_urls.add(pdf_url)
        
        time.sleep(0.2)


def main():
    """Main scraping function."""
    print("=" * 70)
    print(f"🏠 UNDERLAYS & WRAPS SCRAPER (Protocol v{PROTOCOL_VERSION})")
    print("=" * 70)
    
    print_protocol_summary()
    
    print(f"\nStorage: {BUCKET_NAME}/{STORAGE_PREFIX}")
    print("\n⚠️  CRITICAL: Wall vs Roof separation enforced!")
    print("=" * 70)
    
    # ==========================================================================
    # KINGSPAN THERMAKRAFT
    # ==========================================================================
    print("\n" + "=" * 60)
    print("🏭 KINGSPAN THERMAKRAFT")
    print("=" * 60)
    stats["brands_processed"] += 1
    
    process_products("Thermakraft", "Wall Underlay", 
                    "Kingspan_Thermakraft/Wall_Underlay", THERMAKRAFT_WALL_UNDERLAY)
    
    process_products("Thermakraft", "Roof Underlay",
                    "Kingspan_Thermakraft/Roof_Underlay", THERMAKRAFT_ROOF_UNDERLAY)
    
    process_products("Thermakraft", "Foils and Mesh",
                    "Kingspan_Thermakraft/Foils_and_Mesh", THERMAKRAFT_FOILS_MESH)
    
    process_products("Thermakraft", "Tapes and Flashings (Rule 6 - CRITICAL)",
                    "Kingspan_Thermakraft/Tapes_and_Flashings", THERMAKRAFT_TAPES_FLASHINGS)
    
    process_products("Thermakraft", "Bituminous Papers",
                    "Kingspan_Thermakraft/Bituminous_Papers", THERMAKRAFT_BITUMINOUS)
    
    process_products("Thermakraft", "Damp Proof Membranes",
                    "Kingspan_Thermakraft/Damp_Proof_Membranes", THERMAKRAFT_DPM)
    
    # ==========================================================================
    # DRISTUD / DRISPACE
    # ==========================================================================
    print("\n" + "=" * 60)
    print("🏭 DRISTUD / DRISPACE")
    print("=" * 60)
    stats["brands_processed"] += 1
    
    process_products("DriStud", "Wall Wrap",
                    "DriStud/Wall_Wrap", DRISTUD_WALL)
    
    process_products("DriStud", "Roof Underlay",
                    "DriStud/Roof_Underlay", DRISTUD_ROOF)
    
    process_products("DriStud", "Tapes (Rule 6 - CRITICAL)",
                    "DriStud/Tapes", DRISTUD_TAPES)
    
    process_products("DriStud", "Foils",
                    "DriStud/Foils", DRISTUD_FOILS)
    
    process_products("ProctorPassive", "Airtight Membranes",
                    "DriStud/ProctorPassive", DRISTUD_PROCTORPASSIVE)
    
    process_products("VENT", "Passive Ventilation",
                    "DriStud/VENT", DRISTUD_VENT)
    
    # General resources (Rule 8 - Monoliths)
    process_general_resources("DriSpace", "DriStud", DRISTUD_GENERAL)
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 SCRAPING SUMMARY")
    print("=" * 70)
    print(f"Protocol Version:           v{PROTOCOL_VERSION}")
    print(f"Brands processed:           {stats['brands_processed']}")
    print(f"Categories processed:       {stats['categories_processed']}")
    print(f"PDFs found:                 {stats['pdfs_found']}")
    print(f"PDFs uploaded:              {stats['pdfs_uploaded']}")
    print(f"PDFs skipped (duplicate):   {stats['pdfs_skipped_duplicate']}")
    print(f"Monoliths detected (Rule 8): {stats['monoliths_detected']}")
    print(f"Errors:                     {stats['errors']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
