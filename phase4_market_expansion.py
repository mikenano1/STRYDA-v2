#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
    PHASE 4: MARKET EXPANSION - ROOFING & WINDOWS INGESTION
    
    PROTOCOL REQUIREMENTS:
    1. Ingest all PDFs from 02_Roofing/ and 03_Windows/ directories
    2. AUDIT ON ENTRY: Add every product to Compliance_Master_Register.csv
    3. FLAG MISSING_DOCS: Products without BPIR/CodeMark flagged immediately
    4. ANCHOR TAGGING:
       - Roofing: Minimum_Pitch, Fastener_Pattern, Profile_Height
       - Windows: Thermal_Bridge_Rating, Glazing_R_Value, Air_Leakage_Class
═══════════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import json
import re
import csv
import hashlib
import psycopg2
import psycopg2.extras
from datetime import datetime
from pathlib import Path
import fitz  # PyMuPDF
import requests
from typing import Dict, List, Optional, Tuple

# Load environment
env_file = Path('/app/backend-minimal/.env')
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            key, val = line.split('=', 1)
            os.environ[key.strip()] = val.strip()

from supabase import create_client
import openai

# Configuration
DATABASE_URL = os.getenv('DATABASE_URL')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
OPENAI_KEY = os.getenv('OPENAI_API_KEY')
BUCKET = "product-library"
REGISTER_PATH = "/app/protocols/Compliance_Master_Register.csv"

# Initialize clients
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = openai.OpenAI(api_key=OPENAI_KEY)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTOR-SPECIFIC ANCHOR PATTERNS
# ═══════════════════════════════════════════════════════════════════════════════

ROOFING_ANCHORS = {
    'Minimum_Pitch': [
        r'minimum\s+pitch[:\s]+(\d+(?:\.\d+)?)\s*(?:degrees?|°)',
        r'pitch[:\s]+(?:min(?:imum)?\.?[:\s]+)?(\d+(?:\.\d+)?)\s*(?:degrees?|°)',
        r'(\d+(?:\.\d+)?)\s*(?:degrees?|°)\s+(?:min(?:imum)?\s+)?pitch',
        r'roof\s+pitch[:\s]+(\d+(?:\.\d+)?)',
    ],
    'Fastener_Pattern': [
        r'fastener\s+(?:pattern|spacing)[:\s]+([^.]+)',
        r'screw\s+(?:pattern|spacing|centres?)[:\s]+(\d+(?:mm)?(?:\s*[x×]\s*\d+(?:mm)?)?)',
        r'fix(?:ing)?s?\s+at\s+(\d+(?:mm)?\s+centres?)',
        r'nail\s+pattern[:\s]+([^.]+)',
    ],
    'Profile_Height': [
        r'profile\s+height[:\s]+(\d+(?:\.\d+)?)\s*(?:mm)?',
        r'rib\s+height[:\s]+(\d+(?:\.\d+)?)\s*(?:mm)?',
        r'(\d+)\s*mm\s+(?:profile|rib)\s+height',
        r'crest\s+height[:\s]+(\d+(?:\.\d+)?)',
    ],
}

WINDOWS_ANCHORS = {
    'Thermal_Bridge_Rating': [
        r'thermal\s+break[:\s]+([^.]+)',
        r'thermally\s+broken[:\s]+([^.]+)',
        r'thermal\s+bridge[:\s]+rating[:\s]+([^.]+)',
        r'Tb[:\s]+(\d+(?:\.\d+)?)',
    ],
    'Glazing_R_Value': [
        r'glazing\s+r[\s-]?value[:\s]+R?(\d+(?:\.\d+)?)',
        r'R[\s-]?value[:\s]+(\d+(?:\.\d+)?)',
        r'insulation\s+value[:\s]+R?(\d+(?:\.\d+)?)',
        r'Ug[\s-]?value[:\s]+(\d+(?:\.\d+)?)',
    ],
    'Air_Leakage_Class': [
        r'air\s+(?:leakage|infiltration)\s+class[:\s]+([A-Z0-9]+)',
        r'air\s+tightness[:\s]+([^.]+)',
        r'AL[:\s]+(\d+(?:\.\d+)?)',
        r'permeability[:\s]+([^.]+)',
    ],
}

