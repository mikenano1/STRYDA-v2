#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
    TOTAL MARKET LOCKDOWN - V3 AUDITOR PROTOCOL
    
    MISSION: Process EVERY file in the product library
    - Ingest all unprocessed PDFs
    - Run V3 Register-First Audit on ALL products
    - Update Compliance_Master_Register.csv to 100% coverage
    - Flag ALL MISSING_DOCS immediately
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
# SECTOR-SPECIFIC ANCHOR PATTERNS (EXPANDED)
# ═══════════════════════════════════════════════════════════════════════════════

SECTOR_ANCHORS = {
    'roofing': {
        'Minimum_Pitch': [r'minimum\s+pitch[:\s]+(\d+(?:\.\d+)?)', r'pitch[:\s]+(\d+)'],
        'Fastener_Pattern': [r'fastener\s+(?:pattern|spacing)[:\s]+([^.]+)', r'screw\s+centres?[:\s]+(\d+)'],
        'Profile_Height': [r'profile\s+height[:\s]+(\d+)', r'rib\s+height[:\s]+(\d+)'],
    },
    'windows': {
        'Thermal_Bridge_Rating': [r'thermal\s+break[:\s]+([^.]+)', r'thermally\s+broken'],
        'Glazing_R_Value': [r'glazing\s+r[\s-]?value[:\s]+R?(\d+(?:\.\d+)?)', r'R[\s-]?value[:\s]+(\d+)'],
        'Air_Leakage_Class': [r'air\s+(?:leakage|infiltration)\s+class[:\s]+([A-Z0-9]+)'],
    },
    'fasteners': {
        'Load_Capacity': [r'(?:load|capacity)[:\s]+(\d+(?:\.\d+)?)\s*(?:kN|kg)', r'shear[:\s]+(\d+)'],
        'Corrosion_Class': [r'(?:corrosion|durability)\s+class[:\s]+([A-Z0-9]+)', r'z(?:inc)?[:\s]+(\d+)g'],
        'Material_Grade': [r'(?:steel|grade)[:\s]+([A-Z0-9\.]+)', r'stainless\s+(\d{3})'],
    },
    'membranes': {
        'Vapor_Permeance': [r'(?:vapor|vapour)\s+permeance[:\s]+(\d+)', r'Sd[\s-]?value[:\s]+(\d+)'],
        'Water_Column': [r'water\s+column[:\s]+(\d+)', r'hydrostatic\s+head[:\s]+(\d+)'],
        'UV_Exposure': [r'uv\s+exposure[:\s]+(\d+)\s*(?:days?|months?)', r'exposed[:\s]+(\d+)'],
    },
    'timber': {
        'Timber_Grade': [r'(?:timber|structural)\s+grade[:\s]+([A-Z0-9]+)', r'SG(\d+)'],
        'H_Class': [r'H[\s-]?class[:\s]+H?(\d+(?:\.\d)?)', r'hazard\s+class[:\s]+H?(\d+)'],
        'Span_Table_Ref': [r'span\s+table[:\s]+([A-Z0-9\-]+)', r'NZS\s+3604'],
    },
    'insulation': {
        'R_Value': [r'R[\s-]?value[:\s]+R?(\d+(?:\.\d+)?)', r'thermal\s+resistance[:\s]+(\d+)'],
        'Fire_Rating': [r'(?:fire|FRR)[:\s]+(\d+/\d+/\d+)', r'group\s+(\d+[A-Z]?)'],
        'Density': [r'density[:\s]+(\d+)\s*kg', r'(\d+)\s*kg/m'],
    },
    'cladding': {
        'Wind_Zone': [r'wind\s+zone[:\s]+([A-Z]+)', r'(?:very\s+high|high|medium|low)\s+wind'],
        'Cavity_Depth': [r'cavity[:\s]+(\d+)\s*mm', r'(\d+)\s*mm\s+cavity'],
        'E2_Compliance': [r'E2[:\s/]+([^.]+)', r'acceptable\s+solution'],
    },
    'compliance': {
        'NZBC_Clause': [r'(?:clause|NZBC)[:\s]+([A-Z]\d+)', r'building\s+code[:\s]+([^.]+)'],
        'Standard_Ref': [r'(?:NZS|AS/NZS)[:\s]+(\d+)', r'standard[:\s]+([^.]+)'],
        'Verification_Method': [r'verification\s+method[:\s]+([^.]+)', r'VM(\d+)'],
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# SECTOR DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

def detect_sector(storage_path: str, content: str) -> str:
    """Detect the sector based on path and content"""
    path_lower = storage_path.lower()
    content_lower = content.lower()[:3000]
    
    # Path-based detection
    if any(x in path_lower for x in ['roofing', 'roof', 'corrugate', 'longrun']):
        return 'roofing'
    if any(x in path_lower for x in ['window', 'joinery', 'door', 'apl', 'altus']):
        return 'windows'
    if any(x in path_lower for x in ['fastener', 'screw', 'nail', 'bolt', 'mitek', 'pryda']):
        return 'fasteners'
    if any(x in path_lower for x in ['membrane', 'wrap', 'clima', 'nuralite', 'waterproof']):
        return 'membranes'
    if any(x in path_lower for x in ['timber', 'wood', 'xlam', 'prolam', 'clt', 'glulam']):
        return 'timber'
    if any(x in path_lower for x in ['insulation', 'batts', 'kooltherm', 'pink', 'knauf']):
        return 'insulation'
    if any(x in path_lower for x in ['cladding', 'wall', 'facade', 'weatherboard']):
        return 'cladding'
    if any(x in path_lower for x in ['compliance', 'nzbc', 'standard', 'code']):
        return 'compliance'
    
    # Content-based fallback
    if 'roofing' in content_lower or 'pitch' in content_lower:
        return 'roofing'
    if 'window' in content_lower or 'glazing' in content_lower:
        return 'windows'
    if 'fastener' in content_lower or 'screw' in content_lower:
        return 'fasteners'
    
    return 'general'

# ═══════════════════════════════════════════════════════════════════════════════
# COMPLIANCE DETECTION & AUDITING
# ═══════════════════════════════════════════════════════════════════════════════

def detect_compliance_docs(text: str, filename: str) -> Dict:
    """Comprehensive compliance detection"""
    result = {
        'has_bpir': False,
        'has_codemark': False,
        'has_branz': False,
        'has_epd': False,
        'codemark_id': '',
        'branz_number': '',
        'epd_number': '',
        'bpir_status': 'UNDECLARED',
        'expiry_date': '',
    }
    
    text_lower = text.lower()
    filename_lower = filename.lower()
    
    # BPIR Detection
    if 'bpir' in text_lower or 'building product information' in text_lower:
        result['has_bpir'] = True
        result['bpir_status'] = 'DECLARED'
    
    # CodeMark Detection
    codemark_patterns = [
        r'codemark[:\s]+(?:certificate\s+)?(?:no\.?\s+)?([A-Z]{2}\d{4,6})',
        r'CM[\s\-]?(\d{5,6})',
        r'certificate\s+(?:no\.?\s+)?([A-Z]{2}\d{4,6})',
    ]
    for pattern in codemark_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result['has_codemark'] = True
            result['codemark_id'] = match.group(0)[:30]
            break
    
    # BRANZ Detection
    branz_patterns = [
        r'branz\s+appraisal[:\s]+(?:no\.?\s+)?(\d+)',
        r'appraisal\s+(?:no\.?\s+)?(\d{3,4})',
        r'branz[:\s]+(\d{3,4})',
    ]
    for pattern in branz_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result['has_branz'] = True
            result['branz_number'] = match.group(1)
            break
    
    # EPD Detection (Environmental Product Declaration)
    epd_patterns = [
        r'epd[:\s]+(?:no\.?\s+)?([A-Z0-9\-]+)',
        r'environmental\s+product\s+declaration',
    ]
    for pattern in epd_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result['has_epd'] = True
            if match.groups():
                result['epd_number'] = match.group(1)[:20]
            break
    
    # Expiry Date Detection
    expiry_patterns = [
        r'expir(?:y|es?)[:\s]+(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
        r'valid\s+(?:until|to)[:\s]+(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
        r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})\s+expir',
    ]
    for pattern in expiry_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result['expiry_date'] = match.group(1)
            break
    
    return result

