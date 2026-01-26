#!/usr/bin/env python3
"""
Dimond Rainwater Systems - Final Batch
Downloads PDFs from all rainwater product pages and uploads to single folder
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
STORAGE_PATH = 'B_Enclosure/Dimond_Roofing/Rainwater_Systems'

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Rainwater products
RAINWATER_PRODUCTS = [
    {"url": "https://www.dimond.co.nz/products/box125", "name": "Box 125"},
    {"url": "https://www.dimond.co.nz/products/box-175", "name": "Box 175"},
    {"url": "https://www.dimond.co.nz/products/box-300", "name": "Box 300"},
    {"url": "https://www.dimond.co.nz/products/deep-quad", "name": "Deep Quad"},
    {"url": "https://www.dimond.co.nz/products/quad-si", "name": "Quad SI"},
    {"url": "https://www.dimond.co.nz/products/150-half-round", "name": "150 Half Round"},
    {"url": "https://www.dimond.co.nz/products/200-half-round", "name": "200 Half Round"},
    {"url": "https://www.dimond.co.nz/products/downpipes", "name": "Downpipes"},
    {"url": "https://www.dimond.co.nz/products/rainwater-heads", "name": "Rainwater Heads"},
]


def clean_filename(text):
    """Clean text for filename"""
    cleaned = text.replace('/', '-').replace('\\', '-')
    cleaned = cleaned.replace(':', '-').replace('*', '').replace('?', '')
    cleaned = cleaned.replace('"', '').replace('<', '').replace('>', '')
    cleaned = cleaned.replace('|', '-').replace('+', ' ')
    cleaned = cleaned.replace('%20', ' ')
    return ' '.join(cleaned.split())


def create_filename(product_name, link_text):
    """Create standardized filename"""
    clean_text = clean_filename(link_text)
    return f"Dimond Roofing - {product_name} - {clean_text}.pdf"


def download_pdf(url):
    """Download PDF content"""
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200 and len(response.content) > 1000:
            return response.content
        return None
    except:
        return None


def upload_to_supabase(content, filename):
    """Upload PDF to Supabase"""
    storage_path = f"{STORAGE_PATH}/{filename}"
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
            if not pdf_url.startswith('http'):
                pdf_url = urljoin(url, pdf_url)
            
            # Extract filename for link text
            filename = pdf_url.split('/')[-1]
            filename = filename.replace('.pdf', '').replace('+', ' ').replace('%20', ' ')
            filename = filename.replace('_', ' ')
            
            pdfs.append((filename, pdf_url))
        
        return pdfs
    except Exception as e:
        print(f"   ⚠️ Scrape error: {e}")
        return []


def main():
    print("=" * 60)
    print("☔ DIMOND RAINWATER SYSTEMS - FINAL BATCH")
    print("=" * 60)
    print(f"📁 Storage: {BUCKET}/{STORAGE_PATH}/")
    print(f"📋 Products to process: {len(RAINWATER_PRODUCTS)}")
    
    all_pdfs = {}  # Track unique PDFs across products
    
    for i, product in enumerate(RAINWATER_PRODUCTS, 1):
        url = product['url']
        name = product['name']
        
        print(f"\n[{i}/{len(RAINWATER_PRODUCTS)}] 📦 {name}")
        print(f"    URL: {url}")
        
        # Scrape the page
        pdfs = scrape_product_page(url)
        print(f"    Found {len(pdfs)} PDF links")
        
        # Process each PDF
        for link_text, pdf_url in pdfs:
            filename = create_filename(name, link_text)
            
            # Skip if we've already processed this URL
            if pdf_url in all_pdfs:
                continue
            
            all_pdfs[pdf_url] = filename
            
            # Download
            content = download_pdf(pdf_url)
            if not content:
                continue
            
            # Upload
            if upload_to_supabase(content, filename):
                print(f"    ✅ {link_text[:45]}...")
        
        time.sleep(0.5)
    
    # Final verification
    print("\n" + "=" * 60)
    print("📊 VERIFICATION")
    print("=" * 60)
    
    files = supabase.storage.from_(BUCKET).list(STORAGE_PATH)
    pdf_files = [f for f in files if f['name'].endswith('.pdf')]
    
    print(f"\n✅ RAINWATER SYSTEMS COMPLETE")
    print(f"   Total unique PDFs uploaded: {len(pdf_files)}")
    print(f"   Storage path: {BUCKET}/{STORAGE_PATH}/")
    
    print(f"\n📋 Files by product:")
    # Count files by product name
    product_counts = {}
    for f in pdf_files:
        for product in RAINWATER_PRODUCTS:
            if product['name'] in f['name']:
                product_counts[product['name']] = product_counts.get(product['name'], 0) + 1
                break
    
    for name, count in sorted(product_counts.items()):
        print(f"   - {name}: {count} PDFs")
    
    return len(pdf_files)


if __name__ == '__main__':
    main()
