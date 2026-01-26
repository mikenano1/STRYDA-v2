#!/usr/bin/env python3
"""
Steel & Tube Group C - Heavy Structural & Fasteners
Reinforcing, Structural Sections, Fortress Fasteners, Stainless Steel
"""

import os
import sys
import re
import requests
import time
from urllib.parse import urljoin, unquote

sys.path.insert(0, '/app/backend-minimal')

from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

from supabase import create_client

# Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
BUCKET = 'product-library'

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Catalogue page PDFs discovered from crawl - categorized
CATALOGUES = {
    # Reinforcing Mesh & Bar -> A_Structure/Steel_and_Tube/Reinforcing_Mesh_Bar/
    "Reinforcing_Mesh_Bar": {
        "storage_path": "A_Structure/Steel_and_Tube/Reinforcing_Mesh_Bar",
        "naming_prefix": "Steel and Tube - Reinforcing",
        "pdfs": [
            ("661XXL Mesh Spec Sheet", "https://steelandtube.co.nz/sites/default/files/catalogues/Fortress%20Hurricane%20Mesh%20Spec%20Sheet%20661XXL%20Dec%202025.pdf"),
            ("Construction Mesh Spec Sheet", "https://steelandtube.co.nz/sites/default/files/catalogues/Hurricane%20Construction%20Mesh.pdf"),
            ("Seismic Mesh Spec Sheet", "https://steelandtube.co.nz/sites/default/files/catalogues/Hurricane%20Seismic%20Mesh.pdf"),
            ("Step Thru Mesh Spec Sheet", "https://steelandtube.co.nz/sites/default/files/catalogues/Hurricane%20Mesh%20Spec%20Sheet%20August%202025-Step%20thru.pdf"),
            ("Steel Product Guide - Merchant Bar", "https://steelandtube.co.nz/sites/default/files/catalogues/S%26T_Steel_Product_Guide_Feb2017-01_0_0.pdf"),
        ]
    },
    
    # Structural Sections -> A_Structure/Steel_and_Tube/Structural_Sections_Beams/
    "Structural_Sections_Beams": {
        "storage_path": "A_Structure/Steel_and_Tube/Structural_Sections_Beams",
        "naming_prefix": "Steel and Tube - Structural Sections",
        "pdfs": [
            ("Steel Product Guide", "https://steelandtube.co.nz/sites/default/files/catalogues/S%26T_Steel_Product_Guide_Feb2017-01_0_0.pdf"),
            ("Engineering Steels Catalogue", "https://steelandtube.co.nz/sites/default/files/catalogues/ST-Engineering-Steels-Catalogue_Oct%202024.pdf"),
            ("Zalmax Specification Sheet", "https://steelandtube.co.nz/sites/default/files/catalogues/Zalmax%20Spec%20Sheet%20Nov%202025.pdf"),
            ("From The Ground Up Product Guide", "https://steelandtube.co.nz/sites/default/files/catalogues/S%26T%20From%20the%20Ground%20Up%20Product%20Guide_Dec%202024_Final_web.pdf"),
        ]
    },
    
    # Fortress Fasteners -> F_Manufacturers/Fortress_Fasteners/
    "Fortress_Fasteners": {
        "storage_path": "F_Manufacturers/Fortress_Fasteners",
        "naming_prefix": "Fortress Fasteners",
        "pdfs": [
            # Main catalogue
            ("Product Guide Complete", "https://steelandtube.co.nz/sites/default/files/catalogues/Fortress%20Fasteners%20Product%20Guide%202024.pdf"),
            # Rivets
            ("Blind Rivet Nuts Nutserts", "https://steelandtube.co.nz/sites/default/files/catalogues/Fortress-Blind-RIvet-Nuts-%28Nutserts%29-Spec-Sheets_Oct-2024.pdf"),
            ("Blind Rivets Domed CSK Aluminium", "https://steelandtube.co.nz/sites/default/files/catalogues/Fortress%20Blind%20Rivet%20R73AA%20DOMED%20%26%20CSK%20HEAD%20-%20ALUM%20Spec%20Sheet%20Oct%202024.pdf"),
            ("Blind Rivets Domed CSK Aluminium Steel", "https://steelandtube.co.nz/sites/default/files/catalogues/Fortress%20Blind%20Rivet%20R73AS%20R72AS%20DOMED%20%26%20CSK%20HEAD%20-%20ALUM-STEEL%20Spec%20Sheet_Oct%202024_v3.pdf"),
            ("Blind Rivets Domed Monel Steel", "https://steelandtube.co.nz/sites/default/files/catalogues/Fortress%20Blind%20Rivet%20R73MS%20DOMED%20HEAD%20-%20MONEL%20STEEL%20Spec%20Sheet_Oct%202024_v4.pdf"),
            ("Blind Rivets Domed Stainless Steel", "https://steelandtube.co.nz/sites/default/files/catalogues/Fortress%20Blind%20Rivet%20R73STST%20DOMED%20HEAD%20-%20STAINLESS%20STEEL%20Spec%20Sheet_OCT%202024_v4.pdf"),
            ("Blind Rivets Large Flange", "https://steelandtube.co.nz/sites/default/files/catalogues/Fortress%20Blind%20Rivet%20R73ASL%20DOMED%20HEAD%20W%20LARGE%20FLANGE%20-%20ALUM-ST%20Spec%20Sheet_Oct%202024.pdf"),
            # Screws
            ("Bugle Batten Screws", "https://steelandtube.co.nz/sites/default/files/catalogues/Fortress%20Bugle%20Batten%20Screw%20Spec%20Sheet_APR%202024.pdf"),
            ("Decking Wood Screws", "https://steelandtube.co.nz/sites/default/files/catalogues/Fortress%20Decking%20Screws%20Spec%20Sheet_April%202024.pdf"),
            ("Self Drilling Screws Steel", "https://steelandtube.co.nz/sites/default/files/catalogues/Fortress%20Self%20Drilling%20Screws-Steel%20Spec%20Sheet_Apr%202024.pdf"),
            ("Self Drilling Screws Timber Type 17", "https://steelandtube.co.nz/sites/default/files/catalogues/Fortress%20Self%20Drilling%20Screws-Timber%20Type%2017%20Spec%20Sheet_Apr%202024.pdf"),
            ("Wingtek Self Driller", "https://steelandtube.co.nz/sites/default/files/catalogues/Fortress%20Wingteks%20spec%20sheet_Apr%202024.pdf"),
            ("RoofFast Self Drilling Screws", "https://steelandtube.co.nz/sites/default/files/catalogues/Fortress%20RoofFast%20spec%20sheet_Jul%202023_web.pdf"),
            # Anchors
            ("Metal Pin Anchors", "https://steelandtube.co.nz/sites/default/files/catalogues/Metal%20Pin%20Anchor%20Spec%20Sheet%20July%202025.pdf"),
            ("Nail In Anchors", "https://steelandtube.co.nz/sites/default/files/catalogues/Fortress%20Nail%20in%20Anchors%20spec%20sheet_APR%202024.pdf"),
            ("Screw Bolts", "https://steelandtube.co.nz/sites/default/files/catalogues/Fortress%20Screwbolts%20spec%20sheet_April%202024.pdf"),
            ("Throughbolt Galvanised", "https://steelandtube.co.nz/sites/default/files/catalogues/Fortress_Throughbolt_Spec_Sheet_Galvanised_Oct%202025.pdf"),
            ("Throughbolt Stainless", "https://steelandtube.co.nz/sites/default/files/catalogues/Fortress_Throughbolt_Spec_Sheet_Stainless_Oct%202025.pdf"),
            ("TX-Con Screw Anchors CSK Phillips", "https://steelandtube.co.nz/sites/default/files/catalogues/TX-Con%20Screw%20Anchor%20CSK%20Phillips%20Spec%20Sheet.pdf"),
            ("TX-Con Screw Anchors Slot Hex", "https://steelandtube.co.nz/sites/default/files/catalogues/TX-Con%20Screw%20Anchor%20Slot%20Hex%20Spec%20Sheet.pdf"),
            # Bolts & Hardware
            ("Hanger Bolts", "https://steelandtube.co.nz/sites/default/files/catalogues/Fortress%20Hanger%20Bolt%20Spec%20Sheet_April%202024.pdf"),
            ("Threaded Rod Metric", "https://steelandtube.co.nz/sites/default/files/catalogues/Fortress%20Threaded%20Rod%20Spec%20Sheet%20Apr%202024.pdf"),
            ("Tie Wire Fasteners", "https://steelandtube.co.nz/sites/default/files/catalogues/Fortress%20Tire%20Wire%20Spec%20Sheet_APR%202024.pdf"),
            ("Coatings Guide", "https://steelandtube.co.nz/sites/default/files/catalogues/Fortress%20Coating%20Spec%20Sheet_APR%202024.pdf"),
            # Tools
            ("TJEP Gas Powered Nailers", "https://steelandtube.co.nz/sites/default/files/catalogues/TJEP-Gas-powered-Nailers-Product-Guide_Oct-2024.pdf"),
        ]
    },
    
    # Stainless Steel -> B_Enclosure/Steel_and_Tube/Stainless_Steel/
    "Stainless_Steel": {
        "storage_path": "B_Enclosure/Steel_and_Tube/Stainless_Steel",
        "naming_prefix": "Steel and Tube - Stainless Steel",
        "pdfs": [
            ("Product Catalogue", "https://steelandtube.co.nz/sites/default/files/catalogues/S%26T_Stainless_Cat_May2016.pdf"),
            ("Pocket Guide", "https://steelandtube.co.nz/sites/default/files/catalogues/S%26T_Stainless_Pocket_Guide.pdf"),
            ("Kleanflow Product Guide", "https://steelandtube.co.nz/sites/default/files/catalogues/S%26T_Kleanflow.pdf"),
            ("Pipetite Product Guide", "https://steelandtube.co.nz/sites/default/files/catalogues/S%26T_Stainless_Pipetite.pdf"),
            # Architectural Rimex
            ("Rimex Coloured Mirrors Satins", "https://steelandtube.co.nz/sites/default/files/catalogues/ColouredMirrorsSatins.pdf"),
            ("Rimex Colourtex", "https://steelandtube.co.nz/sites/default/files/catalogues/Colourtex.pdf"),
            ("Rimex Granex", "https://steelandtube.co.nz/sites/default/files/catalogues/Granex.pdf"),
            ("Rimex Impressions", "https://steelandtube.co.nz/sites/default/files/catalogues/Impressions.pdf"),
            ("Rimex Metalart", "https://steelandtube.co.nz/sites/default/files/catalogues/MetalArt.pdf"),
            ("Rimex Platinum", "https://steelandtube.co.nz/sites/default/files/catalogues/Platinum.pdf"),
            ("Rimex Rigitube", "https://steelandtube.co.nz/sites/default/files/catalogues/RigiTube.pdf"),
            ("Rimex Super Mirror", "https://steelandtube.co.nz/sites/default/files/catalogues/SuperMirror.pdf"),
            ("Rimex Textured", "https://steelandtube.co.nz/sites/default/files/catalogues/TexturedStainlessSteelPatterns.pdf"),
        ]
    },
    
    # Chain & Rigging -> A_Structure/Steel_and_Tube/Chain_Rigging/
    "Chain_Rigging": {
        "storage_path": "A_Structure/Steel_and_Tube/Chain_Rigging",
        "naming_prefix": "Steel and Tube - Chain Rigging",
        "pdfs": [
            ("Services Product Flyer", "https://steelandtube.co.nz/sites/default/files/catalogues/S%26T%20Chain%20%26%20Rigging%20Flyer_Jan%202021.pdf"),
            ("Lifting Sling WLL Chart", "https://steelandtube.co.nz/sites/default/files/catalogues/Working%20Load%20Limit%20Chart.pdf"),
            ("Mobile Testing Lifting Equipment", "https://steelandtube.co.nz/sites/default/files/catalogues/Testing%20Services%20Catalogue.pdf"),
            ("Pewag Stainless Steel Chain Fittings", "https://steelandtube.co.nz/sites/default/files/catalogues/S%26T_Pewag_Stainless_Steel_Lifting_Jul2017.pdf"),
        ]
    },
}


