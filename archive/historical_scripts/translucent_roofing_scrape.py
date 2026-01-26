#!/usr/bin/env python3
"""
Translucent Roofing Scraper (Protocol v2.0)
============================================
Downloads technical PDFs for Alsynite, Ampelite, and PSP Suntuf translucent roofing.

Implements strict separation: Residential vs Industrial/Commercial

Author: STRYDA Data Pipeline
Date: 2025-01
"""

import os
import sys
import time
import requests
from supabase import create_client
from dotenv import load_dotenv

sys.path.insert(0, '/app/src')
from ingestion_rules import (
    PROTOCOL_VERSION,
    sanitize_filename,
    is_potential_monolith,
    print_protocol_summary
)

load_dotenv("/app/backend-minimal/.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
BUCKET_NAME = "product-library"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

STORAGE_PREFIX = "B_Enclosure/Translucent_Roofing"

stats = {
    "brands_processed": 0,
    "pdfs_found": 0,
    "pdfs_uploaded": 0,
    "pdfs_skipped_duplicate": 0,
    "monoliths_detected": 0,
    "errors": 0,
}

uploaded_urls = set()


# =============================================================================
# ALSYNITE ONE
# =============================================================================
ALSYNITE_PREFIX = f"{STORAGE_PREFIX}/Alsynite_One"

ALSYNITE_COMMERCIAL = {
    "Topglass_GC": [
        ("Data Sheet", "https://alsynite.co.nz/wp-content/uploads/2019/02/Topglass-GC-Data-Sheet.pdf"),
        ("Installation Guide", "https://alsynite.co.nz/wp-content/uploads/2019/02/Topglass-Installation-Guide-1.pdf"),
        ("Product Brochure", "https://alsynite.co.nz/wp-content/uploads/2019/02/2024.0696-Topglass-Brochure-2024-3_web.pdf"),
        ("Design Considerations", "https://alsynite.co.nz/wp-content/uploads/2019/02/Topglass-Design-Considerations-10042013.pdf"),
        ("Popular Profiles", "https://alsynite.co.nz/wp-content/uploads/2019/02/Topglass-Popular-Profiles-April2025-2.pdf"),
        ("Project Solutions", "https://alsynite.co.nz/wp-content/uploads/2019/02/Topglass-Project-Solutions.pdf"),
    ],
    "Topglass_GC_Ultra_Safe": [
        ("Data Sheet", "https://alsynite.co.nz/wp-content/uploads/2019/02/Topglass-GC-Ultra-Safe-Data-Sheet-WEB.pdf"),
        ("Installation Guide", "https://alsynite.co.nz/wp-content/uploads/2019/02/Topglass-Installation-Guide-5.pdf"),
        ("Design Considerations", "https://alsynite.co.nz/wp-content/uploads/2019/02/Topglass-Design-Considerations-10042013-5.pdf"),
    ],
    "Topglass_GC_SPF": [
        ("Data Sheet", "https://alsynite.co.nz/wp-content/uploads/2019/02/Topglass-GC-SPF-Data-Sheet.pdf"),
        ("Installation Guide", "https://alsynite.co.nz/wp-content/uploads/2019/02/Topglass-Installation-Guide-4.pdf"),
        ("Design Considerations", "https://alsynite.co.nz/wp-content/uploads/2019/02/Topglass-Design-Considerations-10042013-4.pdf"),
        ("Popular Profiles", "https://alsynite.co.nz/wp-content/uploads/2019/02/Topglass-Popular-Profiles-April2013-4-1.pdf"),
        ("Project Solutions", "https://alsynite.co.nz/wp-content/uploads/2019/02/Topglass-Project-Solutions-4.pdf"),
    ],
    "Topglass_GC_FR50": [
        ("Data Sheet", "https://alsynite.co.nz/wp-content/uploads/2019/02/Topglass%C2%AE-GC-FR50-Data-Sheet.pdf"),
        ("Installation Guide", "https://alsynite.co.nz/wp-content/uploads/2019/02/Topglass-Installation-Guide-3.pdf"),
        ("Design Considerations", "https://alsynite.co.nz/wp-content/uploads/2019/02/Topglass-Design-Considerations-10042013-3.pdf"),
        ("Popular Profiles", "https://alsynite.co.nz/wp-content/uploads/2019/02/Topglass-Popular-Profiles-April2013-3.pdf"),
        ("Project Solutions", "https://alsynite.co.nz/wp-content/uploads/2019/02/Topglass-Project-Solutions-3.pdf"),
    ],
    "Topclad_GC": [
        ("Data Sheet", "https://alsynite.co.nz/wp-content/uploads/2019/02/Topclad-GC-Data-Sheet.pdf"),
        ("Installation Guide", "https://alsynite.co.nz/wp-content/uploads/2019/02/Topglass-Installation-Guide-7.pdf"),
    ],
}

ALSYNITE_TWIN_SKIN = {
    "TwinSkin_Systems": [
        ("Data Sheet", "https://alsynite.co.nz/wp-content/uploads/2019/02/Twin-Skin-Data-Sheet.pdf"),
        ("Installation Instructions", "https://alsynite.co.nz/wp-content/uploads/2019/02/Twin-Skin-Installation-Instructions-Nov16.pdf"),
    ],
    "TripleSkin_Systems": [
        ("Data Sheet", "https://alsynite.co.nz/wp-content/uploads/2019/02/Triple-Skin-Data-Sheet.pdf"),
        ("Installation Guide", "https://alsynite.co.nz/wp-content/uploads/2019/02/TOP002-Triple-Skin-Installation-web.pdf"),
        ("Profile Detail", "https://alsynite.co.nz/wp-content/uploads/2019/02/Topglass-Triple-Skin-End-Lap-Dec-14.pdf"),
    ],
}

ALSYNITE_RESIDENTIAL = {
    "Laserlite_2000": [
        ("Data Sheet", "https://alsynite.co.nz/wp-content/uploads/2019/02/2Laserlite-NZ-2000P-Data-Sheet-Jun-15.pdf"),
        ("Installation Instructions", "https://alsynite.co.nz/wp-content/uploads/2019/02/Laserlite-NZ-Installation-Instructions-Jun-15.pdf"),
        ("Product Brochure", "https://alsynite.co.nz/wp-content/uploads/2025/03/2024.0656-A1-Laserlite-Brochure-2024_web.pdf"),
        ("Handling Storage Cleaning", "https://alsynite.co.nz/wp-content/uploads/2019/02/Laserlite-handling_storage_cleaning_instructions-WEB.pdf"),
    ],
    "Laserlite_3000": [
        ("Installation Instructions", "https://alsynite.co.nz/wp-content/uploads/2019/02/3Laserlite-NZ-Installation-Instructions-Jun-15.pdf"),
        ("Product Brochure", "https://alsynite.co.nz/wp-content/uploads/2025/03/2024.0656-A1-Laserlite-Brochure-2024_web.pdf"),
    ],
    "Laserlite_Twinwall": [
        ("Product Brochure", "https://alsynite.co.nz/wp-content/uploads/2019/02/2024.0724-Twinwall-Brochure-2024-2_web.pdf"),
        ("Installation Guide", "https://alsynite.co.nz/wp-content/uploads/2019/02/Laserlite-Twinwall-Installation-Guide-WEBv3.pdf"),
    ],
    "Custom_Glaze": [
        ("Product Brochure", "https://alsynite.co.nz/wp-content/uploads/2019/02/2022.0469-AONE-Custom-Glaze-Brochure-2022_web.pdf"),
        ("Installation Guide", "https://alsynite.co.nz/wp-content/uploads/2019/02/2023.0595-Custom-Glaze-Installation-2023.pdf"),
    ],
    "Crystalite_Glazing": [
        ("Product Brochure", "https://alsynite.co.nz/wp-content/uploads/2019/02/2024.0727-Crystalite-Brochure-2024_web-2.pdf"),
        ("Warranty", "https://alsynite.co.nz/wp-content/uploads/2019/02/Crystalite-Warranty.pdf"),
    ],
    "Sunline": [
        ("Product Brochure", "https://alsynite.co.nz/wp-content/uploads/2019/02/Sunline-Technical-Brochure-A4-WEB.pdf"),
    ],
    "Skylite_GRP": [
        ("Product Brochure", "https://alsynite.co.nz/wp-content/uploads/2019/02/FLYER-Skylite-SKY-May-2014.pdf"),
        ("Installation Guide", "https://alsynite.co.nz/wp-content/uploads/2019/02/Skylite-A4-DS-Flyer-Installation-WEB-130514.pdf"),
    ],
    "Sunshade_PVC": [
        ("Product Brochure", "https://alsynite.co.nz/wp-content/uploads/2019/02/Sunshade-Brochure-A4-WEB-May-15.pdf"),
    ],
}

ALSYNITE_VENTILATION = {
    "Industrial_Ventilators": [
        ("Technical Dimensions", "https://alsynite.co.nz/wp-content/uploads/2020/12/2020.0222-AONE-Industrial-Vents-and-Turbines_Installation.pdf"),
        ("Data Sheet", "https://alsynite.co.nz/wp-content/uploads/2020/12/2020.0222-AONE-Industrial-Vents-and-Turbines_DataSheet.pdf"),
        ("Product Brochure", "https://alsynite.co.nz/wp-content/uploads/2019/02/Industrial-Turbine-Ventilators-WEB-Sept-14.pdf"),
    ],
    "Spinaway_300": [
        ("Product Brochure", "https://alsynite.co.nz/wp-content/uploads/2019/02/Spinaway-300-Flyer-WEB.pdf"),
        ("Installation Instructions", "https://alsynite.co.nz/wp-content/uploads/2019/02/Spinaway-Installation-Instructions.pdf"),
    ],
    "Green_Vent_Solar": [
        ("Product Brochure", "https://alsynite.co.nz/wp-content/uploads/2019/02/Green-Vent-Solar-GVS-F-D-032013.pdf"),
        ("Dimensions", "https://alsynite.co.nz/wp-content/uploads/2019/02/GVS-branded-dimensions-1.pdf"),
        ("Maintenance Guide", "https://alsynite.co.nz/wp-content/uploads/2019/02/Green-Vent-Solar-Product-Maintenance-Guide.pdf"),
    ],
    "Sky_Tunnel": [
        ("Product Brochure", "https://alsynite.co.nz/wp-content/uploads/2019/02/Sky-Tunnel-DS-A4-WEB.pdf"),
    ],
    "Lumino_Tubular": [
        ("Product Brochure", "https://alsynite.co.nz/wp-content/uploads/2019/02/Lumino-Brochure-20112012WEB.pdf"),
        ("Warranty", "https://alsynite.co.nz/wp-content/uploads/2019/02/WARRANTY-Lumino-SAMPLE20112012.pdf"),
    ],
    "Roof_Access_Hatches": [
        ("Product Brochure", "https://alsynite.co.nz/wp-content/uploads/2019/02/RAH001-Roof-Access-Hatches-A4-PRINT-no-crops.pdf"),
    ],
}

ALSYNITE_ACCESSORIES = {
    "Accessories": [
        ("Multipurpose Fasteners Brochure", "https://alsynite.co.nz/wp-content/uploads/2019/02/2020.0182-AONE-Multipurpose-Fasteners-DL_web.pdf"),
        ("PC Fixings Brochure", "https://alsynite.co.nz/wp-content/uploads/2019/02/2024.0692-Polycarbonate-Screws-Brochure_web.pdf"),
        ("Polycarbonate Flashings", "https://alsynite.co.nz/wp-content/uploads/2019/02/Polycarbonate-Flashings.pdf"),
    ],
}

ALSYNITE_GENERAL = {
    "00_General_Resources": [
        ("Warranty Request Template", "https://alsynite.co.nz/wp-content/uploads/2019/02/Warranty-Request-Template.pdf"),
    ],
}


# =============================================================================
# AMPELITE NZ
# =============================================================================
AMPELITE_PREFIX = f"{STORAGE_PREFIX}/Ampelite_NZ"

AMPELITE_FIBERGLASS = {
    "Wonderglas_GC": [
        ("End Lap Corrugate Detail", "https://ampelite.co.nz/wp-content/uploads/DWG%20files/Wonderglass-End-Lap-Corrugate-Tech-Details.pdf"),
        ("End Lap Trapezoidal Detail", "https://ampelite.co.nz/wp-content/uploads/DWG%20files/Wonderglass-End-Lap-Trapezoidal-Tech-Details.pdf"),
        ("End Lap Tray Detail", "https://ampelite.co.nz/wp-content/uploads/DWG%20files/Wonderglass-End-Lap-Tray-Tech-Details.pdf"),
        ("End Stop Corrugate Detail", "https://ampelite.co.nz/wp-content/uploads/DWG%20files/Wonderglass-End-Stop-Corrugate-Tech-Details.pdf"),
        ("End Stop Trapezoidal Detail", "https://ampelite.co.nz/wp-content/uploads/DWG%20files/Wonderglass-End-Stop-Trapezoidal-Tech-Details.pdf"),
        ("End Stop Tray Detail", "https://ampelite.co.nz/wp-content/uploads/DWG%20files/Wonderglass-End-Stop-Tray-Tech-Details.pdf"),
        ("Mid Span Support Corrugate", "https://ampelite.co.nz/wp-content/uploads/DWG%20files/Wonderglass-Mid-Span-Support-Corrugate-Tech-Details.pdf"),
        ("Mid Span Support ISO", "https://ampelite.co.nz/wp-content/uploads/DWG%20files/Wonderglass-Mid-Span-Support-Isometric-Tech-Details.pdf"),
        ("Ridge Corrugate Detail", "https://ampelite.co.nz/wp-content/uploads/DWG%20files/Wonderglass-Ridge-Corrugate-Tech-Details.pdf"),
        ("Ridge Trapezoidal Detail", "https://ampelite.co.nz/wp-content/uploads/DWG%20files/Wonderglass-Ridge-Trapezoidal-Tech-Details.pdf"),
        ("Ridge Tray Detail", "https://ampelite.co.nz/wp-content/uploads/DWG%20files/Wonderglass-Ridge-Tray-Tech-Details.pdf"),
        ("Side Lap Corrugate Detail", "https://ampelite.co.nz/wp-content/uploads/DWG%20files/Wonderglass-Side-Lap-Corrugate-Tech-Details.pdf"),
        ("Side Lap Trapezoidal Detail", "https://ampelite.co.nz/wp-content/uploads/DWG%20files/Wonderglass-Side-Lap-Trapezoidal-Tech-Details.pdf"),
        ("Side Lap Tray Detail", "https://ampelite.co.nz/wp-content/uploads/DWG%20files/Wonderglass-Side-Lap-Tray-Tech-Details.pdf"),
        ("Side Lap Tray Multiple Detail", "https://ampelite.co.nz/wp-content/uploads/DWG%20files/Wonderglass-Side-Lap-Tray-Multiple-Tech-Details.pdf"),
    ],
}

AMPELITE_DUALROOF = {
    "Dualroof_Premium": [
        ("5 Rib 2 Wall Lexan Drawing", "https://ampelite.co.nz/wp-content/uploads/DWG%20files/Ampelite-Dualroof-Premium-Drawing-5-Rib-2-Wall-Lexan.pdf"),
        ("5 Rib 5 Wall Lexan Drawing", "https://ampelite.co.nz/wp-content/uploads/DWG%20files/Ampelite-Dualroof-Premium-Drawing-5-Rib-5-Wall-Lexan.pdf"),
    ],
}

AMPELITE_DRIPGUARD = {
    "DripGuard": [
        ("HR Profile Detail", "https://ampelite.co.nz/wp-content/uploads/DWG%20files/DripGuard_HR_Profile.pdf"),
        ("LR Profile Detail", "https://ampelite.co.nz/wp-content/uploads/DWG%20files/DripGuard_LR_Profile.pdf"),
        ("Product Brochure", "https://ampelite.co.nz/wp-content/uploads/DWG%20files/DripGuard-Brochure-v4-web.pdf"),
    ],
}

AMPELITE_THERMOCLICK = {
    "Thermoclick": [
        ("Accessories 1", "https://ampelite.co.nz/wp-content/uploads/DWG%20files/Lexan-Thermoclick-Accessories.pdf"),
        ("Accessories 2", "https://ampelite.co.nz/wp-content/uploads/DWG%20files/Lexan-Thermoclick-Accessories-2.pdf"),
        ("Profiles", "https://ampelite.co.nz/wp-content/uploads/DWG%20files/Lexan-Thermoclick-Accessories-Profiles.pdf"),
        ("Channel Corner Detail", "https://ampelite.co.nz/wp-content/uploads/DWG%20files/Thermoclick-Channel-Corner-Details%20%281%29.pdf"),
        ("External Corner Detail 1", "https://ampelite.co.nz/wp-content/uploads/DWG%20files/Thermoclick-External-Corner-Details-1.pdf"),
        ("External Corner Detail 2", "https://ampelite.co.nz/wp-content/uploads/DWG%20files/Thermoclick-External-Corner-Details-2.pdf"),
        ("Internal Corner Detail 1", "https://ampelite.co.nz/wp-content/uploads/DWG%20files/Thermoclick-Internal-Corner-Details-1.pdf"),
        ("Internal Corner Detail 2", "https://ampelite.co.nz/wp-content/uploads/DWG%20files/Thermoclick-Internal-Corner-Details-2.pdf"),
        ("Typical Glazing Detail 1", "https://ampelite.co.nz/wp-content/uploads/DWG%20files/Thermoclick-Typical-Glazing-Detail-1.pdf"),
        ("Typical Glazing Detail 2", "https://ampelite.co.nz/wp-content/uploads/DWG%20files/Thermoclick-Typical-Glazing-Detail-2.pdf"),
        ("Typical Glazing Detail 3", "https://ampelite.co.nz/wp-content/uploads/DWG%20files/Thermoclick-Typical-Glazing-Detail-3.pdf"),
    ],
}

AMPELITE_GENERAL = {
    "00_General_Resources": [
        ("Commercial Product Catalogue", "https://ampelite.co.nz/wp-content/uploads/2024/08/Ampelite-New-Zealand-Product-Catalogue.pdf"),
    ],
}


# =============================================================================
# PSP SUNTUF
# =============================================================================
PSP_PREFIX = f"{STORAGE_PREFIX}/PSP_Suntuf"

PSP_SUNTUF = {
    "Suntuf_Polycarbonate": [
        ("Product Brochure 2024", "https://www.suntuf.co.nz/range/downloads/Suntuf%20A3%20Fold%20A4%20Brochure_2024_LR.pdf"),
        ("Product Technical Statement", "https://www.suntuf.co.nz/range/downloads/product-technical-statement.pdf"),
        ("Cleaning and Maintenance Guide", "https://www.suntuf.co.nz/range/downloads/Polycarbonate%20Roofing%20Cleaning%20%20Maintenance.pdf"),
        ("Warranty Statements", "https://www.suntuf.co.nz/range/downloads/New%20Warranty%20Statements.pdf"),
        ("CodeMark Pass 2024", "https://www.suntuf.co.nz/range/downloads/19117_PSP_Suntuf_pass_v2_5_exp_05-2024.pdf"),
    ],
    "Suntuf_Commercial": [
        ("Commercial Brochure", "https://www.suntuf.co.nz/range/downloads/SunTuf%20Commercial%20Brochure.pdf"),
        ("Commercial PC Sheets Pass", "https://www.suntuf.co.nz/range/downloads/19218_PSP_Suntuf_Commercial_Polycarbonate_Sheets_pass_v1_3_exp_11-2023.pdf"),
    ],
    "Suntuf_Twinwall": [
        ("Twinwall Brochure", "https://www.suntuf.co.nz/range/downloads/SunTuf%20Twinwall%20Brochure_1.pdf"),
    ],
}

PSP_SUNGLAZE = {
    "SunGlaze": [
        ("Product Brochure", "https://www.suntuf.co.nz/range/downloads/Sunglaze%20Brochure_web.pdf"),
        ("Installation Guide 2024", "https://www.suntuf.co.nz/range/downloads/SunGlaze%20Installation%20Guide_2024.pdf"),
        ("Specification Guide", "https://www.suntuf.co.nz/range/downloads/SunTuf%20Sunglaze%20Specification%20Guide.pdf"),
        ("CodeMark Pass", "https://www.suntuf.co.nz/range/downloads/19157_PSP_Suntuf_Sunglaze_pass_v1_2_exp_11-2022.pdf"),
    ],
    "SunTuf_EZGlaze": [
        ("Product Flyer", "https://www.suntuf.co.nz/range/downloads/PSP_SuntufEZGlaze_Flyer_V1.0.pdf"),
    ],
}


def upload_to_supabase(pdf_url: str, storage_path: str, doc_title: str) -> bool:
    """Download PDF and upload to Supabase."""
    try:
        print(f"    📥 {doc_title[:45]}...")
        response = requests.get(pdf_url, timeout=60, allow_redirects=True)
        if response.status_code != 200:
            print(f"    ❌ HTTP {response.status_code}")
            stats["errors"] += 1
            return False
        
        pdf_content = response.content
        if not pdf_content[:4] == b'%PDF':
            print(f"    ⚠️ Not PDF")
            stats["errors"] += 1
            return False
        
        file_size_mb = len(pdf_content) / (1024 * 1024)
        if is_potential_monolith(file_size_mb=file_size_mb):
            stats["monoliths_detected"] += 1
        
        try:
            supabase.storage.from_(BUCKET_NAME).upload(
                storage_path, pdf_content, {"content-type": "application/pdf"}
            )
            print(f"    ✅ Uploaded ({file_size_mb:.1f}MB)")
            return True
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"    ⏭️ Exists")
                stats["pdfs_skipped_duplicate"] += 1
                return False
            print(f"    ❌ {e}")
            stats["errors"] += 1
            return False
    except Exception as e:
        print(f"    ❌ {e}")
        stats["errors"] += 1
        return False


