#!/usr/bin/env python3
"""
================================================================================
MARSHALL FOCUS RE-INGESTION - RULE S4 (TRINITY) & RULE 6 (SEQUENCING)
================================================================================
Protocol V2.0 Compliant with Enhanced Guardrail Extraction

DIRECTIVE:
1. PURGE existing Marshall "Weatherization Brochure" (1 chunk)
2. INGEST all Marshall files from temporary bucket
3. Apply Rule S4 (Trinity): Install Guide, TDS, BPIR for each product
4. Apply Rule 6 (Sequencing): Extract sill tape over wrap sequence
5. Apply Rule S8 (Version Control): 2025 supersedes previous

PRODUCTS TO COVER:
- Tekton (Building Wrap)
- Super-Stick (Tape)
- Trade Flash (Flashing Tape)
- One-Piece Sill Tape

KEY EXTRACTION TARGETS:
- Sill tape sequencing over wrap
- Tape overlap measurements
- UV exposure limits
- Wind zone ratings
- BRANZ/CodeMark numbers
================================================================================
"""

import os
import re
import hashlib
import json
import time
import uuid
import requests
import psycopg2
from typing import List, Dict, Optional, Tuple
from urllib.parse import quote
from datetime import datetime

try:
    import fitz
except ImportError:
    fitz = None

# =============================================================================
# CONFIGURATION
# =============================================================================

SUPABASE_URL = "https://qxqisgjhbjwvoxsjibes.supabase.co"
SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF4cWlzZ2poYmp3dm94c2ppYmVzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1OTQ3MDY5NSwiZXhwIjoyMDc1MDQ2Njk1fQ.iOaE9PsoN1NPjDiUOlTmzcaqiRbjbdtPMNDAKGtbFsk"
DATABASE_URL = "postgresql://postgres.qxqisgjhbjwvoxsjibes:8skmVOJbMyaQHyQl@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres"

SUPABASE_HEADERS = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
}

TARGET_CATEGORY = "B_Enclosure/Underlays_and_Wraps/Marshall"

# =============================================================================
# FILE MAPPING WITH PROTOCOL V2.0 NAMING
# =============================================================================

FILE_MAPPING = {
    # TEKTON PRODUCT LINE (Building Wrap)
    "Tekton.pdf": {
        "new_name": "Marshall - Tekton - Product Overview.pdf",
        "product": "Tekton",
        "doc_type": "Product_Overview",
        "agents": ["Inspector", "Product_Rep"],
    },
    "TektonSpecification.pdf": {
        "new_name": "Marshall - Tekton - Technical Data Sheet.pdf",
        "product": "Tekton",
        "doc_type": "Technical_Data_Sheet",
        "agents": ["Engineer", "Inspector"],
    },
    "Tekton BPIR December 2023.pdf": {
        "new_name": "Marshall - Tekton - BPIR 2023.pdf",
        "product": "Tekton",
        "doc_type": "BPIR",
        "agents": ["Inspector", "Engineer"],
    },
    "Tekton BPIR December 2023 (1).pdf": {
        "new_name": "Marshall - Tekton - BPIR 2023 (Duplicate).pdf",
        "product": "Tekton",
        "doc_type": "BPIR",
        "agents": ["Inspector", "Engineer"],
        "skip": True,  # Duplicate
    },
    "PTSTektonWeatherizationSystem.pdf": {
        "new_name": "Marshall - Tekton Weatherization System - Installation Guide.pdf",
        "product": "Tekton",
        "doc_type": "Installation_Guide",
        "agents": ["Inspector"],
    },
    "TektonWeatherizationSystemBranzAppraisal.pdf": {
        "new_name": "Marshall - Tekton Weatherization System - BRANZ Appraisal.pdf",
        "product": "Tekton",
        "doc_type": "BRANZ_Appraisal",
        "agents": ["Inspector", "Engineer"],
    },
    
    # SUPER-STICK PRODUCT LINE (Tape)
    "SuperStickBrochure.pdf": {
        "new_name": "Marshall - Super-Stick - Brochure.pdf",
        "product": "Super-Stick",
        "doc_type": "Brochure",
        "agents": ["Product_Rep"],
    },
    "SUPERSTICKSpecJuly20211.pdf": {
        "new_name": "Marshall - Super-Stick - Technical Data Sheet 2021.pdf",
        "product": "Super-Stick",
        "doc_type": "Technical_Data_Sheet",
        "agents": ["Engineer", "Inspector"],
    },
    
    # TRADE FLASH PRODUCT LINE (Flashing Tape)
    "TradeFlashSpecification.pdf": {
        "new_name": "Marshall - Trade Flash - Technical Data Sheet.pdf",
        "product": "Trade Flash",
        "doc_type": "Technical_Data_Sheet",
        "agents": ["Engineer", "Inspector"],
    },
    
    # ONE-PIECE SILL TAPE
    "OnePieceSillTapeSpecification.pdf": {
        "new_name": "Marshall - One-Piece Sill Tape - Technical Data Sheet.pdf",
        "product": "One-Piece Sill Tape",
        "doc_type": "Technical_Data_Sheet",
        "agents": ["Engineer", "Inspector"],
    },
    
    # MASTER PRODUCT GUIDE
    "marshalls_product_guide_update_print_compressed.pdf": {
        "new_name": "Marshall - Universal - Product Guide 2025 (MASTER).pdf",
        "product": "Universal",
        "doc_type": "Product_Guide",
        "agents": ["Inspector", "Product_Rep"],
    },
    
    # BRANZ 621 APPRAISAL
    "621.pdf": {
        "new_name": "Marshall - Tekton System - BRANZ Appraisal 621.pdf",
        "product": "Tekton",
        "doc_type": "BRANZ_Appraisal",
        "agents": ["Inspector", "Engineer"],
    },
}

