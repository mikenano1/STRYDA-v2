#!/usr/bin/env python3
"""
Steel & Tube Structural Products - Smart Sorting Ingestion
ComFlor and HST Purlins into A_Structure with intelligent folder routing
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
BASE_STORAGE_PATH = 'A_Structure/Steel_and_Tube'

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Known PDFs from Steel & Tube ComFlor and Purlins pages
KNOWN_PDFS = {
    # ComFlor Product Guides
    "ComFlor_60": [
        ("ComFlor 60 Product Guide", "https://steelandtube.co.nz/sites/default/files/catalogues/Comflor60_PG-Dec2016-01_0.pdf"),
    ],
    "ComFlor_80": [
        ("ComFlor 80 Product Guide", "https://steelandtube.co.nz/sites/default/files/catalogues/Comflor80_PG-Dec2016-01.pdf"),
    ],
    "ComFlor_210": [
        ("ComFlor 210 Product Guide", "https://steelandtube.co.nz/sites/default/files/catalogues/Comflor210_PG-Dec2016-01.pdf"),
    ],
    "ComFlor_SR": [
        ("ComFlor SR Fire Test Report", "https://steelandtube.co.nz/sites/default/files/ComFlor%20SR%20Fire%20Test%20Report%20Exova%2014%20May%202018.pdf"),
    ],
    # General/Universal ComFlor docs
    "00_General_Resources": [
        ("ComFlor Residential Building Durability Statement", "https://steelandtube.co.nz/sites/default/files/ComFlor%20Residential%20Building%20Durability%20Statement_Jan%202023.pdf"),
        ("ComFlor Commercial Carpark Durability Statement", "https://steelandtube.co.nz/sites/default/files/ComFlor%20Commercial%20Carpark%20Durability%20Statement_Jan%202023.pdf"),
        ("ComFlor Environmental Choice Certificate", "https://steelandtube.co.nz/sites/default/files/ComFlor%20Environmental%20Choice%20Certificate%20Mar23.pdf"),
        ("Hegley Acoustic Report April 2019", "https://steelandtube.co.nz/sites/default/files/18231%20Comflor%20Performance%20Hegley%202019%2004%2010.pdf"),
        ("Composite Slabs Best Practice Design Construction", "https://steelandtube.co.nz/sites/default/files/P300-TP13-Composite-Flooring%20%281%29.pdf"),
        ("SSC Gold Certification 2023-2024", "https://steelandtube.co.nz/sites/default/files/attachments/SSC%20Gold%20Certification%20-%202023-2024.pdf"),
    ],
    # HST Purlins
    "HST_Purlins": [
        ("GALVSTEEL G250 Steel", "https://www.nzsteel.co.nz/assets/Uploads/Files/GALVSTEEL-G250-Steel.pdf"),
        ("GALVSTEEL G450 Steel", "https://www.nzsteel.co.nz/assets/Uploads/Technical-Resources/GALVSTEEL-G450-Steel.pdf"),
        ("GALVSTEEL G500 Steel", "https://www.nzsteel.co.nz/assets/media/94839/GALVSTEEL%C2%AE%20G500%20steel.pdf"),
    ],
}

# URLs to scrape for additional PDFs
SCRAPE_URLS = [
    ("ComFlor_60", "https://steelandtube.co.nz/comflor-60"),
    ("ComFlor_80", "https://steelandtube.co.nz/comflor-80"),
    ("ComFlor_210", "https://steelandtube.co.nz/comflor-210"),
    ("ComFlor_SR", "https://steelandtube.co.nz/comflor-sr"),
    ("HST_Purlins", "https://steelandtube.co.nz/specifiers/hst-purlins-girts"),
    ("HST_Top_Hats", "https://steelandtube.co.nz/hst-top-hats"),
]

# Keywords for smart routing
UNIVERSAL_KEYWORDS = ['warranty', 'terms', 'coating', 'maintenance', 'transport', 
                      'durability', 'environmental', 'certificate', 'acoustic', 'hegley',
                      'best practice', 'ssc gold']
PRODUCT_KEYWORDS = ['span', 'design', 'installation', 'technical', 'datasheet', 
                    'product guide', 'fire test', 'load table']


def clean_filename(text):
    """Clean text for filename"""
    cleaned = unquote(text)
    cleaned = cleaned.replace('/', '-').replace('\\', '-')
    cleaned = cleaned.replace(':', '-').replace('*', '').replace('?', '')
    cleaned = cleaned.replace('"', '').replace('<', '').replace('>', '')
    cleaned = cleaned.replace('|', '-').replace('+', ' ').replace('_', ' ')
    cleaned = cleaned.replace('%20', ' ').replace('&', 'and')
    cleaned = re.sub(r'\.pdf$', '', cleaned, flags=re.IGNORECASE)
    return ' '.join(cleaned.split())


def determine_folder(link_text, default_folder):
    """Smart routing based on link text keywords"""
    link_lower = link_text.lower()
    
    # Check for universal/general keywords
    for keyword in UNIVERSAL_KEYWORDS:
        if keyword in link_lower:
            return "00_General_Resources"
    
    # Default to the product folder
    return default_folder


def create_filename(folder, link_text):
    """Create standardized filename based on folder"""
    clean_text = clean_filename(link_text)
    
    if folder == "00_General_Resources":
        return f"Steel and Tube - Universal - {clean_text}.pdf"
    else:
        product_name = folder.replace('_', ' ')
        return f"Steel and Tube - {product_name} - {clean_text}.pdf"


def download_pdf(url):
    """Download PDF content"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=30, headers=headers, allow_redirects=True)
        if response.status_code == 200 and len(response.content) > 1000:
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
            return True
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
        
        patterns = [
            r'href=["\']([^"\']*\.pdf)["\']',
            r'(https?://[^"\'>\s]+\.pdf)',
        ]
        
        all_urls = set()
        for pattern in patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            all_urls.update(matches)
        
        for pdf_url in all_urls:
            if not pdf_url.startswith('http'):
                pdf_url = urljoin(url, pdf_url)
            
            # Skip external non-Steel & Tube links (except NZ Steel which is supplier)
            if 'gib.co.nz' in pdf_url or 'ryanfire' in pdf_url:
                continue
            
            filename = unquote(pdf_url.split('/')[-1])
            filename = filename.replace('.pdf', '').replace('_', ' ').replace('-', ' ')
            
            pdfs.append((filename, pdf_url))
        
        return pdfs
    except Exception as e:
        print(f"   ⚠️ Scrape error: {e}")
        return []


