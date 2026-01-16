"""
IBS RigidRAP - Download ALL documents from EBOSS
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

# EBOSS download endpoints - these redirect to actual PDFs
EBOSS_DOCS = [
    # Main Documents
    {
        "url": "https://www.eboss.co.nz/library/independent-building-supplies/download/38447",
        "folder": "Installation",
        "filename": "IBS - RigidRAP - Technical Properties April 2025.pdf"
    },
    {
        "url": "https://www.eboss.co.nz/library/independent-building-supplies/download/38429",
        "folder": "Certifications",
        "filename": "IBS - RigidRAP - CodeMark CM70035 Rev2 2022.pdf"
    },
    {
        "url": "https://www.eboss.co.nz/library/independent-building-supplies/download/40461",
        "folder": "Installation",
        "filename": "IBS - RigidRAP - Installation Guide April 2024 (EBOSS).pdf"
    },
    {
        "url": "https://www.eboss.co.nz/library/independent-building-supplies/download/38664",
        "folder": "00_General_Resources",
        "filename": "IBS - RigidRAP - Care and Maintenance Guide Aug 2021.pdf"
    },
    {
        "url": "https://www.eboss.co.nz/library/independent-building-supplies/download/38665",
        "folder": "00_General_Resources",
        "filename": "IBS - RigidRAP - Warranty September 2025.pdf"
    },
    {
        "url": "https://www.eboss.co.nz/library/independent-building-supplies/download/38663",
        "folder": "Brochures",
        "filename": "IBS - RigidRAP - Product Brochure September 2025.pdf"
    },
    # CAD/PDF Details - Key installation details
    {
        "url": "https://www.eboss.co.nz/library/independent-building-supplies/download/8671/254571",
        "folder": "Details",
        "filename": "IBS - RigidRAP - Detail 01.pdf"
    },
    {
        "url": "https://www.eboss.co.nz/library/independent-building-supplies/download/8672/254511",
        "folder": "Details",
        "filename": "IBS - RigidRAP - Detail 02.pdf"
    },
    {
        "url": "https://www.eboss.co.nz/library/independent-building-supplies/download/8674/254515",
        "folder": "Details",
        "filename": "IBS - RigidRAP - Detail 03.pdf"
    },
    {
        "url": "https://www.eboss.co.nz/library/independent-building-supplies/download/8673/254519",
        "folder": "Details",
        "filename": "IBS - RigidRAP - Detail 04.pdf"
    },
    {
        "url": "https://www.eboss.co.nz/library/independent-building-supplies/download/8675/254523",
        "folder": "Details",
        "filename": "IBS - RigidRAP - Detail 05.pdf"
    },
    {
        "url": "https://www.eboss.co.nz/library/independent-building-supplies/download/8678/254527",
        "folder": "Details",
        "filename": "IBS - RigidRAP - Detail 06.pdf"
    },
    {
        "url": "https://www.eboss.co.nz/library/independent-building-supplies/download/8676/254531",
        "folder": "Details",
        "filename": "IBS - RigidRAP - Detail 07.pdf"
    },
    {
        "url": "https://www.eboss.co.nz/library/independent-building-supplies/download/8677/254535",
        "folder": "Details",
        "filename": "IBS - RigidRAP - Detail 08.pdf"
    },
    {
        "url": "https://www.eboss.co.nz/library/independent-building-supplies/download/8655/254539",
        "folder": "Details",
        "filename": "IBS - RigidRAP - Detail 09.pdf"
    },
    {
        "url": "https://www.eboss.co.nz/library/independent-building-supplies/download/8656/254543",
        "folder": "Details",
        "filename": "IBS - RigidRAP - Detail 10.pdf"
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

def download_eboss_pdf(url):
    """Download PDF from EBOSS (follows redirects)."""
    try:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/pdf,*/*",
            "Referer": "https://www.eboss.co.nz/library/independent-building-supplies/ibs-rigidrap",
        })
        
        response = session.get(url, timeout=60, allow_redirects=True)
        
        if response.status_code == 200:
            content = response.content
            
            # Check if it's a valid PDF
            if len(content) > 1000 and content[:4] == b'%PDF':
                return True, content
            elif b'<!DOCTYPE' in content[:200] or b'<html' in content[:200].lower():
                # It's HTML - might need to parse for actual download link
                return False, "Got HTML page"
            else:
                return False, f"Unknown content ({len(content)} bytes)"
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)[:50]

def upload_pdf(content, storage_path):
    """Upload PDF content to Supabase."""
    try:
        result = supabase.storage.from_(BUCKET).upload(
            storage_path,
            content,
            {"content-type": "application/pdf", "upsert": "true"}
        )
        return True
    except Exception as e:
        return False

print("🔍 IBS RigidRAP - Downloading from EBOSS Library")
print("=" * 70)

success = 0
skipped = 0

for doc in EBOSS_DOCS:
    storage_path = f"{BASE_PATH}/{doc['folder']}/{doc['filename']}"
    
    if file_exists(storage_path):
        print(f"\n⏭️ Exists: {doc['filename'][:45]}...")
        skipped += 1
        continue
    
    print(f"\n📥 {doc['filename'][:50]}...")
    
    ok, result = download_eboss_pdf(doc['url'])
    
    if ok:
        if upload_pdf(result, storage_path):
            print(f"   ✅ Uploaded ({len(result):,} bytes)")
            success += 1
        else:
            print(f"   ❌ Upload failed")
    else:
        print(f"   ❌ Download failed: {result}")
    
    time.sleep(0.3)

print(f"\n{'='*70}")
print(f"📊 RESULT: {success} new PDFs uploaded, {skipped} skipped")
print("=" * 70)
