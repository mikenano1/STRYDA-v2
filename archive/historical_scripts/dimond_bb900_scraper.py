#!/usr/bin/env python3
"""
Dimond Brownbuilt 900 PDF Scraper and Uploader
Downloads PDFs from dimond.co.nz/products/brownbuilt-900 and uploads to Supabase
With (BB900) tag for searchability
"""

import os
import sys
import re
import requests

sys.path.insert(0, '/app/backend-minimal')

from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

from supabase import create_client

# Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
STORAGE_PATH = 'B_Enclosure/Dimond_Roofing/Brownbuilt_900'
BUCKET = 'product-library'

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# All PDFs found on the Brownbuilt 900 page
# Format: (link_text, url)
BB900_PDFS = [
    # Product Technical Statement
    ("Product Technical Statement", "https://dimond-roofing.s3.ap-southeast-2.amazonaws.com/downloads/V1+-+PRODUCT+TECHNCIAL+STATEMENT+-+DIMOND+BB900.pdf"),
    
    # Installers Guide
    ("The Installers Guide", "https://dimond-roofing.s3.ap-southeast-2.amazonaws.com/downloads/V1+-+The+Installers+Guide.pdf"),
    
    # Product Brochure
    ("Product Brochure", "https://dimond-roofing.s3.amazonaws.com/downloads/Brochures/FBDI_26_Brochure-BB900-Dimond_V01.00.0618_WEB.pdf"),
    
    # CAD Details - Roofing (1xxx series)
    ("Parapet Detail", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_1010.pdf"),
    ("Barge Detail", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_1020.pdf"),
    ("Wall-Roof Junction", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_1030.pdf"),
    ("Permanent Wall-Roof Junction Cladding", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_1031.pdf"),
    ("Eaves Box Gutter", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_1040.pdf"),
    ("Eaves Box Gutter With Cavity", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_1041.pdf"),
    ("Wall-Roof Junction 90 Deg", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_1050.pdf"),
    ("Wall-Roof Junction 90 Deg On Cavity", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_1051.pdf"),
    ("Roof-Wall Apex", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_1060.pdf"),
    ("Step In Roofing", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_1070.pdf"),
    ("Large Penetration Detail", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_1080.pdf"),
    ("Ridge Detail", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_1090.pdf"),
    ("Valley Gutter Detail", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_1100.pdf"),
    ("Change In Pitch Detail", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_1110.pdf"),
    ("Residential Upper Mono Slope", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_1120.pdf"),
    ("Residential Gutter-Wall Detail", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_1130.pdf"),
    ("Residential Barge-Raking End", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_1140.pdf"),
    ("Alternative Change In Pitch Flashing Detail", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_1150.pdf"),
    ("Recommended Change In Pitch Detail", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_1160.pdf"),
    ("Barge Flashing Fixing", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_1170.pdf"),
    ("Ridged Ventilators Detail", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_1190.pdf"),
    ("Flashing Longitudinal Joint", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_1200.pdf"),
    ("Pipe Penetration Detail", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_1210.pdf"),
    
    # CAD Details - Cladding (2xxx series)
    ("Vertical Non-Cavity Cladding-Internal Corner", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2010.pdf"),
    ("Vertical Non-Cavity Cladding-External Corner", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2020.pdf"),
    ("Vertical Cladding Window Detail-Elevation", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2030.pdf"),
    ("Vertical Cladding With Cavity Window Detail-Elevation", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2031.pdf"),
    ("Vertical Cladding Window Detail-Head", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2040.pdf"),
    ("Vertical Cladding With Cavity Window Detail-Head", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2041.pdf"),
    ("Vertical Cladding Window Detail-Jamb", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2050.pdf"),
    ("Vertical Cladding With Cavity Window Detail-Jamb", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2051.pdf"),
    ("Vertical Cladding Window Detail-Sill", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2060.pdf"),
    ("Vertical Cladding With Cavity Window Detail-Sill", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2061.pdf"),
    ("Horizontal Non-Cavity Cladding-External Corner", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2070.pdf"),
    ("Horizontal Sheet Cladding Vertical Butt Joint", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2080.pdf"),
    ("Horizontal Cavity Cladding-Barge Flashing", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2090.pdf"),
    ("Horizontal Cavity Cladding-External Corner", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2100.pdf"),
    ("Horizontal Cavity Cladding-Internal Corner", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2110.pdf"),
    ("Vertical Cavity Cladding-Internal Corner", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2111.pdf"),
    ("Vertical Cavity Cladding-External Corner", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2114.pdf"),
    ("Horizontal Cavity Cladding-Sheet Butt Join", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2120.pdf"),
    ("Horizontal Cladding Window Detail-Elevation", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2130.pdf"),
    ("Horizontal Cladding With Cavity Window Detail-Elevation", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2131.pdf"),
    ("Horizontal Cladding Window Detail-Head", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2140.pdf"),
    ("Horizontal Cladding With Cavity Window Detail-Head", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2141.pdf"),
    ("Horizontal Cladding Window Detail-Jamb", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2150.pdf"),
    ("Horizontal Cladding With Cavity Window Detail-Jamb", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2151.pdf"),
    ("Horizontal Cladding Window Detail-Sill", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2160.pdf"),
    ("Horizontal Cladding With Cavity Window Detail-Sill", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2161.pdf"),
    ("Horizontal Cavity Cladding-Roof Junction 90 Deg", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2170.pdf"),
    ("Horizontal Cavity Cladding-Wall-Roof Junction", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2180.pdf"),
    ("Non-Cavity Wall To Floor Junction", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2190.pdf"),
    ("Cavity Wall To Floor Junction", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2200.pdf"),
    ("Junction To Panel Cladding", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2210.pdf"),
    ("Junction To Brick", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2220.pdf"),
    ("Pipe Penetration Through Horizontal Wall Cladding", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2230.pdf"),
    ("Junction To Concrete", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2240.pdf"),
    ("Range Hood Penetration", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_bb9_2250.pdf"),
]


def clean_filename(link_text):
    """Clean link text to create valid filename"""
    cleaned = link_text.replace('/', '-').replace('\\', '-')
    cleaned = cleaned.replace(':', '-').replace('*', '').replace('?', '')
    cleaned = cleaned.replace('"', '').replace('<', '').replace('>', '')
    cleaned = cleaned.replace('|', '-')
    cleaned = ' '.join(cleaned.split())
    return cleaned


def create_filename(link_text):
    """Create standardized filename with (BB900) tag"""
    clean_text = clean_filename(link_text)
    return f"Dimond Roofing - Brownbuilt 900 (BB900) - {clean_text}.pdf"


def download_pdf(url):
    """Download PDF and return content"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"   ❌ Download error: {e}")
        return None


def upload_to_supabase(content, filename):
    """Upload PDF to Supabase storage"""
    storage_path = f"{STORAGE_PATH}/{filename}"
    try:
        result = supabase.storage.from_(BUCKET).upload(
            storage_path,
            content,
            {"content-type": "application/pdf", "upsert": "true"}
        )
        return True
    except Exception as e:
        print(f"   ❌ Upload error: {e}")
        return False


def main():
    print("=" * 60)
    print("🏗️ DIMOND BROWNBUILT 900 (BB900) PDF SCRAPER")
    print("=" * 60)
    print(f"\n📁 Target path: {BUCKET}/{STORAGE_PATH}")
    print(f"📄 Total PDFs to process: {len(BB900_PDFS)}")
    print(f"🏷️  Tag: (BB900)")
    
    # Process each PDF
    print("\n🔄 DOWNLOADING AND UPLOADING...")
    successful = 0
    failed = 0
    
    for i, (link_text, url) in enumerate(BB900_PDFS, 1):
        filename = create_filename(link_text)
        print(f"\n[{i}/{len(BB900_PDFS)}] {filename[:60]}...")
        
        # Download
        content = download_pdf(url)
        if not content:
            failed += 1
            continue
        
        # Upload
        if upload_to_supabase(content, filename):
            print(f"   ✅ Uploaded ({len(content)/1024:.1f} KB)")
            successful += 1
        else:
            failed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ COMPLETE")
    print("=" * 60)
    print(f"   Successful: {successful}/{len(BB900_PDFS)}")
    print(f"   Failed: {failed}")
    print(f"   Storage path: {BUCKET}/{STORAGE_PATH}/")
    
    # List uploaded files
    print("\n📋 UPLOADED FILES (sample):")
    try:
        files = supabase.storage.from_(BUCKET).list(STORAGE_PATH)
        pdf_files = [f for f in files if f['name'].endswith('.pdf')]
        for f in sorted(pdf_files, key=lambda x: x['name'])[:10]:
            print(f"   - {f['name']}")
        if len(pdf_files) > 10:
            print(f"   ... and {len(pdf_files) - 10} more")
    except Exception as e:
        print(f"   ⚠️ Could not list files: {e}")
    
    return successful


if __name__ == '__main__':
    main()
