"""
Fix IBS RigidRAP Downloads - Using browser-like headers
"""

import os
import requests
from supabase import create_client
from dotenv import load_dotenv
import time

load_dotenv("/app/backend-minimal/.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
BUCKET = "product-library"
BASE_PATH = "B_Enclosure/Rigid_Air_Barriers/IBS_RigidRAP"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Create session with browser-like headers
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
})

# First, visit the main page to get cookies
print("🔄 Initializing session with IBS website...")
try:
    main_page = session.get("https://ibs.co.nz/products/rigidrap/", timeout=30)
    print(f"   Main page: {main_page.status_code}")
    time.sleep(1)
except Exception as e:
    print(f"   Error: {e}")

IBS_PDFS = [
    {
        "url": "https://ibs.co.nz/files/Technical-Documents/IBS-RigidRAP%C2%AE/IBS_RigidRAP%C2%AE_Design__Installation-Guide_April24-1.pdf",
        "folder": "Installation",
        "filename": "IBS - RigidRAP - Design and Installation Guide.pdf"
    },
    {
        "url": "https://ibs.co.nz/files/Technical-Documents/IBS-RigidRAP%C2%AE/IBS-RigidRAP-Warranty-General-Terms_2025.pdf",
        "folder": "00_General_Resources",
        "filename": "IBS - RigidRAP - Warranty General Terms 2025.pdf"
    },
    {
        "url": "https://ibs.co.nz/files/Technical-Documents/IBS-RigidRAP%C2%AE/IBS-RigidRAP-Codemark.pdf",
        "folder": "Certifications",
        "filename": "IBS - RigidRAP - CodeMark Certificate.pdf"
    },
    {
        "url": "https://ibs.co.nz/files/Technical-Documents/IBS-RigidRAP%C2%AE/IBS_RigidRAP_Technical_Properties_2025.pdf",
        "folder": "Installation",
        "filename": "IBS - RigidRAP - Technical Properties 2025.pdf"
    },
    {
        "url": "https://ibs.co.nz/files/Tapeing-Documents/TK-NZ_Premium-Joining-Tape-Install-Guide.pdf",
        "folder": "Tape_System",
        "filename": "IBS - RigidRAP - Thermakraft Premium Joining Tape Guide.pdf"
    },
    {
        "url": "https://ibs.co.nz/files/Technical-Documents/IBS_RigidRAP%C2%AE-XT/IBS-Rigid-Rap-and-Thermaflash-031220.pdf",
        "folder": "Tape_System",
        "filename": "IBS - RigidRAP - Thermaflash Compatibility Letter.pdf"
    },
    {
        "url": "https://ibs.co.nz/files/Tapeing-Documents/BRANZ-Thermaflash-0920.pdf",
        "folder": "Tape_System",
        "filename": "IBS - RigidRAP - Thermaflash BRANZ Appraisal.pdf"
    },
    {
        "url": "https://ibs.co.nz/files/Tapeing-Documents/40-Below-Platinum-and-Flex-on-IBS-Rigid-Wrap.pdf",
        "folder": "Tape_System",
        "filename": "IBS - RigidRAP - Mason 40 Below Tape Guide.pdf"
    },
    {
        "url": "https://ibs.co.nz/files/Tapeing-Documents/Siga-Wigluv-Branz-appraisal_2025-05-18-222851_qjbm.pdf",
        "folder": "Tape_System",
        "filename": "IBS - RigidRAP - SIGA Wigluv BRANZ Appraisal.pdf"
    },
    {
        "url": "https://ibs.co.nz/files/Technical-Documents/IBS-RigidRAP%C2%AE/Confirmation_Wigluv_IBS.pdf",
        "folder": "Tape_System",
        "filename": "IBS - RigidRAP - SIGA Wigluv Confirmation Letter.pdf"
    },
    {
        "url": "https://ibs.co.nz/files/IBS_Product-_Catalogue_2025.pdf",
        "folder": "00_General_Resources",
        "filename": "IBS - 00 General Resources - Product Catalogue 2025.pdf"
    },
    # Try the alternate path without ®
    {
        "url": "https://ibs.co.nz/files/Technical-Documents/IBS-RigidRAP/IBS-RigidRAP-Codemark.pdf",
        "folder": "Certifications",
        "filename": "IBS - RigidRAP - CodeMark Certificate Alt.pdf"
    },
]

def upload_pdf(url, storage_path):
    """Download and upload a PDF using session."""
    try:
        # Update referer for the download
        session.headers['Referer'] = 'https://ibs.co.nz/products/rigidrap/'
        
        response = session.get(url, timeout=60, allow_redirects=True)
        
        if response.status_code == 200:
            content = response.content
            if len(content) > 1000 and content[:4] == b'%PDF':
                result = supabase.storage.from_(BUCKET).upload(
                    storage_path,
                    content,
                    {"content-type": "application/pdf", "upsert": "true"}
                )
                return True, len(content)
            elif b'<html' in content[:500].lower():
                return False, "Got HTML instead of PDF"
            else:
                return False, f"Invalid content ({len(content)} bytes)"
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

print("\n🔧 Downloading IBS RigidRAP PDFs")
print("=" * 60)

success = 0
for pdf in IBS_PDFS:
    storage_path = f"{BASE_PATH}/{pdf['folder']}/{pdf['filename']}"
    print(f"\n📥 {pdf['filename'][:50]}...")
    
    ok, info = upload_pdf(pdf['url'], storage_path)
    if ok:
        print(f"   ✅ Uploaded ({info:,} bytes)")
        success += 1
    else:
        print(f"   ❌ Failed: {info}")
    
    time.sleep(0.5)

print(f"\n{'='*60}")
print(f"📊 Result: {success}/{len(IBS_PDFS)} PDFs uploaded")
print("=" * 60)
