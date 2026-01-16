"""
Fix Ampelite Gap: Add Installation Guides
==========================================
Downloads the missing Ampelite installation guides that contain Anti-Noise Tape instructions.
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

# Known Ampelite PDFs with Anti-Noise Tape instructions from search results
INSTALLATION_GUIDES = [
    {
        "url": "https://ampelite.co.nz/wp-content/uploads/Installations/Solasafe-Installation-Guide.pdf",
        "folder": "Solasafe_Residential",
        "filename": "Ampelite - Solasafe - Installation Guide (Contains Anti-Noise Tape Instructions).pdf"
    },
    {
        "url": "https://www.ampelite.co.nz/wp-content/uploads/Installations/Wonderglas-Installation-Guide.pdf",
        "folder": "Wonderglas_GC",
        "filename": "Ampelite - Wonderglas GC - Installation Guide.pdf"
    },
    {
        "url": "https://www.ampelite.co.nz/wp-content/uploads/Installations/Webglas-Installation-Guide.pdf",
        "folder": "Webglas",
        "filename": "Ampelite - Webglas - Installation Guide.pdf"
    },
    {
        "url": "https://ampelite.co.nz/wp-content/uploads/Installations/Lexan-Thermoclick-Installation-Instructions.pdf",
        "folder": "Thermoclick",
        "filename": "Ampelite - Thermoclick - Installation Instructions.pdf"
    },
    # Try Ampelite AU source for general installation guide
    {
        "url": "https://www.ampelite.com.au/wp-content/uploads/2019/09/Solasafe-Installation-Guide.pdf",
        "folder": "Solasafe_Residential",
        "filename": "Ampelite - Solasafe - Installation Guide AU.pdf"
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
            result = supabase.storage.from_(BUCKET).upload(
                storage_path,
                response.content,
                {"content-type": "application/pdf", "upsert": "true"}
            )
            return True, len(response.content)
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

print("🔧 Fixing Ampelite Gap: Adding Installation Guides")
print("=" * 60)

success_count = 0
for guide in INSTALLATION_GUIDES:
    storage_path = f"{BASE_PATH}/{guide['folder']}/{guide['filename']}"
    
    print(f"\n📥 Downloading: {guide['filename'][:50]}...")
    print(f"   Source: {guide['url'][:60]}...")
    
    if file_exists(storage_path):
        print(f"   ⏭️ Already exists, skipping")
        continue
    
    success, info = upload_pdf(guide['url'], storage_path)
    
    if success:
        print(f"   ✅ Uploaded ({info:,} bytes)")
        success_count += 1
    else:
        print(f"   ❌ Failed: {info}")

print(f"\n{'='*60}")
print(f"📊 Result: {success_count} new installation guides added")
print("=" * 60)
