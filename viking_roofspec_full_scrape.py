#!/usr/bin/env python3
"""
Viking Roofspec Full Catalog Scraper
=====================================
Scrapes ALL technical documentation from vikingroofspec.co.nz
and uploads to Supabase storage with proper naming conventions.

Categories:
- Membrane Systems: Enviroclad TPO, Torch-On, Rubber, Liquid (SilCoat)
- Pitched Roofing: CertainTeed Shingles, EcoStar
- Warm Roofs: WarmSpan, WarmSpan², WarmRoof
- Specialized: Roof Garden (Green Roofs), Dec-K-ing (Decks)
- Universal Resources: Care & Maintenance, Warranties, Terms

Author: STRYDA Data Pipeline
Date: 2025-01
"""

import os
import re
import time
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote
from supabase import create_client
from dotenv import load_dotenv

load_dotenv("/app/backend-minimal/.env")

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
print(f"🔗 Supabase URL: {SUPABASE_URL[:30]}..." if SUPABASE_URL else "❌ No SUPABASE_URL")
BUCKET_NAME = "product-library"

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Base URL
BASE_URL = "https://www.vikingroofspec.co.nz"

# ============================================================================
# FOLDER MAPPING - Maps product categories to Supabase storage folders
# ============================================================================
FOLDER_MAPPING = {
    # Membrane Systems
    "enviroclad": "B_Enclosure/Viking_Roofspec/Enviroclad_TPO",
    "torch-on": "B_Enclosure/Viking_Roofspec/Torch_On_Membranes",
    "rubber": "B_Enclosure/Viking_Roofspec/Rubber_Membranes",
    "butyl": "B_Enclosure/Viking_Roofspec/Rubber_Membranes",
    "epiclad": "B_Enclosure/Viking_Roofspec/Rubber_Membranes",
    "epdm": "B_Enclosure/Viking_Roofspec/Rubber_Membranes",
    "silcoat": "B_Enclosure/Viking_Roofspec/Liquid_Membranes",
    
    # Pitched Roofing
    "certainteed": "B_Enclosure/Viking_Roofspec/Shingles_Asphalt",
    "shingle": "B_Enclosure/Viking_Roofspec/Shingles_Asphalt",
    "landmark": "B_Enclosure/Viking_Roofspec/Shingles_Asphalt",
    "highland": "B_Enclosure/Viking_Roofspec/Shingles_Asphalt",
    "presidential": "B_Enclosure/Viking_Roofspec/Shingles_Asphalt",
    "ecostar": "B_Enclosure/Viking_Roofspec/Shingles_Synthetic",
    "majestic": "B_Enclosure/Viking_Roofspec/Shingles_Synthetic",
    "seneca": "B_Enclosure/Viking_Roofspec/Shingles_Synthetic",
    
    # Warm Roofs / Insulated Systems
    "warmspan": "B_Enclosure/Viking_Roofspec/Warm_Roofs_Insulated",
    "warmroof": "B_Enclosure/Viking_Roofspec/Warm_Roofs_Insulated",
    "h1": "B_Enclosure/Viking_Roofspec/Warm_Roofs_Insulated",
    
    # Green Roofs
    "roof-garden": "B_Enclosure/Viking_Roofspec/Green_Roofs",
    "roof garden": "B_Enclosure/Viking_Roofspec/Green_Roofs",
    "green roof": "B_Enclosure/Viking_Roofspec/Green_Roofs",
    "anti-root": "B_Enclosure/Viking_Roofspec/Green_Roofs",
    
    # Decking Systems
    "dec-k-ing": "B_Enclosure/Viking_Roofspec/Decking_Systems",
    "decking": "B_Enclosure/Viking_Roofspec/Decking_Systems",
    "deck": "B_Enclosure/Viking_Roofspec/Decking_Systems",
    "buzon": "B_Enclosure/Viking_Roofspec/Decking_Systems",
    "pedestal": "B_Enclosure/Viking_Roofspec/Decking_Systems",
    "floating deck": "B_Enclosure/Viking_Roofspec/Decking_Systems",
    
    # Tanking (Below-ground waterproofing)
    "tanking": "B_Enclosure/Viking_Roofspec/Tanking_Systems",
}

# Universal Resource Keywords - files matching these go to 00_General_Resources
UNIVERSAL_KEYWORDS = [
    "care and maintenance",
    "master warranty",
    "sample warranty",
    "terms of trade",
    "terms and conditions",
    "substrate checklist",
    "membrane roofing code of practice",
    "code of practice",
    "general note",
    "index",
    "revit note",
]