def determine_compliance_status(compliance_info: Dict) -> str:
    """Determine overall compliance status"""
    if compliance_info.get('expiry_date'):
        # Check if expired (simple check)
        return 'CONDITIONAL'
    if compliance_info['has_codemark'] or compliance_info['has_branz']:
        return 'CERTIFIED'
    elif compliance_info['has_bpir']:
        return 'BPIR_ONLY'
    elif compliance_info['has_epd']:
        return 'EPD_ONLY'
    else:
        return 'MISSING'  # ⚠️ MISSING_DOCS

# ═══════════════════════════════════════════════════════════════════════════════
# ANCHOR EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════════

def extract_sector_anchors(text: str, sector: str) -> Dict[str, str]:
    """Extract sector-specific anchor values"""
    anchors = {}
    patterns = SECTOR_ANCHORS.get(sector, {})
    
    for anchor_name, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1) if match.groups() else match.group(0)
                anchors[anchor_name] = str(value).strip()[:100]
                break
    
    return anchors

# ═══════════════════════════════════════════════════════════════════════════════
# PDF PROCESSING
# ═══════════════════════════════════════════════════════════════════════════════

def download_pdf(storage_path: str) -> Optional[bytes]:
    """Download PDF from Supabase storage"""
    try:
        signed = supabase.storage.from_(BUCKET).create_signed_url(storage_path, 300)
        url = signed.get('signedURL')
        if not url:
            return None
        response = requests.get(url, timeout=60)
        if response.status_code == 200:
            return response.content
        return None
    except Exception as e:
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
    except:
        return "", 0

