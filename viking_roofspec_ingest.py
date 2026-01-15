#!/usr/bin/env python3
"""
Viking Roofspec Full Ingestion
Downloads PDFs from all membrane systems and uploads to Supabase with smart sorting
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
BASE_PATH = 'B_Enclosure/Viking_Roofspec'

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# URLs to scrape
PRODUCT_PAGES = [
    ("Enviroclad_TPO", "https://www.vikingroofspec.co.nz/details-documents/membrane-roofing/enviroclad/"),
    ("Torch_On_Bitumen", "https://www.vikingroofspec.co.nz/details-documents/membrane-roofing/torch-on/"),
    ("Rubber_Butyl_EPDM", "https://www.vikingroofspec.co.nz/details-documents/membrane-roofing/rubber-membranes/"),
    ("WarmSpan_Insulated", "https://www.vikingroofspec.co.nz/details-documents/membrane-roofing/warmspan-with-enviroclad/"),
    ("Dec_K_ing", "https://www.vikingroofspec.co.nz/details-documents/waterproof-decks/dec-k-ing/"),
]

# Universal keywords for general resources
UNIVERSAL_KEYWORDS = ['care and maintenance', 'terms of trade', 'warranty sample', 'warranty master',
                      'design guide general', 'chemical resistance chart']


def clean_filename(text):
    """Clean text for filename"""
    cleaned = unquote(text)
    cleaned = cleaned.replace('/', '-').replace('\\', '-')
    cleaned = cleaned.replace(':', '-').replace('*', '').replace('?', '')
    cleaned = cleaned.replace('"', '').replace('<', '').replace('>', '')
    cleaned = cleaned.replace('|', '-').replace('+', ' ')
    cleaned = re.sub(r'\.pdf$', '', cleaned, flags=re.IGNORECASE)
    return ' '.join(cleaned.split())


def determine_folder(link_text, default_folder):
    """Smart routing based on link text"""
    link_lower = link_text.lower()
    for keyword in UNIVERSAL_KEYWORDS:
        if keyword in link_lower:
            return "00_General_Resources"
    return default_folder


def create_filename(folder, link_text):
    """Create standardized filename"""
    clean_text = clean_filename(link_text)
    if folder == "00_General_Resources":
        return f"Viking Roofspec - Universal - {clean_text}.pdf"
    else:
        system_name = folder.replace('_', ' ')
        return f"Viking Roofspec - {system_name} - {clean_text}.pdf"


def download_pdf(url):
    """Download PDF content"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, timeout=60, headers=headers, allow_redirects=True)
        if response.status_code == 200 and len(response.content) > 1000:
            if response.content[:4] == b'%PDF':
                return response.content
        return None
    except:
        return None


def upload_to_supabase(content, folder, filename):
    """Upload PDF to Supabase"""
    storage_path = f"{BASE_PATH}/{folder}/{filename}"
    try:
        supabase.storage.from_(BUCKET).upload(
            storage_path,
            content,
            {"content-type": "application/pdf", "upsert": "true"}
        )
        return True
    except Exception as e:
        if "already exists" in str(e).lower():
            return True
        return False


