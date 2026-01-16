#!/usr/bin/env python3
"""
Roofing Industries Full Catalog Scraper
========================================
Scrapes ALL technical documentation from roof.co.nz
and uploads to Supabase storage with proper naming conventions.

Categories:
- Corrugated: Corrugate, True Oak Corrugate, True Oak Deep, Slimline
- Trapezoidal: RT7, Trimrib, Multirib, Multidek, Ribline, Maxispan
- Architectural: Eurostyle (Epic, Spanlok, Eurolok, Panelok), Slimclad
- Commercial: RI925, DRI-CLAD
- Rainwater: Gutters, Downpipes, Fascia, Screens

Author: STRYDA Data Pipeline
Date: 2025-01
"""

import os
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote
from supabase import create_client
from dotenv import load_dotenv

load_dotenv("/app/backend-minimal/.env")

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
BUCKET_NAME = "product-library"
print(f"🔗 Supabase URL: {SUPABASE_URL[:30]}..." if SUPABASE_URL else "❌ No SUPABASE_URL")

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Base URL
BASE_URL = "https://www.roof.co.nz"

# ============================================================================
# PRODUCT PAGE URLs TO SCRAPE
# ============================================================================
PRODUCT_PAGES = [
    # Corrugated Profiles
    "/product/corrugate",
    "/product/true-oak-corrugate",
    "/product/true-oak-deep",
    "/product/slimline-mini-corrugate",
    
    # Trapezoidal Profiles
    "/product/rt7",
    "/product/trimrib",
    "/product/multirib",
    "/product/multidek",
    "/product/ribline-r-800",
    "/product/ribline-r-960",
    "/product/maxispan",
    "/product/ri925",
    
    # Architectural / Eurostyle Profiles
    "/product/eurostyle-epic",
    "/product/eurostyle-spanlok",
    "/product/eurostyle-eurolok",
    "/product/eurostyle-panelok",
    "/product/slimclad",
    "/product/dri-clad-tm",
    
    # Rainwater Systems
    "/rainwater-solutions",
    "/rainwater-categories/guttering-spouting",
    "/rainwater-categories/downpipes",
    "/rainwater-categories/fascia",
    "/rainwater-solutions/ezi-lok",
    "/rainwater-solutions/rainwater-heads",
]

# ============================================================================
# FOLDER MAPPING - Maps product to storage folders
# ============================================================================
PROFILE_FOLDER_MAP = {
    # Corrugated
    "corrugate": "Corrugate",
    "true-oak-corrugate": "True_Oak_Corrugate",
    "true-oak-deep": "True_Oak_Deep",
    "slimline": "Slimline",
    
    # Trapezoidal
    "rt7": "RT7",
    "trimrib": "Trimrib",
    "multirib": "Multirib",
    "multidek": "Multidek",
    "ribline": "Ribline",
    "maxispan": "Maxispan",
    "ri925": "RI925",
    
    # Architectural
    "eurostyle": "Eurostyle",
    "epic": "Eurostyle_Epic",
    "spanlok": "Eurostyle_Spanlok",
    "eurolok": "Eurostyle_Eurolok",
    "panelok": "Eurostyle_Panelok",
    "slimclad": "Slimclad",
    "dri-clad": "DRI_CLAD",
    
    # Rainwater
    "rainwater": "Rainwater_Systems",
    "gutter": "Rainwater_Systems",
    "downpipe": "Rainwater_Systems",
    "fascia": "Rainwater_Systems",
    "ezi-lok": "Rainwater_Systems",
    "ezi-flo": "Rainwater_Systems",
}

# Universal Resource Keywords - files matching these go to 00_General_Resources
UNIVERSAL_KEYWORDS = [
    "maintenance",
    "handling",
    "storage guide",
    "color chart",
    "colour chart",
    "colorcote",
    "colorsteel",
    "zinacore",
    "magnaflow",
    "alumigard",
    "zincalume",
    "dridex",
    "altimate",
    "matte",
    "maxam",
    "environmental",
    "warranty",
    "choose the right roof",
]

