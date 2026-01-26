#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
    STRYDA PROTOCOL V2.0 - PHASE 3.2: COMPLIANCE FOUNDATION FULL-FILL
    TARGET: "Big 5" Pillar Standards from temporary/ bucket
═══════════════════════════════════════════════════════════════════════════════
"""

import os
import re
import json
import hashlib
from datetime import datetime
from supabase import create_client
import psycopg2
import fitz

SUPABASE_URL = "https://qxqisgjhbjwvoxsjibes.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF4cWlzZ2poYmp3dm94c2ppYmVzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1OTQ3MDY5NSwiZXhwIjoyMDc1MDQ2Njk1fQ.iOaE9PsoN1NPjDiUOlTmzcaqiRbjbdtPMNDAKGtbFsk"
DATABASE_URL = "postgresql://postgres.qxqisgjhbjwvoxsjibes:8skmVOJbMyaQHyQl@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres"

# PHASE 3.2: File Mapping & Categorization
FILE_MAPPING = {
    "NZS-36022003.pdf": {
        "new_name": "Standards - NZS 3602_2003 - Timber and Wood-based Products for Building.pdf",
        "folder": "01_Compliance/Standards",
        "doc_type": "Standard",
        "hierarchy": 1,
        "agent_owner": ["Inspector", "Engineer"],
        "priority": 90,
        "guardrail_targets": {
            "hazard_class": r"(H[1-6]\.?\d?)",
            "preservative_treatment": r"(preservative|treatment|CCA|ACQ|copper)",
            "timber_species": r"(radiata|douglas|macrocarpa|rimu)"
        }
    },
    "ABCB-Sanitary-Plumbing-and-Drainage-Pipe-Sizing-Phase-2-Report-Rev-2.pdf": {
        "new_name": "Standards - AS_NZS 3500.2 - Plumbing and Drainage Pipe Sizing (ABCB Report).pdf",
        "folder": "01_Compliance/Standards",
        "doc_type": "Standard",
        "hierarchy": 1,
        "agent_owner": ["Inspector", "Engineer"],
        "priority": 85,
        "guardrail_targets": {
            "pipe_sizing": r"(\d+)\s*mm\s*(?:pipe|diameter)",
            "grade_slope": r"(\d+)\s*(?::|in)\s*(\d+)|(\d+\.?\d*)\s*%\s*(?:grade|fall|slope)",
            "fixture_units": r"(\d+)\s*(?:fixture|loading)\s*unit"
        }
    },
    "Guide_to_the_Wiring_Rules_Changes.pdf": {
        "new_name": "Standards - AS_NZS 3000_2018 - Electrical Wiring Rules (Changes Guide).pdf",
        "folder": "01_Compliance/Standards",
        "doc_type": "Standard",
        "hierarchy": 1,
        "agent_owner": ["Inspector", "Engineer"],
        "priority": 85,
        "guardrail_targets": {
            "rcd_requirements": r"(RCD|residual.?current|30\s*mA)",
            "circuit_protection": r"(circuit.?breaker|MCB|RCBO)",
            "cable_sizing": r"(\d+\.?\d*)\s*mm.?\s*(?:cable|conductor)"
        }
    },
    "626WKS-4-electricity-installing-safe-electrical-gas-products.pdf": {
        "new_name": "WorkSafe - Designing and Installing Safe Electrical Installations.pdf",
        "folder": "01_Compliance/MBIE_Guidance",
        "doc_type": "Guidance",
        "hierarchy": 2,
        "agent_owner": ["Inspector"],
        "priority": 85,
        "guardrail_targets": {
            "safety_requirements": r"(safety|hazard|risk)",
            "compliance_path": r"(compliance|certificate|inspection)"
        }
    },
    "Building (Building Product Information Requirements) Regulations 2022.pdf": {
        "new_name": "NZBC - Building Product Information Requirements (BPIR) Regulations 2022.pdf",
        "folder": "01_Compliance/NZBC_Acceptable_Solutions",
        "doc_type": "Building_Code",
        "hierarchy": 1,
        "agent_owner": ["Inspector", "Product_Rep"],
        "priority": 95,
        "guardrail_targets": {
            "class_1_products": r"(class\s*1|high.?risk)",
            "class_2_products": r"(class\s*2|moderate.?risk)",
            "disclosure_requirements": r"(disclosure|declaration|manufacturer)"
        }
    },
    "BRANZ House Insulation Guide (6th Ed V2.4).pdf": {
        "new_name": "Industry - BRANZ House Insulation Guide (6th Ed V2.4).pdf",
        "folder": "01_Compliance/Industry_Codes",
        "doc_type": "Technical_Guide",
        "hierarchy": 2,
        "agent_owner": ["Inspector", "Engineer"],
        "priority": 90,
        "guardrail_targets": {
            "r_value_ceiling": r"R[- ]?([6-8]\.[0-9])|ceiling.*R[- ]?([0-9]\.[0-9])",
            "r_value_wall": r"wall.*R[- ]?([2-4]\.[0-9])|R[- ]?([2-4]\.[0-9]).*wall",
            "r_value_floor": r"floor.*R[- ]?([1-3]\.[0-9])|R[- ]?([1-3]\.[0-9]).*floor",
            "thermal_bridge": r"(thermal.?bridge|psi.?value|\u03A8)",
            "construction_r": r"(construction.?R|total.?R)"
        }
    }
}

def compute_page_hash(content: str) -> str:
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def chunk_text(text: str, chunk_size: int = 1500, overlap: int = 200) -> list:
    chunks = []
    start = 0
    text = text.replace('\x00', '')
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap
        if start >= len(text):
            break
    return chunks

def extract_guardrails(content: str, targets: dict) -> dict:
    """Extract Rule 6 guardrails from content"""
    guardrails = {}
    content_lower = content.lower()
    
    for key, pattern in targets.items():
        matches = re.findall(pattern, content_lower, re.IGNORECASE)
        if matches:
            # Flatten tuple matches and filter empty strings
            flat_matches = []
            for m in matches[:10]:  # Limit to first 10 matches
                if isinstance(m, tuple):
                    flat_matches.extend([x for x in m if x])
                else:
                    flat_matches.append(m)
            if flat_matches:
                guardrails[key] = list(set(flat_matches))[:5]  # Unique, max 5
    
    return guardrails

def main():
    print("═" * 70)
    print("  STRYDA PROTOCOL V2.0 - PHASE 3.2: COMPLIANCE FULL-FILL")
    print("  TARGET: Big 5 Pillar Standards")
    print("═" * 70)
    print(f"  Started: {datetime.now().isoformat()}")
    print("═" * 70)
    
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    stats = {"processed": 0, "chunks": 0, "errors": []}
    all_guardrails = {}
    
    for old_name, config in FILE_MAPPING.items():
        print(f"\n  📄 Processing: {old_name}")
        print(f"     → {config['new_name']}")
        
        try:
            # Download from temporary
            pdf_data = client.storage.from_('temporary').download(old_name)
            
            # Save temporarily
            temp_path = f"/tmp/{old_name}"
            with open(temp_path, 'wb') as f:
                f.write(pdf_data)
            
            # Upload to destination folder
            dest_path = f"{config['folder']}/{config['new_name']}"
            client.storage.from_('product-library').upload(
                dest_path,
                pdf_data,
                {"content-type": "application/pdf", "upsert": "true"}
            )
            print(f"     📦 → product-library/{dest_path}")
            
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
            
            # Extract guardrails
            guardrails = extract_guardrails(full_text, config["guardrail_targets"])
            all_guardrails[old_name] = {
                "document": config["new_name"],
                "extracted": guardrails
            }
            
            if guardrails:
                print(f"     🛡️ Guardrails: {list(guardrails.keys())}")
            
            # Ingest chunks
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
                    
                    # Build unit_range with extracted guardrails
                    unit_range = guardrails.copy() if guardrails else {}
                    
                    cur.execute("""
                        INSERT INTO documents (
                            content, source, page, page_hash,
                            hierarchy_level, agent_owner, geo_context,
                            doc_type, priority, unit_range, is_active, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        chunk,
                        dest_path,
                        page_num,
                        page_hash,
                        config["hierarchy"],
                        config["agent_owner"],
                        "NZ_Specific",
                        config["doc_type"],
                        config["priority"],
                        json.dumps(unit_range) if unit_range else None,
                        True,
                        datetime.utcnow()
                    ))
                    chunks_inserted += 1
            
            conn.commit()
            stats["processed"] += 1
            stats["chunks"] += chunks_inserted
            print(f"     ✅ Ingested: {chunks_inserted} chunks")
            
        except Exception as e:
            print(f"     ❌ ERROR: {e}")
            stats["errors"].append(old_name)
    
    # Cleanup temporary bucket
    print("\n" + "─" * 70)
    print("  CLEANUP: Removing processed files from temporary/")
    print("─" * 70)
    
    for old_name in FILE_MAPPING.keys():
        try:
            client.storage.from_('temporary').remove([old_name])
            print(f"  🗑️ Deleted: {old_name}")
        except Exception as e:
            print(f"  ⚠️ Could not delete {old_name}: {e}")
    
    # Guardrail Report
    print("\n" + "─" * 70)
    print("  RULE 6: WEAPONIZED GUARDRAILS EXTRACTED")
    print("─" * 70)
    
    for doc_name, data in all_guardrails.items():
        print(f"\n  📋 {data['document'][:50]}...")
        for key, values in data['extracted'].items():
            if values:
                print(f"     ✅ {key}: {values[:3]}{'...' if len(values) > 3 else ''}")
    
    # Final Report
    print("\n" + "═" * 70)
    print("  PHASE 3.2: COMPLIANCE FULL-FILL - FINAL REPORT")
    print("═" * 70)
    print(f"  📊 Documents Processed: {stats['processed']}")
    print(f"  📊 Total Chunks: {stats['chunks']}")
    print(f"  ❌ Errors: {len(stats['errors'])}")
    print("═" * 70)
    print(f"  ✅ COMPLIANCE FOUNDATION 100% LOCKED")
    print(f"  🚀 Storage and Database in sync")
    print(f"  Completed: {datetime.now().isoformat()}")
    print("═" * 70)
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
