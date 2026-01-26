#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
    STRYDA PROTOCOL V2.0 - MARSHALL INNOVATIONS INGESTION
    TARGET: temporary/ → product-library/B_Enclosure/Underlays_and_Wraps/Marshall/
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

DEST_FOLDER = "B_Enclosure/Underlays_and_Wraps/Marshall"

# Rule S1 & S2: Naming Protocol Mapping - Marshall Files
MARSHALL_FILE_MAPPING = {
    "marshalls_product_guide_update_print_compressed.pdf": {
        "new_name": "Marshall - Product Guide (MASTER).pdf",
        "doc_type": "Product_Guide",
        "hierarchy": 3,
        "agent_owner": ["Inspector", "Product_Rep"],
        "priority": 85
    },
    "SuperStickBrochure.pdf": {
        "new_name": "Marshall - Super-Stick - Brochure.pdf",
        "doc_type": "Brochure",
        "hierarchy": 3,
        "agent_owner": ["Product_Rep"],
        "priority": 75
    },
    "SUPERSTICKSpecJuly20211.pdf": {
        "new_name": "Marshall - Super-Stick - Technical Data Sheet (2021).pdf",
        "doc_type": "Technical_Data_Sheet",
        "hierarchy": 3,
        "agent_owner": ["Inspector", "Engineer"],
        "priority": 85
    },
    "Tekton BPIR December 2023 (1).pdf": {
        "new_name": "Marshall - Tekton - BPIR (Dec 2023).pdf",
        "doc_type": "BPIR",
        "hierarchy": 3,
        "agent_owner": ["Inspector", "Engineer"],
        "priority": 90
    },
    "Tekton BPIR December 2023.pdf": {
        "skip": True,  # Duplicate
        "reason": "Duplicate of Tekton BPIR December 2023 (1).pdf"
    },
    "Tekton.pdf": {
        "new_name": "Marshall - Tekton - Product Overview.pdf",
        "doc_type": "Product_Guide",
        "hierarchy": 3,
        "agent_owner": ["Inspector", "Product_Rep"],
        "priority": 80
    },
    "TektonSpecification.pdf": {
        "new_name": "Marshall - Tekton - Technical Data Sheet.pdf",
        "doc_type": "Technical_Data_Sheet",
        "hierarchy": 3,
        "agent_owner": ["Inspector", "Engineer"],
        "priority": 85
    },
    "TektonWeatherizationSystemBranzAppraisal.pdf": {
        "new_name": "Marshall - Tekton Weatherization System - BRANZ Appraisal.pdf",
        "doc_type": "BRANZ_Appraisal",
        "hierarchy": 3,
        "agent_owner": ["Inspector", "Engineer"],
        "priority": 90
    },
    "TradeFlashSpecification.pdf": {
        "new_name": "Marshall - Trade Flash - Technical Data Sheet.pdf",
        "doc_type": "Technical_Data_Sheet",
        "hierarchy": 3,
        "agent_owner": ["Inspector", "Engineer"],
        "priority": 85
    },
    # Skip Masons files - already ingested
    "Masons - 40 Below Platinum - Technical Data Sheet.pdf": {"skip": True, "reason": "Already ingested"},
    "Masons - Barricade WD - Design and Installation Manual (MASTER).pdf": {"skip": True, "reason": "Already ingested"},
    "Masons - Intertenancy - Wall System Design Guide.pdf": {"skip": True, "reason": "Already ingested"},
    "Masons - UNI PRO - Flexible Air Barrier Installation (2025).pdf": {"skip": True, "reason": "Already ingested"},
    "Masons - VHP Maxi - Roof Underlay Technical PASS (2026).pdf": {"skip": True, "reason": "Already ingested"}
}