# Track uploaded files for deduplication
uploaded_files = set()
universal_files = set()

# Statistics
stats = {
    "pages_scraped": 0,
    "pdfs_found": 0,
    "pdfs_uploaded": 0,
    "pdfs_skipped_duplicate": 0,
    "pdfs_skipped_error": 0,
    "universal_files": 0,
}


def sanitize_filename(name):
    """Clean filename for safe storage"""
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    if len(name) > 200:
        name = name[:200]
    return name


def detect_profile_from_url(url, link_text):
    """Determine product profile from URL and link text"""
    url_lower = url.lower()
    text_lower = link_text.lower()
    combined = f"{url_lower} {text_lower}"
    
    # Check for specific profiles in order of specificity
    profile_checks = [
        ("true-oak-deep", "True Oak Deep"),
        ("true-oak-corrugate", "True Oak Corrugate"),
        ("true-oak", "True Oak"),
        ("corrugate", "Corrugate"),
        ("slimline", "Slimline"),
        ("rt7", "RT7"),
        ("trimrib", "Trimrib"),
        ("multirib", "Multirib"),
        ("multidek", "Multidek"),
        ("ribline-r-960", "Ribline 960"),
        ("ribline-r-800", "Ribline 800"),
        ("ribline", "Ribline"),
        ("maxispan", "Maxispan"),
        ("ri925", "RI925"),
        ("eurostyle-epic", "Eurostyle Epic"),
        ("eurostyle-spanlok", "Eurostyle Spanlok"),
        ("eurostyle-eurolok", "Eurostyle Eurolok"),
        ("eurostyle-panelok", "Eurostyle Panelok"),
        ("epic", "Eurostyle Epic"),
        ("spanlok", "Eurostyle Spanlok"),
        ("eurolok", "Eurostyle Eurolok"),
        ("panelok", "Eurostyle Panelok"),
        ("eurostyle", "Eurostyle"),
        ("slimclad", "Slimclad"),
        ("dri-clad", "DRI-CLAD"),
        ("rainwater", "Rainwater"),
        ("gutter", "Rainwater"),
        ("downpipe", "Rainwater"),
        ("fascia", "Rainwater"),
        ("ezi-lok", "Rainwater"),
        ("ezi-flo", "Rainwater"),
    ]
    
    for keyword, profile in profile_checks:
        if keyword in combined:
            return profile
    
    return "General"


def get_storage_folder(url, link_text):
    """Determine the correct storage folder based on URL and link text"""
    url_lower = url.lower()
    text_lower = link_text.lower()
    
    # Check for universal resources first
    for keyword in UNIVERSAL_KEYWORDS:
        if keyword in text_lower:
            return "B_Enclosure/Roofing_Industries/00_General_Resources"
    
    # Check URL path for profile
    for keyword, folder in PROFILE_FOLDER_MAP.items():
        if keyword in url_lower:
            return f"B_Enclosure/Roofing_Industries/{folder}"
    
    # Check link text
    for keyword, folder in PROFILE_FOLDER_MAP.items():
        if keyword in text_lower:
            return f"B_Enclosure/Roofing_Industries/{folder}"
    
    # Default folder
    return "B_Enclosure/Roofing_Industries/00_General_Resources"


def is_universal_file(link_text):
    """Check if file should be treated as universal resource"""
    text_lower = link_text.lower()
    for keyword in UNIVERSAL_KEYWORDS:
        if keyword in text_lower:
            return True
    return False