# ═══════════════════════════════════════════════════════════════════════════════
# COMPLIANCE REGISTER MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def load_existing_register() -> Dict[str, Dict]:
    """Load existing compliance register entries"""
    register = {}
    if os.path.exists(REGISTER_PATH):
        with open(REGISTER_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = f"{row.get('brand', '')}-{row.get('product', '')}"
                register[key] = row
    return register

def detect_compliance_docs(text: str, filename: str) -> Dict:
    """Detect BPIR, CodeMark, and BRANZ references"""
    result = {
        'has_bpir': False,
        'has_codemark': False,
        'has_branz': False,
        'codemark_id': '',
        'branz_number': '',
        'bpir_status': 'UNDECLARED',
    }
    
    text_lower = text.lower()
    filename_lower = filename.lower()
    
    # BPIR Detection
    if 'bpir' in text_lower or 'building product information' in text_lower:
        result['has_bpir'] = True
        result['bpir_status'] = 'DECLARED'
    
    # CodeMark Detection
    codemark_patterns = [
        r'codemark[:\s]+(?:certificate\s+)?(?:no\.?\s+)?([A-Z]{2}\d{5})',
        r'CM\s*(\d{5,6})',
        r'NZ\s*(\d{5})',
    ]
    for pattern in codemark_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result['has_codemark'] = True
            result['codemark_id'] = match.group(0)
            break
    
    # BRANZ Detection
    branz_patterns = [
        r'branz\s+appraisal[:\s]+(?:no\.?\s+)?(\d+)',
        r'appraisal\s+(?:no\.?\s+)?(\d+)',
        r'branz\s+(\d{3,4})',
    ]
    for pattern in branz_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result['has_branz'] = True
            result['branz_number'] = match.group(1)
            break
    
    return result

def determine_compliance_status(compliance_info: Dict) -> str:
    """Determine overall compliance status"""
    if compliance_info['has_codemark'] or compliance_info['has_branz']:
        return 'CONDITIONAL'  # Has certification but may have scope limitations
    elif compliance_info['has_bpir']:
        return 'CONDITIONAL'
    else:
        return 'MISSING'  # ⚠️ MISSING_DOCS

def add_to_register(brand: str, product: str, doc_type: str, 
                    compliance_info: Dict, scope_limitation: str = '') -> Dict:
    """Add or update entry in compliance register"""
    status = determine_compliance_status(compliance_info)
    
    entry = {
        'brand': brand,
        'product': product,
        'doc_type': doc_type,
        'codemark_id': compliance_info.get('codemark_id', ''),
        'branz_number': compliance_info.get('branz_number', ''),
        'expiry_date': '',
        'is_expired': 'NO',
        'status': status,
        'bpir_status': compliance_info.get('bpir_status', 'UNDECLARED'),
        'scope_limitations': scope_limitation[:100] if scope_limitation else '',
    }
    
    return entry

# ═══════════════════════════════════════════════════════════════════════════════
# ANCHOR EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════════

def extract_sector_anchors(text: str, sector: str) -> Dict[str, str]:
    """Extract sector-specific anchor values from text"""
    anchors = {}
    
    if sector == 'roofing':
        patterns = ROOFING_ANCHORS
    elif sector == 'windows':
        patterns = WINDOWS_ANCHORS
    else:
        return anchors
    
    for anchor_name, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                anchors[anchor_name] = match.group(1).strip()[:100]
                break
    
    return anchors

# ═══════════════════════════════════════════════════════════════════════════════
# PDF PROCESSING
# ═══════════════════════════════════════════════════════════════════════════════

def download_pdf(storage_path: str) -> Optional[bytes]:
    """Download PDF from Supabase storage"""
    try:
        # Get signed URL
        signed = supabase.storage.from_(BUCKET).create_signed_url(storage_path, 300)
        url = signed.get('signedURL')
        if not url:
            return None
        
        response = requests.get(url, timeout=60)
        if response.status_code == 200:
            return response.content
        return None
    except Exception as e:
        print(f"      ❌ Download error: {e}")
        return None

def extract_pdf_content(pdf_bytes: bytes) -> Tuple[str, int]:
    """Extract text content from PDF"""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        full_text = ""
        page_count = len(doc)
        
        for page in doc:
            full_text += page.get_text() + "\n"
        
        doc.close()
        return full_text, page_count
    except Exception as e:
        print(f"      ❌ PDF extraction error: {e}")
        return "", 0

def chunk_text(text: str, chunk_size: int = 1500, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks"""
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to break at sentence boundary
        if end < len(text):
            last_period = chunk.rfind('.')
            if last_period > chunk_size // 2:
                end = start + last_period + 1
                chunk = text[start:end]
        
        if chunk.strip():
            chunks.append(chunk.strip())
        
        start = end - overlap
        if start < 0:
            start = 0
    
    return chunks

def generate_embedding(text: str) -> List[float]:
    """Generate embedding using OpenAI"""
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text[:8000],  # Limit input size
            dimensions=1536
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"      ⚠️ Embedding error: {e}")
        return None

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN INGESTION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def ingest_file(file_info: Dict, sector: str, register_entries: List[Dict]) -> int:
    """Ingest a single PDF file with fresh connection per file"""
    storage_path = file_info['path']
    filename = file_info['name']
    
    # Extract brand from path
    path_parts = storage_path.split('/')
    if len(path_parts) >= 2:
        brand = path_parts[1].replace('_', ' ')
    else:
        brand = 'Unknown'
    
    # Download PDF
    pdf_bytes = download_pdf(storage_path)
    if not pdf_bytes:
        return 0
    
    # Extract content
    full_text, page_count = extract_pdf_content(pdf_bytes)
    if not full_text or page_count == 0:
        return 0
    
    # Generate content hash for deduplication
    content_hash = hashlib.sha256(full_text.encode()).hexdigest()[:16]
    
    # Fresh connection per file to avoid transaction issues
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    conn.autocommit = False
    cur = conn.cursor()
    
    try:
        # Check for duplicates
        cur.execute("SELECT id FROM documents WHERE page_hash = %s LIMIT 1", (content_hash,))
        if cur.fetchone():
            print(f"      ⏭️ Skipping duplicate: {filename[:40]}...")
            conn.close()
            return 0
    
    # Detect compliance documentation
    compliance_info = detect_compliance_docs(full_text, filename)
    
    # Determine document type
    doc_type = 'Unknown'
    filename_lower = filename.lower()
    if 'technical' in filename_lower or 'specification' in filename_lower:
        doc_type = 'Technical_Specification'
    elif 'installation' in filename_lower or 'guide' in filename_lower:
        doc_type = 'Installation_Guide'
    elif 'branz' in filename_lower or 'appraisal' in filename_lower:
        doc_type = 'BRANZ_Appraisal'
    elif 'codemark' in filename_lower:
        doc_type = 'CodeMark_Certificate'
    elif 'warranty' in filename_lower:
        doc_type = 'Warranty'
    elif 'data' in filename_lower and 'sheet' in filename_lower:
        doc_type = 'Technical_Data_Sheet'
    elif 'bpir' in filename_lower or 'bpis' in filename_lower:
        doc_type = 'BPIR_Statement'
    else:
        doc_type = 'Product_Document'
    
    # Extract sector-specific anchors
    anchors = extract_sector_anchors(full_text, sector)
    
    # Extract scope limitations (first paragraph with "limitation" or "scope")
    scope_match = re.search(r'(?:limitation|scope|restriction)[:\s]+([^.]+\.)', full_text, re.IGNORECASE)
    scope_limitation = scope_match.group(1) if scope_match else ''
    
    # Add to compliance register
    product_name = filename.replace('.pdf', '').replace('_', ' ')[:100]
    register_entry = add_to_register(brand, product_name, doc_type, compliance_info, scope_limitation)
    register_entries.append(register_entry)
    
    # Flag MISSING_DOCS
    if register_entry['status'] == 'MISSING':
        print(f"      ⚠️ MISSING_DOCS: {brand} - {product_name[:30]}")
    
    # Chunk and ingest
    chunks = chunk_text(full_text)
    chunks_inserted = 0
    
    for i, chunk in enumerate(chunks):
        # Generate embedding
        embedding = generate_embedding(chunk)
        if not embedding:
            continue
        
        # Calculate page number estimate
        page_estimate = min(i * page_count // len(chunks) + 1, page_count)
        
        # Build metadata
        metadata = {
            'brand': brand,
            'sector': sector,
            'doc_type': doc_type,
            'page_count': page_count,
            'compliance_status': register_entry['status'],
            'anchors': anchors,
        }
        
        if compliance_info['has_codemark']:
            metadata['codemark_id'] = compliance_info['codemark_id']
        if compliance_info['has_branz']:
            metadata['branz_number'] = compliance_info['branz_number']
        
        # Insert into database
        try:
            cur.execute("""
                INSERT INTO documents (
                    content, source, page, embedding, page_hash,
                    hierarchy_level, agent_owner, trade, priority, is_active,
                    source_path, unit_range, doc_type
                ) VALUES (
                    %s, %s, %s, %s::vector, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s
                )
            """, (
                chunk,
                f"{brand} - {filename.replace('.pdf', '')}",
                page_estimate,
                embedding,
                f"{content_hash}_{i}",
                'Product',  # hierarchy_level
                sector,     # agent_owner
                sector,     # trade
                80,         # priority
                True,       # is_active
                storage_path,
                json.dumps(metadata),
                doc_type
            ))
            chunks_inserted += 1
        except Exception as e:
            print(f"      ❌ Insert error: {e}")
            conn.rollback()
            continue
    
        if chunks_inserted > 0:
            conn.commit()
        
        cur.close()
        conn.close()
        return chunks_inserted
        
    except Exception as e:
        print(f"      ❌ Processing error: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return 0

def main():
    """Main ingestion pipeline"""
    print("=" * 80)
    print("PHASE 4: MARKET EXPANSION - ROOFING & WINDOWS INGESTION")
    print("=" * 80)
    print(f"Started: {datetime.now().isoformat()}")
    
    # Load file lists
    with open('/app/phase4_roofing_files.json', 'r') as f:
        roofing_files = json.load(f)
    with open('/app/phase4_windows_files.json', 'r') as f:
        windows_files = json.load(f)
    
    print(f"\n📦 Files to process:")
    print(f"   🏠 Roofing: {len(roofing_files)} PDFs")
    print(f"   🪟 Windows: {len(windows_files)} PDFs")
    
    # Load existing register
    existing_register = load_existing_register()
    new_register_entries = []
    
    # Stats tracking
    stats = {
        'roofing_files': 0,
        'roofing_chunks': 0,
        'windows_files': 0,
        'windows_chunks': 0,
        'missing_docs': 0,
        'errors': 0,
    }
    
    # Process Roofing
    print(f"\n{'=' * 80}")
    print("🏠 PROCESSING ROOFING SECTOR")
    print("=" * 80)
    
    for i, file_info in enumerate(roofing_files, 1):
        filename = file_info['name']
        print(f"\n[{i}/{len(roofing_files)}] {filename[:50]}...")
        
        try:
            chunks = ingest_file(file_info, 'roofing', new_register_entries)
            if chunks > 0:
                stats['roofing_files'] += 1
                stats['roofing_chunks'] += chunks
                print(f"      ✅ Ingested {chunks} chunks")
        except Exception as e:
            stats['errors'] += 1
            print(f"      ❌ Error: {e}")
        
        # Progress update every 50 files
        if i % 50 == 0:
            print(f"\n   📊 Progress: {i}/{len(roofing_files)} files, {stats['roofing_chunks']:,} chunks")
    
    # Process Windows
    print(f"\n{'=' * 80}")
    print("🪟 PROCESSING WINDOWS/JOINERY SECTOR")
    print("=" * 80)
    
    for i, file_info in enumerate(windows_files, 1):
        filename = file_info['name']
        print(f"\n[{i}/{len(windows_files)}] {filename[:50]}...")
        
        try:
            chunks = ingest_file(file_info, 'windows', new_register_entries)
            if chunks > 0:
                stats['windows_files'] += 1
                stats['windows_chunks'] += chunks
                print(f"      ✅ Ingested {chunks} chunks")
        except Exception as e:
            stats['errors'] += 1
            print(f"      ❌ Error: {e}")
    
    # Count MISSING_DOCS
    stats['missing_docs'] = sum(1 for e in new_register_entries if e['status'] == 'MISSING')
    
    # Update Compliance Register
    print(f"\n{'=' * 80}")
    print("📋 UPDATING COMPLIANCE_MASTER_REGISTER.CSV")
    print("=" * 80)
    
    # Merge with existing register
    all_entries = list(existing_register.values())
    for entry in new_register_entries:
        key = f"{entry['brand']}-{entry['product']}"
        if key not in existing_register:
            all_entries.append(entry)
    
    # Write updated register
    fieldnames = ['brand', 'product', 'doc_type', 'codemark_id', 'branz_number', 
                  'expiry_date', 'is_expired', 'status', 'bpir_status', 'scope_limitations']
    
    with open(REGISTER_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_entries)
    
    print(f"   ✅ Register updated: {len(all_entries)} total entries")
    print(f"   ⚠️ MISSING_DOCS flagged: {stats['missing_docs']} products")
    
    # Final stats
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM documents")
    total_chunks = cur.fetchone()[0]
    conn.close()
    
    print(f"\n{'=' * 80}")
    print("📊 PHASE 4 INGESTION SUMMARY")
    print("=" * 80)
    print(f"   🏠 Roofing: {stats['roofing_files']} files → {stats['roofing_chunks']:,} chunks")
    print(f"   🪟 Windows: {stats['windows_files']} files → {stats['windows_chunks']:,} chunks")
    print(f"   📄 Total new chunks: {stats['roofing_chunks'] + stats['windows_chunks']:,}")
    print(f"   📦 Total DB chunks: {total_chunks:,}")
    print(f"   ⚠️ MISSING_DOCS: {stats['missing_docs']}")
    print(f"   ❌ Errors: {stats['errors']}")
    print(f"\nCompleted: {datetime.now().isoformat()}")
    print("=" * 80)

if __name__ == "__main__":
    main()