def main():
    print("=" * 60)
    print("⚙️ STEEL & TUBE STRUCTURAL - SMART SORTING")
    print("=" * 60)
    print(f"📁 Storage: {BUCKET}/{BASE_STORAGE_PATH}/")
    
    uploaded_urls = set()  # Track to avoid duplicates
    results = {}
    
    # Process known PDFs first
    print("\n📦 Processing Known PDFs...")
    for folder, pdfs in KNOWN_PDFS.items():
        if folder not in results:
            results[folder] = 0
        
        print(f"\n   {folder}:")
        for link_text, url in pdfs:
            if url in uploaded_urls:
                continue
            
            # Smart routing
            actual_folder = determine_folder(link_text, folder)
            filename = create_filename(actual_folder, link_text)
            
            content = download_pdf(url)
            if not content:
                print(f"      ❌ {link_text[:40]}...")
                continue
            
            if upload_to_supabase(content, actual_folder, filename):
                uploaded_urls.add(url)
                if actual_folder not in results:
                    results[actual_folder] = 0
                results[actual_folder] += 1
                print(f"      ✅ {link_text[:40]}... → {actual_folder}")
    
    # Scrape additional pages
    print("\n\n📦 Scraping Additional Pages...")
    for default_folder, url in SCRAPE_URLS:
        print(f"\n   Scraping: {url}")
        pdfs = scrape_page_for_pdfs(url)
        print(f"   Found {len(pdfs)} PDF links")
        
        for link_text, pdf_url in pdfs:
            if pdf_url in uploaded_urls:
                continue
            
            actual_folder = determine_folder(link_text, default_folder)
            filename = create_filename(actual_folder, link_text)
            
            content = download_pdf(pdf_url)
            if not content:
                continue
            
            if upload_to_supabase(content, actual_folder, filename):
                uploaded_urls.add(pdf_url)
                if actual_folder not in results:
                    results[actual_folder] = 0
                results[actual_folder] += 1
                print(f"      ✅ {link_text[:40]}... → {actual_folder}")
        
        time.sleep(0.5)
    
    # Final report
    print("\n" + "=" * 60)
    print("📊 FINAL REPORT")
    print("=" * 60)
    
    comflor_total = 0
    purlin_total = 0
    general_total = 0
    
    print(f"\n{'Folder':<30} {'Files':>8}")
    print("-" * 40)
    
    for folder, count in sorted(results.items()):
        print(f"{folder:<30} {count:>8}")
        if 'ComFlor' in folder:
            comflor_total += count
        elif 'Purlin' in folder or 'Top_Hat' in folder or 'HST' in folder:
            purlin_total += count
        elif 'General' in folder:
            general_total += count
    
    print("-" * 40)
    print(f"{'TOTAL':<30} {sum(results.values()):>8}")
    
    print(f"\n📊 CATEGORY BREAKDOWN:")
    print(f"   ComFlor Products: {comflor_total}")
    print(f"   HST Purlins/Girts: {purlin_total}")
    print(f"   General Resources: {general_total}")
    
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
    
    print(f"\n✅ Steel & Tube Structural ingestion complete!")
    return sum(results.values())


if __name__ == '__main__':
    main()
