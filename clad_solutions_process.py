#!/usr/bin/env python3
"""
CLAD Solutions - Full Product Library Processor
================================================
STRYDA Master Protocol v2.0 Compliant

Brands/Products Identified:
- PXR System (Parklex Prodema Cavity Rail System) - CAD details & technical docs
- Parklex Prodema - Exterior timber/composite cladding
- Shera Board - Fibre cement weatherboard system
- SW System - Additional cladding details

Folder Structure:
B_Enclosure/Wall_Cladding/CLAD_Solutions/
├── 00_General_Resources/           ← Universal docs, EPDs, catalogues
├── PXR_Cavity_System/
│   ├── Technical_Manuals/          ← Main manuals & appraisals
│   ├── CAD_Details/                ← All PXR-X-XX detail drawings
│   └── Forms_Templates/            ← QA forms, order lists
├── Parklex_Prodema/                ← Timber composite exterior
└── Shera_Weatherboard/
    ├── Technical_Data/             ← TDS, BPIR docs
    ├── BRANZ_Appraisals/           ← Appraisal documents
    └── CAD_Details/                ← Shera-specific details
"""

import os
import sys
import time
import requests
import hashlib

sys.path.insert(0, '/app/backend-minimal')

from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

from supabase import create_client

# Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
BUCKET_SOURCE = 'temporary'
BUCKET_DEST = 'product-library'
BASE_PATH = 'B_Enclosure/Wall_Cladding/CLAD_Solutions'

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================================
# FILE MAPPING: Original filename -> (New filename, Folder)
# ============================================================

