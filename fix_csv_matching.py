#!/usr/bin/env python3
"""
STRYDA CSV Matching Fix
=======================
Fixes the matching algorithm between storage filenames and database sources.

The key insight:
- Storage: `A_Structure/Abodo_Wood/.../Abodo-Brochure.pdf`
- Database: `Abodo Wood - Abodo-Brochure` (no .pdf, has brand prefix)

Matching patterns to handle:
1. Brand + " - " + filename_without_extension
2. Brand + " Deep Dive - " + filename
3. Direct filename matches
4. Various underscore/space variations
"""

import os
import sys
import csv
import re
from pathlib import Path

sys.path.insert(0, '/app/backend-minimal')

from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

from supabase import create_client

# Initialize Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Known brand mappings (folder name -> DB brand name variations)
BRAND_MAPPINGS = {
    'Abodo_Wood': ['Abodo Wood', 'Abodo'],
    'Kingspan': ['Kingspan', 'Kingspan_'],
    'James_Hardie': ['James Hardie', 'James_Hardie'],
    'Autex': ['Autex', 'Autex Deep Dive'],
    'Bradford': ['Bradford', 'Bradford Deep Dive'],
    'GIB': ['GIB', 'GIB Deep Dive'],
    'Asona_Acoustics': ['Asona', 'Asona Deep Dive'],
    'Pink_Batts': ['Pink Batts', 'Pink Batts Deep Dive'],
    'Mammoth': ['Mammoth', 'Mammoth Deep Dive'],
    'Earthwool': ['Earthwool', 'Earthwool Deep Dive'],
    'Expol': ['Expol', 'Expol Deep Dive'],
    'Firth': ['Firth', 'Firth Deep Dive'],
    'GreenStuf': ['GreenStuf', 'GreenStuf Deep Dive'],
    'CHH': ['CHH', 'CHH Deep Dive'],
    'Red_Stag': ['Red Stag', 'Red Stag Deep Dive'],
    'JL_Duke': ['JL Duke', 'JL Duke Deep Dive'],
    'Bremick': ['Bremick'],
    'Buildex': ['Buildex'],
    'ECKO': ['ECKO', 'Ecko'],
    'Hilti': ['Hilti'],
    'ITW': ['ITW'],
    'Simpson': ['Simpson', 'Simpson Strong-Tie'],
}

# Prefixes to strip when matching
PREFIXES_TO_STRIP = [
    ' Deep Dive - ',
    ' - ',
    '_',
]

# Categories configuration
CATEGORIES = {
    'STRYDA_01_Compliance': {
        'bucket': 'pdfs',
        'path': '',
        'agent_zone': 'Compliance'
    },
    'STRYDA_02_A_Structure': {
        'bucket': 'product-library',
        'path': 'A_Structure',
        'agent_zone': 'Product Rep'
    },
    'STRYDA_03_B_Enclosure': {
        'bucket': 'product-library',
        'path': 'B_Enclosure',
        'agent_zone': 'Product Rep'
    },
    'STRYDA_04_C_Interiors': {
        'bucket': 'product-library',
        'path': 'C_Interiors',
        'agent_zone': 'Product Rep'
    },
    'STRYDA_05_F_Manufacturers': {
        'bucket': 'product-library',
        'path': 'F_Manufacturers',
        'agent_zone': 'Product Rep'
    },
    'STRYDA_06_Kingspan_K12': {
        'bucket': 'product-library',
        'path': '03_Kooltherm_K12_Framing_Board',
        'agent_zone': 'Product Rep'
    },
}

# =============================================================================
# DATABASE FUNCTIONS
# =============================================================================

def get_all_db_sources():
    """Get all unique sources and their chunk counts from the database."""
    result = supabase.table('documents').select('source').execute()
    sources = {}
    for row in result.data:
        src = row.get('source', 'UNKNOWN')
        sources[src] = sources.get(src, 0) + 1
    return sources

def normalize_string(s):
    """Normalize a string for matching: lowercase, remove extensions, standardize spaces."""
    if not s:
        return ''
    # Remove .pdf extension
    s = re.sub(r'\.pdf$', '', s, flags=re.IGNORECASE)
    # Replace underscores with spaces
    s = s.replace('_', ' ')
    # Collapse multiple spaces
    s = re.sub(r'\s+', ' ', s)
    # Lowercase
    s = s.lower().strip()
    return s

