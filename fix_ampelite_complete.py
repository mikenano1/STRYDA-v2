"""
Complete Ampelite Gap Fix: Add All Missing Installation Guides
==============================================================
"""

import os
import requests
from supabase import create_client
from dotenv import load_dotenv

load_dotenv("/app/backend-minimal/.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
BUCKET = "product-library"
BASE_PATH = "B_Enclosure/Translucent_Roofing/Ampelite_NZ"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Complete list of Ampelite PDFs to download
PDFS_TO_DOWNLOAD = [
    # From Ampelite NZ website (verified)
    {
        "url": "https://ampelite.co.nz/wp-content/uploads/2024/07/solasafebrochure.pdf",
        "folder": "Solasafe_Residential",
        "filename": "Ampelite - Solasafe - Product Brochure.pdf"
    },
    {
        "url": "https://ampelite.co.nz/wp-content/uploads/2024/05/Solasafe_BPIR_Information_Sheet_Class_1-1.pdf",
        "folder": "Solasafe_Residential",
        "filename": "Ampelite - Solasafe - BPIR Information Sheet Class 1.pdf"
    },
    # From Ampelite AU website (installation guides with Anti-Noise Tape instructions)
    {
        "url": "https://www.ampelite.com.au/wp-content/uploads/2019/09/Wonderglas-Installation-Guide.pdf",
        "folder": "Wonderglas_GC",
        "filename": "Ampelite - Wonderglas GC - Installation Guide (Contains Anti-Noise Tape Instructions).pdf"
    },
    {
        "url": "https://www.ampelite.com.au/wp-content/uploads/2019/09/Permaglas-Installation-Guide.pdf",
        "folder": "Permaglas",
        "filename": "Ampelite - Permaglas - Installation Guide.pdf"
    },
    {
        "url": "https://www.ampelite.com.au/wp-content/uploads/2019/09/Webglas-Installation-Guide.pdf",
        "folder": "Webglas",
        "filename": "Ampelite - Webglas - Installation Guide.pdf"
    },
    {
        "url": "https://www.ampelite.com.au/wp-content/uploads/2019/09/Wonderclad-Installation-Guide.pdf",
        "folder": "Wonderclad",
        "filename": "Ampelite - Wonderclad - Installation Guide.pdf"
    },
    {
        "url": "https://www.ampelite.com.au/wp-content/uploads/2019/09/Lexan-Thermoclick-Installation-Instructions.pdf",
        "folder": "Thermoclick",
        "filename": "Ampelite - Thermoclick - Installation Instructions (Contains Anti-Noise Tape Instructions).pdf"
    },
    {
        "url": "https://www.ampelite.com.au/wp-content/uploads/2019/09/Lexan-ThermoClear-Installation-Instructions.pdf",
        "folder": "ThermoClear",
        "filename": "Ampelite - ThermoClear - Installation Instructions.pdf"
    },
    {
        "url": "https://www.ampelite.com.au/wp-content/uploads/2019/09/Dualroof-Installation-Guide.pdf",
        "folder": "Dualroof",
        "filename": "Ampelite - Dualroof - Installation Guide.pdf"
    },
    # Third-party mirrored sources
    {
        "url": "https://productspec.co.nz/media/0a1f2peo/solasafe-installation-guide.pdf",
        "folder": "Solasafe_Residential",
        "filename": "Ampelite - Solasafe - Installation Guide NZ (Contains Anti-Noise Tape Instructions).pdf"
    },
    {
        "url": "https://tropex.co.nz/sites/default/files/product_pdfs/Ampelite%20Installation%20Guide.pdf",
        "folder": "00_General_Resources",
        "filename": "Ampelite - 00 General Resources - Installation Guide Master.pdf"
    },
]

def file_exists(path):
    """Check if file exists in storage."""
    folder = "/".join(path.split("/")[:-1])
    filename = path.split("/")[-1]
    try:
        result = supabase.storage.from_(BUCKET).list(folder, {"limit": 1000})
        return any(item['name'] == filename for item in result)
    except:
        return False

def upload_pdf(url, storage_path):
    """Download and upload a PDF."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200 and len(response.content) > 1000:
            # Verify it's a PDF
            if response.content[:4] == b'%PDF':
                result = supabase.storage.from_(BUCKET).upload(
                    storage_path,
                    response.content,
                    {"content-type": "application/pdf", "upsert": "true"}
                )
                return True, len(response.content)
            else:
                return False, "Not a valid PDF"
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

print("🔧 Complete Ampelite Gap Fix: Adding All Missing PDFs")
print("=" * 70)

success_count = 0
failed = []

for pdf in PDFS_TO_DOWNLOAD:
    storage_path = f"{BASE_PATH}/{pdf['folder']}/{pdf['filename']}"
    
    print(f"\n📥 {pdf['filename'][:55]}...")
    
    if file_exists(storage_path):
        print(f"   ⏭️ Already exists")
        continue
    
    success, info = upload_pdf(pdf['url'], storage_path)
    
    if success:
        print(f"   ✅ Uploaded ({info:,} bytes)")
        success_count += 1
    else:
        print(f"   ❌ Failed: {info}")
        failed.append(pdf['filename'])

print(f"\n{'='*70}")
print(f"📊 RESULT: {success_count} new PDFs added to Ampelite_NZ")
if failed:
    print(f"⚠️ Failed downloads: {len(failed)}")
print("=" * 70)
