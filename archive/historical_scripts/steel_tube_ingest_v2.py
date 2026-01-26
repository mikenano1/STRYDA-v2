#!/usr/bin/env python3
"""
Steel & Tube Roofing & Cladding Bulk Ingestion - V2
Uses correct URL patterns discovered from site crawl
"""

import os
import sys
import re
import requests
import time
from urllib.parse import urljoin, unquote

sys.path.insert(0, '/app/backend-minimal')

from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

from supabase import create_client

# Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
BUCKET = 'product-library'
BASE_STORAGE_PATH = 'B_Enclosure/Steel_and_Tube'

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Steel & Tube Products with correct URLs (discovered from crawl)
PRODUCTS = [
    # Roofing & Cladding Profiles
    {"specifier_url": "https://steelandtube.co.nz/specifiers/custom-orb", "bimspec_url": "https://steelandtube.co.nz/bimspec/custom-orb", "name": "Custom Orb", "folder": "Custom_Orb"},
    {"specifier_url": "https://steelandtube.co.nz/six-rib", "bimspec_url": "https://steelandtube.co.nz/bimspec/six-rib", "name": "Six Rib", "folder": "Six_Rib"},
    {"specifier_url": "https://steelandtube.co.nz/st963", "bimspec_url": "https://steelandtube.co.nz/bimspec/st963", "name": "ST963", "folder": "ST963"},
    {"specifier_url": "https://steelandtube.co.nz/st900", "bimspec_url": "https://steelandtube.co.nz/bimspec/st900", "name": "ST900", "folder": "ST900"},
    {"specifier_url": "https://steelandtube.co.nz/st7", "bimspec_url": "https://steelandtube.co.nz/bimspec/st7", "name": "ST7", "folder": "ST7"},
    {"specifier_url": "https://steelandtube.co.nz/trimform", "bimspec_url": "https://steelandtube.co.nz/bimspec/trimform", "name": "Trimform", "folder": "Trimform"},
    {"specifier_url": "https://steelandtube.co.nz/trimline", "bimspec_url": "https://steelandtube.co.nz/bimspec/trimline", "name": "Trimline", "folder": "Trimline"},
    {"specifier_url": "https://steelandtube.co.nz/kliplok", "bimspec_url": "https://steelandtube.co.nz/bimspec/kliplok", "name": "Kliplok", "folder": "Kliplok"},
    {"specifier_url": "https://steelandtube.co.nz/legacy", "bimspec_url": "https://steelandtube.co.nz/bimspec/legacy", "name": "Legacy", "folder": "Legacy"},
    {"specifier_url": "https://steelandtube.co.nz/plumbdek", "bimspec_url": "https://steelandtube.co.nz/bimspec/plumbdek", "name": "Plumbdek", "folder": "Plumbdek"},
    # Tray Roofing
    {"specifier_url": "https://steelandtube.co.nz/specifiers/qbt450%E2%84%A2", "bimspec_url": "https://steelandtube.co.nz/bimspec/qbt450", "name": "QBT450", "folder": "QBT450"},
    # Additional profiles from crawl
    {"specifier_url": "https://steelandtube.co.nz/hi-rib", "bimspec_url": "https://steelandtube.co.nz/bimspec/hi-rib", "name": "Hi Rib", "folder": "Hi_Rib"},
    {"specifier_url": "https://steelandtube.co.nz/STC900", "bimspec_url": "https://steelandtube.co.nz/bimspec/STC900", "name": "STC900", "folder": "STC900"},
    {"specifier_url": "https://steelandtube.co.nz/trimklad", "bimspec_url": "https://steelandtube.co.nz/bimspec/trimklad", "name": "Trimklad", "folder": "Trimklad"},
    # Rainwater & Fascia
    {"specifier_url": "https://steelandtube.co.nz/spouting-fascia-rainwater-0", "bimspec_url": "https://steelandtube.co.nz/bimspec/rainwater-and-flashings", "name": "Rainwater and Fascia", "folder": "Rainwater_Fascia"},
]

