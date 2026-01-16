"""
Fix IBS RigidRAP URLs - URL encoding issue
"""

import os
import requests
from supabase import create_client
from dotenv import load_dotenv

load_dotenv("/app/backend-minimal/.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
BUCKET = "product-library"
BASE_PATH = "B_Enclosure/Rigid_Air_Barriers/IBS_RigidRAP"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Corrected URLs - using proper URL encoding
IBS_PDFS = [
    # Note: The ® symbol needs to be URL encoded as %C2%AE or we use the direct path without it
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
    # Tape documents
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
]

def upload_pdf(url, storage_path):
    """Download and upload a PDF."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=60, allow_redirects=True)
        
        if response.status_code == 200 and len(response.content) > 1000:
            if response.content[:4] == b'%PDF':
                result = supabase.storage.from_(BUCKET).upload(
                    storage_path,
                    response.content,
                    {"content-type": "application/pdf", "upsert": "true"}
                )
                return True, len(response.content)
            else:
                return False, "Not a PDF"
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

print("🔧 Fixing IBS RigidRAP Downloads")
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
        # Try alternate URL pattern
        alt_url = pdf['url'].replace('%C2%AE', '')
        print(f"   🔄 Trying alternate URL...")
        ok2, info2 = upload_pdf(alt_url, storage_path)
        if ok2:
            print(f"   ✅ Uploaded ({info2:,} bytes)")
            success += 1
        else:
            print(f"   ❌ Still failed: {info2}")

print(f"\n{'='*60}")
print(f"📊 Result: {success}/{len(IBS_PDFS)} PDFs uploaded")
print("=" * 60)