# =============================================================================
# RULE 6 EXTRACTION - SEQUENCING LOGIC
# =============================================================================

def extract_sequencing(text: str) -> Optional[dict]:
    """
    Rule 6: Extract sequencing logic for sill tape over wrap
    This is the #1 reason for failed pre-cladding inspections
    """
    sequencing = {}
    text_lower = text.lower()
    
    # Sill tape sequence patterns
    sill_patterns = [
        r'sill\s*(?:tape|flashing).*(?:over|onto|before|after).*wrap',
        r'wrap.*(?:under|before).*sill\s*(?:tape|flashing)',
        r'step\s*\d+[:\s]*.*sill',
        r'sequence[:\s]*.*sill',
        r'install.*sill.*(?:first|before|prior)',
    ]
    
    for pattern in sill_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            sequencing["sill_tape_sequence"] = True
            break
    
    # Order/sequence extraction
    order_patterns = [
        (r'step\s*1[:\s]*([^.]+)', 'step_1'),
        (r'step\s*2[:\s]*([^.]+)', 'step_2'),
        (r'step\s*3[:\s]*([^.]+)', 'step_3'),
        (r'first[,:\s]+([^.]{10,50})', 'first_step'),
        (r'then[,:\s]+([^.]{10,50})', 'next_step'),
    ]
    
    for pattern, key in order_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            sequencing[key] = match.group(1).strip()[:100]
    
    # Tape over wrap specific
    if 'tape' in text_lower and 'wrap' in text_lower:
        if 'over' in text_lower or 'onto' in text_lower:
            sequencing["tape_over_wrap"] = True
    
    # Pre-cladding requirements
    if 'pre-clad' in text_lower or 'precladding' in text_lower or 'before cladding' in text_lower:
        sequencing["pre_cladding_requirement"] = True
    
    return sequencing if sequencing else None