# Known PDF URLs from crawl (common resources)
COMMON_RESOURCES = [
    ("Colorsteel Reflectivity Bulletin", "https://steelandtube.co.nz/sites/default/files/st_file_list/BSS0273-Colorsteel-Reflectivity-Bulletin2.pdf"),
    ("Colorsteel Photovoltaics Bulletin", "https://steelandtube.co.nz/sites/default/files/st_file_list/BSS0298-Photovoltaics-Bulletin.pdf"),
    ("Colorsteel Fire Testing", "https://steelandtube.co.nz/sites/default/files/st_file_list/Fire-Testing-Bulletin.pdf"),
    ("Colorsteel Roofing Installers Guide", "https://steelandtube.co.nz/sites/default/files/st_file_list/Roofing_installers-guide.pdf"),
    ("S&T Roofing Cover Chart", "https://steelandtube.co.nz/sites/default/files/st_file_list/S%26T-Roofing_Cover_Chart.pdf"),
    ("S&T Spring Curving Formula", "https://steelandtube.co.nz/sites/default/files/st_file_list/S%26T_Spring_Curving_Formula.pdf"),
    ("Specifiers Guide", "https://steelandtube.co.nz/sites/default/files/st_file_list/Specifiers_Guide.pdf"),
    ("Topglass Guide 2017", "https://steelandtube.co.nz/sites/default/files/st_file_list/Topglass_Guide_2017.pdf"),
    ("Zinc Run Off From Roofing", "https://steelandtube.co.nz/sites/default/files/st_file_list/Zinc_run_off_from_roofing.pdf"),
    ("Roofing Flashing Order Sheet", "https://steelandtube.co.nz/sites/default/files/Steel%20%26%20Tube%20Roofing%20Flashing%20Order%20Pad_2024_v5_Interactive.pdf"),
    ("Eco Choice Certificate - Flat & Long", "https://steelandtube.co.nz/sites/default/files/attachments/Eco%20Choice%20NZ%20Steel-EC-41-Certificate-May-26.pdf"),
    ("Eco Choice Certificate - Pre-Painted", "https://steelandtube.co.nz/sites/default/files/attachments/Eco%20Choice%20NZ%20Steel-EC-57-Certificate-May-26.pdf"),
]


def clean_filename(text):
    """Clean text for filename"""
    cleaned = unquote(text)
    cleaned = cleaned.replace('/', '-').replace('\\', '-')
    cleaned = cleaned.replace(':', '-').replace('*', '').replace('?', '')
    cleaned = cleaned.replace('"', '').replace('<', '').replace('>', '')
    cleaned = cleaned.replace('|', '-').replace('+', ' ').replace('_', ' ')
    cleaned = cleaned.replace('%20', ' ').replace('&', 'and')
    # Make more readable
    cleaned = re.sub(r'\.pdf$', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'^Steel\s*(and|&)\s*Tube\s*', '', cleaned, flags=re.IGNORECASE)
    return ' '.join(cleaned.split())


def create_filename(product_name, link_text):
    """Create standardized filename"""
    clean_text = clean_filename(link_text)
    return f"Steel and Tube - {product_name} - {clean_text}.pdf"


def download_pdf(url):
    """Download PDF content"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=30, headers=headers, allow_redirects=True)
        if response.status_code == 200 and len(response.content) > 1000:
            # Verify it's actually a PDF
            if response.content[:4] == b'%PDF':
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
        if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
            return True  # Already uploaded
        print(f"   ⚠️ Upload error: {e}")
        return False


def scrape_page_for_pdfs(url):
    """Scrape a page for all PDF links"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=30, headers=headers)
        if response.status_code != 200:
            return []
        
        html = response.text
        pdfs = []
        
        # Find all PDF links - multiple patterns
        patterns = [
            r'href=["\']([^"\']*\.pdf)["\']',
            r'(https?://[^"\'>\s]+\.pdf)',
            r'data-href=["\']([^"\']*\.pdf)["\']',
        ]
        
        all_urls = set()
        for pattern in patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            all_urls.update(matches)
        
        for pdf_url in all_urls:
            if not pdf_url.startswith('http'):
                pdf_url = urljoin(url, pdf_url)
            
            # Extract a readable name from URL
            filename = unquote(pdf_url.split('/')[-1])
            filename = filename.replace('.pdf', '').replace('_', ' ').replace('-', ' ')
            
            # Skip external Colorsteel links (we handle common resources separately)
            if 'colorsteel.co.nz' in pdf_url or 'ctfassets.net' in pdf_url:
                continue
            
            pdfs.append((filename, pdf_url))
        
        return pdfs
    except Exception as e:
        print(f"   ⚠️ Scrape error: {e}")
        return []


