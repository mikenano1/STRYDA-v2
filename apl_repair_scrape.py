#!/usr/bin/env python3
"""
APL Window Solutions - REPAIR SCRIPT
=====================================
Fixes the incomplete APL scrape by adding:
- Metro Series documents
- Installation Details
- BPIR Technical Statements
- 00_General_Resources (Rule 8 Monoliths)

Target: ~20+ PDFs for complete APL coverage
"""

import os
import sys
import time
import requests
from supabase import create_client
from dotenv import load_dotenv

load_dotenv("/app/backend-minimal/.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
BUCKET = "product-library"
STORAGE_PREFIX = "B_Enclosure/Joinery/APL_Window_Solutions"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

stats = {
    "pdfs_found": 0,
    "pdfs_uploaded": 0,
    "pdfs_skipped": 0,
    "errors": 0,
}

# =============================================================================
# APL PDFs - COMPREHENSIVE LIST
# =============================================================================

APL_PDFS = [
    # =========================================================================
    # 00_General_Resources - MONOLITHS & Master Docs (Rule 8)
    # =========================================================================
    {
        "url": "https://www.premierjoinery.co.nz/wp-content/uploads/2023/12/apl-bpir-combined-altherm-dt20231102135059451.pdf",
        "folder": "00_General_Resources",
        "filename": "APL - 00 General - BPIR Combined Altherm (MASTER).pdf",
        "is_monolith": True
    },
    {
        "url": "https://wightaluminium.co.nz/wp-content/uploads/2024/06/apl-bpir-3-residential-non-dt20231102112926621.pdf",
        "folder": "00_General_Resources",
        "filename": "APL - 00 General - BPIR Residential Non-Thermal.pdf"
    },
    {
        "url": "https://d39d3mj7qio96p.cloudfront.net/media/documents/1_1188_2023.pdf",
        "folder": "00_General_Resources",
        "filename": "APL - 00 General - BRANZ Appraisal 1188 Metro Centrafix.pdf",
        "h1_compliance": True
    },
    {
        "url": "https://d39d3mj7qio96p.cloudfront.net/media/documents/1259_2024_A1_.pdf",
        "folder": "00_General_Resources",
        "filename": "APL - 00 General - BRANZ Appraisal 1259 ThermalHEART Plus 2024.pdf",
        "h1_compliance": True
    },
    
    # =========================================================================
    # Metro Series - Sliding Windows (from EBOSS download IDs)
    # =========================================================================
    {
        "url": "https://d39d3mj7qio96p.cloudfront.net/media/documents/1_1188_2023_a2.pdf",
        "folder": "Metro_Series/Sliding_Windows",
        "filename": "APL - Metro ThermalHEART - Sliding Windows BRANZ Appraisal.pdf",
        "h1_compliance": True
    },
    
    # =========================================================================
    # Metro Series - Product Data Sheets (found via search)
    # =========================================================================
    {
        "url": "https://www.altherm.co.nz/assets/Uploads/Metro-Series-data-sheet.pdf",
        "folder": "Metro_Series",
        "filename": "APL - Metro Series - Data Sheet.pdf"
    },
    {
        "url": "https://www.vantage.co.nz/assets/Uploads/Metro-Series-Thermalheart-Data-Sheet.pdf",
        "folder": "Metro_Series",
        "filename": "APL - Metro Series ThermalHEART - Data Sheet.pdf"
    },
    
    # =========================================================================
    # Architectural Series
    # =========================================================================
    {
        "url": "https://www.altherm.co.nz/assets/Uploads/Architectural-Series-data-sheet.pdf",
        "folder": "Architectural_Series",
        "filename": "APL - Architectural Series - Data Sheet.pdf"
    },
    {
        "url": "https://www.altherm.co.nz/assets/Uploads/Architectural-Series-Thermalheart-Data-Sheet.pdf",
        "folder": "Architectural_Series",
        "filename": "APL - Architectural Series ThermalHEART - Data Sheet.pdf"
    },
    
    # =========================================================================
    # Residential Series
    # =========================================================================
    {
        "url": "https://www.altherm.co.nz/assets/Uploads/Residential-Series-data-sheet.pdf",
        "folder": "Residential_Series",
        "filename": "APL - Residential Series - Data Sheet.pdf"
    },
    {
        "url": "https://www.altherm.co.nz/assets/Uploads/Residential-Series-Thermalheart-Data-Sheet.pdf",
        "folder": "Residential_Series",
        "filename": "APL - Residential Series ThermalHEART - Data Sheet.pdf"
    },
    
    # =========================================================================
    # Installation Details - Sliding Windows (EBOSS PDF downloads)
    # These are the actual PDF versions of CAD details
    # =========================================================================
    {
        "url": "https://cdn.eboss.co.nz/downloads/441144.pdf",
        "folder": "Installation_Details/Metro_Sliding_Windows",
        "filename": "APL - Metro Sliding Window - Head Detail Cavity.pdf"
    },
    {
        "url": "https://cdn.eboss.co.nz/downloads/441147.pdf",
        "folder": "Installation_Details/Metro_Sliding_Windows",
        "filename": "APL - Metro Sliding Window - Jamb Detail Cavity.pdf"
    },
    {
        "url": "https://cdn.eboss.co.nz/downloads/441150.pdf",
        "folder": "Installation_Details/Metro_Sliding_Windows",
        "filename": "APL - Metro Sliding Window - Sill Detail Cavity.pdf"
    },
    {
        "url": "https://cdn.eboss.co.nz/downloads/441153.pdf",
        "folder": "Installation_Details/Metro_Sliding_Windows",
        "filename": "APL - Metro Sliding Window - Head Detail Direct Fix.pdf"
    },
    {
        "url": "https://cdn.eboss.co.nz/downloads/441156.pdf",
        "folder": "Installation_Details/Metro_Sliding_Windows",
        "filename": "APL - Metro Sliding Window - Jamb Detail Direct Fix.pdf"
    },
    {
        "url": "https://cdn.eboss.co.nz/downloads/441159.pdf",
        "folder": "Installation_Details/Metro_Sliding_Windows",
        "filename": "APL - Metro Sliding Window - Sill Detail Direct Fix.pdf"
    },
    {
        "url": "https://cdn.eboss.co.nz/downloads/441162.pdf",
        "folder": "Installation_Details/Metro_Sliding_Windows",
        "filename": "APL - Metro Sliding Window - Weatherboard Detail.pdf"
    },
    
    # =========================================================================
    # Span Tables & Performance Data (Critical Rule 6)
    # =========================================================================
    {
        "url": "https://cdn.eboss.co.nz/downloads/43147.pdf",
        "folder": "Metro_Series/Span_Tables",
        "filename": "APL - Metro ThermalHEART - Span Tables Sliding Windows.pdf",
        "h1_compliance": True
    },
    
    # =========================================================================
    # Care & Maintenance
    # =========================================================================
    {
        "url": "https://www.agp.glass/assets/Uploads/AGP-Care-Maintenance-Guide-2021.pdf",
        "folder": "00_General_Resources",
        "filename": "APL AGP - Care and Maintenance Guide.pdf"
    },
    {
        "url": "https://cdn.eboss.co.nz/downloads/42983.pdf",
        "folder": "00_General_Resources",
        "filename": "APL AGP - Condensation Guide.pdf"
    },
    {
        "url": "https://cdn.eboss.co.nz/downloads/37772.pdf",
        "folder": "00_General_Resources",
        "filename": "APL AGP - Visual Quality of Glass Standards.pdf"
    },
    
    # =========================================================================
    # Environmental/Sustainability
    # =========================================================================
    {
        "url": "https://cdn.eboss.co.nz/downloads/42976.pdf",
        "folder": "00_General_Resources",
        "filename": "APL - Declare Label Environmental.pdf"
    },
    {
        "url": "https://cdn.eboss.co.nz/downloads/52754.pdf",
        "folder": "00_General_Resources",
        "filename": "APL - EPD Understanding Global Standard.pdf"
    },
    
    # =========================================================================
    # Additional EBOSS Downloads - Metro ThermalHEART Windows Data
    # =========================================================================
    {
        "url": "https://cdn.eboss.co.nz/downloads/42986.pdf",
        "folder": "Metro_Series",
        "filename": "APL - Metro ThermalHEART - Windows Data Sheet.pdf"
    },
    {
        "url": "https://cdn.eboss.co.nz/downloads/51488.pdf",
        "folder": "00_General_Resources",
        "filename": "APL - R-Value and Ug-Value Calculator Guide.pdf",
        "h1_compliance": True
    },
]


def file_exists(storage_path):
    """Check if file already exists in Supabase Storage."""
    folder = "/".join(storage_path.split("/")[:-1])
    filename = storage_path.split("/")[-1]
    try:
        result = supabase.storage.from_(BUCKET).list(folder, {"limit": 1000})
        return any(item['name'] == filename for item in result)
    except:
        return False


def upload_pdf(url, storage_path, pdf_info):
    """Download and upload a PDF."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/pdf,*/*"
        }
        response = requests.get(url, headers=headers, timeout=60, allow_redirects=True)
        
        if response.status_code == 200:
            content = response.content
            # Check for PDF signature
            if content[:4] != b'%PDF':
                # Might be HTML error page
                if b'<!DOCTYPE' in content[:100] or b'<html' in content[:100]:
                    return False, "HTML response (not PDF)"
                # Some PDFs have BOM or whitespace
                if b'%PDF' in content[:20]:
                    pass  # Still a PDF
                else:
                    return False, "Invalid PDF signature"
            
            result = supabase.storage.from_(BUCKET).upload(
                storage_path,
                content,
                {"content-type": "application/pdf", "upsert": "true"}
            )
            
            return True, len(content)
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)[:50]


def print_summary():
    """Print final summary."""
    print("\n" + "="*70)
    print("📊 APL REPAIR SCRAPE SUMMARY")
    print("="*70)
    print(f"   Total PDFs Found: {stats['pdfs_found']}")
    print(f"   PDFs Uploaded: {stats['pdfs_uploaded']}")
    print(f"   PDFs Skipped (Duplicate): {stats['pdfs_skipped']}")
    print(f"   Errors: {stats['errors']}")
    print("="*70)


def verify_apl():
    """Verify APL folder structure after repair."""
    print("\n🔍 APL POST-REPAIR VERIFICATION")
    print("-"*70)
    
    base = STORAGE_PREFIX
    folders = [
        "00_General_Resources",
        "ThermalHEART",
        "Metro_Series",
        "Metro_Series/Sliding_Windows",
        "Metro_Series/Span_Tables",
        "Architectural_Series",
        "Residential_Series",
        "Installation_Details",
        "Installation_Details/Metro_Sliding_Windows",
    ]
    
    total = 0
    for folder in folders:
        full_path = f"{base}/{folder}"
        try:
            result = supabase.storage.from_(BUCKET).list(full_path, {"limit": 100})
            pdfs = [f['name'] for f in result if f.get('name', '').endswith('.pdf')]
            if pdfs:
                print(f"✅ {folder}: {len(pdfs)} PDFs")
                total += len(pdfs)
            else:
                # Check if it's an expected empty subfolder
                subfolders = [f['name'] for f in result if not f.get('name', '').endswith('.pdf') and f.get('name')]
                if subfolders:
                    print(f"📁 {folder}: (subfolders only)")
                else:
                    print(f"⚠️ {folder}: EMPTY")
        except Exception as e:
            print(f"❌ {folder}: Error - {str(e)[:30]}")
    
    print("-"*70)
    print(f"📊 TOTAL APL PDFs: {total}")
    
    if total >= 20:
        print("✅ APL REPAIR: SUCCESS (≥20 PDFs)")
    else:
        print(f"⚠️ APL REPAIR: INCOMPLETE ({total} PDFs, target ≥20)")
    print("-"*70)


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print("🔧 APL WINDOW SOLUTIONS - REPAIR SCRAPER")
    print("="*70)
    print(f"Target: /{STORAGE_PREFIX}/")
    print("Adding: Metro Series, Installation Details, BPIR Documents")
    print("="*70)
    
    for pdf in APL_PDFS:
        storage_path = f"{STORAGE_PREFIX}/{pdf['folder']}/{pdf['filename']}"
        stats["pdfs_found"] += 1
        
        # Check if exists
        if file_exists(storage_path):
            print(f"⏭️ Exists: {pdf['filename'][:50]}...")
            stats["pdfs_skipped"] += 1
            continue
        
        print(f"📥 {pdf['filename'][:55]}...")
        
        success, info = upload_pdf(pdf['url'], storage_path, pdf)
        
        if success:
            tags = []
            if pdf.get("is_monolith"):
                tags.append("MONOLITH")
            if pdf.get("h1_compliance"):
                tags.append("H1")
            
            tag_str = f" [{', '.join(tags)}]" if tags else ""
            print(f"   ✅ Uploaded ({info:,} bytes){tag_str}")
            stats["pdfs_uploaded"] += 1
        else:
            print(f"   ❌ Failed: {info}")
            stats["errors"] += 1
        
        time.sleep(0.3)
    
    print_summary()
    verify_apl()
    print("\n✅ APL Repair Scrape Complete!")
