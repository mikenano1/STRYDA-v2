#!/usr/bin/env python3
"""
MITEK REFINERY PROTOCOL
=======================
V2/V3 Law Enforcement for MiTek Product Library

Tasks:
1. Pull files from temporary bucket
2. Sanitize names (Law 1)
3. Route to product-library/F_Manufacturers/Structural/MiTek/
4. Identify Structural Bibles
5. Create Synonym Mapping
"""
import os
import sys
import re
import json
from pathlib import Path
from datetime import datetime

# Load env
env_file = Path('/app/backend-minimal/.env')
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            key, val = line.split('=', 1)
            os.environ[key.strip()] = val.strip()

from supabase import create_client

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 80)
print("🔧 MITEK REFINERY PROTOCOL - V2/V3 LAW ENFORCEMENT")
print(f"   Started: {datetime.now().isoformat()}")
print("=" * 80)

# ============================================================================
# LAW 0: RECON - STRUCTURAL BIBLE IDENTIFICATION
# ============================================================================

STRUCTURAL_BIBLES = {
    'Residential-Manual': 'STRUCTURAL_BIBLE',
    'PosiStrut-Manual': 'STRUCTURAL_BIBLE', 
    'FLITCH-BEAM-Manual': 'STRUCTURAL_BIBLE',
    'Characteristic_Loadings': 'SPEC_MASTER',
    'BPIR': 'COMPLIANCE_CERT',
    'Test-Results': 'TEST_DATA',
    'Span': 'SPAN_TABLE'
}

# ============================================================================
# SYNONYM MAPPING - BRAND HIERARCHY
# ============================================================================

MITEK_BRANDS = {
    'Lumberlok': 'MiTek',
    'LUMBERLOK': 'MiTek', 
    'Bowmac': 'MiTek',
    'BOWMAC': 'MiTek',
    'Gang-Nail': 'MiTek',
    'GIB-HandiBrac': 'MiTek',
    'PosiStrut': 'MiTek',
    'Stud-Lok': 'MiTek',
    'STUD-LOK': 'MiTek',
    'Plate-Lok': 'MiTek',
    'Multi-Brace': 'MiTek'
}

# ============================================================================
# LAW 1: FILE NAME SANITIZATION
# ============================================================================

def sanitize_filename(original_name):
    """
    Apply Law 1 naming: MiTek - [Product Group] - [Specific Name].pdf
    """
    name = original_name.replace('.pdf', '')
    
    # Detect product group
    product_group = "General"
    
    if 'BOWMAC' in name.upper():
        product_group = "Bowmac Brackets"
    elif 'LUMBERLOK' in name.upper():
        product_group = "Lumberlok Connectors"
    elif 'STUD-LOK' in name.upper() or 'STUDLOK' in name.upper():
        product_group = "Stud-Lok Fixings"
    elif 'GIB' in name.upper():
        product_group = "GIB Systems"
    elif 'BPIR' in name.upper():
        product_group = "BPIR Compliance"
    elif 'Manual' in name:
        product_group = "Technical Manuals"
    elif 'Pile' in name or 'Subfloor' in name:
        product_group = "Foundation Fixings"
    elif 'Joist' in name or 'Deck' in name:
        product_group = "Floor Systems"
    elif 'Plate' in name and 'Top' in name:
        product_group = "Plate Fixings"
    elif 'Purlin' in name or 'Cleat' in name:
        product_group = "Roof Fixings"
    elif 'Brace' in name or 'Stiffener' in name:
        product_group = "Bracing Systems"
    elif 'PosiStrut' in name:
        product_group = "PosiStrut Flooring"
    elif 'Test' in name or 'Results' in name:
        product_group = "Test Data"
    elif 'Span' in name:
        product_group = "Span Tables"
    
    # Clean up specific name
    specific_name = name
    # Remove common prefixes
    specific_name = re.sub(r'^(BOWMAC|LUMBERLOK|STUD-LOK|MiTek)[_-]?', '', specific_name, flags=re.IGNORECASE)
    # Remove date suffixes
    specific_name = re.sub(r'_?\d{4}-v\d+', '', specific_name)
    specific_name = re.sub(r'_?\d{2}\.\d{4}', '', specific_name)
    # Clean underscores/dashes
    specific_name = specific_name.replace('_', ' ').replace('-', ' ')
    specific_name = re.sub(r'\s+', ' ', specific_name).strip()
    # Title case
    specific_name = specific_name.title()
    
    # Build sanitized name
    sanitized = f"MiTek - {product_group} - {specific_name}.pdf"
    
    return sanitized, product_group


def identify_document_type(filename):
    """Law 0: Identify document classification"""
    for pattern, doc_type in STRUCTURAL_BIBLES.items():
        if pattern.lower() in filename.lower():
            return doc_type
    return "PRODUCT_TDS"


def extract_kn_ratings(filename):
    """Detect kN ratings from filename"""
    matches = re.findall(r'(\d+)\s*kN', filename, re.IGNORECASE)
    return [f"{m}kN" for m in matches] if matches else []


# ============================================================================
# MAIN REFINERY PROCESS
# ============================================================================

print("\n📂 SCANNING TEMPORARY BUCKET...")

# Get all files from temporary
files_to_process = []
try:
    items = supabase.storage.from_('temporary').list('', {'limit': 500})
    for item in items:
        if item['name'].lower().endswith('.pdf'):
            files_to_process.append({
                'original_name': item['name'],
                'source_path': item['name'],
                'bucket': 'temporary'
            })
