#!/usr/bin/env python3
"""
Dimond Bulk Profile Ingestion
=============================
Iterates through all Dimond product profiles and ingests PDFs to Supabase
"""

import os
import sys
import re
import requests
import time
from urllib.parse import urljoin

sys.path.insert(0, '/app/backend-minimal')

from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

from supabase import create_client

# Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
BUCKET = 'product-library'
BASE_STORAGE_PATH = 'B_Enclosure/Dimond_Roofing'

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Profile configurations
PROFILES = [
    # Residential & Commercial
    {"url": "https://www.dimond.co.nz/products/styleline", "name": "Styleline", "folder": "Styleline", "prefix": "sty"},
    {"url": "https://www.dimond.co.nz/products/veedek", "name": "Veedek", "folder": "Veedek", "prefix": "vdk"},
    {"url": "https://www.dimond.co.nz/products/v-rib", "name": "V-Rib", "folder": "V_Rib", "prefix": "vrb"},
    {"url": "https://www.dimond.co.nz/products/lt7", "name": "LT7", "folder": "LT7", "prefix": "lt7"},
    {"url": "https://www.dimond.co.nz/products/hi-five", "name": "Hi Five", "folder": "Hi_Five", "prefix": "hf5"},
    {"url": "https://www.dimond.co.nz/products/six-rib", "name": "Six Rib", "folder": "Six_Rib", "prefix": "6rb"},
    {"url": "https://www.dimond.co.nz/products/dp955", "name": "DP955", "folder": "DP955", "prefix": "dp9"},
    
    # Architectural Trays
    {"url": "https://www.dimond.co.nz/products/dimondek-400", "name": "Dimondek 400", "folder": "Dimondek_400", "prefix": "dd4"},
    {"url": "https://www.dimond.co.nz/products/dimondek-630", "name": "Dimondek 630", "folder": "Dimondek_630", "prefix": "dd6"},
    {"url": "https://www.dimond.co.nz/products/heritage-tray", "name": "Heritage Tray", "folder": "Heritage_Tray", "prefix": "hrt"},
    {"url": "https://www.dimond.co.nz/products/eurotray-roll-cap", "name": "Eurotray Roll Cap", "folder": "Eurotray_Roll_Cap", "prefix": "erc"},
    {"url": "https://www.dimond.co.nz/products/eurotray-angle-seam", "name": "Eurotray Angle Seam", "folder": "Eurotray_Angle_Seam", "prefix": "eas"},
    {"url": "https://www.dimond.co.nz/products/solar-rib", "name": "Solar-Rib", "folder": "Solar_Rib", "prefix": "slr"},
    
    # Wall Cladding
    {"url": "https://www.dimond.co.nz/products/dimondclad-rib20", "name": "Dimondclad Rib 20", "folder": "Dimondclad_Rib20", "prefix": "dr2"},
    {"url": "https://www.dimond.co.nz/products/dimondclad-rib50", "name": "Dimondclad Rib 50", "folder": "Dimondclad_Rib50", "prefix": "dr5"},
    {"url": "https://www.dimond.co.nz/products/dimondclad-interlock", "name": "Dimondclad Interlock", "folder": "Dimondclad_Interlock", "prefix": "dci"},
    
    # Structural (different domain)
    {"url": "https://www.dimondstructural.co.nz/products/topspan", "name": "Topspan", "folder": "Topspan", "prefix": "tsp", "structural": True},
    {"url": "https://www.dimondstructural.co.nz/products/steelspan-900", "name": "Steelspan 900", "folder": "Steelspan_900", "prefix": "ss9", "structural": True},
    {"url": "https://www.dimondstructural.co.nz/products/hibond-55", "name": "Hibond 55", "folder": "Hibond_55", "prefix": "hb5", "structural": True},
    {"url": "https://www.dimondstructural.co.nz/products/dhs-purlins", "name": "DHS Purlins", "folder": "DHS_Purlins", "prefix": "dhs", "structural": True},
]

# Common CAD detail patterns (roofing 1xxx, cladding 2xxx)
CAD_DETAILS_ROOFING = [
    ("Parapet Detail", "1010"),
    ("Barge Detail", "1020"),
    ("Wall-Roof Junction", "1030"),
    ("Permanent Wall-Roof Junction Cladding", "1031"),
    ("Eaves Box Gutter", "1040"),
    ("Eaves Box Gutter With Cavity", "1041"),
    ("Wall-Roof Junction 90 Deg", "1050"),
    ("Wall-Roof Junction 90 Deg On Cavity", "1051"),
    ("Roof-Wall Apex", "1060"),
    ("Step In Roofing", "1070"),
    ("Large Penetration Detail", "1080"),
    ("Ridge Detail", "1090"),
    ("Valley Gutter Detail", "1100"),
    ("Change In Pitch Detail", "1110"),
    ("Residential Upper Mono Slope", "1120"),
    ("Residential Gutter-Wall Detail", "1130"),
    ("Residential Barge-Raking End", "1140"),
    ("Alternative Change In Pitch Flashing Detail", "1150"),
    ("Recommended Change In Pitch Detail", "1160"),
    ("Barge Flashing Fixing", "1170"),
    ("Barge Rolled Flashing", "1180"),
    ("Ridged Ventilators Detail", "1190"),
    ("Flashing Longitudinal Joint", "1200"),
    ("Pipe Penetration Detail", "1210"),
]

