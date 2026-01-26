"""
IBS RigidRAP - Download from ALL alternative mirror sources
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

# All alternative sources found from web searches
IBS_ALT_SOURCES = [
    # ProductSpec.co.nz - Warranty
    {
        "url": "https://productspec.co.nz/media/wgkeypcs/warranty-general-terms_aug21_rigidrap.pdf",
        "folder": "00_General_Resources",
        "filename": "IBS - RigidRAP - Warranty General Terms Aug 2021.pdf"
    },
    # EBOSS.co.nz - RigidRAP-XT Installation Guide 2024
    {
        "url": "https://www.eboss.co.nz/assets/literature/292/40460/Installation-Guide_RigidRAP-XT_2024.pdf",
        "folder": "Installation",
        "filename": "IBS - RigidRAP XT - Installation Guide 2024 (EBOSS).pdf"
    },
    # CodeHub Building.govt.nz - CodeMark certificates (try direct PDF links)
    {
        "url": "https://d39d3mj7qio96p.cloudfront.net/media/documents/70035.V4.1024_IBS_RigidRAP.pdf",
        "folder": "Certifications",
        "filename": "IBS - RigidRAP - CodeMark CMNZ70035 v4.pdf"
    },
    {
        "url": "https://d39d3mj7qio96p.cloudfront.net/media/documents/70091.V3.0224_IBS_RigidRAP-XT.pdf",
        "folder": "Certifications", 
        "filename": "IBS - RigidRAP XT - CodeMark CMNZ70091 v3.pdf"
    },
    # RigidRAP-XT Design & Installation from IBS (try anyway)
    {
        "url": "https://ibs.co.nz/files/Technical-Documents/IBS_RigidRAP%C2%AE-XT/IBS_RigidRAP-XT_Design__Installation_Guide_April-24.pdf",
        "folder": "Installation",
        "filename": "IBS - RigidRAP XT - Design Installation Guide April 2024.pdf"
    },
    # Thermakraft tape guide (from Tropex)
    {
        "url": "https://tropex.co.nz/sites/default/files/product_pdfs/TK_Premium-Joining-Tape-Install-Guide.pdf",
        "folder": "Tape_System",
        "filename": "IBS - RigidRAP - Thermakraft Premium Joining Tape Guide.pdf"
    },
    # Try EBOSS download endpoint
    {
        "url": "https://www.eboss.co.nz/library/independent-building-supplies/download/38425",
        "folder": "Installation",
        "filename": "IBS - RigidRAP - EBOSS Download.pdf"
    },
    # ProductSpec general page PDF
    {
        "url": "https://productspec.co.nz/media/0kta4x0h/ibs-rigidrap-installation-guide.pdf",
        "folder": "Installation",
        "filename": "IBS - RigidRAP - Installation Guide (ProductSpec).pdf"
    },
    # Try Mitre10 or other distributors
    {
        "url": "https://www.mitre10.co.nz/documents/IBS-RigidRAP-Installation-Guide.pdf",
        "folder": "Installation",
        "filename": "IBS - RigidRAP - Installation Guide (Mitre10).pdf"
    },
    # ITM distributor
    {
        "url": "https://www.itm.co.nz/media/documents/IBS-RigidRAP-Installation.pdf",
        "folder": "Installation", 
        "filename": "IBS - RigidRAP - Installation Guide (ITM).pdf"
    },
]

def file_exists(storage_path):
    """Check if file exists."""
    folder = "/".join(storage_path.split("/")[:-1])
    filename = storage_path.split("/")[-1]
    try:
        result = supabase.storage.from_(BUCKET).list(folder, {"limit": 1000})
        return any(item['name'] == filename for item in result)
    except:
        return False

def upload_pdf(url, storage_path):
    """Download and upload a PDF."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/pdf,*/*",
            "Accept-Language": "en-US,en;q=0.9",
        }
        response = requests.get(url, headers=headers, timeout=60, allow_redirects=True)
        
        if response.status_code == 200:
            content = response.content
            # Check if it's a valid PDF
            if len(content) > 1000 and content[:4] == b'%PDF':
                result = supabase.storage.from_(BUCKET).upload(
                    storage_path,
                    content,
                    {"content-type": "application/pdf", "upsert": "true"}
                )
                return True, len(content)
            elif b'<!DOCTYPE' in content[:100] or b'<html' in content[:100].lower():
                return False, "Got HTML (redirect/error page)"
            else:
                return False, f"Invalid content ({len(content)} bytes, starts: {content[:20]})"
        else:
            return False, f"HTTP {response.status_code}"
    except requests.exceptions.Timeout:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)[:50]

print("🔍 IBS RigidRAP - Downloading from Alternative Sources")
print("=" * 70)

success = 0
failed = []

for pdf in IBS_ALT_SOURCES:
    storage_path = f"{BASE_PATH}/{pdf['folder']}/{pdf['filename']}"
    
    # Skip if exists
    if file_exists(storage_path):
        print(f"\n⏭️ Already exists: {pdf['filename'][:45]}...")
        continue
    
    print(f"\n📥 {pdf['filename'][:50]}...")
    print(f"   Source: {pdf['url'][:60]}...")
    
    ok, info = upload_pdf(pdf['url'], storage_path)
    if ok:
        print(f"   ✅ Uploaded ({info:,} bytes)")
        success += 1
    else:
        print(f"   ❌ Failed: {info}")
        failed.append(pdf['filename'])
    
    time.sleep(0.5)

print(f"\n{'='*70}")
print(f"📊 RESULT: {success} new PDFs uploaded")
if failed:
    print(f"⚠️ Failed: {len(failed)} sources")
print("=" * 70)