# Rule 6: Guardrail Extraction Patterns for Marshall Products
GUARDRAIL_PATTERNS = {
    "uv_exposure": [
        (180, r"180\s*days?"),
        (150, r"150\s*days?"),
        (120, r"120\s*days?"),
        (90, r"90\s*days?"),
    ],
    "tape_sequence": [
        r"tape\s*over\s*wrap",
        r"wrap\s*first.*tape",
        r"apply.*tape.*after.*wrap",
        r"sequence.*tape",
    ],
    "overlap_mm": r"(\d+)\s*mm\s*(?:overlap|lap)",
    "wind_zone": r"(very\s*high|high|medium|low)\s*wind\s*zone",
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

def extract_marshall_guardrails(content: str, filename: str) -> dict:
    """Extract Rule 6 guardrails from Marshall document content"""
    guardrails = {
        "brand": "Marshall Innovations",
        "uv_exposure_days": None,
        "tape_sequence": None,
        "overlap_mm": None,
        "wind_zone": None,
        "product_line": None
    }
    
    content_lower = content.lower()
    
    # Detect product line
    if "tekton" in filename.lower() or "tekton" in content_lower:
        guardrails["product_line"] = "Tekton"
    elif "super" in filename.lower() and "stick" in filename.lower():
        guardrails["product_line"] = "Super-Stick"
    elif "trade" in filename.lower() and "flash" in filename.lower():
        guardrails["product_line"] = "Trade Flash"
    
    # Extract UV exposure days
    for days, pattern in GUARDRAIL_PATTERNS["uv_exposure"]:
        if re.search(pattern, content_lower):
            guardrails["uv_exposure_days"] = days
            break
    
    # Check for tape sequencing (critical for Marshall Tekton system)
    for pattern in GUARDRAIL_PATTERNS["tape_sequence"]:
        if re.search(pattern, content_lower):
            guardrails["tape_sequence"] = "tape_over_wrap"
            break
    
    # Extract overlap requirements
    overlap_match = re.search(GUARDRAIL_PATTERNS["overlap_mm"], content_lower)
    if overlap_match:
        guardrails["overlap_mm"] = int(overlap_match.group(1))
    
    # Extract wind zone applicability
    wind_match = re.search(GUARDRAIL_PATTERNS["wind_zone"], content_lower)
    if wind_match:
        guardrails["wind_zone"] = wind_match.group(1).title()
    
    return guardrails

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("═" * 70)
    print("  STRYDA PROTOCOL V2.0 - MARSHALL INNOVATIONS INGESTION")
    print("═" * 70)
    print(f"  Started: {datetime.now().isoformat()}")
    print("═" * 70)
    
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    stats = {
        "processed": 0,
        "skipped": 0,
        "chunks_created": 0,
        "copied_to_storage": 0,
        "errors": []
    }
    
    # Get files from temporary bucket
    files = client.storage.from_('temporary').list()
    marshall_files = [f for f in files if f.get('name') in MARSHALL_FILE_MAPPING]
    
    print(f"\n📁 Found {len(marshall_files)} Marshall files to process")
    
    for file_info in marshall_files:
        old_name = file_info.get('name')
        config = MARSHALL_FILE_MAPPING.get(old_name, {})
        
        # Skip duplicates or already-ingested files
        if config.get('skip'):
            print(f"\n  ⏭️ SKIP: {old_name}")
            print(f"     Reason: {config.get('reason', 'Marked for skip')}")
            stats["skipped"] += 1
            continue
        
        new_name = config.get('new_name', old_name)
        print(f"\n  📄 Processing: {old_name}")
        print(f"     → Renamed: {new_name}")
        
        try:
            # Download from temporary bucket
            pdf_data = client.storage.from_('temporary').download(old_name)
            
            # Save temporarily
            temp_path = f"/tmp/{old_name}"
            with open(temp_path, 'wb') as f:
                f.write(pdf_data)
            
            # Extract text with PyMuPDF
            doc = fitz.open(temp_path)
            full_text = ""
            page_texts = []
            
            for page_num, page in enumerate(doc):
                page_text = page.get_text()
                page_texts.append({"page": page_num + 1, "text": page_text})
                full_text += page_text + "\n"
            
            doc.close()
            
            # Extract guardrails
            guardrails = extract_marshall_guardrails(full_text, old_name)
            
            if guardrails["uv_exposure_days"] or guardrails["tape_sequence"]:
                print(f"     🛡️ Guardrails: UV={guardrails['uv_exposure_days']} days, Sequence={guardrails['tape_sequence']}")
            
            # Build storage path
            storage_path = f"{DEST_FOLDER}/{new_name}"
            
            # Copy to permanent storage
            try:
                with open(temp_path, 'rb') as f:
                    client.storage.from_('product-library').upload(
                        storage_path,
                        f.read(),
                        {"content-type": "application/pdf", "upsert": "true"}
                    )
                stats["copied_to_storage"] += 1
                print(f"     📦 Copied to: product-library/{storage_path}")
            except Exception as e:
                print(f"     ⚠️ Storage copy failed: {e}")
            
            os.remove(temp_path)
            
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
                    
                    # Build unit_range with guardrails
                    unit_range = {}
                    if guardrails["uv_exposure_days"]:
                        unit_range["uv_exposure_limit_days"] = guardrails["uv_exposure_days"]
                    if guardrails["tape_sequence"]:
                        unit_range["tape_sequence"] = guardrails["tape_sequence"]
                    if guardrails["overlap_mm"]:
                        unit_range["overlap_mm"] = guardrails["overlap_mm"]
                    if guardrails["product_line"]:
                        unit_range["product_line"] = guardrails["product_line"]
                    
                    cur.execute("""
                        INSERT INTO documents (
                            content, source, page, page_hash,
                            hierarchy_level, agent_owner, geo_context,
                            doc_type, priority, unit_range, brand_name,
                            trade, is_active, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                        json.dumps(unit_range) if unit_range else None,
                        "Marshall Innovations",
                        "underlays",
                        True,
                        datetime.utcnow()
                    ))
                    chunks_inserted += 1
            
            conn.commit()
            stats["processed"] += 1
            stats["chunks_created"] += chunks_inserted
            print(f"     ✅ Ingested: {chunks_inserted} chunks")
            
        except Exception as e:
            print(f"     ❌ ERROR: {e}")
            stats["errors"].append(old_name)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CLEANUP: Delete processed Marshall files from temporary
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n" + "─" * 70)
    print("  CLEANUP: Removing processed files from temporary/")
    print("─" * 70)
    
    for file_info in files:
        filename = file_info.get('name')
        if filename in MARSHALL_FILE_MAPPING:
            try:
                client.storage.from_('temporary').remove([filename])
                print(f"  🗑️ Deleted: {filename}")
            except Exception as e:
                print(f"  ⚠️ Failed to delete {filename}: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # FINAL REPORT
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n" + "═" * 70)
    print("  MARSHALL INNOVATIONS INGESTION - FINAL REPORT")
    print("═" * 70)
    print(f"  📊 Documents Processed: {stats['processed']}")
    print(f"  📊 Documents Skipped: {stats['skipped']}")
    print(f"  📊 Total Chunks Created: {stats['chunks_created']}")
    print(f"  📊 Files Copied to Storage: {stats['copied_to_storage']}")
    print(f"  ❌ Errors: {len(stats['errors'])}")
    if stats["errors"]:
        for err in stats["errors"]:
            print(f"      • {err}")
    print("═" * 70)
    print(f"  ✅ MARSHALL INNOVATIONS - PROTOCOL V2.0 COMPLETE")
    print(f"  Completed: {datetime.now().isoformat()}")
    print("═" * 70)
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
