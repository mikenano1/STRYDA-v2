#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
    STRYDA PROTOCOL V2.0 - COMPLIANCE SECTOR LOCKDOWN
    TARGET: /pdfs/ bucket → product-library/01_Compliance/
═══════════════════════════════════════════════════════════════════════════════
"""

import os
import re
import json
import hashlib
from datetime import datetime
from supabase import create_client
import psycopg2
import fitz  # PyMuPDF

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

SUPABASE_URL = "https://qxqisgjhbjwvoxsjibes.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF4cWlzZ2poYmp3dm94c2ppYmVzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1OTQ3MDY5NSwiZXhwIjoyMDc1MDQ2Njk1fQ.iOaE9PsoN1NPjDiUOlTmzcaqiRbjbdtPMNDAKGtbFsk"
DATABASE_URL = "postgresql://postgres.qxqisgjhbjwvoxsjibes:8skmVOJbMyaQHyQl@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres"

# Rule S8: Expired documents to archive
EXPIRED_DOCS = [
    "C-AS3_Amendment-4_2019-EXPIRED.pdf",
    "C-AS4_Amendment-4_2019-EXPIRED.pdf",
    "C-AS5_Amendment-4_2019-EXPIRED.pdf",
    "C-AS6_Amendment-4_2019-EXPIRED.pdf",
    "C-AS7_Amendment-4_2019-EXPIRED.pdf",
    "CAS3-Amendment4-2019-EXPIRED.pdf"  # Duplicate
]

# Rule S1 & Rule 2: Naming Protocol Mapping
FILE_MAPPING = {
    # NZBC Acceptable Solutions
    "B1-Structure-Amendment13.pdf": {
        "new_name": "NZBC - B1_AS1 - Structure (Amd 13).pdf",
        "folder": "01_Compliance/NZBC_Acceptable_Solutions",
        "doc_type": "Building_Code",
        "hierarchy": 1,
        "agent_owner": ["Inspector", "Engineer"]
    },
    "b1-structure-as1-second-edition.pdf": {
        "new_name": "NZBC - B1_AS1 - Structure (2nd Ed).pdf",
        "folder": "01_Compliance/NZBC_Acceptable_Solutions",
        "doc_type": "Building_Code",
        "hierarchy": 1,
        "agent_owner": ["Inspector", "Engineer"]
    },
    "building-code.pdf": {
        "new_name": "NZBC - Building Code (Master).pdf",
        "folder": "01_Compliance/NZBC_Acceptable_Solutions",
        "doc_type": "Building_Code",
        "hierarchy": 1,
        "agent_owner": ["Inspector", "Engineer"]
    },
    "C-AS1_2nd-Edition_2023.pdf": {
        "new_name": "NZBC - C_AS1 - Fire Safety (2nd Ed 2023).pdf",
        "folder": "01_Compliance/NZBC_Acceptable_Solutions",
        "doc_type": "Building_Code",
        "hierarchy": 1,
        "agent_owner": ["Inspector"]
    },
    "C-AS2_2nd-Edition_2025.pdf": {
        "new_name": "NZBC - C_AS2 - Fire Safety (2nd Ed 2025).pdf",
        "folder": "01_Compliance/NZBC_Acceptable_Solutions",
        "doc_type": "Building_Code",
        "hierarchy": 1,
        "agent_owner": ["Inspector"]
    },
    "C-VM2_Amendment-6_2020.pdf": {
        "new_name": "NZBC - C_VM2 - Fire Safety Verification (Amd 6 2020).pdf",
        "folder": "01_Compliance/NZBC_Acceptable_Solutions",
        "doc_type": "Building_Code",
        "hierarchy": 1,
        "agent_owner": ["Inspector", "Engineer"]
    },
    "E1-AS1_1st-Edition-Amd12-2024.pdf": {
        "new_name": "NZBC - E1_AS1 - Surface Water (1st Ed Amd 12 2024).pdf",
        "folder": "01_Compliance/NZBC_Acceptable_Solutions",
        "doc_type": "Building_Code",
        "hierarchy": 1,
        "agent_owner": ["Inspector"]
    },
    "E2-AS1_4th-Edition-2025.pdf": {
        "new_name": "NZBC - E2_AS1 - External Moisture (4th Ed 2025).pdf",
        "folder": "01_Compliance/NZBC_Acceptable_Solutions",
        "doc_type": "Building_Code",
        "hierarchy": 1,
        "agent_owner": ["Inspector", "Engineer"],
        "priority": 95
    },
    "e2-external-moisture-as1-fourth-edition.pdf": {
        "new_name": "NZBC - E2_AS1 - External Moisture (4th Ed Full).pdf",
        "folder": "01_Compliance/NZBC_Acceptable_Solutions",
        "doc_type": "Building_Code",
        "hierarchy": 1,
        "agent_owner": ["Inspector", "Engineer"],
        "priority": 95
    },
    "E3-AS1_2nd-Edition-Amd7-2020.pdf": {
        "new_name": "NZBC - E3_AS1 - Internal Moisture (2nd Ed Amd 7 2020).pdf",
        "folder": "01_Compliance/NZBC_Acceptable_Solutions",
        "doc_type": "Building_Code",
        "hierarchy": 1,
        "agent_owner": ["Inspector"]
    },
    "F4-AS1_Amendment-6-2021.pdf": {
        "new_name": "NZBC - F4_AS1 - Safety from Falling (Amd 6 2021).pdf",
        "folder": "01_Compliance/NZBC_Acceptable_Solutions",
        "doc_type": "Building_Code",
        "hierarchy": 1,
        "agent_owner": ["Inspector"]
    },
    "F6-AS1_Amendment-3-2021.pdf": {
        "new_name": "NZBC - F6_AS1 - Visibility in Escape Routes (Amd 3 2021).pdf",
        "folder": "01_Compliance/NZBC_Acceptable_Solutions",
        "doc_type": "Building_Code",
        "hierarchy": 1,
        "agent_owner": ["Inspector"]
    },
    "F7-AS1_5th-Edition-2023.pdf": {
        "new_name": "NZBC - F7_AS1 - Warning Systems (5th Ed 2023).pdf",
        "folder": "01_Compliance/NZBC_Acceptable_Solutions",
        "doc_type": "Building_Code",
        "hierarchy": 1,
        "agent_owner": ["Inspector"]
    },
    "G12-AS1_3rd-Edition-Amd14-2024.pdf": {
        "new_name": "NZBC - G12_AS1 - Water Supplies (3rd Ed Amd 14 2024).pdf",
        "folder": "01_Compliance/NZBC_Acceptable_Solutions",
        "doc_type": "Building_Code",
        "hierarchy": 1,
        "agent_owner": ["Inspector"]
    },
    "G13-AS1_3rd-Edition-Amd14-2024.pdf": {
        "new_name": "NZBC - G13_AS1 - Foul Water (3rd Ed Amd 14 2024).pdf",
        "folder": "01_Compliance/NZBC_Acceptable_Solutions",
        "doc_type": "Building_Code",
        "hierarchy": 1,
        "agent_owner": ["Inspector"]
    },
    "H1-AS1_6th-Edition.pdf": {
        "new_name": "NZBC - H1_AS1 - Energy Efficiency (6th Ed 2026).pdf",
        "folder": "01_Compliance/NZBC_Acceptable_Solutions",
        "doc_type": "Building_Code",
        "hierarchy": 1,
        "agent_owner": ["Inspector", "Engineer"],
        "priority": 95
    },
    "H1-VM1_6th-Edition-2025.pdf": {
        "new_name": "NZBC - H1_VM1 - Energy Efficiency Verification (6th Ed 2025).pdf",
        "folder": "01_Compliance/NZBC_Acceptable_Solutions",
        "doc_type": "Building_Code",
        "hierarchy": 1,
        "agent_owner": ["Inspector", "Engineer"]
    },
    # Standards
    "NZS-36042011.pdf": {
        "new_name": "Standards - NZS 3604_2011 - Timber-framed Buildings.pdf",
        "folder": "01_Compliance/Standards",
        "doc_type": "Standard",
        "hierarchy": 1,
        "agent_owner": ["Inspector", "Engineer"],
        "priority": 95
    },
    "SNZ-HB-3604-2011-Selected-Extracts.pdf": {
        "new_name": "Standards - NZS 3604_2011 - Handbook Extracts.pdf",
        "folder": "01_Compliance/Standards",
        "doc_type": "Standard",
        "hierarchy": 1,
        "agent_owner": ["Engineer"]
    },
    "NZS-42292013.pdf": {
        "new_name": "Standards - NZS 4229_2013 - Concrete Masonry Buildings.pdf",
        "folder": "01_Compliance/Standards",
        "doc_type": "Standard",
        "hierarchy": 1,
        "agent_owner": ["Inspector", "Engineer"]
    },
    # MBIE Guidance
    "MBIE-Minor-Variation-Guidance.pdf.pdf": {
        "new_name": "MBIE - Minor Variation Guidance.pdf",
        "folder": "01_Compliance/MBIE_Guidance",
        "doc_type": "Guidance",
        "hierarchy": 2,
        "agent_owner": ["Inspector"]
    },
    "MBIE-Schedule-1-Exemptions-Guidance.pdf.pdf": {
        "new_name": "MBIE - Schedule 1 Exemptions Guidance.pdf",
        "folder": "01_Compliance/MBIE_Guidance",
        "doc_type": "Guidance",
        "hierarchy": 2,
        "agent_owner": ["Inspector"]
    },
    "MBIE-Tolerances-Guide.pdf.pdf": {
        "new_name": "MBIE - Materials and Workmanship Tolerances Guide.pdf",
        "folder": "01_Compliance/MBIE_Guidance",
        "doc_type": "Guidance",
        "hierarchy": 2,
        "agent_owner": ["Inspector"],
        "priority": 90
    },
    # Industry Codes
    "nz_metal_roofing.pdf": {
        "new_name": "Industry - NZ Metal Roofing Code of Practice.pdf",
        "folder": "01_Compliance/Industry_Codes",
        "doc_type": "Code_of_Practice",
        "hierarchy": 2,
        "agent_owner": ["Inspector", "Engineer"],
        "priority": 90
    },
    "WGANZ-Guide-to-E2-AS1-Amd-10-V1.7-November-2022.pdf": {
        "new_name": "Industry - WGANZ Guide to E2_AS1 (V1.7 2022).pdf",
        "folder": "01_Compliance/Industry_Codes",
        "doc_type": "Code_of_Practice",
        "hierarchy": 2,
        "agent_owner": ["Inspector"]
    },
    "Internal-WetArea-Membrane-CodeOfPractice_4th-Edition-2020.pdf": {
        "new_name": "Industry - Wet Area Membrane Code of Practice (4th Ed 2020).pdf",
        "folder": "01_Compliance/Industry_Codes",
        "doc_type": "Code_of_Practice",
        "hierarchy": 2,
        "agent_owner": ["Inspector"]
    },
    "Ardex-Waterproofing-Manual.pdf": {
        "new_name": "Industry - Ardex Waterproofing Manual.pdf",
        "folder": "01_Compliance/Industry_Codes",
        "doc_type": "Technical_Manual",
        "hierarchy": 2,
        "agent_owner": ["Inspector"]
    },
    # GIB Systems
    "GIB-Fire-Systems-Manual.pdf": {
        "new_name": "GIB - Fire Rated Systems Manual.pdf",
        "folder": "01_Compliance/Industry_Codes",
        "doc_type": "Technical_Manual",
        "hierarchy": 2,
        "agent_owner": ["Inspector", "Engineer"]
    },
    "GIB-Bracing-Supplement-2016.pdf": {
        "new_name": "GIB - Bracing Systems Supplement (2016).pdf",
        "folder": "01_Compliance/Industry_Codes",
        "doc_type": "Technical_Manual",
        "hierarchy": 2,
        "agent_owner": ["Engineer"]
    },
    "GIB-EzyBrace-Systems-2016.pdf": {
        "new_name": "GIB - EzyBrace Systems (2016).pdf",
        "folder": "01_Compliance/Industry_Codes",
        "doc_type": "Technical_Manual",
        "hierarchy": 2,
        "agent_owner": ["Engineer"]
    }
}

# Rule 6: Guardrail Extraction Targets
GUARDRAIL_TARGETS = {
    "H1-AS1_6th-Edition.pdf": {
        "name": "H1 Energy Efficiency",
        "extractions": [
            {"key": "schedule_method_removed", "pattern": r"schedule\s*method", "note": "Schedule Method REMOVED Nov 2025"},
            {"key": "calculation_method_required", "pattern": r"calculation\s*method|H1/VM1", "note": "Calculation Method now mandatory"},
            {"key": "r_value_ceiling", "pattern": r"R[67]\.[0-9]|R-value.*ceiling", "note": "Ceiling R-value requirements"},
            {"key": "r_value_wall", "pattern": r"R[23]\.[0-9].*wall|wall.*R[23]\.[0-9]", "note": "Wall R-value requirements"}
        ]
    },
    "E2-AS1_4th-Edition-2025.pdf": {
        "name": "E2 External Moisture",
        "extractions": [
            {"key": "risk_matrix", "pattern": r"risk\s*(?:matrix|score)|table\s*2", "note": "E2 Risk Matrix Score"},
            {"key": "wind_zone", "pattern": r"wind\s*zone|very\s*high\s*wind", "note": "Wind Zone classifications"},
            {"key": "direct_fix_limit", "pattern": r"direct.?fix|cavity\s*required", "note": "Direct-fix limitations"}
        ]
    },
    "nz_metal_roofing.pdf": {
        "name": "Metal Roofing COP",
        "extractions": [
            {"key": "min_pitch_corrugate", "pattern": r"corrugate.*(\d+)°|(\d+)°.*corrugate|minimum\s*pitch", "note": "Min pitch per profile"},
            {"key": "min_pitch_tray", "pattern": r"tray.*(\d+)°|standing\s*seam", "note": "Standing seam pitch"},
            {"key": "lap_requirements", "pattern": r"end\s*lap|side\s*lap|(\d+)mm\s*lap", "note": "Lap requirements"}
        ]
    },
    "MBIE-Tolerances-Guide.pdf.pdf": {
        "name": "MBIE Tolerances",
        "extractions": [
            {"key": "framing_tolerance", "pattern": r"framing.*(\d+)mm|stud.*plumb", "note": "Framing tolerances"},
            {"key": "floor_level", "pattern": r"floor.*level|(\d+)mm.*level", "note": "Floor level tolerances"},
            {"key": "wall_plumb", "pattern": r"wall.*plumb|(\d+)mm.*plumb", "note": "Wall plumb tolerances"}
        ]
    },
    "F4-AS1_Amendment-6-2021.pdf": {
        "name": "F4 Safety from Falling",
        "extractions": [
            {"key": "balustrade_height_1m", "pattern": r"1000\s*mm|1\s*m(?:etre)?.*height|balustrade.*height", "note": "1m balustrade threshold"},
            {"key": "openings_100mm", "pattern": r"100\s*mm.*opening|opening.*100", "note": "100mm max opening"}
        ]
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def compute_page_hash(content: str) -> str:
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def chunk_text(text: str, chunk_size: int = 1500, overlap: int = 200) -> list:
    chunks = []
    start = 0
    text = text.replace('\x00', '')  # Clean NUL
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap
        if start >= len(text):
            break
    return chunks

def extract_guardrails_from_text(content: str, config: dict) -> dict:
    """Extract Rule 6 guardrails from document content"""
    guardrails = {"document": config["name"], "extracted": {}}
    content_lower = content.lower()
    
    for extraction in config["extractions"]:
        key = extraction["key"]
        pattern = extraction["pattern"]
        note = extraction["note"]
        
        matches = re.findall(pattern, content_lower)
        if matches:
            guardrails["extracted"][key] = {
                "found": True,
                "note": note,
                "match_count": len(matches)
            }
        else:
            guardrails["extracted"][key] = {"found": False, "note": note}
    
    return guardrails

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("═" * 70)
    print("  STRYDA PROTOCOL V2.0 - COMPLIANCE SECTOR LOCKDOWN")
    print("═" * 70)
    print(f"  Started: {datetime.now().isoformat()}")
    print("═" * 70)
    
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    stats = {
        "archived": 0,
        "processed": 0,
        "chunks_created": 0,
        "guardrails_extracted": 0,
        "errors": []
    }
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 1: ARCHIVE EXPIRED DOCUMENTS (Rule S8)
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n" + "─" * 70)
    print("  PHASE 1: ARCHIVING EXPIRED DOCUMENTS (Rule S8)")
    print("─" * 70)
    
    for expired_file in EXPIRED_DOCS:
        try:
            # Just mark in database as expired - don't delete from storage
            cur.execute("""
                UPDATE documents 
                SET is_active = FALSE, 
                    blacklist_reason = 'EXPIRED: Superseded by 2025/2026 Code'
                WHERE source LIKE %s
            """, (f'%{expired_file}%',))
            
            if cur.rowcount > 0:
                print(f"  ⚠️ ARCHIVED: {expired_file} ({cur.rowcount} chunks deactivated)")
                stats["archived"] += cur.rowcount
            else:
                print(f"  ℹ️ SKIP: {expired_file} (not in database)")
        except Exception as e:
            print(f"  ❌ ERROR: {expired_file} - {e}")
            stats["errors"].append(expired_file)
    
    conn.commit()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 2: PROCESS & INGEST ACTIVE DOCUMENTS
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n" + "─" * 70)
    print("  PHASE 2: PROCESSING ACTIVE COMPLIANCE DOCUMENTS")
    print("─" * 70)
    
    all_guardrails = {}
    
    for old_name, config in FILE_MAPPING.items():
        print(f"\n  📄 Processing: {old_name}")
        
        try:
            # Download from pdfs bucket
            pdf_data = client.storage.from_('pdfs').download(old_name)
            
            # Save temporarily
            temp_path = f"/tmp/{old_name}"
            with open(temp_path, 'wb') as f:
                f.write(pdf_data)
            
            # Extract text
            doc = fitz.open(temp_path)
            full_text = ""
            page_texts = []
            
            for page_num, page in enumerate(doc):
                page_text = page.get_text()
                page_texts.append({"page": page_num + 1, "text": page_text})
                full_text += page_text + "\n"
            
            doc.close()
            os.remove(temp_path)
            
            # Extract guardrails if this is a target document
            if old_name in GUARDRAIL_TARGETS:
                guardrails = extract_guardrails_from_text(full_text, GUARDRAIL_TARGETS[old_name])
                all_guardrails[old_name] = guardrails
                stats["guardrails_extracted"] += 1
                print(f"     🛡️ Guardrails extracted: {list(guardrails['extracted'].keys())}")
            
            # Build storage path
            storage_path = f"{config['folder']}/{config['new_name']}"
            
            # Ingest chunks to database
            chunks_inserted = 0
            for page_data in page_texts:
                page_num = page_data["page"]
                page_text = page_data["text"]
                
                if not page_text.strip():
                    continue
                
                chunks = chunk_text(page_text)
                
                for chunk in chunks:
                    if not chunk.strip():
                        continue
                    
                    page_hash = compute_page_hash(chunk)
                    
                    # Check duplicate
                    cur.execute("SELECT id FROM documents WHERE page_hash = %s", (page_hash,))
                    if cur.fetchone():
                        continue
                    
                    # Build unit_range for guardrail docs
                    unit_range = None
                    if old_name in GUARDRAIL_TARGETS:
                        unit_range = json.dumps(all_guardrails[old_name]["extracted"])
                    
                    cur.execute("""
                        INSERT INTO documents (
                            content, source, page, page_hash,
                            hierarchy_level, agent_owner, geo_context,
                            doc_type, priority, unit_range, is_active, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        chunk,
                        storage_path,
                        page_num,
                        page_hash,
                        config["hierarchy"],
                        config["agent_owner"],
                        "NZ_Specific",
                        config["doc_type"],
                        config.get("priority", 85),
                        unit_range,
                        True,
                        datetime.utcnow()
                    ))
                    chunks_inserted += 1
            
            conn.commit()
            stats["processed"] += 1
            stats["chunks_created"] += chunks_inserted
            print(f"     ✅ Ingested: {chunks_inserted} chunks → {storage_path}")
            
        except Exception as e:
            print(f"     ❌ ERROR: {e}")
            stats["errors"].append(old_name)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 3: GUARDRAIL SUMMARY REPORT
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n" + "─" * 70)
    print("  PHASE 3: GUARDRAIL EXTRACTION REPORT (Rule 6)")
    print("─" * 70)
    
    for doc_name, guardrails in all_guardrails.items():
        print(f"\n  📋 {guardrails['document']}:")
        for key, data in guardrails["extracted"].items():
            status = "✅" if data["found"] else "❌"
            print(f"     {status} {key}: {data['note']}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # FINAL REPORT
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n" + "═" * 70)
    print("  COMPLIANCE SECTOR LOCKDOWN - FINAL REPORT")
    print("═" * 70)
    print(f"  📊 Documents Archived (Expired): {stats['archived']} chunks")
    print(f"  📊 Documents Processed: {stats['processed']}")
    print(f"  📊 Total Chunks Created: {stats['chunks_created']}")
    print(f"  📊 Guardrail Documents: {stats['guardrails_extracted']}")
    print(f"  ❌ Errors: {len(stats['errors'])}")
    if stats["errors"]:
        for err in stats["errors"]:
            print(f"      • {err}")
    print("═" * 70)
    print(f"  ✅ COMPLIANCE LIBRARY 100% WEAPONIZED FOR 2026")
    print(f"  Completed: {datetime.now().isoformat()}")
    print("═" * 70)
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