# ============================================================================
# PRODUCT PAGE URLs TO SCRAPE
# ============================================================================
PRODUCT_PAGES = [
    # Membrane Roofing - Product Pages
    "/products-systems/membrane-roofing/enviroclad/",
    "/products-systems/membrane-roofing/torch-on/",
    "/products-systems/membrane-roofing/rubber-membranes/",
    "/products-systems/membrane-roofing/silcoat/",
    "/products-systems/membrane-roofing/warmspan/",
    "/products-systems/membrane-roofing/warmspan2/",
    "/products-systems/membrane-roofing/warmroof/",
    "/products-systems/membrane-roofing/roof-garden/",
    
    # Shingle and Tile Roofing
    "/products-systems/shingle-and-tile-roofing/certainteed-asphalt-shingles/",
    "/products-systems/shingle-and-tile-roofing/ecostar/",
    
    # Waterproof Decks
    "/products-systems/waterproof-decks/dec-k-ing/",
    "/products-systems/waterproof-decks/buzon-pedestals/",
    "/products-systems/waterproof-decks/floating-deck-systems/",
    
    # Tanking
    "/products-systems/tanking/",
    
    # Document Libraries - These have the most comprehensive PDF lists
    "/details-documents/membrane-roofing/enviroclad/",
    "/details-documents/membrane-roofing/torch-on/",
    "/details-documents/membrane-roofing/warmspan2/",
    "/details-documents/membrane-roofing/warmroof-with-enviroclad/",
    "/details-documents/membrane-roofing/warmroof-with-torch-on/",
    "/details-documents/membrane-roofing/warmspan-with-enviroclad/",
    "/details-documents/membrane-roofing/warmspan-with-torch-on/",
    "/details-documents/membrane-roofing/rubber-membranes/",
    "/details-documents/membrane-roofing/roof-garden/",
    "/details-documents/membrane-roofing/silcoat/",
    "/details-documents/shingle-and-tile-roofing/certainteed-asphalt-shingles/",
    "/details-documents/shingle-and-tile-roofing/ecostar/",
    "/details-documents/waterproof-decks/dec-k-ing/",
    "/details-documents/waterproof-decks/buzon-pedestals/",
    "/details-documents/tanking/",
]

# Track uploaded files for deduplication
uploaded_files = set()
universal_files = set()  # Track universal files to avoid duplicates

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
    # Remove or replace invalid characters
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    # Limit length
    if len(name) > 200:
        name = name[:200]
    return name


def detect_product_from_url_and_text(url, link_text):
    """Determine product category from URL path and link text"""
    url_lower = url.lower()
    text_lower = link_text.lower()
    combined = f"{url_lower} {text_lower}"
    
    # Check for specific products in order of specificity
    product_checks = [
        # Specific products first
        ("enviroclad", "Enviroclad"),
        ("torch-on", "Torch-On"),
        ("torch on", "Torch-On"),
        ("gemini", "Torch-On"),
        ("lybra", "Torch-On"),
        ("phoenix", "Torch-On"),
        ("halley", "Torch-On"),
        ("butylclad", "Rubber"),
        ("epiclad", "Rubber"),
        ("rubber", "Rubber"),
        ("epdm", "Rubber"),
        ("silcoat", "SilCoat"),
        ("certainteed", "CertainTeed"),
        ("shingle", "CertainTeed"),
        ("landmark", "CertainTeed"),
        ("highland slate", "CertainTeed"),
        ("presidential", "CertainTeed"),
        ("ecostar", "EcoStar"),
        ("majestic", "EcoStar"),
        ("seneca", "EcoStar"),
        ("warmspan2", "WarmSpan2"),
        ("warmspan²", "WarmSpan2"),
        ("warmspan", "WarmSpan"),
        ("warmroof", "WarmRoof"),
        ("roof-garden", "Roof Garden"),
        ("roof garden", "Roof Garden"),
        ("anti-root", "Roof Garden"),
        ("dec-k-ing", "Dec-K-ing"),
        ("decking", "Dec-K-ing"),
        ("buzon", "Buzon"),
        ("pedestal", "Buzon"),
        ("floating deck", "Floating Deck"),
        ("tanking", "Tanking"),
    ]
    
    for keyword, product in product_checks:
        if keyword in combined:
            return product
    
    return "General"