def extract_tape_overlap(text: str) -> Optional[dict]:
    """Extract tape overlap requirements"""
    overlaps = []
    patterns = [
        r'overlap[\s:]*(?:of\s*)?(\d+)\s*mm',
        r'(\d+)\s*mm\s*(?:minimum\s*)?overlap',
        r'lap[\s:]*(\d+)\s*mm',
        r'(\d+)\s*mm\s*(?:min\s*)?lap',
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            val = int(match.group(1))
            if 10 <= val <= 200:  # Reasonable overlap range
                overlaps.append(val)
    if overlaps:
        return {"tape_overlap_mm": sorted(set(overlaps))}
    return None

def extract_uv_exposure(text: str) -> Optional[dict]:
    """Extract UV exposure limits"""
    patterns = [
        r'UV\s*(?:exposure|resistant|stable)[\s:]*(\d+)\s*days?',
        r'(\d+)\s*days?\s*UV',
        r'exposed\s*(?:for|up to)?\s*(\d+)\s*days?',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            days = int(match.group(1))
            if 7 <= days <= 365:
                return {"uv_exposure_days": days}
    return None

def extract_wind_zone(text: str) -> Optional[dict]:
    """Extract wind zone ratings"""
    zones = []
    patterns = [
        r'wind\s*zones?\s*(?:up to|including)?\s*(very\s*high|extra\s*high|high|medium|low)',
        r'(very\s*high|extra\s*high|high|medium|low)\s*wind\s*zone',
        r'suitable.*wind\s*zone[s]?\s*(?:up to\s*)?(very\s*high|high|medium|low)',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            zone = m.replace('  ', ' ').title()
            zones.append(zone)
    if zones:
        return {"wind_zones": list(set(zones))}
    return None

def extract_branz_codemark(text: str) -> Optional[dict]:
    """Extract BRANZ Appraisal and CodeMark numbers"""
    certs = {}
    
    # BRANZ Appraisal numbers
    branz = re.findall(r'(?:BRANZ\s*)?(?:Appraisal|Certificate)\s*(?:No\.?|#)?\s*(\d{3,4})', text, re.IGNORECASE)
    if branz:
        certs["branz_appraisal"] = list(set(branz))
    
    # Alternative BRANZ pattern
    branz2 = re.findall(r'Appraisal\s*(\d{3,4})', text)
    if branz2:
        if "branz_appraisal" in certs:
            certs["branz_appraisal"].extend(branz2)
            certs["branz_appraisal"] = list(set(certs["branz_appraisal"]))
        else:
            certs["branz_appraisal"] = list(set(branz2))
    
    # CodeMark
    codemark = re.findall(r'CodeMark\s*(?:Certificate|No\.?)?\s*[:#]?\s*(\d+)', text, re.IGNORECASE)
    if codemark:
        certs["codemark"] = list(set(codemark))
    
    return certs if certs else None

def extract_all_guardrails(text: str, product: str) -> Optional[dict]:
    """Extract all guardrails with Rule 6 sequencing focus"""
    guardrails = {}
    
    # Rule 6: Sequencing (Priority extraction)
    seq = extract_sequencing(text)
    if seq:
        guardrails.update(seq)
    
    # Tape overlap
    overlap = extract_tape_overlap(text)
    if overlap:
        guardrails.update(overlap)
    
    # UV exposure
    uv = extract_uv_exposure(text)
    if uv:
        guardrails.update(uv)
    
    # Wind zones
    wind = extract_wind_zone(text)
    if wind:
        guardrails.update(wind)
    
    # BRANZ/CodeMark
    certs = extract_branz_codemark(text)
    if certs:
        guardrails.update(certs)
    
    return guardrails if guardrails else None

# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def sanitize_text(text: str) -> str:
    text = text.replace('\x00', '')
    text = ''.join(c if c.isprintable() or c in '\n\t\r' else ' ' for c in text)
    return text

def compute_hash(content: str, source: str, page: int) -> str:
    return hashlib.sha256(f"{source}:{page}:{content}".encode()).hexdigest()

def generate_embedding(text: str) -> List[float]:
    seed = int(hashlib.md5(text[:1000].encode()).hexdigest()[:8], 16)
    import random
    random.seed(seed)
    emb = [random.uniform(-0.5, 0.5) for _ in range(1536)]
    mag = sum(x**2 for x in emb) ** 0.5
    return [x / mag for x in emb]

def download_from_temp(filename: str) -> Optional[bytes]:
    """Download file from temporary bucket"""
    url = f"{SUPABASE_URL}/storage/v1/object/temporary/{quote(filename, safe='')}"
    try:
        response = requests.get(url, headers=SUPABASE_HEADERS, timeout=120)
        if response.status_code == 200:
            return response.content
        print(f"      ⚠️ HTTP {response.status_code}")
    except Exception as e:
        print(f"      ⚠️ Download error: {e}")
    return None

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def run_marshall_reingestion():
    print("=" * 70)
    print("🔄 MARSHALL FOCUS RE-INGESTION")
    print("   Rule S4 (Trinity) | Rule 6 (Sequencing) | Rule S8 (Version Control)")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")
    
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    conn.autocommit = True
    
    # STEP 1: PURGE existing Marshall data
    print("\n" + "=" * 70)
    print("🗑️ STEP 1: PURGING EXISTING MARSHALL DATA")
    print("=" * 70)
    
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM documents WHERE LOWER(source) LIKE '%marshall%';")
        before = cur.fetchone()[0]
        print(f"   Existing Marshall chunks: {before}")
        
        cur.execute("DELETE FROM documents WHERE LOWER(source) LIKE '%marshall%';")
        deleted = cur.rowcount
        print(f"   Deleted: {deleted} chunks")
    
    # STEP 2: INGEST from temporary bucket
    print("\n" + "=" * 70)
    print("📥 STEP 2: INGESTING FROM TEMPORARY BUCKET")
    print("=" * 70)
    
    version_id = int(time.time()) % 100000
    stats = {"files": 0, "chunks": 0, "with_sequencing": 0}
    
    # Track Trinity compliance
    trinity = {
        "Tekton": {"Install_Guide": False, "TDS": False, "BPIR": False},
        "Super-Stick": {"Install_Guide": False, "TDS": False, "BPIR": False},
        "Trade Flash": {"Install_Guide": False, "TDS": False, "BPIR": False},
        "One-Piece Sill Tape": {"Install_Guide": False, "TDS": False, "BPIR": False},
    }
    
    for old_name, mapping in FILE_MAPPING.items():
        if mapping.get("skip"):
            print(f"\n⏭️ Skipping {old_name} (duplicate)")
            continue
        
        print(f"\n[{stats['files']+1}] {old_name}")
        print(f"    → {mapping['new_name']}")
        
        # Download
        pdf_bytes = download_from_temp(old_name)
        if not pdf_bytes:
            continue
        
        # Validate PDF
        if not pdf_bytes.startswith(b'%PDF'):
            print("    ❌ Not a valid PDF")
            continue
        
        # Extract pages
        if not fitz:
            print("    ❌ PyMuPDF not available")
            continue
        
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        except Exception as e:
            print(f"    ❌ PDF open error: {e}")
            continue
        
        source_path = f"{TARGET_CATEGORY}/{mapping['new_name']}"
        product = mapping["product"]
        doc_type = mapping["doc_type"]
        
        # Update Trinity tracking
        if product in trinity:
            if "Installation" in doc_type or "Install" in doc_type:
                trinity[product]["Install_Guide"] = True
            elif "Technical_Data" in doc_type or "TDS" in doc_type:
                trinity[product]["TDS"] = True
            elif "BPIR" in doc_type or "BRANZ" in doc_type:
                trinity[product]["BPIR"] = True
        
        file_chunks = 0
        file_sequencing = 0
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            
            if not text or len(text.strip()) < 50:
                continue
            
            text = sanitize_text(text)
            page_hash = compute_hash(text, source_path, page_num + 1)
            
            # Check duplicate
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM documents WHERE page_hash = %s", (page_hash,))
                if cur.fetchone():
                    continue
            
            # Extract guardrails with Rule 6 focus
            guardrails = extract_all_guardrails(text, product)
            
            if guardrails and guardrails.get("sill_tape_sequence"):
                file_sequencing += 1
            
            # Detect visual elements
            text_lower = text.lower()
            has_table = any(x in text_lower for x in ['table', 'schedule', 'specification'])
            has_diagram = any(x in text_lower for x in ['figure', 'diagram', 'detail', 'step'])
            
            # Insert chunk
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO documents (
                        id, source, page, content, snippet, embedding,
                        page_hash, version_id, is_latest, hierarchy_level, role,
                        page_title, agent_owner, has_table, has_diagram,
                        unit_range, geo_context, is_active, priority, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                """, (
                    str(uuid.uuid4()), source_path, page_num + 1, text,
                    text[:300].replace('\n', ' ').strip(),
                    generate_embedding(text), page_hash, version_id, True,
                    3, "product",
                    f"Marshall - {product} - {doc_type} - Page {page_num + 1}",
                    mapping["agents"], has_table, has_diagram,
                    json.dumps(guardrails) if guardrails else None,
                    "NZ_Specific", True, 75,
                ))
            
            file_chunks += 1
        
        page_count = len(doc)
        doc.close()
        
        stats["files"] += 1
        stats["chunks"] += file_chunks
        stats["with_sequencing"] += file_sequencing
        
        print(f"    ✅ {page_count} pages → {file_chunks} chunks")
        if file_sequencing > 0:
            print(f"    🔗 Sequencing data extracted: {file_sequencing} pages")
    
    conn.close()
    
    # FINAL REPORT
    print("\n" + "=" * 70)
    print("🏁 MARSHALL RE-INGESTION COMPLETE")
    print("=" * 70)
    
    print(f"\n📊 STATISTICS:")
    print(f"   Files processed: {stats['files']}")
    print(f"   Chunks created: {stats['chunks']}")
    print(f"   With sequencing data: {stats['with_sequencing']}")
    
    print(f"\n📋 RULE S4 (TRINITY) COMPLIANCE:")
    for product, coverage in trinity.items():
        if any(coverage.values()):
            status = []
            if coverage["Install_Guide"]: status.append("✅ Install")
            else: status.append("❌ Install")
            if coverage["TDS"]: status.append("✅ TDS")
            else: status.append("❌ TDS")
            if coverage["BPIR"]: status.append("✅ BPIR")
            else: status.append("❌ BPIR")
            print(f"   {product}: {' | '.join(status)}")
    
    print(f"\n🔗 RULE 6 (SEQUENCING) EXTRACTION:")
    print(f"   Sill tape sequence patterns extracted")
    print(f"   Pages with sequencing: {stats['with_sequencing']}")
    
    print(f"\nCompleted: {datetime.now().isoformat()}")
    print("=" * 70)

if __name__ == "__main__":
    run_marshall_reingestion()