def generate_filename(url, link_text, profile_name):
    """Generate standardized filename"""
    # Clean link text for use in filename
    clean_text = sanitize_filename(link_text)
    
    # If no good link text, try to extract from URL
    if not clean_text or len(clean_text) < 5:
        # Extract filename from URL
        url_path = urlparse(url).path
        clean_text = unquote(url_path.split('/')[-1])
        clean_text = clean_text.replace('.pdf', '').replace('-', ' ').replace('_', ' ')
        clean_text = sanitize_filename(clean_text)
    
    # Check if universal
    if is_universal_file(link_text) or is_universal_file(clean_text):
        filename = f"Roofing Industries - Universal - {clean_text}.pdf"
    else:
        filename = f"Roofing Industries - {profile_name} - {clean_text}.pdf"
    
    return sanitize_filename(filename)


def file_exists_in_storage(folder, filename):
    """Check if file already exists in Supabase storage"""
    try:
        result = supabase.storage.from_(BUCKET_NAME).list(folder)
        existing_files = [f['name'] for f in result] if result else []
        return filename in existing_files
    except Exception:
        return False


def upload_to_supabase(content, folder, filename):
    """Upload file to Supabase storage"""
    try:
        file_path = f"{folder}/{filename}"
        
        # Check if already uploaded this session
        if file_path in uploaded_files:
            print(f"  ⏭️  Already uploaded this session: {filename}")
            stats["pdfs_skipped_duplicate"] += 1
            return False
        
        # Check if file exists in storage
        if file_exists_in_storage(folder, filename):
            print(f"  ⏭️  Already exists in storage: {filename}")
            stats["pdfs_skipped_duplicate"] += 1
            uploaded_files.add(file_path)
            return False
        
        # Upload the file
        result = supabase.storage.from_(BUCKET_NAME).upload(
            file_path,
            content,
            {"content-type": "application/pdf", "upsert": "false"}
        )
        
        uploaded_files.add(file_path)
        print(f"  ✅ Uploaded: {filename}")
        return True
        
    except Exception as e:
        error_msg = str(e)
        if "Duplicate" in error_msg or "already exists" in error_msg.lower():
            print(f"  ⏭️  Duplicate: {filename}")
            stats["pdfs_skipped_duplicate"] += 1
            uploaded_files.add(f"{folder}/{filename}")
            return False
        else:
            print(f"  ❌ Upload error: {filename} - {error_msg[:100]}")
            stats["pdfs_skipped_error"] += 1
            return False


def download_and_upload_pdf(pdf_url, link_text, source_url):
    """Download PDF and upload to appropriate Supabase folder"""
    try:
        # Determine profile and folder
        profile_name = detect_profile_from_url(source_url, link_text)
        folder = get_storage_folder(source_url, link_text)
        filename = generate_filename(pdf_url, link_text, profile_name)
        
        # Handle universal file deduplication
        if is_universal_file(link_text) or is_universal_file(filename):
            universal_key = filename.lower()
            if universal_key in universal_files:
                print(f"  ⏭️  Universal file already processed: {filename}")
                stats["pdfs_skipped_duplicate"] += 1
                return False
            universal_files.add(universal_key)
            stats["universal_files"] += 1
        
        print(f"  📥 Downloading: {link_text[:60]}...")
        print(f"      → Profile: {profile_name}")
        print(f"      → Folder: {folder}")
        print(f"      → Filename: {filename}")
        
        # Download PDF
        response = requests.get(pdf_url, timeout=60, stream=True)
        response.raise_for_status()
        
        content = response.content
        
        # Verify it's a PDF
        if not content[:4] == b'%PDF':
            print(f"  ⚠️  Not a valid PDF: {link_text}")
            stats["pdfs_skipped_error"] += 1
            return False
        
        # Upload to Supabase
        success = upload_to_supabase(content, folder, filename)
        if success:
            stats["pdfs_uploaded"] += 1
        
        return success
        
    except requests.RequestException as e:
        print(f"  ❌ Download error: {link_text[:50]} - {str(e)[:50]}")
        stats["pdfs_skipped_error"] += 1
        return False
    except Exception as e:
        print(f"  ❌ Error processing: {link_text[:50]} - {str(e)[:50]}")
        stats["pdfs_skipped_error"] += 1
        return False


