#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
    STRYDA PROTOCOL V2.0 - KOOLTHERM K12 FRAMING BOARD MIGRATION
    SOURCE: product-library/03_Kooltherm_K12_Framing_Board/ (misplaced)
    DEST: product-library/C_Interiors/Kingspan_Insulation/03_Kooltherm_K12_Framing_Board/
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

SOURCE_FOLDER = "03_Kooltherm_K12_Framing_Board"
DEST_FOLDER = "C_Interiors/Kingspan_Insulation/03_Kooltherm_K12_Framing_Board"

# V2.0 File Naming & Categorization
FILE_CONFIG = {
    "doc_types": {
        "data-sheet": "Technical_Data_Sheet",
        "installation-guide": "Installation_Guide",
        "codemark": "CodeMark_Certificate",
        "branz-appraisal": "BRANZ_Appraisal",
        "greentag": "GreenTag_Certificate",
        "epd": "EPD",
        "warranty": "Warranty",
    },
    "hierarchy": 3,  # Manufacturer level
    "brand_name": "Kingspan",
    "product_line": "Kooltherm K12 Framing Board",
    "trade": "insulation",
    "geo_context": "NZ_Specific"
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

def determine_doc_type(filename: str) -> str:
    filename_lower = filename.lower()
    for key, doc_type in FILE_CONFIG["doc_types"].items():
        if key in filename_lower:
            return doc_type
    return "Technical_Drawing"  # Default for detail drawings

def determine_agent_owner(filename: str) -> list:
    filename_lower = filename.lower()
    if "installation" in filename_lower or "guide" in filename_lower:
        return ["Inspector"]
    elif "codemark" in filename_lower or "branz" in filename_lower or "certificate" in filename_lower:
        return ["Inspector", "Engineer"]
    elif "data-sheet" in filename_lower or "specification" in filename_lower:
        return ["Inspector", "Engineer"]
    elif "epd" in filename_lower or "greentag" in filename_lower:
        return ["Product_Rep"]
    else:
        return ["Inspector"]  # Technical drawings default to Inspector

def extract_k12_guardrails(content: str, filename: str) -> dict:
    """Extract Rule 6 guardrails for K12 Framing Board"""
    guardrails = {
        "product_line": "Kooltherm K12 Framing Board",
        "r_value": None,
        "thickness_mm": None,
        "application": None
    }
    
    content_lower = content.lower()
    
    # Extract R-value
    r_match = re.search(r'R[- ]?(\d+\.?\d*)', content)
    if r_match:
        guardrails["r_value"] = f"R{r_match.group(1)}"
    
    # Extract thickness
    thick_match = re.search(r'(\d+)\s*mm\s*(?:thick|thickness|board)?', content_lower)
    if thick_match:
        guardrails["thickness_mm"] = int(thick_match.group(1))
    
    # Determine application from filename
    if "external" in filename.lower():
        guardrails["application"] = "External"
    elif "internal" in filename.lower():
        guardrails["application"] = "Internal"
    
    return guardrails

def v2_rename_file(old_name: str) -> str:
    """Apply V2.0 naming convention"""
    # Already mostly well-named, just ensure Kingspan prefix
    if not old_name.lower().startswith("kingspan"):
        return f"Kingspan - {old_name}"
    return old_name

def main():
    print("═" * 70)
    print("  STRYDA PROTOCOL V2.0 - KOOLTHERM K12 MIGRATION")
    print("═" * 70)
    print(f"  Started: {datetime.now().isoformat()}")
    print(f"  Source: {SOURCE_FOLDER}/")
    print(f"  Dest: {DEST_FOLDER}/")
    print("═" * 70)
    
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    stats = {"moved": 0, "ingested": 0, "chunks": 0, "errors": []}
    
    # Get files from misplaced folder
    files = client.storage.from_('product-library').list(SOURCE_FOLDER)
    print(f"\n📁 Found {len(files)} files to migrate")
    
    for file_info in files:
        old_name = file_info.get('name')
        if not old_name:
            continue
            
        print(f"\n  📄 {old_name}")
        
        try:
            # Download file
            old_path = f"{SOURCE_FOLDER}/{old_name}"
            pdf_data = client.storage.from_('product-library').download(old_path)
            
            # Apply V2.0 naming
            new_name = v2_rename_file(old_name)
            new_path = f"{DEST_FOLDER}/{new_name}"
            
            # Upload to correct location
            client.storage.from_('product-library').upload(
                new_path,
                pdf_data,
                {"content-type": "application/pdf", "upsert": "true"}
            )
            print(f"     ✅ Moved → {DEST_FOLDER}/{new_name}")
            stats["moved"] += 1
            
            # Save temporarily for ingestion
            temp_path = f"/tmp/{old_name}"
            with open(temp_path, 'wb') as f:
                f.write(pdf_data)
            
            # Extract text
            try:
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
                guardrails = extract_k12_guardrails(full_text, old_name)
                doc_type = determine_doc_type(old_name)
                agent_owner = determine_agent_owner(old_name)
                
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
                        
                        # Build unit_range
                        unit_range = {}
                        if guardrails["r_value"]:
                            unit_range["r_value"] = guardrails["r_value"]
                        if guardrails["thickness_mm"]:
                            unit_range["thickness_mm"] = guardrails["thickness_mm"]
                        if guardrails["application"]:
                            unit_range["application"] = guardrails["application"]
                        unit_range["product_line"] = guardrails["product_line"]
                        
                        cur.execute("""
                            INSERT INTO documents (
                                content, source, page, page_hash,
                                hierarchy_level, agent_owner, geo_context,
                                doc_type, brand_name, trade, unit_range,
                                is_active, created_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            chunk,
                            new_path,
                            page_num,
                            page_hash,
                            FILE_CONFIG["hierarchy"],
                            agent_owner,
                            FILE_CONFIG["geo_context"],
                            doc_type,
                            FILE_CONFIG["brand_name"],
                            FILE_CONFIG["trade"],
                            json.dumps(unit_range) if unit_range else None,
                            True,
                            datetime.utcnow()
                        ))
                        chunks_inserted += 1
                
                conn.commit()
                stats["ingested"] += 1
                stats["chunks"] += chunks_inserted
                print(f"     📊 Ingested: {chunks_inserted} chunks ({doc_type})")
                
            except Exception as e:
                print(f"     ⚠️ Ingestion skipped: {e}")
                
        except Exception as e:
            print(f"     ❌ ERROR: {e}")
            stats["errors"].append(old_name)
    
    # Delete original misplaced folder contents
    print("\n" + "─" * 70)
    print("  CLEANUP: Removing misplaced folder")
    print("─" * 70)
    
    for file_info in files:
        old_name = file_info.get('name')
        if old_name:
            try:
                old_path = f"{SOURCE_FOLDER}/{old_name}"
                client.storage.from_('product-library').remove([old_path])
                print(f"  🗑️ Deleted: {old_path}")
            except Exception as e:
                print(f"  ⚠️ Could not delete {old_path}: {e}")
    
    # Final Report
    print("\n" + "═" * 70)
    print("  KOOLTHERM K12 MIGRATION - FINAL REPORT")
    print("═" * 70)
    print(f"  📊 Files Moved: {stats['moved']}")
    print(f"  📊 Files Ingested: {stats['ingested']}")
    print(f"  📊 Total Chunks: {stats['chunks']}")
    print(f"  ❌ Errors: {len(stats['errors'])}")
    print("═" * 70)
    print(f"  ✅ KOOLTHERM K12 FRAMING BOARD - PROTOCOL V2.0 COMPLETE")
    print(f"  Completed: {datetime.now().isoformat()}")
    print("═" * 70)
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
