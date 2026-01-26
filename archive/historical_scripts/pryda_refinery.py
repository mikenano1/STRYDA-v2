#!/usr/bin/env python3
"""
⚡ PRYDA REFINERY PROTOCOL
==========================
V2/V3 Law Enforcement for Pryda Connector Files

Laws Applied:
- Law 0: Structural Recon (Technical Scan)
- Law 1: Context-Aware Naming
- Law 2: Sanitization
- Deduplication by filename/checksum

Source: Supabase /temporary bucket
Target: product-library/F_Manufacturers/Fasteners/Pryda/
"""
import os
import sys
import re
import hashlib
import json
from datetime import datetime
from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

from supabase import create_client

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

SOURCE_BUCKET = 'temporary'
TARGET_BUCKET = 'product-library'
TARGET_PATH = 'F_Manufacturers/Fasteners/Pryda'

# ==============================================================================
# LAW 1 & 2: SANITIZATION AND NAMING
# ==============================================================================

def sanitize_filename(original_name):
    """
    Apply Law 1 (Context-Aware Naming) and Law 2 (Sanitization)
    
    Format: Pryda - [Product Category] - [Detail].pdf
    """
    # Remove extension
    name = original_name.replace('.pdf', '').replace('.PDF', '')
    
    # Remove common prefixes
    name = re.sub(r'^NZ[-_\s]*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'^pryda[-_\s]*', '', name, flags=re.IGNORECASE)
    
    # Clean up separators
    name = name.replace('-', ' ').replace('_', ' ')
    name = re.sub(r'\s+', ' ', name).strip()
    
    # Title case
    name = name.title()
    
    # Map common terms to consistent naming
    name = name.replace('Connectors And Engineered Systems', '')
    name = name.replace('Design Guide', 'Design Guide')
    name = name.replace('V1.01', 'v1.01')
    name = name.replace('V1.02', 'v1.02')
    name = name.replace('August', '')
    name = re.sub(r'\s*1$', '', name)  # Remove trailing "1"
    
    # Clean again
    name = re.sub(r'\s+', ' ', name).strip()
    
    # Build final name
    final_name = f"Pryda - {name}.pdf"
    
    # Final cleanup
    final_name = final_name.replace('  ', ' ')
    final_name = final_name.replace(' .pdf', '.pdf')
    
    return final_name


# ==============================================================================
# DEDUPLICATION
# ==============================================================================

def get_existing_files():
    """Get list of existing Pryda files with checksums"""
    existing = supabase.storage.from_(TARGET_BUCKET).list(TARGET_PATH, {'limit': 500})
    
    checksums = {}
    for f in existing:
        name = f['name']
        # Download and hash
        try:
            data = supabase.storage.from_(TARGET_BUCKET).download(f"{TARGET_PATH}/{name}")
            if data:
                checksums[name] = hashlib.md5(data).hexdigest()
        except:
            pass
    
    return existing, checksums


def check_duplicate(new_name, new_data, existing_files, existing_checksums):
    """Check if file is duplicate by name similarity or checksum"""
    new_checksum = hashlib.md5(new_data).hexdigest()
    
    # Check checksum match
    for ex_name, ex_checksum in existing_checksums.items():
        if new_checksum == ex_checksum:
            return True, f"Checksum match with {ex_name}"
    
    # Check name similarity
    new_norm = new_name.lower().replace('-', '').replace('_', '').replace(' ', '')[:30]
    for ex in existing_files:
        ex_norm = ex['name'].lower().replace('-', '').replace('_', '').replace(' ', '')[:30]
        if new_norm == ex_norm:
            return True, f"Name match with {ex['name']}"
    
    return False, None


# ==============================================================================
# LAW 0: TECHNICAL RECON
# ==============================================================================

def technical_scan(pdf_data, filename):
    """
    Perform structural recon on PDF content.
    Identify span tables, kN loads, and technical patterns.
    """
    findings = {
        'has_span_tables': False,
        'has_kn_loads': False,
        'has_dimensions': False,
        'technical_keywords': [],
        'load_patterns': [],
        'estimated_complexity': 'LOW'
    }
    
    # Try to extract text for scanning
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=pdf_data, filetype='pdf')
        
        text = ""
        for page in doc:
            text += page.get_text()
        
        doc.close()
        text_lower = text.lower()
        
        # Detect span tables
        span_keywords = ['span', 'spacing', 'centres', 'maximum span', 'min span']
        for kw in span_keywords:
            if kw in text_lower:
                findings['has_span_tables'] = True
                findings['technical_keywords'].append(kw)
        
        # Detect kN loads
        kn_patterns = re.findall(r'(\d+\.?\d*)\s*kn', text_lower)
        if kn_patterns:
            findings['has_kn_loads'] = True
            findings['load_patterns'] = list(set(kn_patterns[:10]))
        
        # Detect dimensions
        dim_patterns = re.findall(r'\d+\s*x\s*\d+', text_lower)
        if dim_patterns:
            findings['has_dimensions'] = True
        
        # Specific Pryda patterns
        pryda_keywords = [
            'tie-down', 'bracing', 'connector', 'hanger', 'strap',
            'anchor', 'bracket', 'joist', 'bearer', 'rafter',
            'truss', 'nail plate', 'cyclonic', 'wind zone'
        ]
        for kw in pryda_keywords:
            if kw in text_lower:
                findings['technical_keywords'].append(kw)
        
        # Estimate complexity
        keyword_count = len(findings['technical_keywords'])
        if findings['has_kn_loads'] and len(findings['load_patterns']) > 5:
            findings['estimated_complexity'] = 'HIGH'
        elif findings['has_span_tables'] or keyword_count > 5:
            findings['estimated_complexity'] = 'MEDIUM'
        
    except Exception as e:
        findings['scan_error'] = str(e)[:50]
    
    return findings