def scrape_viking_page(url):
    """Scrape a Viking page for PDF links"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, timeout=30, headers=headers)
        if response.status_code != 200:
            return []
        
        html = response.text
        pdfs = []
        
        # Pattern 1: Find all PDF links with image alt text or nearby h3 text
        # Viking uses format: href="...pdf" with ### Title nearby
        
        # Find all PDF URLs
        pdf_pattern = r'href=["\']([^"\']*\.pdf)["\']'
        pdf_urls = re.findall(pdf_pattern, html, re.IGNORECASE)
        
        for pdf_url in set(pdf_urls):
            # Skip non-Viking PDFs
            if 'vikingroofspec' not in pdf_url and not pdf_url.startswith('/'):
                continue
            
            # Make absolute URL
            if pdf_url.startswith('/'):
                pdf_url = f"https://www.vikingroofspec.co.nz{pdf_url}"
            
            # Skip zip and dwg files
            if '.zip' in pdf_url.lower() or '.dwg' in pdf_url.lower():
                continue
            
            # Extract filename as link text
            filename = unquote(pdf_url.split('/')[-1])
            link_text = filename.replace('.pdf', '').replace('-', ' ').replace('_', ' ')
            
            # Try to find better title from HTML (### Title pattern)
            # Look for h3 near the PDF link
            escaped_url = re.escape(pdf_url.split('/')[-1])
            title_pattern = rf'###\s*([^<\n]+?)(?:\n|<)'
            
            pdfs.append((link_text, pdf_url))
        
        return pdfs
    except Exception as e:
        print(f"   ⚠️ Scrape error: {e}")
        return []


def process_product(folder, url):
    """Process a single product page"""
    print(f"\n{'='*60}")
    print(f"📦 {folder}")
    print(f"   URL: {url}")
    
    pdfs = scrape_viking_page(url)
    print(f"   Found {len(pdfs)} PDF links")
    
    if not pdfs:
        return 0
    
    uploaded_urls = set()
    successful = 0
    
    # Prioritize "Full Set" PDFs
    full_set_pdfs = [(t, u) for t, u in pdfs if 'full' in t.lower() and 'set' in t.lower()]
    other_pdfs = [(t, u) for t, u in pdfs if not ('full' in t.lower() and 'set' in t.lower())]
    
    # Process Full Set first
    for link_text, pdf_url in full_set_pdfs + other_pdfs:
        if pdf_url in uploaded_urls:
            continue
        uploaded_urls.add(pdf_url)
        
        actual_folder = determine_folder(link_text, folder)
        filename = create_filename(actual_folder, link_text)
        
        content = download_pdf(pdf_url)
        if not content:
            continue
        
        size_kb = len(content) / 1024
        if upload_to_supabase(content, actual_folder, filename):
            successful += 1
            # Truncate long names for display
            display_name = link_text[:40] + "..." if len(link_text) > 40 else link_text
            print(f"   ✅ {display_name} ({size_kb:.0f}KB)")
    
    print(f"   📊 Uploaded: {successful}")
    return successful


def main():
    print("=" * 60)
    print("🛡️ VIKING ROOFSPEC - FULL INGESTION")
    print("=" * 60)
    print(f"📁 Storage: {BUCKET}/{BASE_PATH}/")
    
    results = {}
    total_files = 0
    
    for folder, url in PRODUCT_PAGES:
        count = process_product(folder, url)
        results[folder] = count
        total_files += count
        time.sleep(1)
    
    # Final report
    print("\n" + "=" * 60)
    print("📊 FINAL REPORT")
    print("=" * 60)
    print(f"\n{'System':<35} {'Files':>8}")
    print("-" * 45)
    for name, count in results.items():
        status = "✅" if count > 0 else "⚠️"
        print(f"{status} {name:<33} {count:>8}")
    
    print("-" * 45)
    print(f"{'TOTAL':<35} {total_files:>8}")
    
    # Verify storage
    print("\n📂 STORAGE VERIFICATION:")
    try:
        folders = supabase.storage.from_(BUCKET).list(BASE_PATH)
        verified_total = 0
        for f in folders:
            if f.get('id') is None:
                files = supabase.storage.from_(BUCKET).list(f"{BASE_PATH}/{f['name']}")
                pdf_count = len([x for x in files if x['name'].endswith('.pdf')])
                verified_total += pdf_count
                print(f"   {f['name']}: {pdf_count} PDFs")
        print(f"\n   TOTAL VERIFIED: {verified_total} PDFs")
    except Exception as e:
        print(f"   ⚠️ Could not verify: {e}")
    
    print(f"\n✅ Viking Roofspec ingestion complete!")
    return total_files


if __name__ == '__main__':
    main()
