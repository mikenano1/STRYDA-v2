"""
Fix IBS RigidRAP Downloads - Using alternative sources
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

# Alternative sources for IBS RigidRAP PDFs
IBS_PDFS = [
    # PlaceMakers mirror
    {
        "url": "https://pimstorageaueprod.blob.core.windows.net/placemakers/media-assets/1160550_RRAP082412_installation.pdf",
        "folder": "Installation",
        "filename": "IBS - RigidRAP - Installation Guide (PlaceMakers).pdf"
    },
    # ArchiPro mirror - RigidRAP-XT
    {
        "url": "https://archipro.com.au/assets/MemberUploads/Installation-GuideRigidRAP-XTMay22-7.pdf",
        "folder": "Installation",
        "filename": "IBS - RigidRAP XT - Installation Guide May 2022.pdf"
    },
    # CodeHub / Building.govt.nz certification documents
    {
        "url": "https://codehub.building.govt.nz/resources/cmnz70091-version-3",
        "folder": "Certifications",
        "filename": "IBS - RigidRAP - CodeMark CMNZ70091.pdf",
        "is_page": True  # This is a webpage, not direct PDF
    },
]

def upload_pdf(url, storage_path):
    """Download and upload a PDF."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=60, allow_redirects=True)
        
        if response.status_code == 200:
            content = response.content
            if len(content) > 1000 and content[:4] == b'%PDF':
                result = supabase.storage.from_(BUCKET).upload(
                    storage_path,
                    content,
                    {"content-type": "application/pdf", "upsert": "true"}
                )
                return True, len(content)
            else:
                return False, f"Not a PDF ({len(content)} bytes)"
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

print("🔧 Downloading IBS RigidRAP from Alternative Sources")
print("=" * 60)

success = 0
for pdf in IBS_PDFS:
    if pdf.get("is_page"):
        print(f"\n⏭️ Skipping webpage: {pdf['filename']}")
        continue
        
    storage_path = f"{BASE_PATH}/{pdf['folder']}/{pdf['filename']}"
    print(f"\n📥 {pdf['filename'][:50]}...")
    print(f"   Source: {pdf['url'][:60]}...")
    
    ok, info = upload_pdf(pdf['url'], storage_path)
    if ok:
        print(f"   ✅ Uploaded ({info:,} bytes)")
        success += 1
    else:
        print(f"   ❌ Failed: {info}")
    
    time.sleep(0.3)

print(f"\n{'='*60}")
print(f"📊 Result: {success} PDFs uploaded from alternative sources")
print("=" * 60)