def get_storage_folder(url, link_text):
    """Determine the correct storage folder based on URL and link text"""
    url_lower = url.lower()
    text_lower = link_text.lower()
    combined = f"{url_lower} {text_lower}"
    
    # Check for universal resources first
    for keyword in UNIVERSAL_KEYWORDS:
        if keyword in text_lower:
            return "B_Enclosure/Viking_Roofspec/00_General_Resources"
    
    # Check URL path for product category (most reliable)
    # Enviroclad files
    if "/enviroclad" in url_lower or "vik_env" in text_lower or "env_" in text_lower:
        return "B_Enclosure/Viking_Roofspec/Enviroclad_TPO"
    
    # Torch-On files
    if "/torch-on" in url_lower or "torch" in text_lower or "gemini" in text_lower or "lybra" in text_lower or "phoenix" in text_lower or "halley" in text_lower:
        return "B_Enclosure/Viking_Roofspec/Torch_On_Membranes"
    
    # Rubber membranes
    if "/rubber" in url_lower or "butyl" in text_lower or "epiclad" in text_lower or "epdm" in text_lower:
        return "B_Enclosure/Viking_Roofspec/Rubber_Membranes"
    
    # SilCoat
    if "/silcoat" in url_lower or "silcoat" in text_lower:
        return "B_Enclosure/Viking_Roofspec/Liquid_Membranes"
    
    # WarmSpan2 (check before WarmSpan to avoid false matches)
    if "warmspan2" in url_lower or "warmspan²" in url_lower or "warmspan2" in text_lower or "h1-roof" in text_lower or "h1 roof" in text_lower:
        return "B_Enclosure/Viking_Roofspec/Warm_Roofs_Insulated"
    
    # WarmSpan
    if "/warmspan" in url_lower or "warmspan" in text_lower:
        return "B_Enclosure/Viking_Roofspec/Warm_Roofs_Insulated"
    
    # WarmRoof
    if "/warmroof" in url_lower or "warmroof" in text_lower:
        return "B_Enclosure/Viking_Roofspec/Warm_Roofs_Insulated"
    
    # Roof Garden / Green Roofs
    if "/roof-garden" in url_lower or "roof garden" in text_lower or "anti-root" in text_lower:
        return "B_Enclosure/Viking_Roofspec/Green_Roofs"
    
    # CertainTeed Shingles
    if "/certainteed" in url_lower or "certainteed" in text_lower or "landmark" in text_lower or "highland" in text_lower or "presidential" in text_lower:
        return "B_Enclosure/Viking_Roofspec/Shingles_Asphalt"
    
    # EcoStar
    if "/ecostar" in url_lower or "ecostar" in text_lower or "majestic" in text_lower or "seneca" in text_lower:
        return "B_Enclosure/Viking_Roofspec/Shingles_Synthetic"
    
    # Dec-K-ing / Decking
    if "/dec-k-ing" in url_lower or "dec-k-ing" in text_lower or "decking" in text_lower:
        return "B_Enclosure/Viking_Roofspec/Decking_Systems"
    
    # Buzon / Pedestals
    if "/buzon" in url_lower or "buzon" in text_lower or "pedestal" in text_lower:
        return "B_Enclosure/Viking_Roofspec/Decking_Systems"
    
    # Floating Deck
    if "/floating-deck" in url_lower or "floating deck" in text_lower:
        return "B_Enclosure/Viking_Roofspec/Decking_Systems"
    
    # Tanking
    if "/tanking" in url_lower or "tanking" in text_lower:
        return "B_Enclosure/Viking_Roofspec/Tanking_Systems"
    
    # Default folder
    return "B_Enclosure/Viking_Roofspec/00_General_Resources"


def is_universal_file(link_text):
    """Check if file should be treated as universal resource"""
    text_lower = link_text.lower()
    for keyword in UNIVERSAL_KEYWORDS:
        if keyword in text_lower:
            return True
    return False


def generate_filename(url, link_text, product_name):
    """Generate standardized filename"""
    # Clean link text for use in filename
    clean_text = sanitize_filename(link_text)
    
    # Check if universal
    if is_universal_file(link_text):
        filename = f"Viking Roofspec - Universal - {clean_text}.pdf"
    else:
        filename = f"Viking Roofspec - {product_name} - {clean_text}.pdf"
    
    return sanitize_filename(filename)


def file_exists_in_storage(folder, filename):
    """Check if file already exists in Supabase storage"""
    try:
        # List files in folder
        result = supabase.storage.from_(BUCKET_NAME).list(folder)
        existing_files = [f['name'] for f in result] if result else []
        return filename in existing_files
    except Exception as e:
        # If folder doesn't exist, file doesn't exist
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
        # Determine product and folder
        product_name = detect_product_from_url_and_text(pdf_url, link_text)
        folder = get_storage_folder(pdf_url, link_text)
        filename = generate_filename(pdf_url, link_text, product_name)
        
        # Handle universal file deduplication
        if is_universal_file(link_text):
            # Create unique key for universal files
            universal_key = filename.lower()
            if universal_key in universal_files:
                print(f"  ⏭️  Universal file already processed: {filename}")
                stats["pdfs_skipped_duplicate"] += 1
                return False
            universal_files.add(universal_key)
            stats["universal_files"] += 1
        
        print(f"  📥 Downloading: {link_text[:60]}...")
        print(f"      → Folder: {folder}")
        print(f"      → Filename: {filename}")
        
        # Download PDF
        response = requests.get(pdf_url, timeout=60, stream=True)
        response.raise_for_status()
        
        # Get content
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
        
        # Find all links
        pdf_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Check if it's a PDF link
            if '.pdf' in href.lower():
                # Get absolute URL
                pdf_url = urljoin(full_url, href)
                
                # Get link text
                link_text = link.get_text(strip=True)
                if not link_text:
                    # Try to get from title or alt
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
    print("🚀 VIKING ROOFSPEC FULL CATALOG SCRAPER")
    print("=" * 70)
    print(f"\n📊 Target: {len(PRODUCT_PAGES)} pages to scrape")
    print(f"📁 Destination bucket: {BUCKET_NAME}")
    print(f"📂 Base folder: B_Enclosure/Viking_Roofspec/\n")
    
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