def chunk_text(text: str, chunk_size: int = 1500, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
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

def generate_embedding(text: str) -> Optional[List[float]]:
    """Generate embedding using OpenAI"""
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text[:8000],
            dimensions=1536
        )
        return response.data[0].embedding
    except:
        return None

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN INGESTION & AUDIT ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def process_file(file_info: Dict, register_entries: List[Dict], processed_hashes: set) -> Tuple[int, Dict]:
    """Process a single PDF file - ingest AND audit"""
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
        return 0, None
    
    # Extract content
    full_text, page_count = extract_pdf_content(pdf_bytes)
    if not full_text or page_count == 0:
        return 0, None
    
    # Generate content hash
    content_hash = hashlib.sha256(full_text.encode()).hexdigest()[:16]
    
    # Check for duplicates in this run
    if content_hash in processed_hashes:
        return 0, None
    processed_hashes.add(content_hash)
    
    # Detect sector
    sector = detect_sector(storage_path, full_text)
    
    # Detect compliance
    compliance_info = detect_compliance_docs(full_text, filename)
    compliance_status = determine_compliance_status(compliance_info)
    
    # Determine doc type
    doc_type = 'Product_Document'
    filename_lower = filename.lower()
    if 'technical' in filename_lower or 'specification' in filename_lower:
        doc_type = 'Technical_Specification'
    elif 'installation' in filename_lower or 'guide' in filename_lower:
        doc_type = 'Installation_Guide'
    elif 'branz' in filename_lower or 'appraisal' in filename_lower:
        doc_type = 'BRANZ_Appraisal'
    elif 'codemark' in filename_lower:
        doc_type = 'CodeMark_Certificate'
    elif 'bpir' in filename_lower:
        doc_type = 'BPIR_Statement'
    elif 'epd' in filename_lower:
        doc_type = 'EPD'
    elif 'detail' in filename_lower or 'drawing' in filename_lower:
        doc_type = 'Technical_Detail'
    
    # Extract anchors
    anchors = extract_sector_anchors(full_text, sector)
    
    # Create register entry (for CSV)
    product_name = filename.replace('.pdf', '').replace('_', ' ')[:100]
    register_entry = {
        'brand': brand,
        'product': product_name,
        'sector': sector,
        'doc_type': doc_type,
        'codemark_id': compliance_info.get('codemark_id', ''),
        'branz_number': compliance_info.get('branz_number', ''),
        'epd_number': compliance_info.get('epd_number', ''),
        'expiry_date': compliance_info.get('expiry_date', ''),
        'status': compliance_status,
        'bpir_status': compliance_info.get('bpir_status', 'UNDECLARED'),
        'storage_path': storage_path,
        'anchors': json.dumps(anchors) if anchors else '',
    }
    register_entries.append(register_entry)
    
    # Database connection
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    conn.autocommit = False
    cur = conn.cursor()
    
    try:
        # Check if already in DB
        cur.execute("SELECT id FROM documents WHERE page_hash LIKE %s LIMIT 1", (f"{content_hash}%",))
        if cur.fetchone():
            conn.close()
            return 0, register_entry  # Already exists, but still audit it
        
        # Chunk and ingest
        chunks = chunk_text(full_text)
        chunks_inserted = 0
        
        for i, chunk in enumerate(chunks):
            embedding = generate_embedding(chunk)
            if not embedding:
                continue
            
            page_estimate = min(i * page_count // max(len(chunks), 1) + 1, page_count)
            
            metadata = {
                'brand': brand,
                'sector': sector,
                'doc_type': doc_type,
                'page_count': page_count,
                'compliance_status': compliance_status,
                'anchors': anchors,
            }
            
            cur.execute("""
                INSERT INTO documents (
                    content, source, page, embedding, page_hash,
                    trade, priority, is_active,
                    ingestion_source, unit_range, doc_type
                ) VALUES (
                    %s, %s, %s, %s::vector, %s,
                    %s, %s, %s,
                    %s, %s::jsonb, %s
                )
            """, (
                chunk,
                f"{brand} - {filename.replace('.pdf', '')}",
                page_estimate,
                embedding,
                f"{content_hash}_{i}",
                sector,
                80,
                True,
                storage_path,
                json.dumps(metadata),
                doc_type
            ))
            chunks_inserted += 1
        
        if chunks_inserted > 0:
            conn.commit()
        
        cur.close()
        conn.close()
        return chunks_inserted, register_entry
        
    except Exception as e:
        print(f"      ❌ DB Error: {e}")
        try:
            conn.rollback()
            conn.close()
        except:
            pass
        return 0, register_entry

def main():
    """Main Total Market Lockdown execution"""
    print("=" * 80)
    print("⚔️  TOTAL MARKET LOCKDOWN - V3 AUDITOR PROTOCOL")
    print("=" * 80)
    print(f"Started: {datetime.now().isoformat()}")
    
    # Load full library file list
    with open('/app/full_library_audit_files.json', 'r') as f:
        all_files = json.load(f)
    
    print(f"\n📦 Total files to process: {len(all_files)}")
    
    # Track all register entries and processed hashes
    register_entries = []
    processed_hashes = set()
    
    # Stats
    stats = {
        'total_files': len(all_files),
        'processed': 0,
        'ingested': 0,
        'chunks_total': 0,
        'certified': 0,
        'bpir_only': 0,
        'missing_docs': 0,
        'errors': 0,
    }
    
    # Process all files
    for i, file_info in enumerate(all_files, 1):
        filename = file_info['name']
        print(f"\n[{i}/{len(all_files)}] {filename[:50]}...")
        
        try:
            chunks, entry = process_file(file_info, register_entries, processed_hashes)
            stats['processed'] += 1
            
            if chunks > 0:
                stats['ingested'] += 1
                stats['chunks_total'] += chunks
                print(f"      ✅ Ingested {chunks} chunks")
            
            if entry:
                status = entry.get('status', 'UNKNOWN')
                if status == 'CERTIFIED':
                    stats['certified'] += 1
                elif status == 'BPIR_ONLY':
                    stats['bpir_only'] += 1
                elif status == 'MISSING':
                    stats['missing_docs'] += 1
                    print(f"      ⚠️ MISSING_DOCS: {entry['brand'][:20]} - {entry['product'][:30]}")
                    
        except Exception as e:
            stats['errors'] += 1
            print(f"      ❌ Error: {e}")
        
        # Progress every 100 files
        if i % 100 == 0:
            print(f"\n   📊 Progress: {i}/{len(all_files)} files")
            print(f"      Chunks: {stats['chunks_total']:,}")
            print(f"      Certified: {stats['certified']}, Missing: {stats['missing_docs']}")
    
    # Write complete Compliance Register
    print(f"\n{'=' * 80}")
    print("📋 WRITING COMPLIANCE_MASTER_REGISTER.CSV")
    print("=" * 80)
    
    fieldnames = ['brand', 'product', 'sector', 'doc_type', 'codemark_id', 'branz_number', 
                  'epd_number', 'expiry_date', 'status', 'bpir_status', 'storage_path', 'anchors']
    
    with open(REGISTER_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(register_entries)
    
    print(f"   ✅ Register written: {len(register_entries)} entries")
    
    # Final database count
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM documents")
    total_chunks = cur.fetchone()[0]
    conn.close()
    
    # Summary
    print(f"\n{'=' * 80}")
    print("📊 TOTAL MARKET LOCKDOWN - FINAL SUMMARY")
    print("=" * 80)
    print(f"   📁 Files processed: {stats['processed']:,}/{stats['total_files']:,}")
    print(f"   📄 Files ingested: {stats['ingested']:,}")
    print(f"   📦 Total chunks created: {stats['chunks_total']:,}")
    print(f"   📦 Total DB chunks: {total_chunks:,}")
    print(f"\n   COMPLIANCE AUDIT:")
    print(f"   ✅ CERTIFIED (BRANZ/CodeMark): {stats['certified']}")
    print(f"   📋 BPIR_ONLY: {stats['bpir_only']}")
    print(f"   ⚠️  MISSING_DOCS: {stats['missing_docs']}")
    print(f"   ❌ Errors: {stats['errors']}")
    print(f"\n   📋 Register: {REGISTER_PATH}")
    print(f"      Total entries: {len(register_entries)}")
    print(f"\nCompleted: {datetime.now().isoformat()}")
    print("=" * 80)

if __name__ == "__main__":
    main()
