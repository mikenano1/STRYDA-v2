#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
    STRYDA PROTOCOL V2.0 - PHYSICAL STORAGE MIGRATION
    SOURCE: pdfs/ bucket → product-library/01_Compliance/ hierarchy
═══════════════════════════════════════════════════════════════════════════════
"""

from datetime import datetime
from supabase import create_client

SUPABASE_URL = "https://qxqisgjhbjwvoxsjibes.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF4cWlzZ2poYmp3dm94c2ppYmVzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1OTQ3MDY5NSwiZXhwIjoyMDc1MDQ2Njk1fQ.iOaE9PsoN1NPjDiUOlTmzcaqiRbjbdtPMNDAKGtbFsk"

# Complete migration map: pdfs/ filename -> product-library/ destination
MIGRATION_MAP = {
    # NZBC Acceptable Solutions
    "B1-Structure-Amendment13.pdf": "01_Compliance/NZBC_Acceptable_Solutions/NZBC - B1_AS1 - Structure (Amd 13).pdf",
    "b1-structure-as1-second-edition.pdf": "01_Compliance/NZBC_Acceptable_Solutions/NZBC - B1_AS1 - Structure (2nd Ed).pdf",
    "building-code.pdf": "01_Compliance/NZBC_Acceptable_Solutions/NZBC - Building Code (Master).pdf",
    "C-AS1_2nd-Edition_2023.pdf": "01_Compliance/NZBC_Acceptable_Solutions/NZBC - C_AS1 - Fire Safety (2nd Ed 2023).pdf",
    "C-AS2_2nd-Edition_2025.pdf": "01_Compliance/NZBC_Acceptable_Solutions/NZBC - C_AS2 - Fire Safety (2nd Ed 2025).pdf",
    "C-VM2_Amendment-6_2020.pdf": "01_Compliance/NZBC_Acceptable_Solutions/NZBC - C_VM2 - Fire Safety Verification (Amd 6 2020).pdf",
    "E1-AS1_1st-Edition-Amd12-2024.pdf": "01_Compliance/NZBC_Acceptable_Solutions/NZBC - E1_AS1 - Surface Water (1st Ed Amd 12 2024).pdf",
    "E2-AS1_4th-Edition-2025.pdf": "01_Compliance/NZBC_Acceptable_Solutions/NZBC - E2_AS1 - External Moisture (4th Ed 2025).pdf",
    "e2-external-moisture-as1-fourth-edition.pdf": "01_Compliance/NZBC_Acceptable_Solutions/NZBC - E2_AS1 - External Moisture (4th Ed Full).pdf",
    "E3-AS1_2nd-Edition-Amd7-2020.pdf": "01_Compliance/NZBC_Acceptable_Solutions/NZBC - E3_AS1 - Internal Moisture (2nd Ed Amd 7 2020).pdf",
    "F4-AS1_Amendment-6-2021.pdf": "01_Compliance/NZBC_Acceptable_Solutions/NZBC - F4_AS1 - Safety from Falling (Amd 6 2021).pdf",
    "F6-AS1_Amendment-3-2021.pdf": "01_Compliance/NZBC_Acceptable_Solutions/NZBC - F6_AS1 - Visibility in Escape Routes (Amd 3 2021).pdf",
    "F7-AS1_5th-Edition-2023.pdf": "01_Compliance/NZBC_Acceptable_Solutions/NZBC - F7_AS1 - Warning Systems (5th Ed 2023).pdf",
    "G12-AS1_3rd-Edition-Amd14-2024.pdf": "01_Compliance/NZBC_Acceptable_Solutions/NZBC - G12_AS1 - Water Supplies (3rd Ed Amd 14 2024).pdf",
    "G13-AS1_3rd-Edition-Amd14-2024.pdf": "01_Compliance/NZBC_Acceptable_Solutions/NZBC - G13_AS1 - Foul Water (3rd Ed Amd 14 2024).pdf",
    "H1-AS1_6th-Edition.pdf": "01_Compliance/NZBC_Acceptable_Solutions/NZBC - H1_AS1 - Energy Efficiency (6th Ed 2026).pdf",
    "H1-VM1_6th-Edition-2025.pdf": "01_Compliance/NZBC_Acceptable_Solutions/NZBC - H1_VM1 - Energy Efficiency Verification (6th Ed 2025).pdf",
    
    # Standards
    "NZS-36042011.pdf": "01_Compliance/Standards/Standards - NZS 3604_2011 - Timber-framed Buildings.pdf",
    "SNZ-HB-3604-2011-Selected-Extracts.pdf": "01_Compliance/Standards/Standards - NZS 3604_2011 - Handbook Extracts.pdf",
    "NZS-42292013.pdf": "01_Compliance/Standards/Standards - NZS 4229_2013 - Concrete Masonry Buildings.pdf",
    
    # MBIE Guidance
    "MBIE-Minor-Variation-Guidance.pdf.pdf": "01_Compliance/MBIE_Guidance/MBIE - Minor Variation Guidance.pdf",
    "MBIE-Schedule-1-Exemptions-Guidance.pdf.pdf": "01_Compliance/MBIE_Guidance/MBIE - Schedule 1 Exemptions Guidance.pdf",
    "MBIE-Tolerances-Guide.pdf.pdf": "01_Compliance/MBIE_Guidance/MBIE - Materials and Workmanship Tolerances Guide.pdf",
    
    # Industry Codes
    "nz_metal_roofing.pdf": "01_Compliance/Industry_Codes/Industry - NZ Metal Roofing Code of Practice.pdf",
    "WGANZ-Guide-to-E2-AS1-Amd-10-V1.7-November-2022.pdf": "01_Compliance/Industry_Codes/Industry - WGANZ Guide to E2_AS1 (V1.7 2022).pdf",
    "Internal-WetArea-Membrane-CodeOfPractice_4th-Edition-2020.pdf": "01_Compliance/Industry_Codes/Industry - Wet Area Membrane Code of Practice (4th Ed 2020).pdf",
    "Ardex-Waterproofing-Manual.pdf": "01_Compliance/Industry_Codes/Industry - Ardex Waterproofing Manual.pdf",
    "GIB-Fire-Systems-Manual.pdf": "01_Compliance/Industry_Codes/GIB - Fire Rated Systems Manual.pdf",
    "GIB-Bracing-Supplement-2016.pdf": "01_Compliance/Industry_Codes/GIB - Bracing Systems Supplement (2016).pdf",
    "GIB-EzyBrace-Systems-2016.pdf": "01_Compliance/Industry_Codes/GIB - EzyBrace Systems (2016).pdf",
}

# Expired files to move to archive
ARCHIVE_FILES = [
    "C-AS3_Amendment-4_2019-EXPIRED.pdf",
    "C-AS4_Amendment-4_2019-EXPIRED.pdf",
    "C-AS5_Amendment-4_2019-EXPIRED.pdf",
    "C-AS6_Amendment-4_2019-EXPIRED.pdf",
    "C-AS7_Amendment-4_2019-EXPIRED.pdf",
    "CAS3-Amendment4-2019-EXPIRED.pdf",
]

def main():
    print("═" * 70)
    print("  STRYDA PROTOCOL V2.0 - PHYSICAL STORAGE MIGRATION")
    print("═" * 70)
    print(f"  Started: {datetime.now().isoformat()}")
    print("═" * 70)
    
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    stats = {
        "migrated": 0,
        "archived": 0,
        "errors": []
    }
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 1: MIGRATE ACTIVE FILES
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n" + "─" * 70)
    print("  PHASE 1: MIGRATING ACTIVE COMPLIANCE FILES")
    print("─" * 70)
    
    for old_name, new_path in MIGRATION_MAP.items():
        try:
            # Download from pdfs bucket
            print(f"\n  📄 {old_name}")
            pdf_data = client.storage.from_('pdfs').download(old_name)
            
            # Upload to product-library with new path
            client.storage.from_('product-library').upload(
                new_path,
                pdf_data,
                {"content-type": "application/pdf", "upsert": "true"}
            )
            
            print(f"     ✅ → {new_path}")
            stats["migrated"] += 1
            
        except Exception as e:
            error_msg = str(e)
            if "not found" in error_msg.lower() or "404" in error_msg:
                print(f"     ⚠️ Source not found (may already be migrated)")
            else:
                print(f"     ❌ ERROR: {error_msg[:50]}")
                stats["errors"].append(old_name)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 2: ARCHIVE EXPIRED FILES
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n" + "─" * 70)
    print("  PHASE 2: ARCHIVING EXPIRED FILES")
    print("─" * 70)
    
    for old_name in ARCHIVE_FILES:
        try:
            print(f"\n  📄 {old_name}")
            pdf_data = client.storage.from_('pdfs').download(old_name)
            
            archive_path = f"01_Compliance/_Archive_Expired/{old_name}"
            client.storage.from_('product-library').upload(
                archive_path,
                pdf_data,
                {"content-type": "application/pdf", "upsert": "true"}
            )
            
            print(f"     ⚠️ → {archive_path}")
            stats["archived"] += 1
            
        except Exception as e:
            error_msg = str(e)
            if "not found" in error_msg.lower() or "404" in error_msg:
                print(f"     ⚠️ Source not found (may already be archived)")
            else:
                print(f"     ❌ ERROR: {error_msg[:50]}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 3: VERIFY NEW STRUCTURE
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n" + "─" * 70)
    print("  PHASE 3: VERIFYING NEW FOLDER STRUCTURE")
    print("─" * 70)
    
    folders = [
        "01_Compliance/NZBC_Acceptable_Solutions",
        "01_Compliance/Standards",
        "01_Compliance/MBIE_Guidance",
        "01_Compliance/Industry_Codes",
        "01_Compliance/_Archive_Expired"
    ]
    
    for folder in folders:
        try:
            files = client.storage.from_('product-library').list(folder)
            print(f"\n  📁 {folder}/")
            print(f"     {len(files)} files")
        except Exception as e:
            print(f"\n  📁 {folder}/")
            print(f"     ⚠️ Could not list: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # FINAL REPORT
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n" + "═" * 70)
    print("  PHYSICAL STORAGE MIGRATION - FINAL REPORT")
    print("═" * 70)
    print(f"  📊 Files Migrated: {stats['migrated']}")
    print(f"  📊 Files Archived: {stats['archived']}")
    print(f"  ❌ Errors: {len(stats['errors'])}")
    if stats["errors"]:
        for err in stats["errors"]:
            print(f"      • {err}")
    print("═" * 70)
    print(f"  ✅ PHYSICAL MIGRATION COMPLETE")
    print(f"  🚀 Refresh your Supabase Dashboard now!")
    print(f"  Completed: {datetime.now().isoformat()}")
    print("═" * 70)

if __name__ == "__main__":
    main()
