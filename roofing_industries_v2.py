#!/usr/bin/env python3
"""
Roofing Industries Smart Scraper v2
===================================
Improved scraper with context-aware filename generation:
- Extracts section headings to generate meaningful filenames
- Strips hash codes from filenames
- Handles generic "Download" link text

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

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

BASE_URL = "https://www.roof.co.nz"

# Product pages to scrape
PRODUCT_PAGES = [
    "/product/corrugate",
    "/product/true-oak-corrugate",
    "/product/true-oak-deep",
    "/product/slimline-mini-corrugate",
    "/product/rt7",
    "/product/trimrib",
    "/product/multirib",
    "/product/multidek",
    "/product/ribline-r-800",
    "/product/ribline-r-960",
    "/product/maxispan",
    "/product/ri925",
    "/product/eurostyle-epic",
    "/product/eurostyle-spanlok",
    "/product/eurostyle-eurolok",
    "/product/eurostyle-panelok",
    "/product/slimclad",
    "/product/dri-clad-tm",
    "/rainwater-solutions",
    "/rainwater-categories/guttering-spouting",
    "/rainwater-categories/downpipes",
    "/rainwater-categories/fascia",
    "/rainwater-solutions/ezi-lok",
    "/rainwater-solutions/rainwater-heads",
]

# Profile folder mapping
PROFILE_FOLDER_MAP = {
    "corrugate": "Corrugate",
    "true-oak-corrugate": "True_Oak_Corrugate",
    "true-oak-deep": "True_Oak_Deep",
    "slimline": "Slimline",
    "rt7": "RT7",
    "trimrib": "Trimrib",
    "multirib": "Multirib",
    "multidek": "Multidek",
    "ribline": "Ribline",
    "maxispan": "Maxispan",
    "ri925": "RI925",
    "eurostyle": "Eurostyle",
    "epic": "Eurostyle",
    "spanlok": "Eurostyle",
    "eurolok": "Eurostyle",
    "panelok": "Eurostyle",
    "slimclad": "Slimclad",
    "dri-clad": "DRI_CLAD",
    "rainwater": "Rainwater_Systems",
    "gutter": "Rainwater_Systems",
    "downpipe": "Rainwater_Systems",
    "fascia": "Rainwater_Systems",
    "ezi-lok": "Rainwater_Systems",
    "ezi-flo": "Rainwater_Systems",
}

# Universal keywords that go to 00_General_Resources
UNIVERSAL_KEYWORDS = [
    "maintenance", "handling", "storage guide", "color chart", "colour chart",
    "colorcote", "colorsteel", "zinacore", "magnaflow", "alumigard",
    "zincalume", "dridex", "altimate", "matte", "maxam", "environmental",
    "warranty", "choose the right roof", "durability",
]

# Generic link text that needs context scraping
GENERIC_LINK_TEXT = ["download", "download guide", "download brochure", "view", "click here", "pdf", ""]

uploaded_files = set()
universal_files = set()
stats = {
    "pages_scraped": 0,
    "pdfs_found": 0,
    "pdfs_uploaded": 0,
    "pdfs_skipped_duplicate": 0,
    "pdfs_skipped_error": 0,
    "universal_files": 0,
}


def sanitize_filename(name):
    """Clean filename - remove trademark symbols and invalid chars"""
    name = name.replace('™', '').replace('®', '').replace('©', '')
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    if len(name) > 200:
        name = name[:200]
    return name


def strip_hash_code(filename):
    """
    Strip leading hash codes from filenames.
    Pattern: Long alphanumeric string (16+ chars) at the start followed by space/underscore
    Example: "6552b5706abc123 True Oak DEEP 2023" -> "True Oak DEEP 2023"
    """
    # Pattern: starts with hex-like string (16+ chars), then separator
    pattern = r'^[0-9a-fA-F]{16,}[\s_-]+'
    cleaned = re.sub(pattern, '', filename)
    return cleaned if cleaned else filename


def clean_filename_from_url(url):
    """Extract and clean filename from URL, stripping hash codes"""
    path = urlparse(url).path
    filename = unquote(path.split('/')[-1])
    filename = filename.replace('.pdf', '').replace('-', ' ').replace('_', ' ')
    filename = strip_hash_code(filename)
    return sanitize_filename(filename)


def find_context_heading(link, soup):
    """
    Find the section heading that provides context for this download link.
    Searches up the DOM tree for preceding H2, H3, H4 elements.
    """
    heading_text = None
    
    # Strategy 1: Look at preceding siblings in parent containers
    parent = link.parent
    max_levels = 10
    
    for _ in range(max_levels):
        if parent is None:
            break
        
        # Look for preceding headings
        for sibling in parent.find_all_previous(['h2', 'h3', 'h4'], limit=3):
            text = sibling.get_text(strip=True)
            if text and len(text) > 3 and text.lower() not in ['download', 'view', 'pdf']:
                heading_text = text
                break
        
        if heading_text:
            break
        
        # Check within parent div for headings
        for h in parent.find_all(['h2', 'h3', 'h4'], limit=1):
            text = h.get_text(strip=True)
            if text and len(text) > 3 and text.lower() not in ['download', 'view', 'pdf']:
                heading_text = text
                break
        
        if heading_text:
            break
        
        parent = parent.parent
    
    return heading_text


def generate_smart_filename(link, link_text, pdf_url, source_url, soup):
    """
    Generate a meaningful filename using context scraping rules.
    
    Rules:
    1. If link_text is generic ("Download", "View"), use section heading instead
    2. Strip hash codes from filenames
    3. Fall back to cleaned URL filename
    """
    # Determine if link text is generic/useless
    is_generic = not link_text or link_text.lower().strip() in GENERIC_LINK_TEXT
    
    # Get section heading context
    heading = find_context_heading(link, soup) if is_generic else None
    
    # Determine the final document name
    if is_generic and heading:
        # Use the section heading as the document name
        doc_name = sanitize_filename(heading)
    elif link_text and not is_generic:
        # Link text is meaningful, use it
        doc_name = sanitize_filename(link_text)
    else:
        # Fall back to cleaned URL filename
        doc_name = clean_filename_from_url(pdf_url)
    
    # Strip any hash codes from the doc name
    doc_name = strip_hash_code(doc_name)
    
    # If still empty or too short, use URL filename
    if not doc_name or len(doc_name) < 3:
        doc_name = clean_filename_from_url(pdf_url)
    
    return doc_name


def detect_profile_from_url(url, link_text):
    """Determine product profile from URL and link text"""
    url_lower = url.lower()
    text_lower = (link_text or "").lower()
    combined = f"{url_lower} {text_lower}"
    
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


def get_storage_folder(url, link_text, doc_name):
    """Determine the correct storage folder"""
    url_lower = url.lower()
    text_lower = (link_text or "").lower()
    doc_lower = (doc_name or "").lower()
    combined = f"{url_lower} {text_lower} {doc_lower}"
    
    # Check for universal resources first
    for keyword in UNIVERSAL_KEYWORDS:
        if keyword in combined:
            return "B_Enclosure/Roofing_Industries/00_General_Resources"
    
    # Check URL path for profile
    for keyword, folder in PROFILE_FOLDER_MAP.items():
        if keyword in url_lower:
            return f"B_Enclosure/Roofing_Industries/{folder}"
    
    return "B_Enclosure/Roofing_Industries/00_General_Resources"


def is_universal_file(doc_name):
    """Check if file should be treated as universal resource"""
    doc_lower = (doc_name or "").lower()
    for keyword in UNIVERSAL_KEYWORDS:
        if keyword in doc_lower:
            return True
    return False


def build_filename(profile_name, doc_name):
    """Build final filename with proper format"""
    if is_universal_file(doc_name):
        filename = f"Roofing Industries - Universal - {doc_name}.pdf"
    else:
        filename = f"Roofing Industries - {profile_name} - {doc_name}.pdf"
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
        
        if file_path in uploaded_files:
            print(f"  ⏭️  Already uploaded this session: {filename}")
            stats["pdfs_skipped_duplicate"] += 1
            return False
        
        if file_exists_in_storage(folder, filename):
            print(f"  ⏭️  Already exists in storage: {filename}")
            stats["pdfs_skipped_duplicate"] += 1
            uploaded_files.add(file_path)
            return False
        
        result = supabase.storage.from_(BUCKET_NAME).upload(
            file_path, content,
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


def scrape_page_for_pdfs(page_url):
    """Scrape a page for all PDF links with context"""
    full_url = urljoin(BASE_URL, page_url)
    print(f"\n📄 Scraping: {page_url}")
    
    try:
        response = requests.get(full_url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        pdf_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            if '.pdf' in href.lower():
                pdf_url = urljoin(full_url, href)
                link_text = link.get_text(strip=True)
                
                # Generate smart filename using context
                doc_name = generate_smart_filename(link, link_text, pdf_url, page_url, soup)
                
                pdf_links.append({
                    'url': pdf_url,
                    'link_text': link_text,
                    'doc_name': doc_name,
                    'source_url': page_url
                })
        
        # Deduplicate by URL
        seen_urls = set()
        unique_links = []
        for item in pdf_links:
            if item['url'] not in seen_urls:
                seen_urls.add(item['url'])
                unique_links.append(item)
        
        print(f"  Found {len(unique_links)} unique PDF links")
        stats["pdfs_found"] += len(unique_links)
        stats["pages_scraped"] += 1
        
        return unique_links
        
    except Exception as e:
        print(f"  ❌ Error scraping page: {str(e)[:100]}")
        return []


def download_and_upload_pdf(pdf_info):
    """Download PDF and upload with smart naming"""
    try:
        pdf_url = pdf_info['url']
        link_text = pdf_info['link_text']
        doc_name = pdf_info['doc_name']
        source_url = pdf_info['source_url']
        
        profile_name = detect_profile_from_url(source_url, doc_name)
        folder = get_storage_folder(source_url, link_text, doc_name)
        filename = build_filename(profile_name, doc_name)
        
        # Track universal files
        if is_universal_file(doc_name):
            universal_key = filename.lower()
            if universal_key in universal_files:
                print(f"  ⏭️  Universal file already processed: {filename}")
                stats["pdfs_skipped_duplicate"] += 1
                return False
            universal_files.add(universal_key)
            stats["universal_files"] += 1
        
        print(f"  📥 Downloading...")
        print(f"      Doc Name: {doc_name}")
        print(f"      Profile: {profile_name}")
        print(f"      Folder: {folder}")
        print(f"      Filename: {filename}")
        
        response = requests.get(pdf_url, timeout=60)
        response.raise_for_status()
        
        content = response.content
        if not content[:4] == b'%PDF':
            print(f"  ⚠️  Not a valid PDF")
            stats["pdfs_skipped_error"] += 1
            return False
        
        success = upload_to_supabase(content, folder, filename)
        if success:
            stats["pdfs_uploaded"] += 1
        
        return success
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:50]}")
        stats["pdfs_skipped_error"] += 1
        return False


def run_test_scrape():
    """Test scrape on True Oak Corrugate only"""
    print("=" * 70)
    print("🧪 ROOFING INDUSTRIES - TEST SCRAPE (True Oak Corrugate)")
    print("=" * 70)
    
    test_page = "/product/true-oak-corrugate"
    pdf_links = scrape_page_for_pdfs(test_page)
    
    print("\n" + "=" * 70)
    print("📋 FILES TO BE UPLOADED:")
    print("=" * 70)
    
    for i, pdf in enumerate(pdf_links, 1):
        profile = detect_profile_from_url(test_page, pdf['doc_name'])
        filename = build_filename(profile, pdf['doc_name'])
        print(f"\n{i}. {filename}")
        print(f"   Original link text: '{pdf['link_text']}'")
        print(f"   Context-derived name: '{pdf['doc_name']}'")
    
    return pdf_links


def run_full_scrape():
    """Run full catalog scrape"""
    print("=" * 70)
    print("🚀 ROOFING INDUSTRIES FULL CATALOG SCRAPER v2")
    print("=" * 70)
    print(f"\n📊 Target: {len(PRODUCT_PAGES)} pages")
    
    all_pdf_links = []
    
    print("\n" + "=" * 70)
    print("PHASE 1: COLLECTING PDF LINKS WITH CONTEXT")
    print("=" * 70)
    
    for page_url in PRODUCT_PAGES:
        links = scrape_page_for_pdfs(page_url)
        all_pdf_links.extend(links)
        time.sleep(0.5)
    
    # Deduplicate by URL
    seen_urls = set()
    unique_pdf_links = []
    for item in all_pdf_links:
        if item['url'] not in seen_urls:
            seen_urls.add(item['url'])
            unique_pdf_links.append(item)
    
    print(f"\n📊 Total unique PDFs found: {len(unique_pdf_links)}")
    
    print("\n" + "=" * 70)
    print("PHASE 2: DOWNLOADING AND UPLOADING PDFs")
    print("=" * 70)
    
    for i, pdf_info in enumerate(unique_pdf_links, 1):
        print(f"\n[{i}/{len(unique_pdf_links)}] Processing...")
        download_and_upload_pdf(pdf_info)
        time.sleep(0.3)
    
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
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        run_test_scrape()
    else:
        run_full_scrape()