def extract_core_filename(source_name):
    """Extract the core filename from a database source name."""
    # Try to extract after various prefixes
    for prefix in PREFIXES_TO_STRIP:
        if prefix in source_name:
            parts = source_name.split(prefix, 1)
            if len(parts) == 2:
                return parts[1]
    return source_name

# =============================================================================
# MATCHING ALGORITHM
# =============================================================================

def find_matching_source(filename, storage_path, db_sources):
    """
    Find the matching database source for a storage filename.
    
    Returns: (source_name, chunk_count) or (None, 0)
    """
    # Clean up filename
    filename_clean = filename.replace('.pdf', '').replace('.PDF', '')
    filename_normalized = normalize_string(filename)
    
    # Extract brand from storage path
    brand_from_path = None
    path_parts = storage_path.split('/')
    for part in path_parts:
        if part in BRAND_MAPPINGS:
            brand_from_path = part
            break
    
    # Build list of possible source patterns to match
    patterns_to_try = []
    
    # Pattern 1: Brand + " - " + filename (most common for Abodo Wood)
    if brand_from_path:
        for brand_variant in BRAND_MAPPINGS.get(brand_from_path, []):
            patterns_to_try.append(f"{brand_variant} - {filename_clean}")
            patterns_to_try.append(f"{brand_variant} Deep Dive - {filename_clean}")
            patterns_to_try.append(f"{brand_variant} - {filename}")  # with .pdf
            patterns_to_try.append(f"{brand_variant} Deep Dive - {filename}")
    
    # Pattern 2: Direct filename match
    patterns_to_try.append(filename_clean)
    patterns_to_try.append(filename)
    
    # Pattern 3: Filename with dashes replaced
    patterns_to_try.append(filename_clean.replace('-', ' '))
    
    # Try exact matches first
    for pattern in patterns_to_try:
        if pattern in db_sources:
            return pattern, db_sources[pattern]
    
    # Try normalized matching
    for db_source, count in db_sources.items():
        db_normalized = normalize_string(db_source)
        
        # Check if filename is contained in source
        if filename_normalized and filename_normalized in db_normalized:
            return db_source, count
        
        # Check if source core filename matches
        core_filename = normalize_string(extract_core_filename(db_source))
        if core_filename and core_filename == filename_normalized:
            return db_source, count
        
        # Partial match: check significant overlap
        if filename_normalized and len(filename_normalized) > 10:
            # Check if 80% of words match
            file_words = set(filename_normalized.split())
            db_words = set(db_normalized.split())
            if file_words and db_words:
                overlap = len(file_words & db_words) / len(file_words)
                if overlap > 0.8:
                    return db_source, count
    
    return None, 0

# =============================================================================
# STORAGE LISTING
# =============================================================================

def list_all_files(bucket, path=""):
    """Recursively list all files in a bucket/path."""
    files_list = []
    try:
        items = supabase.storage.from_(bucket).list(path if path else None)
        for item in items:
            full_path = f"{path}/{item['name']}" if path else item['name']
            if item.get('id') is None:  # It's a folder
                files_list.extend(list_all_files(bucket, full_path))
            else:  # It's a file
                # Get file size in MB
                size_mb = item.get('metadata', {}).get('size', 0) / (1024 * 1024) if item.get('metadata') else 0
                files_list.append({
                    'path': full_path,
                    'name': item['name'],
                    'size_mb': round(size_mb, 2)
                })
    except Exception as e:
        print(f"Error listing {bucket}/{path}: {e}")
    return files_list

def extract_brand_from_path(storage_path):
    """Extract brand name from storage path."""
    path_parts = storage_path.split('/')
    for part in path_parts:
        # Check against known brand folders
        if part in BRAND_MAPPINGS:
            return BRAND_MAPPINGS[part][0]  # Return primary brand name
    
    # Fallback: try to extract from second level folder
    if len(path_parts) >= 2:
        potential_brand = path_parts[1].replace('_', ' ')
        return potential_brand
    
    return 'Unknown'

def extract_category_from_path(storage_path):
    """Extract category from storage path."""
    if storage_path.startswith('A_Structure'):
        return 'A_Structure'
    elif storage_path.startswith('B_Enclosure'):
        return 'B_Enclosure'
    elif storage_path.startswith('C_Interiors'):
        return 'C_Interiors'
    elif storage_path.startswith('F_Manufacturers'):
        return 'F_Manufacturers'
    elif storage_path.startswith('03_Kooltherm'):
        return 'Kingspan_K12'
    else:
        return 'Compliance'

# =============================================================================
# CSV GENERATION
# =============================================================================