def scrape_page_for_pdfs(page_url):
    """Scrape a page for all PDF links"""
    full_url = urljoin(BASE_URL, page_url)
    print(f"\n📄 Scraping: {page_url}")
    
    try:
        response = requests.get(full_url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        pdf_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Check if it's a PDF link
            if '.pdf' in href.lower():
                pdf_url = urljoin(full_url, href)
                
                # Get link text
                link_text = link.get_text(strip=True)
                if not link_text:
                    link_text = link.get('title', '')
                    if not link_text:
                        # Extract from filename
                        link_text = unquote(urlparse(pdf_url).path.split('/')[-1])
                        link_text = link_text.replace('.pdf', '').replace('-', ' ').replace('_', ' ')
                
                # Clean up link text
                link_text = re.sub(r'\s+', ' ', link_text).strip()
                if link_text:
                    pdf_links.append((pdf_url, link_text))
        
        # Remove duplicates (same URL)
        seen_urls = set()
        unique_links = []
        for url, text in pdf_links:
            if url not in seen_urls:
                seen_urls.add(url)
                unique_links.append((url, text))
        
        print(f"  Found {len(unique_links)} unique PDF links")
        stats["pdfs_found"] += len(unique_links)
        stats["pages_scraped"] += 1
        
        return unique_links
        
    except Exception as e:
        print(f"  ❌ Error scraping page: {str(e)[:100]}")
        return []


def run_full_scrape():
    """Run the full catalog scrape"""
    print("=" * 70)
    print("🚀 ROOFING INDUSTRIES FULL CATALOG SCRAPER")
    print("=" * 70)
    print(f"\n📊 Target: {len(PRODUCT_PAGES)} pages to scrape")
    print(f"📁 Destination bucket: {BUCKET_NAME}")
    print(f"📂 Base folder: B_Enclosure/Roofing_Industries/\n")
    
    all_pdf_links = []
    
    # Phase 1: Collect all PDF links from all pages
    print("\n" + "=" * 70)
    print("PHASE 1: COLLECTING PDF LINKS")
    print("=" * 70)
    
    for page_url in PRODUCT_PAGES:
        links = scrape_page_for_pdfs(page_url)
        for pdf_url, link_text in links:
            all_pdf_links.append((pdf_url, link_text, page_url))
        time.sleep(0.5)  # Be polite to the server
    
    # Deduplicate by URL
    seen_urls = set()
    unique_pdf_links = []
    for pdf_url, link_text, source in all_pdf_links:
        if pdf_url not in seen_urls:
            seen_urls.add(pdf_url)
            unique_pdf_links.append((pdf_url, link_text, source))
    
    print(f"\n📊 Total unique PDFs found: {len(unique_pdf_links)}")
    
    # Phase 2: Download and upload all PDFs
    print("\n" + "=" * 70)
    print("PHASE 2: DOWNLOADING AND UPLOADING PDFs")
    print("=" * 70)
    
    for i, (pdf_url, link_text, source) in enumerate(unique_pdf_links, 1):
        print(f"\n[{i}/{len(unique_pdf_links)}] Processing...")
        download_and_upload_pdf(pdf_url, link_text, source)
        time.sleep(0.3)  # Rate limiting
    
    # Final Statistics
    print("\n" + "=" * 70)
    print("📊 FINAL STATISTICS")
    print("=" * 70)
    print(f"  Pages scraped:         {stats['pages_scraped']}")
    print(f"  PDFs found:            {stats['pdfs_found']}")
    print(f"  PDFs uploaded:         {stats['pdfs_uploaded']}")
    print(f"  Universal files:       {stats['universal_files']}")
    print(f"  Skipped (duplicate):   {stats['pdfs_skipped_duplicate']}")
    print(f"  Skipped (error):       {stats['pdfs_skipped_error']}")
    print("=" * 70)
    
    return stats


if __name__ == "__main__":
    run_full_scrape()
