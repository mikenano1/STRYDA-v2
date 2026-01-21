#!/usr/bin/env python3
"""
MASONS FINAL INGESTION - Rule 6 Extraction
============================================
Target: 5 Masons files from temporary/ bucket
Guardrails to Extract:
- UNI PRO: 150-day UV exposure limit
- 40 Below Platinum: 180-day UV limit + 2-layer sill requirement
"""

import os
import re
import hashlib
import json
from datetime import datetime
from supabase import create_client
import fitz  # PyMuPDF

# Configuration
SUPABASE_URL = "https://qxqisgjhbjwvoxsjibes.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF4cWlzZ2poYmp3dm94c2ppYmVzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1OTQ3MDY5NSwiZXhwIjoyMDc1MDQ2Njk1fQ.iOaE9PsoN1NPjDiUOlTmzcaqiRbjbdtPMNDAKGtbFsk"
DATABASE_URL = "postgresql://postgres.qxqisgjhbjwvoxsjibes:8skmVOJbMyaQHyQl@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres"

# Target files
MASONS_FILES = [
    "Masons - 40 Below Platinum - Technical Data Sheet.pdf",
    "Masons - Barricade WD - Design and Installation Manual (MASTER).pdf",
    "Masons - Intertenancy - Wall System Design Guide.pdf",
    "Masons - UNI PRO - Flexible Air Barrier Installation (2025).pdf",
    "Masons - VHP Maxi - Roof Underlay Technical PASS (2026).pdf"
]

# Rule 6 Guardrail Patterns
GUARDRAIL_PATTERNS = {
    "uv_exposure_days": [
        r"(\d+)\s*(?:day|days)\s*(?:UV|ultra.?violet|exposure)",
        r"UV\s*(?:exposure|limit)[:\s]*(\d+)\s*days?",
        r"expose[d]?\s*(?:for|up\s*to)?\s*(\d+)\s*days?",
        r"(\d+)\s*days?\s*(?:maximum|max)?\s*(?:UV|exposure)",
    ],
    "sill_requirement": [
        r"(2[-\s]?layer\s*sill)",
        r"(double\s*sill)",
        r"(sill\s*flashing\s*(?:2|two)\s*layer)",
        r"(two[-\s]?layer\s*sill)",
    ],
    "nail_sealability": [
        r"(nail\s*seal)",
        r"(screw\s*seal)",
        r"(self[-\s]?seal)",
        r"(puncture\s*seal)",
    ]
}

def extract_guardrails(content: str, filename: str) -> dict:
    """Extract Rule 6 guardrails from content"""
    guardrails = {
        "uv_exposure_days": None,
        "sill_requirement": None,
        "nail_sealability": False,
        "product_specific": {}
    }
    
    content_lower = content.lower()
    
    # Extract UV exposure days
    for pattern in GUARDRAIL_PATTERNS["uv_exposure_days"]:
        matches = re.findall(pattern, content_lower)
        if matches:
            # Get the highest UV day value found
            days = [int(m) for m in matches if m.isdigit()]
            if days:
                guardrails["uv_exposure_days"] = max(days)
                break
    
    # Extract sill requirements
    for pattern in GUARDRAIL_PATTERNS["sill_requirement"]:
        if re.search(pattern, content_lower):
            guardrails["sill_requirement"] = "2-layer sill required"
            break
    
    # Check nail/screw sealability
    for pattern in GUARDRAIL_PATTERNS["nail_sealability"]:
        if re.search(pattern, content_lower):
            guardrails["nail_sealability"] = True
            break
    
    # Product-specific extractions
    if "40 below" in filename.lower() or "40 below" in content_lower:
        guardrails["product_specific"]["product_name"] = "40 Below Platinum"
        guardrails["product_specific"]["target_uv_days"] = 180
        # Look for specific 180-day mention
        if "180" in content:
            guardrails["uv_exposure_days"] = 180
            
    if "uni pro" in filename.lower() or "uni pro" in content_lower:
        guardrails["product_specific"]["product_name"] = "UNI PRO"
        guardrails["product_specific"]["target_uv_days"] = 150
        # Look for specific 150-day mention
        if "150" in content:
            guardrails["uv_exposure_days"] = 150
    
    return guardrails