CAD_DETAILS_CLADDING = [
    ("Vertical Non-Cavity Cladding-Internal Corner", "2010"),
    ("Vertical Non-Cavity Cladding-External Corner", "2020"),
    ("Vertical Cladding Window Detail-Elevation", "2030"),
    ("Vertical Cladding With Cavity Window Detail-Elevation", "2031"),
    ("Vertical Cladding Window Detail-Head", "2040"),
    ("Vertical Cladding With Cavity Window Detail-Head", "2041"),
    ("Vertical Cladding Window Detail-Jamb", "2050"),
    ("Vertical Cladding With Cavity Window Detail-Jamb", "2051"),
    ("Vertical Cladding Window Detail-Sill", "2060"),
    ("Vertical Cladding With Cavity Window Detail-Sill", "2061"),
    ("Horizontal Non-Cavity Cladding-External Corner", "2070"),
    ("Horizontal Sheet Cladding Vertical Butt Joint", "2080"),
    ("Horizontal Cavity Cladding-Barge Flashing", "2090"),
    ("Horizontal Cavity Cladding-External Corner", "2100"),
    ("Horizontal Cavity Cladding-Internal Corner", "2110"),
    ("Vertical Cavity Cladding-Internal Corner", "2111"),
    ("Vertical Cavity Cladding-External Corner", "2114"),
    ("Horizontal Cavity Cladding-Sheet Butt Join", "2120"),
    ("Horizontal Cladding Window Detail-Elevation", "2130"),
    ("Horizontal Cladding With Cavity Window Detail-Elevation", "2131"),
    ("Horizontal Cladding Window Detail-Head", "2140"),
    ("Horizontal Cladding With Cavity Window Detail-Head", "2141"),
    ("Horizontal Cladding Window Detail-Jamb", "2150"),
    ("Horizontal Cladding With Cavity Window Detail-Jamb", "2151"),
    ("Horizontal Cladding Window Detail-Sill", "2160"),
    ("Horizontal Cladding With Cavity Window Detail-Sill", "2161"),
    ("Horizontal Cavity Cladding-Roof Junction 90 Deg", "2170"),
    ("Horizontal Cavity Cladding-Wall-Roof Junction", "2180"),
    ("Non-Cavity Wall To Floor Junction", "2190"),
    ("Cavity Wall To Floor Junction", "2200"),
    ("Junction To Panel Cladding", "2210"),
    ("Junction To Brick", "2220"),
    ("Pipe Penetration Through Horizontal Wall Cladding", "2230"),
    ("Junction To Concrete", "2240"),
    ("Range Hood Penetration", "2250"),
]


def clean_filename(text):
    """Clean text for filename"""
    cleaned = text.replace('/', '-').replace('\\', '-')
    cleaned = cleaned.replace(':', '-').replace('*', '').replace('?', '')
    cleaned = cleaned.replace('"', '').replace('<', '').replace('>', '')
    cleaned = cleaned.replace('|', '-')
    return ' '.join(cleaned.split())


def create_filename(profile_name, link_text):
    """Create standardized filename"""
    clean_text = clean_filename(link_text)
    return f"Dimond Roofing - {profile_name} - {clean_text}.pdf"


def download_pdf(url):
    """Download PDF content"""
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200 and len(response.content) > 1000:
            return response.content
        return None
    except Exception as e:
        return None


def upload_to_supabase(content, folder, filename):
    """Upload PDF to Supabase"""
    storage_path = f"{BASE_STORAGE_PATH}/{folder}/{filename}"
    try:
        supabase.storage.from_(BUCKET).upload(
            storage_path,
            content,
            {"content-type": "application/pdf", "upsert": "true"}
        )
        return True
    except Exception as e:
        return False


