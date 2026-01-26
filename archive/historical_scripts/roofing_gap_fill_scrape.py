#!/usr/bin/env python3
"""
Roofing Gap Fill Scraper (Protocol v2.0)
========================================
Completes the roofing sector with Tiles, Shingles, and Membranes.

Target Manufacturers:
- Gerard Roofing (Metal Tiles)
- GAF Shingles (Asphalt)
- Nuralite Membranes (Flat Roofs)
- Solerati Tiles (Clay) - SKIPPED: Website not accessible

Uses src/ingestion_rules.py for Protocol v2.0 enforcement

Author: STRYDA Data Pipeline
Date: 2025-01
"""

import os
import sys
import re
import time
import requests
from supabase import create_client
from dotenv import load_dotenv

sys.path.insert(0, '/app/src')
from ingestion_rules import (
    PROTOCOL_VERSION,
    is_generic_filename,
    sanitize_filename,
    is_potential_monolith,
    print_protocol_summary
)

load_dotenv("/app/backend-minimal/.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
BUCKET_NAME = "product-library"

print(f"🔗 Supabase URL: {SUPABASE_URL[:30]}..." if SUPABASE_URL else "❌ No SUPABASE_URL")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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
# GAF SHINGLES (Asphalt)
# =============================================================================
GAF_SHINGLES_PREFIX = "B_Enclosure/GAF_Shingles"

GAF_TIMBERLINE_HDZ = {
    "Timberline_HDZ": [
        # Technical Specs
        ("BRANZ Appraisal 529", "https://gafroofing.co.nz/wp-content/downloads/GAF-technical-documents/529_2022.pdf"),
        ("NZ Specifications 2018", "https://gafroofing.co.nz/wp-content/downloads/GAF-technical-documents/GAF-specifications-nz-2018.pdf"),
        ("Cross Section Detail", "https://gafroofing.co.nz/wp-content/downloads/GAF-technical-documents/GAF-cross-section-08.10.2018.pdf"),
        ("Timberline Application Instructions", "https://gafroofing.co.nz/wp-content/downloads/GAF-technical-documents/Timberline_Series_Application_Instructions.pdf.pdf"),
        ("System Design Details", "https://gafroofing.co.nz/wp-content/downloads/GAF-technical-documents/Asphalt_Shingle_Roof_System_Design_Details_05.07.18.pdf"),
        ("Timberline HDZ Data Sheet", "https://gafroofing.co.nz/wp-content/downloads/GAF-technical-documents/timberline-hdz-restz102c-data-sheet.pdf"),
        # Nailing & Installation
        ("Fixing Specifications", "https://gafroofing.co.nz/wp-content/downloads/drawings/fixing_specifications.pdf"),
        ("Construction Notes", "https://gafroofing.co.nz/wp-content/downloads/drawings/construction_notes.pdf"),
        ("Shingle Application Low Slopes", "https://gafroofing.co.nz/wp-content/downloads/GAF-technical-documents/shingle-application-on-low-slopes-2-12-to-4-12-steep-slope-43-817-v2.pdf"),
        ("Staples vs Nails", "https://gafroofing.co.nz/wp-content/downloads/GAF-technical-documents/staples-vs-nails-for-shingle-applications-steep-slope-tec-43-822-v2.pdf"),
        ("Fastening Method Detail", "https://gafroofing.co.nz/wp-content/downloads/drawings/27_fastening_method.pdf"),
        # Maintenance
        ("Roof Maintenance Schedule", "https://gafroofing.co.nz/wp-content/downloads/GAF-MAINTENANCE.pdf"),
    ],
}

GAF_SLATELINE = {
    "Slateline": [
        ("Slateline Data Sheet", "https://gafroofing.co.nz/wp-content/downloads/GAF-technical-documents/slateline-shingles-resgn467sl-data-sheet.pdf"),
    ],
}

GAF_INSTALLATION_DETAILS = {
    "Installation_Details": [
        ("Cross Section", "https://gafroofing.co.nz/wp-content/downloads/drawings/2_cross_section.pdf"),
        ("Eave Detail", "https://gafroofing.co.nz/wp-content/downloads/drawings/3_eave.pdf"),
        ("Apron Flashing Transverse", "https://gafroofing.co.nz/wp-content/downloads/drawings/4_apron.pdf"),
        ("Apron Flashing Vented", "https://gafroofing.co.nz/wp-content/downloads/drawings/5_apron_vented.pdf"),
        ("Roof Wall Ridge", "https://gafroofing.co.nz/wp-content/downloads/drawings/6_roof_wall_ridge.pdf"),
        ("Roof Wall Ridge Vented", "https://gafroofing.co.nz/wp-content/downloads/drawings/7_roof_wall_ridge_vented.pdf"),
        ("Ridge Cladding", "https://gafroofing.co.nz/wp-content/downloads/drawings/8_ridge_cladding.pdf"),
        ("Ridge Beam", "https://gafroofing.co.nz/wp-content/downloads/drawings/8.1_ridge_beam_cladding.pdf"),
        ("Slope to Wall", "https://gafroofing.co.nz/wp-content/downloads/drawings/9_slope_to_wall.pdf"),
        ("Pitch Change", "https://gafroofing.co.nz/wp-content/downloads/drawings/10_pitch_change.pdf"),
        ("Flat Roof Transition", "https://gafroofing.co.nz/wp-content/downloads/drawings/10.1_flat_roof_membrane_transition.pdf"),
        ("Mansard Pitch Change", "https://gafroofing.co.nz/wp-content/downloads/drawings/10.2_pitch_change_mansard.pdf"),
        ("Gutter Wall Junction", "https://gafroofing.co.nz/wp-content/downloads/drawings/11_gutter_wall_junction.pdf"),
        ("Step Flashings", "https://gafroofing.co.nz/wp-content/downloads/drawings/12_step_flashings.pdf"),
        ("Barge End", "https://gafroofing.co.nz/wp-content/downloads/drawings/13_barge_end.pdf"),
        ("Apron Termination", "https://gafroofing.co.nz/wp-content/downloads/drawings/14_apron_termination.pdf"),
        ("Kick Out Flashing", "https://gafroofing.co.nz/wp-content/downloads/drawings/15_kick_out_flashing.pdf"),
        ("Gable to Ridge", "https://gafroofing.co.nz/wp-content/downloads/drawings/16_gable_to_ridge.pdf"),
        ("Dutch Dormer Gable Junction", "https://gafroofing.co.nz/wp-content/downloads/drawings/16.1_dutch_dormer_gable_junction.pdf"),
        ("Dutch Gable", "https://gafroofing.co.nz/wp-content/downloads/drawings/17_dutch_gable.pdf"),
        ("Specific Penetration", "https://gafroofing.co.nz/wp-content/downloads/drawings/18_specific_penetration.pdf"),
        ("Chimney Cricket", "https://gafroofing.co.nz/wp-content/downloads/drawings/19_chimney_cricket.pdf"),
        ("Valley to Dormer", "https://gafroofing.co.nz/wp-content/downloads/drawings/20_valley_to_dormer.pdf"),
        ("Rainwater Spreader", "https://gafroofing.co.nz/wp-content/downloads/drawings/21_rainwater_spreader.pdf"),
        ("Pipe Penetration", "https://gafroofing.co.nz/wp-content/downloads/drawings/22_pipe_penetration.pdf"),
        ("Masterflow Box Vent", "https://gafroofing.co.nz/wp-content/downloads/drawings/23_box_vent.pdf"),
        ("Valley Cladding", "https://gafroofing.co.nz/wp-content/downloads/drawings/24_valley_cladding.pdf"),
        ("Penetration Openings", "https://gafroofing.co.nz/wp-content/downloads/drawings/25_penetration_openings.pdf"),
        ("Hip Ridge Capping", "https://gafroofing.co.nz/wp-content/downloads/drawings/26_hip_ridge_cap.pdf"),
        ("Ridge to Wall", "https://gafroofing.co.nz/wp-content/downloads/drawings/28_ridge_to_wall.pdf"),
        ("Roof to Wall Flashings", "https://gafroofing.co.nz/wp-content/downloads/drawings/29_roof_to_wall_flashings.pdf"),
        ("Roof Wall Inside Corners", "https://gafroofing.co.nz/wp-content/downloads/drawings/30_roof_to_wall_corners.pdf"),
        ("Internal Valley Cricket", "https://gafroofing.co.nz/wp-content/downloads/drawings/31_internal_valley_cricket.pdf"),
        ("PV Solar Panel Mount", "https://gafroofing.co.nz/wp-content/downloads/drawings/32_solar_panel_mount.pdf"),
        ("Surface Intake Vent", "https://gafroofing.co.nz/wp-content/downloads/drawings/33.1_surface_intake_vent.pdf"),
        ("Surface Exhaust Vent", "https://gafroofing.co.nz/wp-content/downloads/drawings/33.2_surface_exhaust_vent.pdf"),
        ("Intertenancy 134A", "https://gafroofing.co.nz/wp-content/downloads/tpo/134A-INTERTENANCY-ROOF-JUNCTION-GIB.pdf"),
        ("Intertenancy 134B", "https://gafroofing.co.nz/wp-content/downloads/tpo/134B-INTERTENANCY-ROOF-JUCTION-BLOCK-WALL.pdf"),
    ],
}

GAF_UNDERLAY = {
    "Underlay": [
        ("D226 UltraGuard Underlay Data Sheet 2025", "https://gafroofing.co.nz/wp-content/downloads/GAF-technical-documents/D226+UltraGuard_Underlay_Data_Sheet_2025.pdf"),
    ],
}

GAF_WATER = {
    "Water_Collection": [
        ("Stormwater and Potable Water Data Sheet", "https://gafroofing.co.nz/wp-content/downloads/GAF-water-documents/Stormwater_and_Potable_Water_Shingle_Roofs_Data_Sheet.pdf"),
        ("AMS Laboratories Drinking Water NZS4020", "https://gafroofing.co.nz/wp-content/downloads/GAF-water-documents/AMS-Laboritories-Drinking-water-2015.pdf"),
    ],
}

GAF_ACCESSORIES = {
    "Accessories": [
        ("Cobra Exhaust Vent Application", "https://gafroofing.co.nz/wp-content/downloads/GAF-brochures/Cobra_Nail_Gun_Detailed_Application_Instructions.pdf"),
        ("Seal A Ridge Application", "https://gafroofing.co.nz/wp-content/downloads/GAF-brochures/Seal_A_Ridge_Application_Instructions.pdf"),
    ],
}


# =============================================================================
# NURALITE MEMBRANES (Flat Roofs)
# =============================================================================
NURALITE_PREFIX = "B_Enclosure/Nuralite_Membranes"

NURALITE_3PM = {
    "Nuraply_3PM": [
        ("Product Brochure", "https://www.nuralite.co.nz/_files/ugd/06ffae_e9280a44bf99477c80d7608fcd86e236.pdf"),
    ],
}

# Note: Nuralite uses a dynamic document library that requires login - we can only get the public brochure
# Additional docs would need manual extraction or API access


# =============================================================================
# UPLOAD FUNCTION
# =============================================================================
def upload_to_supabase(pdf_url: str, storage_path: str, doc_title: str) -> bool:
    """Download PDF and upload to Supabase storage."""
    try:
        print(f"    📥 Downloading: {doc_title[:45]}...")
        response = requests.get(pdf_url, timeout=60, allow_redirects=True)
        if response.status_code != 200:
            print(f"    ❌ Failed (HTTP {response.status_code})")
            stats["errors"] += 1
            return False
        
        pdf_content = response.content
        
        if not pdf_content[:4] == b'%PDF':
            print(f"    ⚠️ Not a valid PDF")
            stats["errors"] += 1
            return False
        
        file_size_mb = len(pdf_content) / (1024 * 1024)
        if is_potential_monolith(file_size_mb=file_size_mb):
            stats["monoliths_detected"] += 1
            print(f"    ⚠️ Rule 8: Monolith ({file_size_mb:.1f}MB)")
        
        try:
            supabase.storage.from_(BUCKET_NAME).upload(
                storage_path,
                pdf_content,
                {"content-type": "application/pdf"}
            )
            print(f"    ✅ Uploaded")
            return True
        except Exception as e:
            if "Duplicate" in str(e) or "already exists" in str(e).lower():
                print(f"    ⏭️ Already exists")
                stats["pdfs_skipped_duplicate"] += 1
                return False
            else:
                print(f"    ❌ Upload error: {e}")
                stats["errors"] += 1
                return False
                
    except Exception as e:
        print(f"    ❌ Error: {e}")
        stats["errors"] += 1
        return False


def process_products(brand: str, prefix: str, category: str, folder: str, products: dict):
    """Process products for a category."""
    print(f"\n  📁 {category}")
    
    for product_name, docs in products.items():
        for doc_title, pdf_url in docs:
            stats["pdfs_found"] += 1
            
            if pdf_url in uploaded_urls:
                stats["pdfs_skipped_duplicate"] += 1
                continue
            
            clean_title = sanitize_filename(doc_title)
            filename = f"{brand} - {clean_title}.pdf"
            storage_path = f"{prefix}/{folder}/{filename}"
            
            if upload_to_supabase(pdf_url, storage_path, doc_title):
                stats["pdfs_uploaded"] += 1
                uploaded_urls.add(pdf_url)
            
            time.sleep(0.2)


def main():
    """Main scraping function."""
    print("=" * 70)
    print(f"🏠 ROOFING GAP FILL SCRAPER (Protocol v{PROTOCOL_VERSION})")
    print("=" * 70)
    
    print_protocol_summary()
    print("=" * 70)
    
    # ==========================================================================
    # GAF SHINGLES
    # ==========================================================================
    print("\n" + "=" * 60)
    print("🏭 GAF SHINGLES (Asphalt)")
    print("=" * 60)
    stats["brands_processed"] += 1
    
    process_products("GAF", GAF_SHINGLES_PREFIX, "Timberline HDZ", 
                    "Timberline_HDZ", GAF_TIMBERLINE_HDZ)
    process_products("GAF", GAF_SHINGLES_PREFIX, "Slateline",
                    "Slateline", GAF_SLATELINE)
    process_products("GAF", GAF_SHINGLES_PREFIX, "Installation Details (CRITICAL - Nailing Patterns)",
                    "Installation_Details", GAF_INSTALLATION_DETAILS)
    process_products("GAF", GAF_SHINGLES_PREFIX, "Underlay",
                    "Underlay", GAF_UNDERLAY)
    process_products("GAF", GAF_SHINGLES_PREFIX, "Water Collection",
                    "Water_Collection", GAF_WATER)
    process_products("GAF", GAF_SHINGLES_PREFIX, "Accessories",
                    "Accessories", GAF_ACCESSORIES)
    
    # ==========================================================================
    # NURALITE MEMBRANES
    # ==========================================================================
    print("\n" + "=" * 60)
    print("🏭 NURALITE MEMBRANES (Flat Roofs)")
    print("=" * 60)
    stats["brands_processed"] += 1
    
    process_products("Nuralite", NURALITE_PREFIX, "Nuraply 3PM (Double Layer Torch-on)",
                    "Nuraply_3PM", NURALITE_3PM)
    
    print("\n  ⚠️ Note: Nuralite uses a login-protected document library.")
    print("     Only public brochure captured. Full library requires manual access.")
    
    # ==========================================================================
    # SKIPPED: Gerard & Solerati (Website issues)
    # ==========================================================================
    print("\n" + "=" * 60)
    print("⏭️ SKIPPED MANUFACTURERS")
    print("=" * 60)
    print("  ❌ Gerard Roofing: No public PDF download URLs found")
    print("  ❌ Solerati Tiles: Website not accessible (404)")
    print("  💡 Recommendation: Contact manufacturers for direct document access")
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 SCRAPING SUMMARY")
    print("=" * 70)
    print(f"Protocol Version:           v{PROTOCOL_VERSION}")
    print(f"Brands processed:           {stats['brands_processed']}")
    print(f"PDFs found:                 {stats['pdfs_found']}")
    print(f"PDFs uploaded:              {stats['pdfs_uploaded']}")
    print(f"PDFs skipped (duplicate):   {stats['pdfs_skipped_duplicate']}")
    print(f"Monoliths detected:         {stats['monoliths_detected']}")
    print(f"Errors:                     {stats['errors']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