def compute_page_hash(content: str) -> str:
    """Compute SHA-256 hash for deduplication"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def determine_agent_owner(filename: str, content: str) -> list:
    """Assign agent owner based on document type"""
    filename_lower = filename.lower()
    content_lower = content.lower()
    
    owners = []
    
    if "installation" in filename_lower or "install" in content_lower:
        owners.append("Inspector")
    if "technical" in filename_lower or "data sheet" in filename_lower:
        owners.extend(["Inspector", "Engineer"])
    if "design" in filename_lower or "guide" in filename_lower:
        owners.append("Engineer")
    if "bpir" in filename_lower or "compliance" in content_lower:
        owners.append("Product_Rep")
    
    return owners if owners else ["Inspector"]

def chunk_text(text: str, chunk_size: int = 1500, overlap: int = 200) -> list:
    """Split text into overlapping chunks"""
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]
        
        # Clean NUL characters
        chunk = chunk.replace('\x00', '')
        
        if chunk.strip():
            chunks.append(chunk)
        
        start = end - overlap
        if start >= text_len:
            break
    
    return chunks

def process_pdf(client, filename: str) -> dict:
    """Download and process a single PDF"""
    print(f"\n📄 Processing: {filename}")
    
    try:
        # Download from temporary bucket
        response = client.storage.from_('temporary').download(filename)
        
        # Save temporarily
        temp_path = f"/tmp/{filename}"
        with open(temp_path, 'wb') as f:
            f.write(response)
        
        # Extract text with PyMuPDF
        doc = fitz.open(temp_path)
        full_text = ""
        page_texts = []
        
        for page_num, page in enumerate(doc):
            page_text = page.get_text()
            page_texts.append({"page": page_num + 1, "text": page_text})
            full_text += page_text + "\n"
        
        doc.close()
        os.remove(temp_path)
        
        # Extract guardrails from full document
        guardrails = extract_guardrails(full_text, filename)
        
        print(f"  📊 Extracted {len(page_texts)} pages")
        print(f"  🛡️ Guardrails: UV={guardrails['uv_exposure_days']} days, Sill={guardrails['sill_requirement']}, NailSeal={guardrails['nail_sealability']}")
        
        return {
            "filename": filename,
            "full_text": full_text,
            "page_texts": page_texts,
            "guardrails": guardrails,
            "page_count": len(page_texts)
        }
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None

def ingest_to_database(pdf_data: dict) -> int:
    """Ingest processed PDF into database"""
    import psycopg2
    
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    chunks_inserted = 0
    filename = pdf_data["filename"]
    guardrails = pdf_data["guardrails"]
    
    # Determine storage path
    storage_path = f"B_Enclosure/Underlays_and_Wraps/Masons/{filename}"
    
    # Process each page
    for page_data in pdf_data["page_texts"]:
        page_num = page_data["page"]
        page_text = page_data["text"]
        
        if not page_text.strip():
            continue
        
        # Chunk the page
        chunks = chunk_text(page_text)
        
        for chunk_idx, chunk_content in enumerate(chunks):
            if not chunk_content.strip():
                continue
            
            # Compute page hash
            page_hash = compute_page_hash(chunk_content)
            
            # Check for duplicates
            cur.execute(
                "SELECT id FROM documents WHERE page_hash = %s",
                (page_hash,)
            )
            if cur.fetchone():
                continue  # Skip duplicate
            
            # Build unit_range with guardrails
            unit_range = {}
            if guardrails["uv_exposure_days"]:
                unit_range["uv_exposure_limit_days"] = guardrails["uv_exposure_days"]
            if guardrails["sill_requirement"]:
                unit_range["sill_requirement"] = guardrails["sill_requirement"]
            if guardrails["nail_sealability"]:
                unit_range["nail_screw_sealability"] = True
            if guardrails["product_specific"]:
                unit_range["product_info"] = guardrails["product_specific"]
            
            # Determine agent owner
            agent_owner = determine_agent_owner(filename, chunk_content)
            
            # Insert chunk
            cur.execute("""
                INSERT INTO documents (
                    content, source, page, page_hash,
                    hierarchy_level, agent_owner, geo_context,
                    unit_range, is_active, created_at, brand_name, trade
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                chunk_content,
                storage_path,
                page_num,
                page_hash,
                3,  # Manufacturer hierarchy
                agent_owner,
                "NZ_Specific",
                json.dumps(unit_range) if unit_range else None,
                True,
                datetime.utcnow(),
                "Masons",
                "underlays"
            ))
            
            chunks_inserted += 1
    
    conn.commit()
    cur.close()
    conn.close()
    
    return chunks_inserted

def main():
    print("=" * 70)
    print("🔧 MASONS FINAL INGESTION - Rule 6 Extraction")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")
    
    # Connect to Supabase
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    total_chunks = 0
    results = []
    
    for filename in MASONS_FILES:
        pdf_data = process_pdf(client, filename)
        
        if pdf_data:
            chunks = ingest_to_database(pdf_data)
            total_chunks += chunks
            results.append({
                "file": filename,
                "chunks": chunks,
                "guardrails": pdf_data["guardrails"]
            })
            print(f"  ✅ Inserted {chunks} chunks")
    
    print("\n" + "=" * 70)
    print("📊 INGESTION SUMMARY")
    print("=" * 70)
    
    for r in results:
        print(f"\n📄 {r['file']}")
        print(f"   Chunks: {r['chunks']}")
        print(f"   UV Limit: {r['guardrails']['uv_exposure_days']} days")
        print(f"   Sill Req: {r['guardrails']['sill_requirement']}")
        print(f"   Nail Seal: {r['guardrails']['nail_sealability']}")
    
    print(f"\n✅ TOTAL CHUNKS INGESTED: {total_chunks}")
    print(f"Completed: {datetime.now().isoformat()}")

if __name__ == "__main__":
    main()