def get_pdf_urls_for_profile(profile):
    """Generate PDF URLs for a profile based on common patterns"""
    pdfs = []
    prefix = profile['prefix']
    name = profile['name']
    is_structural = profile.get('structural', False)
    
    if is_structural:
        # Structural products use different URL patterns
        base_url = "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/"
    else:
        base_url = "https://dimond-roofing.s3.amazonaws.com/downloads/CAD/pdf/"
    
    # Product Technical Statement
    pts_urls = [
        f"https://dimond-roofing.s3.ap-southeast-2.amazonaws.com/downloads/V1+-+PRODUCT+TECHNCIAL+STATEMENT+-+{name.upper().replace(' ', '+')}.pdf",
        f"https://dimond-roofing.s3.ap-southeast-2.amazonaws.com/downloads/V1+-+PRODUCT+TECHNCIAL+STATEMENT+-+DIMOND+{name.upper().replace(' ', '+')}.pdf",
    ]
    for url in pts_urls:
        pdfs.append(("Product Technical Statement", url))
    
    # Installers Guide (shared)
    pdfs.append(("The Installers Guide", "https://dimond-roofing.s3.ap-southeast-2.amazonaws.com/downloads/V1+-+The+Installers+Guide.pdf"))
    
    # Product Brochure patterns
    brochure_patterns = [
        f"https://dimond-roofing.s3.amazonaws.com/downloads/Brochures/FBDI_*_Brochure-{name.replace(' ', '-')}-Dimond_*.pdf",
    ]
    
    # CAD details - roofing
    for detail_name, code in CAD_DETAILS_ROOFING:
        url = f"{base_url}dim_{prefix}_{code}.pdf"
        pdfs.append((detail_name, url))
    
    # CAD details - cladding
    for detail_name, code in CAD_DETAILS_CLADDING:
        url = f"{base_url}dim_{prefix}_{code}.pdf"
        pdfs.append((detail_name, url))
    
    return pdfs


def scrape_profile_page(url):
    """Scrape a profile page to find actual PDF links"""
    try:
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            return []
        
        html = response.text
        pdfs = []
        
        # Find all PDF links
        pdf_pattern = r'href=["\']([^"\']*\.pdf)["\']'
        matches = re.findall(pdf_pattern, html, re.IGNORECASE)
        
        # Also look for S3 links
        s3_pattern = r'(https://dimond-roofing\.s3[^"\'>\s]+\.pdf)'
        s3_matches = re.findall(s3_pattern, html, re.IGNORECASE)
        
        all_urls = set(matches + s3_matches)
        
        for pdf_url in all_urls:
            # Make absolute URL if needed
            if not pdf_url.startswith('http'):
                pdf_url = urljoin(url, pdf_url)
            
            # Extract filename for link text
            filename = pdf_url.split('/')[-1].replace('.pdf', '').replace('+', ' ').replace('%20', ' ')
            
            # Clean up the name
            if 'dim_' in filename:
                # CAD detail - extract code
                parts = filename.split('_')
                if len(parts) >= 3:
                    code = parts[-1]
                    # Find matching detail name
                    for name, c in CAD_DETAILS_ROOFING + CAD_DETAILS_CLADDING:
                        if c == code:
                            filename = name
                            break
            
            pdfs.append((filename, pdf_url))
        
        return pdfs
    except Exception as e:
        print(f"   ⚠️ Scrape error: {e}")
        return []


def process_profile(profile):
    """Process a single profile"""
    name = profile['name']
    folder = profile['folder']
    url = profile['url']
    
    print(f"\n{'='*60}")
    print(f"📦 Processing: {name}")
    print(f"   URL: {url}")
    print(f"   Folder: {folder}")
    
    # Scrape the page for PDF links
    pdfs = scrape_profile_page(url)
    print(f"   Found {len(pdfs)} PDF links")
    
    if not pdfs:
        print(f"   ⚠️ No PDFs found, skipping...")
        return 0, name
    
    # Download and upload each PDF
    successful = 0
    for link_text, pdf_url in pdfs:
        filename = create_filename(name, link_text)
        
        # Download
        content = download_pdf(pdf_url)
        if not content:
            continue
        
        # Upload
        if upload_to_supabase(content, folder, filename):
            successful += 1
            print(f"   ✅ {link_text[:40]}...")
    
    print(f"   📊 Uploaded: {successful}/{len(pdfs)}")
    return successful, None


def main():
    print("=" * 60)
    print("🚀 DIMOND BULK PROFILE INGESTION")
    print("=" * 60)
    print(f"📁 Storage: {BUCKET}/{BASE_STORAGE_PATH}/")
    print(f"📋 Profiles to process: {len(PROFILES)}")
    
    results = []
    failed_urls = []
    total_files = 0
    
    for i, profile in enumerate(PROFILES, 1):
        print(f"\n[{i}/{len(PROFILES)}]", end="")
        count, failed = process_profile(profile)
        results.append((profile['name'], count))
        total_files += count
        if failed:
            failed_urls.append(profile['url'])
        
        # Small delay between profiles
        time.sleep(1)
    
    # Final report
    print("\n" + "=" * 60)
    print("📊 FINAL REPORT")
    print("=" * 60)
    print(f"\n{'Profile':<30} {'Files':>8}")
    print("-" * 40)
    for name, count in results:
        status = "✅" if count > 0 else "❌"
        print(f"{status} {name:<28} {count:>8}")
    
    print("-" * 40)
    print(f"{'TOTAL':<30} {total_files:>8}")
    
    if failed_urls:
        print(f"\n❌ FAILED URLs ({len(failed_urls)}):")
        for url in failed_urls:
            print(f"   - {url}")
    
    print(f"\n✅ Bulk ingestion complete!")
    return total_files, failed_urls


if __name__ == '__main__':
    main()