# ==============================================================================
# MAIN REFINERY EXECUTION
# ==============================================================================

def run_refinery():
    """Execute the full Pryda Refinery Protocol"""
    
    print("=" * 70)
    print("   ⚡ PRYDA REFINERY PROTOCOL - EXECUTING")
    print(f"   Started: {datetime.now().isoformat()}")
    print("=" * 70)
    
    # Get source files
    print("\n📥 PHASE 1: SCANNING SOURCE")
    print("-" * 50)
    
    all_temp = supabase.storage.from_(SOURCE_BUCKET).list('', {'limit': 500})
    pryda_files = [f for f in all_temp if 'pryda' in f['name'].lower()]
    
    print(f"   Found {len(pryda_files)} Pryda files in {SOURCE_BUCKET}")
    
    # Get existing files for dedup
    print("\n🔍 PHASE 2: LOADING EXISTING FILES FOR DEDUP")
    print("-" * 50)
    
    existing_files, existing_checksums = get_existing_files()
    print(f"   Existing Pryda files: {len(existing_files)}")
    print(f"   Checksums computed: {len(existing_checksums)}")
    
    # Process files
    print("\n⚙️ PHASE 3: PROCESSING FILES (Law 1, Law 2)")
    print("-" * 50)
    
    results = {
        'processed': 0,
        'moved': 0,
        'duplicates': 0,
        'errors': 0,
        'files': [],
        'recon': []
    }
    
    for f in pryda_files:
        original_name = f['name']
        print(f"\n   📄 {original_name[:55]}...")
        
        try:
            # Download
            data = supabase.storage.from_(SOURCE_BUCKET).download(original_name)
            if not data:
                print(f"      ❌ Download failed")
                results['errors'] += 1
                continue
            
            # Sanitize name (Law 1 & 2)
            new_name = sanitize_filename(original_name)
            print(f"      → {new_name}")
            
            # Dedup check
            is_dup, reason = check_duplicate(new_name, data, existing_files, existing_checksums)
            if is_dup:
                print(f"      ⏭️ SKIP: Duplicate ({reason})")
                results['duplicates'] += 1
                continue
            
            # Technical scan (Law 0)
            scan = technical_scan(data, new_name)
            print(f"      🔬 Complexity: {scan['estimated_complexity']}")
            if scan['has_kn_loads']:
                print(f"         kN values: {scan['load_patterns'][:5]}")
            if scan['technical_keywords']:
                print(f"         Keywords: {scan['technical_keywords'][:5]}")
            
            # Upload to target
            target_file = f"{TARGET_PATH}/{new_name}"
            upload_result = supabase.storage.from_(TARGET_BUCKET).upload(
                target_file, 
                data,
                {'content-type': 'application/pdf', 'upsert': 'true'}
            )
            
            print(f"      ✅ Moved to {TARGET_PATH}/")
            results['moved'] += 1
            results['files'].append({
                'original': original_name,
                'sanitized': new_name,
                'path': target_file
            })
            results['recon'].append({
                'file': new_name,
                **scan
            })
            
        except Exception as e:
            print(f"      ❌ Error: {str(e)[:50]}")
            results['errors'] += 1
        
        results['processed'] += 1
    
    # Final Report
    print("\n" + "=" * 70)
    print("   📊 PRYDA REFINERY - FINAL REPORT")
    print("=" * 70)
    print(f"""
   Total Processed:   {results['processed']}
   ✅ Moved:          {results['moved']}
   ⏭️ Duplicates:     {results['duplicates']}
   ❌ Errors:         {results['errors']}
""")
    
    # Recon Summary
    print("=" * 70)
    print("   🔬 LAW 0 RECON - TECHNICAL ANALYSIS")
    print("=" * 70)
    
    high_complexity = [r for r in results['recon'] if r['estimated_complexity'] == 'HIGH']
    medium_complexity = [r for r in results['recon'] if r['estimated_complexity'] == 'MEDIUM']
    
    print(f"\n   HIGH COMPLEXITY (Need God-Tier Parsing): {len(high_complexity)}")
    for r in high_complexity:
        print(f"      🔴 {r['file'][:50]}")
        if r['load_patterns']:
            print(f"         kN Groups: {r['load_patterns']}")
    
    print(f"\n   MEDIUM COMPLEXITY: {len(medium_complexity)}")
    for r in medium_complexity:
        print(f"      🟡 {r['file'][:50]}")
    
    # Collect all unique kN patterns
    all_kn = []
    all_keywords = []
    for r in results['recon']:
        all_kn.extend(r.get('load_patterns', []))
        all_keywords.extend(r.get('technical_keywords', []))
    
    print(f"\n   📊 DETECTED kN LOAD VALUES:")
    unique_kn = sorted(set(all_kn), key=lambda x: float(x))
    print(f"      {unique_kn}")
    
    print(f"\n   📊 TECHNICAL KEYWORDS FOUND:")
    unique_kw = list(set(all_keywords))
    print(f"      {unique_kw}")
    
    # Save report
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'processed': results['processed'],
            'moved': results['moved'],
            'duplicates': results['duplicates'],
            'errors': results['errors']
        },
        'files_moved': results['files'],
        'technical_recon': results['recon'],
        'kn_patterns': unique_kn,
        'keywords': unique_kw
    }
    
    with open('/app/pryda_refinery_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n   📁 Report saved: /app/pryda_refinery_report.json")
    print("=" * 70)
    print(f"   ⚡ PRYDA REFINERY PROTOCOL COMPLETE")
    print(f"   Completed: {datetime.now().isoformat()}")
    print("=" * 70)
    
    return results


if __name__ == "__main__":
    run_refinery()