FILE_MAPPING = {
    # ==========================================
    # PXR CAVITY SYSTEM - TECHNICAL MANUALS
    # ==========================================
    "PXR-Residential-Cavity-Rail-System-1-Technical-Manual-2023Jul.pdf": (
        "CLAD Solutions - PXR System - Technical Manual Jul 2023.pdf",
        "PXR_Cavity_System/Technical_Manuals"
    ),
    "PXR-Residential-Cavity-Rail-System-2-Appraisal_1_1252_2023.pdf": (
        "CLAD Solutions - PXR System - BRANZ Appraisal 1252-2023.pdf",
        "PXR_Cavity_System/Technical_Manuals"
    ),
    "04 PXR System BPIS 311023.pdf": (
        "CLAD Solutions - PXR System - BPIR Oct 2023.pdf",
        "PXR_Cavity_System/Technical_Manuals"
    ),
    "PXR-4-Maintenance-2023Jul.pdf": (
        "CLAD Solutions - PXR System - Maintenance Guide Jul 2023.pdf",
        "PXR_Cavity_System/Technical_Manuals"
    ),
    
    # PXR OVERVIEW & 3D
    "PXR-0-3D-Overview.pdf": (
        "CLAD Solutions - PXR System - 3D Overview.pdf",
        "PXR_Cavity_System/Technical_Manuals"
    ),
    
    # PXR FORMS & TEMPLATES
    "PXR-3-QA-2023Jul Fillable.pdf": (
        "CLAD Solutions - PXR System - QA Checklist Form Jul 2023.pdf",
        "PXR_Cavity_System/Forms_Templates"
    ),
    "PXR-5-Order-List-2023Jul Fillable.pdf": (
        "CLAD Solutions - PXR System - Order List Form Jul 2023.pdf",
        "PXR_Cavity_System/Forms_Templates"
    ),
    
    # ==========================================
    # PXR CAD DETAILS - SECTION 1 (Foundation/Base)
    # ==========================================
    "PXR-1-01.pdf": ("CLAD Solutions - PXR Detail 1-01 - Base Detail.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-1-02.pdf": ("CLAD Solutions - PXR Detail 1-02 - Base Detail.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-1-03.pdf": ("CLAD Solutions - PXR Detail 1-03 - Base Detail.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-1-04.pdf": ("CLAD Solutions - PXR Detail 1-04 - Base Detail.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-1-06-FF.pdf": ("CLAD Solutions - PXR Detail 1-06-FF - Base Face Fixed.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-1-06-SM.pdf": ("CLAD Solutions - PXR Detail 1-06-SM - Base Secret Mount.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-1-11-AF.pdf": ("CLAD Solutions - PXR Detail 1-11-AF - Base Aluminium Frame.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-1-11-HY.pdf": ("CLAD Solutions - PXR Detail 1-11-HY - Base Hybrid.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-1-12-AF.pdf": ("CLAD Solutions - PXR Detail 1-12-AF - Base Aluminium Frame.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-1-12-HY.pdf": ("CLAD Solutions - PXR Detail 1-12-HY - Base Hybrid.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-1-13-HY.pdf": ("CLAD Solutions - PXR Detail 1-13-HY - Base Hybrid.pdf", "PXR_Cavity_System/CAD_Details"),
    
    # PXR CAD DETAILS - SECTION 2 (Junctions)
    "PXR-2-11-AF.pdf": ("CLAD Solutions - PXR Detail 2-11-AF - Junction Aluminium Frame.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-2-15.pdf": ("CLAD Solutions - PXR Detail 2-15 - Junction.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-2-21-HY.pdf": ("CLAD Solutions - PXR Detail 2-21-HY - Junction Hybrid.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-2-25.pdf": ("CLAD Solutions - PXR Detail 2-25 - Junction.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-2-31.pdf": ("CLAD Solutions - PXR Detail 2-31 - Junction.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-2-32.pdf": ("CLAD Solutions - PXR Detail 2-32 - Junction.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-2-35.pdf": ("CLAD Solutions - PXR Detail 2-35 - Junction.pdf", "PXR_Cavity_System/CAD_Details"),
    
    # PXR CAD DETAILS - SECTION 3 (Windows/Openings)
    "PXR-3-01.pdf": ("CLAD Solutions - PXR Detail 3-01 - Window Head.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-3-02.pdf": ("CLAD Solutions - PXR Detail 3-02 - Window Jamb.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-3-11.pdf": ("CLAD Solutions - PXR Detail 3-11 - Window.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-3-12.pdf": ("CLAD Solutions - PXR Detail 3-12 - Window.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-3-14-FA.pdf": ("CLAD Solutions - PXR Detail 3-14-FA - Window Flush Abutment.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-3-21-C.pdf": ("CLAD Solutions - PXR Detail 3-21-C - Window Corner.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-3-21-T.pdf": ("CLAD Solutions - PXR Detail 3-21-T - Window Tee.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-3-21-T-3D.pdf": ("CLAD Solutions - PXR Detail 3-21-T-3D - Window Tee 3D.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-3-23-NS.pdf": ("CLAD Solutions - PXR Detail 3-23-NS - Window No Sill.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-3-31.pdf": ("CLAD Solutions - PXR Detail 3-31 - Opening.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-3-32.pdf": ("CLAD Solutions - PXR Detail 3-32 - Opening.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-3-35.pdf": ("CLAD Solutions - PXR Detail 3-35 - Opening.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-3-51.pdf": ("CLAD Solutions - PXR Detail 3-51 - Penetration.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-3-52.pdf": ("CLAD Solutions - PXR Detail 3-52 - Penetration.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-3-54.pdf": ("CLAD Solutions - PXR Detail 3-54 - Penetration.pdf", "PXR_Cavity_System/CAD_Details"),
    
    # PXR CAD DETAILS - SECTION 4 (Face Fixed & Secret Mount Variations)
    "PXR-4-01-FF.pdf": ("CLAD Solutions - PXR Detail 4-01-FF - Panel Face Fixed.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-4-01-SM.pdf": ("CLAD Solutions - PXR Detail 4-01-SM - Panel Secret Mount.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-4-02-FF.pdf": ("CLAD Solutions - PXR Detail 4-02-FF - Panel Face Fixed.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-4-02-SM.pdf": ("CLAD Solutions - PXR Detail 4-02-SM - Panel Secret Mount.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-4-03-FF.pdf": ("CLAD Solutions - PXR Detail 4-03-FF - Panel Face Fixed.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-4-03-SM.pdf": ("CLAD Solutions - PXR Detail 4-03-SM - Panel Secret Mount.pdf", "PXR_Cavity_System/CAD_Details"),
    
    # PXR CAD DETAILS - SECTION 4-05 (Multiple Joint Types)
    "PXR-4-05-FF-A-2-SJ.pdf": ("CLAD Solutions - PXR Detail 4-05-FF-A2 - Soft Joint.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-4-05-FF-A-4-HJ.pdf": ("CLAD Solutions - PXR Detail 4-05-FF-A4 - Hard Joint.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-4-05-FF-B-1-MS.pdf": ("CLAD Solutions - PXR Detail 4-05-FF-B1 - Metal Strip.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-4-05-FF-B-2-SJ.pdf": ("CLAD Solutions - PXR Detail 4-05-FF-B2 - Soft Joint.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-4-05-FF-B-3-MJ.pdf": ("CLAD Solutions - PXR Detail 4-05-FF-B3 - Metal Joint.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-4-05-FF-B-4-HJ.pdf": ("CLAD Solutions - PXR Detail 4-05-FF-B4 - Hard Joint.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-4-05-FF-B-5-MH.pdf": ("CLAD Solutions - PXR Detail 4-05-FF-B5 - Metal Hybrid.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-4-05-FF-C-2-SJ.pdf": ("CLAD Solutions - PXR Detail 4-05-FF-C2 - Soft Joint.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-4-05-FF-C-4-HJ.pdf": ("CLAD Solutions - PXR Detail 4-05-FF-C4 - Hard Joint.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-4-05-FF-C-4-HJ-2.pdf": ("CLAD Solutions - PXR Detail 4-05-FF-C4-2 - Hard Joint Alt.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-4-05-SM-A-2-SJ.pdf": ("CLAD Solutions - PXR Detail 4-05-SM-A2 - Soft Joint.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-4-05-SM-A-4-HJ.pdf": ("CLAD Solutions - PXR Detail 4-05-SM-A4 - Hard Joint.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-4-05-SM-B-1-MS.pdf": ("CLAD Solutions - PXR Detail 4-05-SM-B1 - Metal Strip.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-4-05-SM-B-2-SJ.pdf": ("CLAD Solutions - PXR Detail 4-05-SM-B2 - Soft Joint.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-4-05-SM-B-3-MJ.pdf": ("CLAD Solutions - PXR Detail 4-05-SM-B3 - Metal Joint.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-4-05-SM-B-4-HJ.pdf": ("CLAD Solutions - PXR Detail 4-05-SM-B4 - Hard Joint.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-4-05-SM-B-5-MH.pdf": ("CLAD Solutions - PXR Detail 4-05-SM-B5 - Metal Hybrid.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-4-05-SM-C-2-SJ.pdf": ("CLAD Solutions - PXR Detail 4-05-SM-C2 - Soft Joint.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-4-05-SM-C-4-HJ.pdf": ("CLAD Solutions - PXR Detail 4-05-SM-C4 - Hard Joint.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-4-05-SM-C-4-HJ-2.pdf": ("CLAD Solutions - PXR Detail 4-05-SM-C4-2 - Hard Joint Alt.pdf", "PXR_Cavity_System/CAD_Details"),
    
    # PXR CAD DETAILS - SECTION 6 (Corners/Edges)
    "PXR-6-01-AF.pdf": ("CLAD Solutions - PXR Detail 6-01-AF - Corner Aluminium Frame.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-6-11.pdf": ("CLAD Solutions - PXR Detail 6-11 - Corner.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-6-12-AF.pdf": ("CLAD Solutions - PXR Detail 6-12-AF - Corner Aluminium Frame.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-6-13-AF.pdf": ("CLAD Solutions - PXR Detail 6-13-AF - Corner Aluminium Frame.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-6-15-AF.pdf": ("CLAD Solutions - PXR Detail 6-15-AF - Corner Aluminium Frame.pdf", "PXR_Cavity_System/CAD_Details"),
    
    # PXR CAD DETAILS - SECTION 7 (Flashings)
    "PXR-7-01.pdf": ("CLAD Solutions - PXR Detail 7-01 - Flashing.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-7-02.pdf": ("CLAD Solutions - PXR Detail 7-02 - Flashing.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-7-03-AF.pdf": ("CLAD Solutions - PXR Detail 7-03-AF - Flashing Aluminium Frame.pdf", "PXR_Cavity_System/CAD_Details"),
    
    # PXR CAD DETAILS - SECTION 8 (Soffits/Eaves)
    "PXR-8-01.pdf": ("CLAD Solutions - PXR Detail 8-01 - Soffit Eave.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-8-02.pdf": ("CLAD Solutions - PXR Detail 8-02 - Soffit Eave.pdf", "PXR_Cavity_System/CAD_Details"),
    "PXR-8-04.pdf": ("CLAD Solutions - PXR Detail 8-04 - Soffit Eave.pdf", "PXR_Cavity_System/CAD_Details"),
    
    # ==========================================
    # PARKLEX PRODEMA
    # ==========================================
    "Parklex Prodema - Exterior - Product Catalogue.pdf": (
        "CLAD Solutions - Parklex Prodema - Product Catalogue.pdf",
        "Parklex_Prodema"
    ),
    "Parklex Prodema - PXR Cavity System - BRANZ Appraisal.pdf": (
        "CLAD Solutions - Parklex Prodema - BRANZ Appraisal.pdf",
        "Parklex_Prodema"
    ),
    "Parklex Prodema - PXR Cavity System - BRANZ Appraisal (1).pdf": (
        None,  # Duplicate
        None
    ),
    "PARKLEX-PRODEMA-Tech.-Guide-cladding-soffit-siding-1.pdf": (
        "CLAD Solutions - Parklex Prodema - Technical Guide Cladding Soffit Siding.pdf",
        "Parklex_Prodema"
    ),
    "PARKLEX-PRODEMA-Tech.-Guide-cladding-soffit-siding-1 (1).pdf": (
        None,  # Duplicate
        None
    ),
    "EPD-Large-size fibre cement panels, pigmented coated (5).pdf": (
        "CLAD Solutions - Parklex Prodema - EPD Environmental Product Declaration.pdf",
        "Parklex_Prodema"
    ),
    
    # ==========================================
    # SHERA WEATHERBOARD SYSTEM
    # ==========================================
    # Hash files identified by content
    "40fca4_060a7d5dc00f44c99b03e7e8cace290b.pdf": (
        "CLAD Solutions - Shera Board - Technical Data Sheet Jan 2024.pdf",
        "Shera_Weatherboard/Technical_Data"
    ),
    "40fca4_10f318c18e5f41ff8172f979896eeb9c.pdf": (
        "CLAD Solutions - Shera Shiplap Horizontal - BRANZ Appraisal.pdf",
        "Shera_Weatherboard/BRANZ_Appraisals"
    ),
    "40fca4_1a3a16ecdf0142f0a6fec70734f05dc1.pdf": (
        "CLAD Solutions - Shera Shiplap Vertical - BRANZ Appraisal.pdf",
        "Shera_Weatherboard/BRANZ_Appraisals"
    ),
    "40fca4_3dea4ec7e3b9409381dfba8b14c27cd2.pdf": (
        "CLAD Solutions - Shera Weatherboard - BRANZ Appraisal.pdf",
        "Shera_Weatherboard/BRANZ_Appraisals"
    ),
    "40fca4_52a8d705e22f498b95c62886333caf8a.pdf": (
        "CLAD Solutions - Shera Detail CSTEGS30v - CAD Drawing Jun 2025.pdf",
        "Shera_Weatherboard/CAD_Details"
    ),
    "40fca4_6d0ed69fc0474072828d1943f9264201.pdf": (
        "CLAD Solutions - Shera Bevelback - Technical Manual Feb 2025.pdf",
        "Shera_Weatherboard/Technical_Data"
    ),
    "40fca4_7f172d421a534669995c5b8bdf9ff3bc.pdf": (
        "CLAD Solutions - Shera Detail CSTEGW30 - CAD Drawing Jun 2025.pdf",
        "Shera_Weatherboard/CAD_Details"
    ),
    "40fca4_801a9819d26a4efe8c3d71941044324a.pdf": (
        "CLAD Solutions - Shera Shiplap Vertical - BRANZ Appraisal v2.pdf",
        "Shera_Weatherboard/BRANZ_Appraisals"
    ),
    "40fca4_843d6cc548b24528b8d98f9385a34a13.pdf": (
        "CLAD Solutions - Shera Shiplap Vertical - BPIR Oct 2023.pdf",
        "Shera_Weatherboard/Technical_Data"
    ),
    "40fca4_90447c3bb6804cb591b16c214b5e5c96.pdf": (
        "CLAD Solutions - Shera Shiplap Vertical - Technical Manual.pdf",
        "Shera_Weatherboard/Technical_Data"
    ),
    "40fca4_95814c1bc4484fa8b8fb04a360b652b3.pdf": (
        "CLAD Solutions - Shera Detail CSTESS30v - CAD Drawing Jan 2025.pdf",
        "Shera_Weatherboard/CAD_Details"
    ),
    "40fca4_ade2ae542ad74653aaca76ed3c79bf1b.pdf": (
        "CLAD Solutions - Shera 40mm Structural Cavity Batten - Technical Data.pdf",
        "Shera_Weatherboard/Technical_Data"
    ),
    "40fca4_b1e658027c8e4898a95ab931624cb294.pdf": (
        "CLAD Solutions - Shera Weatherboard - BPIR Oct 2023.pdf",
        "Shera_Weatherboard/Technical_Data"
    ),
    
    # ==========================================
    # SW SYSTEM (Additional cladding details)
    # ==========================================
    "_SW-08 Detail List 2025Feb.pdf": (
        "CLAD Solutions - SW System - Detail List Feb 2025.pdf",
        "00_General_Resources"
    ),
    "_SW-08 Detail List 2025Feb (1).pdf": (
        None,  # Duplicate
        None
    ),
    "_SW-3D-Overview.pdf": (
        "CLAD Solutions - SW System - 3D Overview.pdf",
        "00_General_Resources"
    ),
    "_SW-3D-Overview (1).pdf": (
        None,  # Duplicate
        None
    ),
}


def download_from_temp(filename):
    """Download file from temporary bucket"""
    try:
        signed = supabase.storage.from_(BUCKET_SOURCE).create_signed_url(filename, 120)
        if signed and signed.get('signedURL'):
            response = requests.get(signed['signedURL'], timeout=120)
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
    print("CLAD SOLUTIONS - FULL PRODUCT LIBRARY PROCESSOR")
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
    print(f"📋 Mapping defined for {len(FILE_MAPPING)} files")
    
    stats = {
        "processed": 0,
        "skipped_duplicate": 0,
        "skipped_unknown": 0,
        "failed": 0
    }
    
    processed_files = []
    
    # Process by category for cleaner output
    categories = {
        "PXR_Cavity_System/Technical_Manuals": [],
        "PXR_Cavity_System/CAD_Details": [],
        "PXR_Cavity_System/Forms_Templates": [],
        "Parklex_Prodema": [],
        "Shera_Weatherboard/Technical_Data": [],
        "Shera_Weatherboard/BRANZ_Appraisals": [],
        "Shera_Weatherboard/CAD_Details": [],
        "00_General_Resources": [],
    }
    
    # Categorize files
    for orig_filename in sorted(temp_filenames):
        if orig_filename in FILE_MAPPING:
            new_filename, folder = FILE_MAPPING[orig_filename]
            if new_filename and folder:
                categories.get(folder, []).append((orig_filename, new_filename))
    
    # Process each category
    for folder, files in categories.items():
        if not files:
            continue
            
        print(f"\n{'=' * 70}")
        print(f"📁 {folder}/ ({len(files)} files)")
        print("=" * 70)
        
        for orig_filename, new_filename in files:
            print(f"\n  📄 {orig_filename[:50]}...")
            print(f"     → {new_filename}")
            
            content = download_from_temp(orig_filename)
            if not content:
                print(f"     ❌ Download failed")
                stats["failed"] += 1
                continue
            
            if upload_to_destination(content, folder, new_filename):
                print(f"     ✅ Uploaded ({len(content):,} bytes)")
                stats["processed"] += 1
                processed_files.append(orig_filename)
            else:
                stats["failed"] += 1
            
            time.sleep(0.2)
    
    # Handle duplicates and unknown files
    print(f"\n{'=' * 70}")
    print("HANDLING DUPLICATES & UNKNOWN FILES")
    print("=" * 70)
    
    for orig_filename in temp_filenames:
        if orig_filename in FILE_MAPPING:
            new_filename, folder = FILE_MAPPING[orig_filename]
            if new_filename is None:
                print(f"  🚫 Duplicate: {orig_filename}")
                stats["skipped_duplicate"] += 1
                processed_files.append(orig_filename)  # Mark for deletion
        elif orig_filename not in processed_files:
            print(f"  ⚠️ Unknown: {orig_filename}")
            stats["skipped_unknown"] += 1
    
    # Summary
    print(f"\n{'=' * 70}")
    print("PROCESSING SUMMARY")
    print("=" * 70)
    print(f"✅ Processed & uploaded: {stats['processed']}")
    print(f"🚫 Skipped (duplicates): {stats['skipped_duplicate']}")
    print(f"⚠️ Skipped (unknown): {stats['skipped_unknown']}")
    print(f"❌ Failed: {stats['failed']}")
    
    # Clean up
    if processed_files:
        print(f"\n🧹 Cleaning up {len(processed_files)} files from temporary...")
        for filename in processed_files:
            if delete_from_temp(filename):
                pass  # Silent success
            
    print("\n✅ Cleanup complete")
    
    # Final structure verification
    print(f"\n{'=' * 70}")
    print("FINAL DIRECTORY STRUCTURE")
    print("=" * 70)
    
    def list_folder(path, indent=0):
        try:
            result = supabase.storage.from_(BUCKET_DEST).list(path)
            items = sorted([f for f in result if f.get('name')], key=lambda x: x['name'])
            
            for item in items:
                name = item['name']
                is_folder = item.get('id') is None
                
                if is_folder:
                    sub_path = f"{path}/{name}"
                    sub_result = supabase.storage.from_(BUCKET_DEST).list(sub_path)
                    sub_count = len([f for f in sub_result if f.get('name')])
                    print(f"{'  ' * indent}📁 {name}/ ({sub_count} files)")
                    list_folder(sub_path, indent + 1)
                else:
                    print(f"{'  ' * indent}└─ {name}")
        except Exception as e:
            print(f"{'  ' * indent}❌ Error: {e}")
    
    list_folder(BASE_PATH)
    
    return stats['failed'] == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
