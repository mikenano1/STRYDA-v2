#!/usr/bin/env python3
"""
OPERATION BREMICK SWEEP - V2 Protocol Executor
Processes Bremick fastener PDFs with intelligent naming and routing

Usage:
    python3 bremick_sweep.py --dry-run    # Preview changes without executing
    python3 bremick_sweep.py --execute    # Apply V2 transformations
"""

import os
import re
import sys
import json
import hashlib
import argparse
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, '/app')

# Load environment
env_file = Path('/app/backend-minimal/.env')
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            key, val = line.split('=', 1)
            os.environ[key.strip()] = val.strip()

from supabase import create_client

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
BUCKET = "product-library"
BREMICK_PATH = "F_Manufacturers/Fasteners/Bremick"

# Initialize Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================================================
# V2 TRANSFORMATION LOGIC
# ============================================================================

def detect_bremick_doc_type(filename):
    """
    Intelligent document type detection for Bremick fastener files.
    Prioritizes Technical Data Sheet detection.
    """
    fname_lower = filename.lower()
    
    # Priority 1: Explicit TDS markers
    if any(x in fname_lower for x in ['tds', 'technical-data', 'technical_data', 
                                       'tech-data', 'data-sheet', 'datasheet']):
        return 'Technical Data Sheet'
    
    # Priority 2: Fastener component names (usually TDS)
    fastener_components = [
        'hex-nut', 'hex-bolt', 'hex-head', 'socket-screw', 'socket-cap',
        'washer', 'anchor', 'rivet', 'nail', 'pin', 'stud', 'thread', 'tap',
        'coupling-nut', 'lock-nut', 'flange-nut', 'wing-nut', 'cap-nut',
        'set-screw', 'machine-screw', 'self-tap', 'wood-screw', 'coach-screw',
        'dyna-bolt', 'chem-anchor', 'drop-in', 'wedge-anchor', 'sleeve-anchor'
    ]
    if any(x in fname_lower for x in fastener_components):
        return 'Technical Data Sheet'
    
    # Priority 3: Grade/material specs (usually TDS)
    if re.search(r'grade[_\-\s]?\d+', fname_lower) or \
       re.search(r'class[_\-\s]?\d+', fname_lower) or \
       any(x in fname_lower for x in ['zinc', 'galv', 'stainless', 'brass', 'chrome']):
        return 'Technical Data Sheet'
    
    # Priority 4: Catalogue
    if 'catalogue' in fname_lower or 'catalog' in fname_lower:
        return 'Catalogue'
    
    # Priority 5: Installation guides
    if any(x in fname_lower for x in ['install', 'guide', 'manual', 'instruction', 'how-to']):
        return 'Installation Guide'
    
    # Priority 6: Specifications
    if any(x in fname_lower for x in ['spec', 'specification']):
        return 'Specification'
    
    # Priority 7: Compliance docs
    if any(x in fname_lower for x in ['sds', 'msds', 'safety', 'compliance', 'certificate']):
        return 'Safety Data Sheet'
    
    return 'Product Document'

def sanitize_product_name(filename):
    """
    Extract and clean product name from Bremick filename.
    """
    # Remove extension
    name = filename.replace('.pdf', '').replace('.PDF', '')
    
    # Remove Bremick prefix variations
    name = re.sub(r'^Bremick[_\-\s]*', '', name, flags=re.IGNORECASE)
    
    # Remove common suffixes
    name = re.sub(r'[_\-\s]*(TDS|tds|datasheet|data-sheet).*$', '', name)
    
    # Convert separators to spaces
    name = name.replace('_', ' ').replace('-', ' ')
    
    # Clean up multiple spaces
    name = ' '.join(name.split())
    
    # Title case
    name = name.title()
    
    # Limit length
    return name[:45]

def build_v2_filename(original_filename):
    """
    Build V2 compliant filename: Bremick - [Product] - [Type].pdf
    """
    product = sanitize_product_name(original_filename)
    doc_type = detect_bremick_doc_type(original_filename)
    
    v2_name = f"Bremick - {product} - {doc_type}.pdf"
    
    return v2_name, doc_type

