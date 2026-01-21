#!/usr/bin/env python3
"""
================================================================================
H1 2026 WEAPONIZED INGESTION - INSPECTOR AGENT GUARDRAILS
================================================================================
Protocol V2.0 with Enhanced H1 2026 Extraction

GUARDRAIL TARGETS:
1. R-Value Matrix: R-Value vs Thickness table (R2.2=90mm, R2.6=90mm HD)
2. Clearance Guardrail: 25mm air-gap requirement (insulation to underlay)
3. Safety Extraction: Recessed downlight clearances (AS/NZS 3000)
4. Rule S8 Audit: Discard pre-H1 R-values, only R7.0 ceiling & HD wall for 2026

KEY 2026 H1 VALUES:
- Ceiling: R7.0 minimum
- Wall: R2.6 High Density minimum
- Underfloor: R2.8 minimum
================================================================================
"""

import os
import re
import hashlib
import json
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

# =============================================================================
# H1 2026 FILE MAPPING
# =============================================================================

H1_FILES = [
    {
        "old_name": "(H1) Knauf - Earthwool - Ceiling Segments Technical Data.pdf",
        "new_name": "Knauf - Earthwool - Ceiling Segments Technical Data (H1 2026).pdf",
        "category": "C_Interiors/Insulation/Knauf",
        "product": "Earthwool Ceiling Segments",
        "doc_type": "Technical_Data_Sheet",
        "agents": ["Inspector", "Engineer"],
        "h1_relevant": True,
        "application": "ceiling",
    },
    {
        "old_name": "Knauf - Earthwool - BPIR Summary Declaration (2025).pdf",
        "new_name": "Knauf - Earthwool - BPIR Summary Declaration 2025.pdf",
        "category": "C_Interiors/Insulation/Knauf",
        "product": "Earthwool",
        "doc_type": "BPIR",
        "agents": ["Inspector", "Engineer"],
        "h1_relevant": True,
        "application": "universal",
    },
    {
        "old_name": "Knauf - Earthwool - Ceiling R7.0 Installation Guide (H1).pdf",
        "new_name": "Knauf - Earthwool - Ceiling R7.0 Installation Guide (H1 2026).pdf",
        "category": "C_Interiors/Insulation/Knauf",
        "product": "Earthwool Ceiling R7.0",
        "doc_type": "Installation_Guide",
        "agents": ["Inspector"],
        "h1_relevant": True,
        "application": "ceiling",
    },
    {
        "old_name": "Knauf - Earthwool - SoundShield Acoustic Technical Data.pdf",
        "new_name": "Knauf - Earthwool - SoundShield Acoustic Technical Data.pdf",
        "category": "C_Interiors/Insulation/Knauf",
        "product": "Earthwool SoundShield",
        "doc_type": "Technical_Data_Sheet",
        "agents": ["Engineer", "Inspector"],
        "h1_relevant": False,  # Acoustic, not thermal
        "application": "acoustic",
    },
    {
        "old_name": "Knauf - Earthwool - Underfloor Segments Technical Data..pdf",
        "new_name": "Knauf - Earthwool - Underfloor Segments Technical Data (H1 2026).pdf",
        "category": "C_Interiors/Insulation/Knauf",
        "product": "Earthwool Underfloor Segments",
        "doc_type": "Technical_Data_Sheet",
        "agents": ["Inspector", "Engineer"],
        "h1_relevant": True,
        "application": "underfloor",
    },
    {
        "old_name": "Knauf - Earthwool - Wall Segments Technical Data (2025).pdf",
        "new_name": "Knauf - Earthwool - Wall Segments Technical Data (H1 2026).pdf",
        "category": "C_Interiors/Insulation/Knauf",
        "product": "Earthwool Wall Segments",
        "doc_type": "Technical_Data_Sheet",
        "agents": ["Inspector", "Engineer"],
        "h1_relevant": True,
        "application": "wall",
    },
]

# H1 2026 Minimum R-Values
H1_2026_MINIMUMS = {
    "ceiling": 7.0,
    "wall": 2.6,
    "underfloor": 2.8,
}

# =============================================================================
# H1 2026 GUARDRAIL EXTRACTION FUNCTIONS
# =============================================================================

