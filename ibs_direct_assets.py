"""
IBS RigidRAP - Try direct EBOSS asset URLs
"""

import os
import requests
from supabase import create_client
from dotenv import load_dotenv
import time
import re

load_dotenv("/app/backend-minimal/.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
BUCKET = "product-library"
BASE_PATH = "B_Enclosure/Rigid_Air_Barriers/IBS_RigidRAP"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Try direct asset URLs based on EBOSS pattern
DIRECT_URLS = [
    # Based on earlier successful download pattern
    {
        "url": "https://www.eboss.co.nz/assets/literature/292/40461/Installation-Guide_RigidRAP_2024.pdf",
        "folder": "Installation",
        "filename": "IBS - RigidRAP - Installation Guide 2024.pdf"
    },
    {
        "url": "https://www.eboss.co.nz/assets/literature/292/38447/Technical-Properties_RigidRAP_2025.pdf",
        "folder": "Installation",
        "filename": "IBS - RigidRAP - Technical Properties 2025.pdf"
    },
    {
        "url": "https://www.eboss.co.nz/assets/literature/292/38429/CodeMark-CM70035_RigidRAP.pdf",
        "folder": "Certifications",
        "filename": "IBS - RigidRAP - CodeMark CM70035.pdf"
    },
    {
        "url": "https://www.eboss.co.nz/assets/literature/292/38664/Care-Maintenance_RigidRAP.pdf",
        "folder": "00_General_Resources",
        "filename": "IBS - RigidRAP - Care and Maintenance.pdf"
    },
    {
        "url": "https://www.eboss.co.nz/assets/literature/292/38665/Warranty_RigidRAP.pdf",
        "folder": "00_General_Resources",
        "filename": "IBS - RigidRAP - Warranty.pdf"
    },
    {
        "url": "https://www.eboss.co.nz/assets/literature/292/38663/Brochure_RigidRAP.pdf",
        "folder": "Brochures",
        "filename": "IBS - RigidRAP - Product Brochure.pdf"
    },
]

def upload_pdf(url, storage_path):
    """Download and upload a PDF."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        }
        response = requests.get(url, headers=headers, timeout=60, allow_redirects=True)
        
        if response.status_code == 200:
            content = response.content
            if len(content) > 1000 and content[:4] == b'%PDF':
                supabase.storage.from_(BUCKET).upload(
                    storage_path,
                    content,
                    {"content-type": "application/pdf", "upsert": "true"}
                )
                return True, len(content)
            else:
                return False, "Not a PDF"
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)[:50]

print("🔍 IBS RigidRAP - Trying Direct Asset URLs")
print("=" * 70)

# First, let's check what the actual asset URL patterns are
print("\n📋 Checking actual EBOSS asset URL pattern...")

# Get the page and look for actual asset URLs
try:
    resp = requests.get(
        "https://www.eboss.co.nz/library/independent-building-supplies/ibs-rigidrap",
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30
    )
    
    # Look for asset URLs in the page
    asset_pattern = r'https://www\.eboss\.co\.nz/assets/[^"\'>\s]+'
    assets = re.findall(asset_pattern, resp.text)
    
    pdf_assets = [a for a in assets if '.pdf' in a.lower() or 'literature' in a.lower()]
    
    if pdf_assets:
        print(f"   Found {len(pdf_assets)} potential PDF assets")
        for a in pdf_assets[:5]:
            print(f"   - {a[:70]}...")
except Exception as e:
    print(f"   Error: {e}")

success = 0
for doc in DIRECT_URLS:
    storage_path = f"{BASE_PATH}/{doc['folder']}/{doc['filename']}"
    print(f"\n📥 {doc['filename'][:50]}...")
    
    ok, info = upload_pdf(doc['url'], storage_path)
    if ok:
        print(f"   ✅ Uploaded ({info:,} bytes)")
        success += 1
    else:
        print(f"   ❌ Failed: {info}")

print(f"\n{'='*70}")
print(f"📊 RESULT: {success} PDFs from direct assets")
print("=" * 70)