def determine_route(filename, doc_type):
    """
    Determine destination subfolder based on fastener type.
    """
    fname_lower = filename.lower()
    base = '/01_Structure/Fasteners/Bremick/'
    
    # Route by fastener category
    routes = {
        'Bolts': ['bolt', 'hex-head', 'coach', 'carriage'],
        'Screws': ['screw', 'socket-cap', 'set-screw', 'self-tap', 'tek'],
        'Anchors': ['anchor', 'dyna', 'chem', 'drop-in', 'wedge', 'sleeve', 'masonry'],
        'Nuts_Washers': ['nut', 'washer', 'lock-nut', 'flange'],
        'Rivets': ['rivet', 'pop-rivet', 'blind-rivet'],
        'Stainless_Steel': ['stainless', '304', '316'],
        '00_Catalogues': ['catalogue', 'catalog', 'brochure'],
        '00_Compliance': ['sds', 'msds', 'safety', 'certificate']
    }
    
    for folder, keywords in routes.items():
        if any(kw in fname_lower for kw in keywords):
            return base + folder + '/'
    
    return base + 'General/'

# ============================================================================
# SWEEP EXECUTOR
# ============================================================================

def scan_bremick_files():
    """Scan Supabase for all Bremick files"""
    try:
        items = supabase.storage.from_(BUCKET).list(BREMICK_PATH, {'limit': 1000})
        files = [item for item in items if item['name'].endswith('.pdf')]
        return files
    except Exception as e:
        print(f"❌ Error scanning: {e}")
        return []

def run_sweep(dry_run=True):
    """Execute the Bremick Sweep"""
    print("=" * 100)
    print("                    OPERATION BREMICK SWEEP - V2 PROTOCOL")
    print("=" * 100)
    print(f"Mode: {'DRY RUN (Preview Only)' if dry_run else '🚨 LIVE EXECUTION'}")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 100)
    
    # Scan files
    files = scan_bremick_files()
    print(f"\n📂 Found {len(files)} Bremick PDF files\n")
    
    if not files:
        print("⚠️ No files to process. Upload Bremick PDFs first.")
        return
    
    # Process each file
    results = []
    print(f"{'#':<4} {'CURRENT':<40} {'V2 NAME':<40} {'ROUTE':<20}")
    print("-" * 100)
    
    for i, f in enumerate(files, 1):
        original = f['name']
        v2_name, doc_type = build_v2_filename(original)
        route = determine_route(original, doc_type)
        
        results.append({
            'original': original,
            'v2_name': v2_name,
            'doc_type': doc_type,
            'route': route
        })
        
        # Display
        curr = original[:38] + '..' if len(original) > 40 else original
        v2 = v2_name[:38] + '..' if len(v2_name) > 40 else v2_name
        rt = route.split('/')[-2] + '/'
        
        print(f"{i:<4} {curr:<40} {v2:<40} {rt:<20}")
    
    print("-" * 100)
    
    # Summary
    doc_types = {}
    for r in results:
        dt = r['doc_type']
        doc_types[dt] = doc_types.get(dt, 0) + 1
    
    print(f"\n📊 DOCUMENT TYPE BREAKDOWN:")
    for dt, count in sorted(doc_types.items(), key=lambda x: -x[1]):
        print(f"   {dt}: {count}")
    
    if dry_run:
        print(f"\n✅ DRY RUN COMPLETE - No changes made")
        print(f"   Run with --execute to apply transformations")
    else:
        print(f"\n🚀 EXECUTING TRANSFORMATIONS...")
        # TODO: Implement actual rename/move logic when ready
        print(f"   (Rename logic pending - files would be renamed here)")
    
    # Save results
    with open('/app/bremick_sweep_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n📋 Results saved to /app/bremick_sweep_results.json")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Bremick Sweep - V2 Protocol')
    parser.add_argument('--dry-run', action='store_true', help='Preview without changes')
    parser.add_argument('--execute', action='store_true', help='Apply transformations')
    args = parser.parse_args()
    
    if args.execute:
        run_sweep(dry_run=False)
    else:
        run_sweep(dry_run=True)