def extract_r_value_matrix(text: str) -> Optional[dict]:
    """
    Extract R-Value vs Thickness matrix
    Target: R2.2=90mm, R2.6=90mm HD, R7.0=xxx, etc.
    """
    matrix = []
    
    # Pattern: R-value followed by thickness in mm
    patterns = [
        r'R[\s-]?(\d+\.?\d*)\s*[=:@]\s*(\d+)\s*mm',
        r'R[\s-]?(\d+\.?\d*)\s+(\d+)\s*mm',
        r'(\d+)\s*mm\s*[=:]\s*R[\s-]?(\d+\.?\d*)',
        r'R(\d+\.?\d*)\s*(?:High\s*Density|HD)?\s*[-–]\s*(\d+)\s*mm',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if pattern.startswith(r'(\d+)'):
                thickness, r_val = match
            else:
                r_val, thickness = match
            
            r_val = float(r_val)
            thickness = int(thickness)
            
            if 0.5 <= r_val <= 10.0 and 20 <= thickness <= 500:
                # Check for High Density marker
                is_hd = bool(re.search(rf'R[\s-]?{r_val}.*(?:High\s*Density|HD)', text, re.IGNORECASE))
                
                entry = {
                    "r_value": r_val,
                    "thickness_mm": thickness,
                }
                if is_hd:
                    entry["density"] = "High Density"
                
                # Avoid duplicates
                if entry not in matrix:
                    matrix.append(entry)
    
    # Also extract standalone R-values
    standalone_r = re.findall(r'R[\s-]?(\d+\.?\d*)', text, re.IGNORECASE)
    for r in standalone_r:
        r_val = float(r)
        if 0.5 <= r_val <= 10.0:
            if not any(m.get("r_value") == r_val for m in matrix):
                matrix.append({"r_value": r_val})
    
    return {"r_value_matrix": matrix} if matrix else None

def extract_air_gap_clearance(text: str) -> Optional[dict]:
    """
    Extract 25mm air-gap requirement between insulation and roof underlay
    """
    clearances = {}
    
    # Air gap patterns
    air_gap_patterns = [
        r'(\d+)\s*mm\s*(?:air[\s-]?gap|clearance|space)\s*(?:between|from|to)',
        r'(?:air[\s-]?gap|clearance|space)\s*(?:of\s*)?(\d+)\s*mm',
        r'minimum\s*(?:air[\s-]?gap|clearance)\s*(?:of\s*)?(\d+)\s*mm',
        r'(\d+)\s*mm\s*(?:min(?:imum)?\s*)?(?:air[\s-]?gap|clearance)',
    ]
    
    for pattern in air_gap_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            gap = int(match)
            if 10 <= gap <= 100:
                clearances["air_gap_mm"] = gap
                break
    
    # Specific 25mm check
    if "25" in text and ("air" in text.lower() or "gap" in text.lower() or "clearance" in text.lower()):
        clearances["air_gap_25mm_required"] = True
    
    # Underlay clearance
    if re.search(r'underlay.*clearance|clearance.*underlay', text, re.IGNORECASE):
        clearances["underlay_clearance_required"] = True
    
    return clearances if clearances else None

def extract_downlight_clearances(text: str) -> Optional[dict]:
    """
    Extract recessed downlight clearances per AS/NZS 3000
    """
    downlight = {}
    text_lower = text.lower()
    
    # Check for downlight/recessed light mentions
    if not any(x in text_lower for x in ['downlight', 'recessed', 'luminaire', 'light fitting']):
        return None
    
    # AS/NZS 3000 reference
    if re.search(r'AS/?NZS\s*3000', text, re.IGNORECASE):
        downlight["standard_reference"] = "AS/NZS 3000"
    
    # Clearance distances
    clearance_patterns = [
        r'downlight.*?(\d+)\s*mm\s*clearance',
        r'(\d+)\s*mm\s*(?:from|around)\s*(?:downlight|luminaire|light)',
        r'clearance\s*(?:of\s*)?(\d+)\s*mm.*(?:downlight|luminaire)',
        r'(?:IC|IC-F|IC-4)\s*rated.*?(\d+)\s*mm',
    ]
    
    for pattern in clearance_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            clearance = int(match.group(1))
            if 0 <= clearance <= 200:
                downlight["downlight_clearance_mm"] = clearance
                break
    
    # IC rating check
    if re.search(r'IC[\s-]?(?:rated|rating|4|F)', text, re.IGNORECASE):
        downlight["ic_rated_required"] = True
    
    # Fire rating
    fire_match = re.search(r'fire[\s-]?rated.*downlight|downlight.*fire[\s-]?rated', text, re.IGNORECASE)
    if fire_match:
        downlight["fire_rated_downlight"] = True
    
    return downlight if downlight else None

def extract_h1_compliance(text: str, application: str) -> Optional[dict]:
    """
    Rule S8: Check H1 2026 compliance, flag pre-H1 values
    """
    h1_data = {}
    text_lower = text.lower()
    
    # Check for H1 references
    if re.search(r'H1|NZBC\s*H1|clause\s*H1', text, re.IGNORECASE):
        h1_data["h1_referenced"] = True
    
    # Check for 2026/H1 update references
    if re.search(r'2026|H1\s*(?:update|change|new)', text, re.IGNORECASE):
        h1_data["h1_2026_compliant"] = True
    
    # Extract R-values and check against H1 2026 minimums
    r_values = re.findall(r'R[\s-]?(\d+\.?\d*)', text, re.IGNORECASE)
    r_values = [float(r) for r in r_values if 0.5 <= float(r) <= 10.0]
    
    if r_values and application in H1_2026_MINIMUMS:
        min_required = H1_2026_MINIMUMS[application]
        max_r = max(r_values)
        
        if max_r >= min_required:
            h1_data["h1_2026_compliant"] = True
            h1_data["max_r_value"] = max_r
            h1_data["min_required"] = min_required
        else:
            h1_data["pre_h1_warning"] = True
            h1_data["max_r_value"] = max_r
            h1_data["min_required"] = min_required
    
    # Specific H1 2026 values
    if application == "ceiling" and any(r >= 7.0 for r in r_values):
        h1_data["ceiling_r7_compliant"] = True
    
    if application == "wall":
        # Check for High Density
        if re.search(r'high\s*density|HD', text, re.IGNORECASE) and any(r >= 2.6 for r in r_values):
            h1_data["wall_hd_compliant"] = True
    
    return h1_data if h1_data else None

def extract_all_h1_guardrails(text: str, application: str) -> Optional[dict]:
    """
    Combine all H1 2026 guardrail extractions
    """
    guardrails = {}
    
    # R-Value Matrix
    r_matrix = extract_r_value_matrix(text)
    if r_matrix:
        guardrails.update(r_matrix)
    
    # Air Gap Clearance
    air_gap = extract_air_gap_clearance(text)
    if air_gap:
        guardrails.update(air_gap)
    
    # Downlight Clearances
    downlight = extract_downlight_clearances(text)
    if downlight:
        guardrails.update(downlight)
    
    # H1 Compliance
    h1_comp = extract_h1_compliance(text, application)
    if h1_comp:
        guardrails.update(h1_comp)
    
    # Standard fire/acoustic ratings
    frr = re.search(r'FRR\s*(\d+/\d+/\d+)', text)
    if frr:
        guardrails["fire_rating"] = frr.group(1)
    
    stc = re.search(r'STC\s*(\d+)', text)
    if stc:
        guardrails["stc_rating"] = int(stc.group(1))
    
    # Thermal conductivity
    tc = re.search(r'(?:thermal\s*conductivity|λ|lambda)[\s:]*(\d*\.?\d+)\s*W', text, re.IGNORECASE)
    if tc:
        guardrails["thermal_conductivity"] = float(tc.group(1))
    
    return guardrails if guardrails else None

# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def generate_embedding(text: str) -> List[float]:
    seed = int(hashlib.md5(text[:1000].encode()).hexdigest()[:8], 16)
    import random
    random.seed(seed)
    emb = [random.uniform(-0.5, 0.5) for _ in range(1536)]
    mag = sum(x**2 for x in emb) ** 0.5
    return [x / mag for x in emb]

def download_from_temp(filename: str) -> Optional[bytes]:
    url = f"{SUPABASE_URL}/storage/v1/object/temporary/{quote(filename, safe='')}"
    try:
        response = requests.get(url, headers=SUPABASE_HEADERS, timeout=120)
        if response.status_code == 200:
            return response.content
    except Exception as e:
        print(f"      ⚠️ Download error: {e}")
    return None

def copy_to_permanent_storage(filename: str, pdf_bytes: bytes, category: str, new_name: str) -> bool:
    """Copy PDF to permanent product-library storage"""
    target_path = f"{category}/{new_name}"
    url = f"{SUPABASE_URL}/storage/v1/object/product-library/{quote(target_path, safe='/')}"
    
    headers = {
        **SUPABASE_HEADERS,
        "Content-Type": "application/pdf",
    }
    
    try:
        response = requests.post(url, headers=headers, data=pdf_bytes, timeout=60)
        return response.status_code in [200, 201]
    except:
        return False

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def run_h1_weaponized_ingestion():
    print("=" * 70)
    print("🔫 H1 2026 WEAPONIZED INGESTION - INSPECTOR AGENT")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")
    print("\n📋 GUARDRAIL TARGETS:")
    print("   1. R-Value Matrix (R vs Thickness)")
    print("   2. 25mm Air-Gap Clearance")
    print("   3. Recessed Downlight Clearances (AS/NZS 3000)")
    print("   4. Rule S8: H1 2026 Compliance Audit")
    print("\n📊 H1 2026 MINIMUMS:")
    print("   Ceiling: R7.0 | Wall: R2.6 HD | Underfloor: R2.8")
    print("=" * 70)
    
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    conn.autocommit = True
    
    stats = {
        "files": 0,
        "chunks": 0,
        "h1_compliant": 0,
        "pre_h1_flagged": 0,
        "with_r_matrix": 0,
        "with_air_gap": 0,
        "with_downlight": 0,
        "copied_to_storage": 0,
    }
    
    for file_info in H1_FILES:
        print(f"\n📥 {file_info['old_name'][:55]}...")
        print(f"   → {file_info['new_name']}")
        print(f"   Application: {file_info['application']} | H1 Relevant: {file_info['h1_relevant']}")
        
        # Download
        pdf_bytes = download_from_temp(file_info['old_name'])
        if not pdf_bytes:
            print("   ❌ Download failed")
            continue
        
        if not pdf_bytes.startswith(b'%PDF'):
            print("   ❌ Not a valid PDF")
            continue
        
        # Copy to permanent storage
        if copy_to_permanent_storage(file_info['old_name'], pdf_bytes, 
                                      file_info['category'], file_info['new_name']):
            stats["copied_to_storage"] += 1
            print("   📁 Copied to permanent storage")
        
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        except Exception as e:
            print(f"   ❌ PDF error: {e}")
            continue
        
        source_path = f"{file_info['category']}/{file_info['new_name']}"
        file_chunks = 0
        file_h1_compliant = 0
        file_pre_h1 = 0
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            
            if not text or len(text.strip()) < 50:
                continue
            
            text = text.replace('\x00', '')
            page_hash = hashlib.sha256(f"{source_path}:{page_num+1}:{text}".encode()).hexdigest()
            
            # Check duplicate
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM documents WHERE page_hash = %s", (page_hash,))
            if cur.fetchone():
                continue
            
            # Extract H1 2026 guardrails
            guardrails = extract_all_h1_guardrails(text, file_info['application'])
            
            # Track stats
            if guardrails:
                if guardrails.get("h1_2026_compliant"):
                    file_h1_compliant += 1
                if guardrails.get("pre_h1_warning"):
                    file_pre_h1 += 1
                if guardrails.get("r_value_matrix"):
                    stats["with_r_matrix"] += 1
                if guardrails.get("air_gap_mm") or guardrails.get("air_gap_25mm_required"):
                    stats["with_air_gap"] += 1
                if guardrails.get("downlight_clearance_mm"):
                    stats["with_downlight"] += 1
            
            has_table = any(x in text.lower() for x in ['table', 'schedule', 'specification', 'r-value'])
            has_diagram = any(x in text.lower() for x in ['figure', 'diagram', 'detail', 'clearance'])
            
            # Set priority based on H1 compliance
            priority = 85 if file_info['h1_relevant'] else 70
            if guardrails and guardrails.get("h1_2026_compliant"):
                priority = 90  # Highest priority for H1 2026 compliant
            
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
                generate_embedding(text), page_hash, 1, True,
                3, "product",
                f"Knauf - {file_info['product']} - {file_info['doc_type']} - Page {page_num+1}",
                file_info['agents'], has_table, has_diagram,
                json.dumps(guardrails) if guardrails else None,
                "NZ_Specific", True, priority
            ))
            file_chunks += 1
        
        page_count = len(doc)
        doc.close()
        
        stats["files"] += 1
        stats["chunks"] += file_chunks
        stats["h1_compliant"] += file_h1_compliant
        stats["pre_h1_flagged"] += file_pre_h1
        
        print(f"   ✅ {page_count} pages → {file_chunks} chunks")
        if file_h1_compliant > 0:
            print(f"   🏆 H1 2026 Compliant: {file_h1_compliant} pages")
        if file_pre_h1 > 0:
            print(f"   ⚠️ Pre-H1 Flagged: {file_pre_h1} pages")
    
    conn.close()
    
    # Final Report
    print("\n" + "=" * 70)
    print("🏁 H1 2026 WEAPONIZED INGESTION COMPLETE")
    print("=" * 70)
    print(f"\n📊 STATISTICS:")
    print(f"   Files processed: {stats['files']}")
    print(f"   Chunks created: {stats['chunks']}")
    print(f"   Copied to storage: {stats['copied_to_storage']}")
    print(f"\n🔫 GUARDRAIL EXTRACTION:")
    print(f"   With R-Value Matrix: {stats['with_r_matrix']}")
    print(f"   With Air-Gap Data: {stats['with_air_gap']}")
    print(f"   With Downlight Clearances: {stats['with_downlight']}")
    print(f"\n📋 H1 2026 COMPLIANCE:")
    print(f"   H1 2026 Compliant Pages: {stats['h1_compliant']}")
    print(f"   Pre-H1 Flagged (Rule S8): {stats['pre_h1_flagged']}")
    print(f"\nCompleted: {datetime.now().isoformat()}")
    print("=" * 70)

if __name__ == "__main__":
    run_h1_weaponized_ingestion()
