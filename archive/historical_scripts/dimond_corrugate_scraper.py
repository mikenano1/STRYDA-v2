#!/usr/bin/env python3
"""
Dimond Corrugate PDF Scraper and Uploader
Downloads PDFs from dimond.co.nz/products/corrugate and uploads to Supabase
"""

import os
import sys
import re
import requests
import tempfile

sys.path.insert(0, '/app/backend-minimal')

from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

from supabase import create_client

# Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
STORAGE_PATH = 'B_Enclosure/Dimond_Roofing/Corrugate'
BUCKET = 'product-library'

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# All PDFs found on the Corrugate page
# Format: (link_text, url)
CORRUGATE_PDFS = [
    # Product Technical Statement
    ("Product Technical Statement", "https://dimond-roofing.s3.ap-southeast-2.amazonaws.com/downloads/V1+-+PRODUCT+TECHNCIAL+STATEMENT+-+CORRUGATE.pdf"),
    
    # Installers Guide
    ("The Installers Guide", "https://dimond-roofing.s3.ap-southeast-2.amazonaws.com/downloads/V1+-+The+Installers+Guide.pdf"),
    
    # Product Brochure
    ("Product Brochure", "https://dimond-roofing.s3.amazonaws.com/downloads/Brochures/FBDI_27_Brochure-Corrugate-Dimond_V01.00.0618_WEB.pdf"),
    
    # CAD Details - Roofing (1xxx series)
    ("Parapet Detail", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_1010.pdf"),
    ("Barge Detail", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_1020.pdf"),
    ("Wall-Roof Junction", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_1030.pdf"),
    ("Permanent Wall-Roof Junction Cladding", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_1031.pdf"),
    ("Eaves Box Gutter", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_1040.pdf"),
    ("Eaves Box Gutter With Cavity", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_1041.pdf"),
    ("Wall-Roof Junction 90 Deg", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_1050.pdf"),
    ("Wall-Roof Junction 90 Deg On Cavity", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_1051.pdf"),
    ("Roof-Wall Apex", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_1060.pdf"),
    ("Step In Roofing", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_1070.pdf"),
    ("Large Penetration Detail", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_1080.pdf"),
    ("Ridge Detail", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_1090.pdf"),
    ("Valley Gutter Detail", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_1100.pdf"),
    ("Change In Pitch Detail", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_1110.pdf"),
    ("Residential Upper Mono Slope", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_1120.pdf"),
    ("Residential Gutter-Wall Detail", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_1130.pdf"),
    ("Residential Barge-Raking End", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_1140.pdf"),
    ("Alternative Change In Pitch Flashing Detail", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_1150.pdf"),
    ("Recommended Change In Pitch Detail", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_1160.pdf"),
    ("Barge Flashing Fixing", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_1170.pdf"),
    ("Barge Rolled Flashing", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_1180.pdf"),
    ("Ridged Ventilators Detail", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_1190.pdf"),
    ("Flashing Longitudinal Joint", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_1200.pdf"),
    ("Pipe Penetration Detail", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_1210.pdf"),
    
    # CAD Details - Cladding (2xxx series)
    ("Vertical Non-Cavity Cladding-Internal Corner", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2010.pdf"),
    ("Vertical Non-Cavity Cladding-External Corner", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2020.pdf"),
    ("Vertical Cladding Window Detail-Elevation", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2030.pdf"),
    ("Vertical Cladding With Cavity Window Detail-Elevation", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2031.pdf"),
    ("Vertical Cladding Window Detail-Head", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2040.pdf"),
    ("Vertical Cladding With Cavity Window Detail-Head", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2041.pdf"),
    ("Vertical Cladding Window Detail-Jamb", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2050.pdf"),
    ("Vertical Cladding With Cavity Window Detail-Jamb", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2051.pdf"),
    ("Vertical Cladding Window Detail-Sill", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2060.pdf"),
    ("Vertical Cladding With Cavity Window Detail-Sill", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2061.pdf"),
    ("Horizontal Non-Cavity Cladding-External Corner", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2070.pdf"),
    ("Horizontal Sheet Cladding Vertical Butt Joint", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2080.pdf"),
    ("Horizontal Cavity Cladding-Barge Flashing", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2090.pdf"),
    ("Horizontal Cavity Cladding-External Corner", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2100.pdf"),
    ("Horizontal Cavity Cladding-Internal Corner", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2110.pdf"),
    ("Vertical Cavity Cladding-Internal Corner", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2111.pdf"),
    ("Vertical Cavity Cladding-External Corner", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2114.pdf"),
    ("Horizontal Cavity Cladding-Sheet Butt Join", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2120.pdf"),
    ("Horizontal Cladding Window Detail-Elevation", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2130.pdf"),
    ("Horizontal Cladding With Cavity Window Detail-Elevation", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2131.pdf"),
    ("Horizontal Cladding Window Detail-Head", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2140.pdf"),
    ("Horizontal Cladding With Cavity Window Detail-Head", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2141.pdf"),
    ("Horizontal Cladding Window Detail-Jamb", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2150.pdf"),
    ("Horizontal Cladding With Cavity Window Detail-Jamb", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2151.pdf"),
    ("Horizontal Cladding Window Detail-Sill", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2160.pdf"),
    ("Horizontal Cladding With Cavity Window Detail-Sill", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2161.pdf"),
    ("Horizontal Cavity Cladding-Roof Junction 90 Deg", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2170.pdf"),
    ("Horizontal Cavity Cladding-Wall-Roof Junction", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2180.pdf"),
    ("Non-Cavity Wall To Floor Junction", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2190.pdf"),
    ("Cavity Wall To Floor Junction", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2200.pdf"),
    ("Junction To Panel Cladding", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2210.pdf"),
    ("Junction To Brick", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2220.pdf"),
    ("Pipe Penetration Through Horizontal Wall Cladding", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2230.pdf"),
    ("Junction To Concrete", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2240.pdf"),
    ("Range Hood Penetration", "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/dim_cor_2250.pdf"),
]


def clean_filename(link_text):
    """Clean link text to create valid filename"""
    # Remove special characters that could cause path issues
    cleaned = link_text.replace('/', '-').replace('\\', '-')
    cleaned = cleaned.replace(':', '-').replace('*', '').replace('?', '')
    cleaned = cleaned.replace('"', '').replace('<', '').replace('>', '')
    cleaned = cleaned.replace('|', '-')
    # Remove extra spaces
    cleaned = ' '.join(cleaned.split())
    return cleaned


def create_filename(link_text):
    """Create standardized filename: Dimond Roofing - Corrugate - [Link Text].pdf"""
    clean_text = clean_filename(link_text)
    return f"Dimond Roofing - Corrugate - {clean_text}.pdf"


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
        # Upload file
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
    print("🏗️ DIMOND CORRUGATE PDF SCRAPER")
    print("=" * 60)
    print(f"\n📁 Target path: {BUCKET}/{STORAGE_PATH}")
    print(f"📄 Total PDFs to process: {len(CORRUGATE_PDFS)}")
    
    # Create folder structure first (placeholder)
    print("\n📂 Creating folder structure...")
    try:
        placeholder = b"placeholder"
        supabase.storage.from_(BUCKET).upload(
            f"{STORAGE_PATH}/_placeholder.txt",
            placeholder,
            {"content-type": "text/plain", "upsert": "true"}
        )
        print("   ✅ Folder created")
    except Exception as e:
        print(f"   ⚠️ Folder may already exist: {e}")
    
    # Process each PDF
    print("\n🔄 DOWNLOADING AND UPLOADING...")
    successful = 0
    failed = 0
    
    for i, (link_text, url) in enumerate(CORRUGATE_PDFS, 1):
        filename = create_filename(link_text)
        print(f"\n[{i}/{len(CORRUGATE_PDFS)}] {filename[:60]}...")
        
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
    print(f"   Successful: {successful}/{len(CORRUGATE_PDFS)}")
    print(f"   Failed: {failed}")
    print(f"   Storage path: {BUCKET}/{STORAGE_PATH}/")
    
    # List uploaded files
    print("\n📋 UPLOADED FILES:")
    try:
        files = supabase.storage.from_(BUCKET).list(STORAGE_PATH)
        for f in files:
            if f['name'].endswith('.pdf'):
                print(f"   - {f['name']}")
    except Exception as e:
        print(f"   ⚠️ Could not list files: {e}")
    
    return successful


if __name__ == '__main__':
    main()