def process_product(product):
    """Process a single product"""
    name = product['name']
    folder = product['folder']
    specifier_url = product['specifier_url']
    bimspec_url = product.get('bimspec_url', '')
    
    print(f"\n{'='*60}")
    print(f"📦 Processing: {name}")
    print(f"   Specifier: {specifier_url}")
    
    all_pdfs = {}
    
    # Scrape specifier page
    pdfs = scrape_page_for_pdfs(specifier_url)
    for link_text, pdf_url in pdfs:
        all_pdfs[pdf_url] = link_text
    print(f"   Found {len(pdfs)} PDFs on specifier page")
    
    # Scrape BIM page if available
    if bimspec_url:
        pdfs = scrape_page_for_pdfs(bimspec_url)
        for link_text, pdf_url in pdfs:
            if pdf_url not in all_pdfs:
                all_pdfs[pdf_url] = link_text
        print(f"   Found {len(pdfs)} PDFs on BIM page")
    
    # Download and upload each PDF
    successful = 0
    for pdf_url, link_text in all_pdfs.items():
        filename = create_filename(name, link_text)
        
        content = download_pdf(pdf_url)
        if not content:
            continue
        
        if upload_to_supabase(content, folder, filename):
            successful += 1
            print(f"   ✅ {link_text[:45]}...")
    
    print(f"   📊 Uploaded: {successful}")
    return successful


def upload_common_resources():
    """Upload common resources to a General folder"""
    print(f"\n{'='*60}")
    print(f"📦 Processing: Common Resources")
    
    successful = 0
    for name, url in COMMON_RESOURCES:
        filename = create_filename("General", name)
        content = download_pdf(url)
        if not content:
            continue
        
        if upload_to_supabase(content, "General_Resources", filename):
            successful += 1
            print(f"   ✅ {name[:45]}...")
    
    print(f"   📊 Uploaded: {successful}")
    return successful


def main():
    print("=" * 60)
    print("🔩 STEEL & TUBE - ROOFING & CLADDING INGESTION V2")
    print("=" * 60)
    print(f"📁 Storage: {BUCKET}/{BASE_STORAGE_PATH}/")
    print(f"📋 Products to process: {len(PRODUCTS)}")
    
    results = []
    total_files = 0
    
    # Process common resources first
    count = upload_common_resources()
    results.append(("General Resources", count))
    total_files += count
    
    # Process each product
    for i, product in enumerate(PRODUCTS, 1):
        print(f"\n[{i}/{len(PRODUCTS)}]", end="")
        count = process_product(product)
        results.append((product['name'], count))
        total_files += count
        time.sleep(0.5)
    
    # Final report
    print("\n" + "=" * 60)
    print("📊 FINAL REPORT")
    print("=" * 60)
    print(f"\n{'Product':<30} {'Files':>8}")
    print("-" * 40)
    for name, count in results:
        status = "✅" if count > 0 else "⚠️"
        print(f"{status} {name:<28} {count:>8}")
    
    print("-" * 40)
    print(f"{'TOTAL':<30} {total_files:>8}")
    
    # Verify in storage
    print("\n📂 STORAGE VERIFICATION:")
    try:
        folders = supabase.storage.from_(BUCKET).list(BASE_STORAGE_PATH)
        total_verified = 0
        for folder in folders:
            if folder.get('id') is None:
                folder_name = folder['name']
                files = supabase.storage.from_(BUCKET).list(f"{BASE_STORAGE_PATH}/{folder_name}")
                pdf_count = len([f for f in files if f['name'].endswith('.pdf')])
                total_verified += pdf_count
                print(f"   {folder_name}: {pdf_count} PDFs")
        print(f"\n   TOTAL VERIFIED: {total_verified} PDFs")
    except Exception as e:
        print(f"   ⚠️ Could not verify: {e}")
    
    print(f"\n✅ Steel & Tube ingestion complete!")
    return total_files


if __name__ == '__main__':
    main()