def process_category(brand: str, prefix: str, category: str, folder: str, products: dict):
    """Process products."""
    print(f"\n  📁 {category}")
    
    for product_name, docs in products.items():
        for doc_title, pdf_url in docs:
            stats["pdfs_found"] += 1
            if pdf_url in uploaded_urls:
                stats["pdfs_skipped_duplicate"] += 1
                continue
            
            clean_title = sanitize_filename(doc_title)
            clean_product = product_name.replace('_', ' ')
            filename = f"{brand} - {clean_product} - {clean_title}.pdf"
            storage_path = f"{prefix}/{folder}/{filename}"
            
            if upload_to_supabase(pdf_url, storage_path, doc_title):
                stats["pdfs_uploaded"] += 1
                uploaded_urls.add(pdf_url)
            time.sleep(0.2)


def main():
    print("=" * 70)
    print(f"🌤️ TRANSLUCENT ROOFING SCRAPER (Protocol v{PROTOCOL_VERSION})")
    print("=" * 70)
    print_protocol_summary()
    print("=" * 70)
    
    # ALSYNITE
    print("\n" + "=" * 60)
    print("🏭 ALSYNITE ONE")
    print("=" * 60)
    stats["brands_processed"] += 1
    
    process_category("Alsynite", ALSYNITE_PREFIX, "Commercial (Topglass Industrial GRP)", "Topglass_Industrial", ALSYNITE_COMMERCIAL)
    process_category("Alsynite", ALSYNITE_PREFIX, "Twin/Triple Skin Systems (Insulated)", "Twin_Skin_Systems", ALSYNITE_TWIN_SKIN)
    process_category("Alsynite", ALSYNITE_PREFIX, "Residential (Laserlite DIY)", "Laserlite_Residential", ALSYNITE_RESIDENTIAL)
    process_category("Alsynite", ALSYNITE_PREFIX, "Ventilation", "Ventilation", ALSYNITE_VENTILATION)
    process_category("Alsynite", ALSYNITE_PREFIX, "Accessories", "Accessories", ALSYNITE_ACCESSORIES)
    process_category("Alsynite", ALSYNITE_PREFIX, "General Resources", "00_General_Resources", ALSYNITE_GENERAL)
    
    # AMPELITE
    print("\n" + "=" * 60)
    print("🏭 AMPELITE NZ")
    print("=" * 60)
    stats["brands_processed"] += 1
    
    process_category("Ampelite", AMPELITE_PREFIX, "Wonderglas GC (Industrial Fibreglass)", "Wonderglas_GC", AMPELITE_FIBERGLASS)
    process_category("Ampelite", AMPELITE_PREFIX, "Dualroof Premium", "Dualroof", AMPELITE_DUALROOF)
    process_category("Ampelite", AMPELITE_PREFIX, "DripGuard (Condensation Control)", "DripGuard", AMPELITE_DRIPGUARD)
    process_category("Ampelite", AMPELITE_PREFIX, "Thermoclick (Glazing System)", "Thermoclick", AMPELITE_THERMOCLICK)
    process_category("Ampelite", AMPELITE_PREFIX, "General Resources", "00_General_Resources", AMPELITE_GENERAL)
    
    # PSP SUNTUF
    print("\n" + "=" * 60)
    print("🏭 PSP SUNTUF")
    print("=" * 60)
    stats["brands_processed"] += 1
    
    process_category("PSP", PSP_PREFIX, "Suntuf Polycarbonate (DIY)", "Suntuf", PSP_SUNTUF)
    process_category("PSP", PSP_PREFIX, "SunGlaze Glazing System", "SunGlaze", PSP_SUNGLAZE)
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"Brands: {stats['brands_processed']}")
    print(f"PDFs found: {stats['pdfs_found']}")
    print(f"PDFs uploaded: {stats['pdfs_uploaded']}")
    print(f"Skipped (duplicate): {stats['pdfs_skipped_duplicate']}")
    print(f"Monoliths: {stats['monoliths_detected']}")
    print(f"Errors: {stats['errors']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
