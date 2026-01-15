#!/usr/bin/env python3
"""
Steel & Tube Roofing & Cladding Bulk Ingestion
Downloads PDFs from all product pages and uploads to Supabase
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
BASE_STORAGE_PATH = 'B_Enclosure/Steel_and_Tube'

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Steel & Tube Products
PRODUCTS = [
    # Residential & Commercial
    {"url": "https://steelandtube.co.nz/products/custom-orb", "name": "Custom Orb", "folder": "Custom_Orb"},
    {"url": "https://steelandtube.co.nz/products/six-rib", "name": "Six Rib", "folder": "Six_Rib"},
    {"url": "https://steelandtube.co.nz/products/st963", "name": "ST963", "folder": "ST963"},
    {"url": "https://steelandtube.co.nz/products/st900", "name": "ST900", "folder": "ST900"},
    {"url": "https://steelandtube.co.nz/products/st7", "name": "ST7", "folder": "ST7"},
    {"url": "https://steelandtube.co.nz/products/trimform", "name": "Trimform", "folder": "Trimform"},
    {"url": "https://steelandtube.co.nz/products/trimline", "name": "Trimline", "folder": "Trimline"},
    {"url": "https://steelandtube.co.nz/products/kliplok", "name": "Kliplok", "folder": "Kliplok"},
    {"url": "https://steelandtube.co.nz/products/legacy", "name": "Legacy", "folder": "Legacy"},
    {"url": "https://steelandtube.co.nz/products/plumbdek", "name": "Plumbdek", "folder": "Plumbdek"},
    # Tray Roofing
    {"url": "https://steelandtube.co.nz/products/qbt450", "name": "QBT450", "folder": "QBT450"},
    # Rainwater & Fascia
    {"url": "https://steelandtube.co.nz/products/multiline-fascia", "name": "Multiline Fascia", "folder": "Multiline_Fascia"},
    {"url": "https://steelandtube.co.nz/products/rainwater-systems", "name": "Rainwater Systems", "folder": "Rainwater_Systems"},
]


def clean_filename(text):
    """Clean text for filename"""
    cleaned = text.replace('/', '-').replace('\\', '-')
    cleaned = cleaned.replace(':', '-').replace('*', '').replace('?', '')
    cleaned = cleaned.replace('"', '').replace('<', '').replace('>', '')
    cleaned = cleaned.replace('|', '-').replace('+', ' ')
    cleaned = cleaned.replace('%20', ' ').replace('_', ' ')
    # Remove common generic prefixes
    cleaned = re.sub(r'^PTS[_\s]*', 'Product Technical Statement ', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'^IG[_\s]*', 'Installation Guide ', cleaned, flags=re.IGNORECASE)
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
        response = requests.get(url, timeout=30, headers=headers)
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
        print(f"   ⚠️ Upload error: {e}")
        return False


def scrape_product_page(url):
    """Scrape a product page to find PDF links"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=30, headers=headers)
        if response.status_code != 200:
            print(f"   ⚠️ HTTP {response.status_code}")
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
            
            # Extract filename for link text
            filename = pdf_url.split('/')[-1]
            filename = filename.replace('.pdf', '').replace('+', ' ').replace('%20', ' ')
            
            # Try to find the link text from HTML
            # Look for anchor text near the PDF link
            link_pattern = rf'>\s*([^<]+)\s*</a>\s*.*?{re.escape(filename.split("/")[-1])}'
            link_match = re.search(link_pattern, html, re.IGNORECASE | re.DOTALL)
            if link_match:
                filename = link_match.group(1).strip()
            
            pdfs.append((filename, pdf_url))
        
        return pdfs
    except Exception as e:
        print(f"   ⚠️ Scrape error: {e}")
        return []


def process_product(product):
    """Process a single product"""
    name = product['name']
    folder = product['folder']
    url = product['url']
    
    print(f"\n{'='*60}")
    print(f"📦 Processing: {name}")
    print(f"   URL: {url}")
    print(f"   Folder: {folder}")
    
    # Scrape the page for PDF links
    pdfs = scrape_product_page(url)
    print(f"   Found {len(pdfs)} PDF links")
    
    if not pdfs:
        print(f"   ⚠️ No PDFs found")
        return 0
    
    # Download and upload each PDF
    successful = 0
    uploaded_urls = set()  # Track duplicates
    
    for link_text, pdf_url in pdfs:
        if pdf_url in uploaded_urls:
            continue
        uploaded_urls.add(pdf_url)
        
        filename = create_filename(name, link_text)
        
        # Download
        content = download_pdf(pdf_url)
        if not content:
            continue
        
        # Upload
        if upload_to_supabase(content, folder, filename):
            successful += 1
            print(f"   ✅ {link_text[:45]}...")
    
    print(f"   📊 Uploaded: {successful}")
    return successful


def main():
    print("=" * 60)
    print("🔩 STEEL & TUBE - ROOFING & CLADDING INGESTION")
    print("=" * 60)
    print(f"📁 Storage: {BUCKET}/{BASE_STORAGE_PATH}/")
    print(f"📋 Products to process: {len(PRODUCTS)}")
    
    results = []
    total_files = 0
    
    for i, product in enumerate(PRODUCTS, 1):
        print(f"\n[{i}/{len(PRODUCTS)}]", end="")
        count = process_product(product)
        results.append((product['name'], count))
        total_files += count
        time.sleep(1)
    
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
        for folder in folders:
            if folder.get('id') is None:
                folder_name = folder['name']
                files = supabase.storage.from_(BUCKET).list(f"{BASE_STORAGE_PATH}/{folder_name}")
                pdf_count = len([f for f in files if f['name'].endswith('.pdf')])
                print(f"   {folder_name}: {pdf_count} PDFs")
    except Exception as e:
        print(f"   ⚠️ Could not verify: {e}")
    
    print(f"\n✅ Steel & Tube ingestion complete!")
    return total_files


if __name__ == '__main__':
    main()