def clean_filename(text):
    """Clean text for filename"""
    cleaned = unquote(text)
    cleaned = cleaned.replace('/', '-').replace('\\', '-')
    cleaned = cleaned.replace(':', '-').replace('*', '').replace('?', '')
    cleaned = cleaned.replace('"', '').replace('<', '').replace('>', '')
    cleaned = cleaned.replace('|', '-').replace('+', ' ').replace('_', ' ')
    cleaned = cleaned.replace('%20', ' ').replace('&', 'and')
    cleaned = re.sub(r'\.pdf$', '', cleaned, flags=re.IGNORECASE)
    return ' '.join(cleaned.split())


def create_filename(prefix, link_text):
    """Create standardized filename"""
    clean_text = clean_filename(link_text)
    return f"{prefix} - {clean_text}.pdf"


def download_pdf(url):
    """Download PDF content"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=60, headers=headers, allow_redirects=True)
        if response.status_code == 200 and len(response.content) > 1000:
            if response.content[:4] == b'%PDF':
                return response.content
        return None
    except Exception as e:
        print(f"      ⚠️ Download error: {e}")
        return None


def upload_to_supabase(content, storage_path, filename):
    """Upload PDF to Supabase"""
    full_path = f"{storage_path}/{filename}"
    try:
        supabase.storage.from_(BUCKET).upload(
            full_path,
            content,
            {"content-type": "application/pdf", "upsert": "true"}
        )
        return True
    except Exception as e:
        if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
            return True
        print(f"      ⚠️ Upload error: {e}")
        return False


def process_category(category_name, config):
    """Process a category of PDFs"""
    storage_path = config['storage_path']
    prefix = config['naming_prefix']
    pdfs = config['pdfs']
    
    print(f"\n{'='*60}")
    print(f"📦 {category_name}")
    print(f"   Path: {BUCKET}/{storage_path}/")
    print(f"   PDFs to process: {len(pdfs)}")
    
    successful = 0
    for link_text, url in pdfs:
        filename = create_filename(prefix, link_text)
        
        content = download_pdf(url)
        if not content:
            print(f"   ❌ {link_text[:45]}...")
            continue
        
        size_kb = len(content) / 1024
        if upload_to_supabase(content, storage_path, filename):
            successful += 1
            print(f"   ✅ {link_text[:45]}... ({size_kb:.0f}KB)")
    
    print(f"   📊 Uploaded: {successful}/{len(pdfs)}")
    return successful


def main():
    print("=" * 60)
    print("🏗️ STEEL & TUBE GROUP C - HEAVY STRUCTURAL & FASTENERS")
    print("=" * 60)
    
    results = {}
    total_files = 0
    
    for category_name, config in CATALOGUES.items():
        count = process_category(category_name, config)
        results[category_name] = count
        total_files += count
        time.sleep(0.5)
    
    # Final report
    print("\n" + "=" * 60)
    print("📊 FINAL REPORT")
    print("=" * 60)
    print(f"\n{'Category':<35} {'Files':>8}")
    print("-" * 45)
    for name, count in results.items():
        status = "✅" if count > 0 else "⚠️"
        print(f"{status} {name:<33} {count:>8}")
    
    print("-" * 45)
    print(f"{'TOTAL':<35} {total_files:>8}")
    
    # Category breakdown
    reinforcing = results.get('Reinforcing_Mesh_Bar', 0)
    structural = results.get('Structural_Sections_Beams', 0)
    fasteners = results.get('Fortress_Fasteners', 0)
    stainless = results.get('Stainless_Steel', 0)
    rigging = results.get('Chain_Rigging', 0)
    
    print(f"\n📊 CATEGORY BREAKDOWN:")
    print(f"   Reinforcing Mesh & Bar: {reinforcing}")
    print(f"   Structural Sections: {structural}")
    print(f"   Fortress Fasteners: {fasteners}")
    print(f"   Stainless Steel: {stainless}")
    print(f"   Chain & Rigging: {rigging}")
    
    print(f"\n✅ Steel & Tube Group C ingestion complete!")
    return total_files


if __name__ == '__main__':
    main()