except Exception as e:
    print(f"❌ Error scanning: {e}")
    sys.exit(1)

print(f"   Found {len(files_to_process)} PDF files")

# ============================================================================
# PROCESS EACH FILE
# ============================================================================

TARGET_BUCKET = 'product-library'
TARGET_PATH = 'F_Manufacturers/Structural/MiTek'

manifest = {
    'processed': [],
    'structural_bibles': [],
    'compliance_certs': [],
    'kn_ratings': {},
    'synonym_map': MITEK_BRANDS,
    'errors': []
}

print(f"\n🔄 PROCESSING {len(files_to_process)} FILES...")
print(f"   Target: {TARGET_BUCKET}/{TARGET_PATH}")
print("-" * 80)

for i, file_info in enumerate(files_to_process, 1):
    original = file_info['original_name']
    
    # Apply Law 1: Sanitize name
    sanitized_name, product_group = sanitize_filename(original)
    
    # Law 0: Identify document type
    doc_type = identify_document_type(original)
    
    # Extract kN ratings
    kn_ratings = extract_kn_ratings(original)
    
    print(f"\n[{i:2}/{len(files_to_process)}] {original[:50]}...")
    print(f"       → {sanitized_name[:55]}")
    print(f"       📁 Group: {product_group} | Type: {doc_type}")
    if kn_ratings:
        print(f"       ⚡ kN Ratings: {', '.join(kn_ratings)}")
    
    try:
        # Download from temporary
        pdf_data = supabase.storage.from_('temporary').download(file_info['source_path'])
        
        if not pdf_data:
            print(f"       ⚠️ Download failed - skipping")
            manifest['errors'].append(original)
            continue
        
        # Upload to product-library with sanitized name
        target_path = f"{TARGET_PATH}/{sanitized_name}"
        
        # Check if exists
        try:
            existing = supabase.storage.from_(TARGET_BUCKET).list(TARGET_PATH, {'limit': 500})
            exists = any(e['name'] == sanitized_name for e in existing)
        except:
            exists = False
        
        if exists:
            print(f"       ⏭️ Already exists - skipping")
            manifest['processed'].append({
                'original': original,
                'sanitized': sanitized_name,
                'status': 'EXISTS',
                'doc_type': doc_type,
                'product_group': product_group
            })
            continue
        
        # Upload
        result = supabase.storage.from_(TARGET_BUCKET).upload(
            target_path,
            pdf_data,
            {'content-type': 'application/pdf'}
        )
        
        print(f"       ✅ Uploaded to {TARGET_BUCKET}")
        
        # Track in manifest
        entry = {
            'original': original,
            'sanitized': sanitized_name,
            'path': target_path,
            'status': 'UPLOADED',
            'doc_type': doc_type,
            'product_group': product_group,
            'kn_ratings': kn_ratings
        }
        manifest['processed'].append(entry)
        
        if doc_type == 'STRUCTURAL_BIBLE':
            manifest['structural_bibles'].append(sanitized_name)
        elif doc_type == 'COMPLIANCE_CERT':
            manifest['compliance_certs'].append(sanitized_name)
        
        if kn_ratings:
            manifest['kn_ratings'][sanitized_name] = kn_ratings
        
        # Delete from temporary after successful upload
        try:
            supabase.storage.from_('temporary').remove([file_info['source_path']])
            print(f"       🗑️ Removed from temporary")
        except Exception as e:
            print(f"       ⚠️ Could not remove from temp: {str(e)[:30]}")
        
    except Exception as e:
        print(f"       ❌ Error: {str(e)[:50]}")
        manifest['errors'].append(original)

# ============================================================================
# FINAL REPORT
# ============================================================================

print("\n" + "=" * 80)
print("📋 MITEK REFINERY - FINAL MANIFEST")
print("=" * 80)

print(f"\n✅ PROCESSED: {len([p for p in manifest['processed'] if p['status'] == 'UPLOADED'])}")
print(f"⏭️ EXISTED: {len([p for p in manifest['processed'] if p['status'] == 'EXISTS'])}")
print(f"❌ ERRORS: {len(manifest['errors'])}")

print(f"\n📚 STRUCTURAL BIBLES ({len(manifest['structural_bibles'])}):")
for bible in manifest['structural_bibles']:
    print(f"   📖 {bible}")

print(f"\n📜 COMPLIANCE CERTS ({len(manifest['compliance_certs'])}):")
for cert in manifest['compliance_certs']:
    print(f"   🏅 {cert}")

print(f"\n⚡ kN RATING INDEX:")
for doc, ratings in manifest['kn_ratings'].items():
    print(f"   • {doc[:50]}: {', '.join(ratings)}")

print(f"\n🔗 BRAND SYNONYM MAP (for Engineer Agent):")
for sub_brand, parent in manifest['synonym_map'].items():
    print(f"   {sub_brand} → {parent}")

# Save manifest
manifest['generated'] = datetime.now().isoformat()
manifest['target_location'] = f"{TARGET_BUCKET}/{TARGET_PATH}"

with open('/app/mitek_manifest.json', 'w') as f:
    json.dump(manifest, f, indent=2)

print(f"\n💾 Manifest saved to: /app/mitek_manifest.json")
print("=" * 80)
print("🔧 MITEK REFINERY PROTOCOL - COMPLETE")
print("=" * 80)