def generate_csv(category_name, config, db_sources, output_dir):
    """Generate a CSV for a specific category."""
    bucket = config['bucket']
    path = config['path']
    agent_zone = config['agent_zone']
    
    # Get all files from storage
    files = list_all_files(bucket, path)
    
    # Filter out placeholder files
    files = [f for f in files if not f['name'].startswith('_placeholder') and f['name'].endswith('.pdf')]
    
    print(f"\n{'='*60}")
    print(f"Processing: {category_name}")
    print(f"  Bucket: {bucket}, Path: {path}")
    print(f"  Found {len(files)} PDF files")
    
    # Build CSV rows
    rows = []
    ingested_count = 0
    total_chunks = 0
    
    for file_info in files:
        filename = file_info['name']
        storage_path = file_info['path']
        size_mb = file_info['size_mb']
        
        # Extract brand and category
        brand = extract_brand_from_path(storage_path)
        category = extract_category_from_path(storage_path)
        
        # Find matching source in database
        db_source, chunks = find_matching_source(filename, storage_path, db_sources)
        
        if db_source:
            ingest_status = 'Ingested'
            ingested_count += 1
            total_chunks += chunks
        else:
            ingest_status = 'Not Ingested'
            db_source = ''
            chunks = 0
        
        rows.append({
            'agent_zone': agent_zone,
            'category': category,
            'brand': brand,
            'filename': filename,
            'file_size_mb': size_mb,
            'ingest_status': ingest_status,
            'text_chunks': chunks,
            'visual_assets': 0,  # Placeholder for now
            'db_source': db_source,
            'storage_path': storage_path
        })
    
    # Sort rows
    rows.sort(key=lambda x: (x['brand'], x['filename']))
    
    # Write CSV
    csv_path = os.path.join(output_dir, f"{category_name}.csv")
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['agent_zone', 'category', 'brand', 'filename', 'file_size_mb', 
                     'ingest_status', 'text_chunks', 'visual_assets', 'db_source', 'storage_path']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    # Print summary
    total_files = len(files)
    pct = (ingested_count / total_files * 100) if total_files > 0 else 0
    print(f"  ✅ Ingested: {ingested_count}/{total_files} ({pct:.1f}%)")
    print(f"  📊 Total chunks: {total_chunks}")
    print(f"  💾 Saved: {csv_path}")
    
    return {
        'category': category_name,
        'total_files': total_files,
        'ingested': ingested_count,
        'not_ingested': total_files - ingested_count,
        'total_chunks': total_chunks,
        'percentage': pct
    }

# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("STRYDA CSV MATCHING FIX")
    print("=" * 60)
    
    # Create output directories
    output_dirs = ['/app/data', '/app/frontend/public/exports']
    for d in output_dirs:
        os.makedirs(d, exist_ok=True)
    
    # Get all database sources
    print("\n📊 Fetching database sources...")
    db_sources = get_all_db_sources()
    print(f"   Found {len(db_sources)} unique sources")
    print(f"   Total chunks: {sum(db_sources.values())}")
    
    # Generate CSVs for each category
    summaries = []
    for category_name, config in CATEGORIES.items():
        summary = generate_csv(category_name, config, db_sources, '/app/data')
        summaries.append(summary)
        
        # Copy to public exports
        import shutil
        src = f"/app/data/{category_name}.csv"
        dst = f"/app/frontend/public/exports/{category_name}.csv"
        shutil.copy(src, dst)
    
    # Print final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"\n{'Category':<30} {'PDFs':>6} {'Ingested':>10} {'Not':>6} {'%':>8} {'Chunks':>8}")
    print("-" * 70)
    
    total_pdfs = 0
    total_ingested = 0
    total_chunks = 0
    
    for s in summaries:
        print(f"{s['category']:<30} {s['total_files']:>6} {s['ingested']:>10} {s['not_ingested']:>6} {s['percentage']:>7.1f}% {s['total_chunks']:>8}")
        total_pdfs += s['total_files']
        total_ingested += s['ingested']
        total_chunks += s['total_chunks']
    
    print("-" * 70)
    overall_pct = (total_ingested / total_pdfs * 100) if total_pdfs > 0 else 0
    print(f"{'TOTAL':<30} {total_pdfs:>6} {total_ingested:>10} {total_pdfs - total_ingested:>6} {overall_pct:>7.1f}% {total_chunks:>8}")
    
    print("\n✅ All CSVs generated successfully!")
    print(f"   Output: /app/data/ and /app/frontend/public/exports/")

if __name__ == '__main__':
    main()
