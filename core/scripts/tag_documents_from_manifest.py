#!/usr/bin/env python3
"""
STRYDA-v2 Document Tagging from Manifest
Populates metadata fields from docs_manifest.jsonl
"""

import json
import os
import psycopg2
import re
from dotenv import load_dotenv

load_dotenv()

MANIFEST_PATH = "/app/backend-minimal/training/docs_manifest.jsonl"
DATABASE_URL = os.getenv("DATABASE_URL")

def infer_trade(path: str, cat: str, trade_manifest: str) -> str:
    """Infer trade from filename and category"""
    if trade_manifest and trade_manifest != 'unknown':
        return trade_manifest
    
    path_lower = path.lower()
    
    if 'fire' in path_lower or cat.startswith('fire_'):
        return 'fire'
    if 'roof' in path_lower or 'metal_roofing' in path_lower:
        return 'roofing'
    if 'e2-' in path_lower or 'external-moisture' in path_lower:
        return 'cladding'
    if 'e3-' in path_lower or 'wetarea' in path_lower:
        return 'bathroom_internal_moisture'
    if 'h1-' in path_lower:
        return 'energy'
    if 'g12-' in path_lower:
        return 'plumbing'
    if 'g13-' in path_lower:
        return 'drainage'
    if '3604' in path_lower or 'hb-3604' in path_lower:
        return 'structure'
    if 'gib' in path_lower:
        return 'structure'
    if 'b1-' in path_lower or 'b1/' in path_lower:
        return 'structure'
    if 'waterproof' in path_lower or 'ardex' in path_lower:
        return 'waterproofing'
    
    return 'unknown'

def derive_metadata(entry: dict) -> dict:
    """Derive metadata fields from manifest entry"""
    cat = entry.get("category", "")
    s = entry.get("status", "unknown")
    path = entry.get("supabase_path", "")
    trade_manifest = entry.get("trade", "unknown")
    phase = entry.get("phase", 0)
    
    # Infer trade
    trade = infer_trade(path, cat, trade_manifest)
    
    # Derive doc_type, status, priority
    doc_type = "unclassified"
    status = s
    priority = 50
    
    # A) NZBC Acceptable Solutions (current)
    if cat == 'nzbc_as' and s == 'current':
        doc_type = 'acceptable_solution_current'
        status = 'current'
        priority = 90
    
    # B) NZBC Verification Methods (current)
    elif cat == 'nzbc_vm' and s == 'current':
        doc_type = 'verification_method_current'
        status = 'current'
        priority = 85
    
    # C) Fire Acceptable Solutions (current)
    elif cat.startswith('fire_acceptance_current'):
        doc_type = 'acceptable_solution_current'
        status = 'current'
        priority = 90
    
    # Fire Acceptable Solutions (legacy)
    elif cat.startswith('fire_acceptance_legacy') or s == 'expired':
        doc_type = 'acceptable_solution_legacy'
        status = 'legacy'
        priority = 70
    
    # D) Fire Verification
    elif cat == 'fire_verification':
        doc_type = 'verification_method_legacy'
        status = 'legacy'
        priority = 65
    
    # E) Manufacturer bracing
    elif cat == 'manufacturer_bracing':
        doc_type = 'manufacturer_manual_bracing'
        status = 'current'
        priority = 75
    
    # F) Manufacturer fire
    elif cat == 'manufacturer_fire':
        doc_type = 'manufacturer_manual_fire'
        status = 'current'
        priority = 75
    
    # G) Internal wet area Code of Practice
    elif cat == 'internal_wet_area_code':
        doc_type = 'industry_code_of_practice'
        status = 'current'
        priority = 80
    
    # H) Manufacturer waterproofing
    elif cat == 'manufacturer_waterproofing':
        doc_type = 'manufacturer_manual_waterproofing'
        status = 'current'
        priority = 75
    
    # I) Unclassified docs
    elif cat == 'unclassified':
        doc_type = 'handbook_guide'
        status = 'current'
        priority = 60
    
    # Extract version label
    version_label = extract_version_label(path)
    
    return {
        "doc_type": doc_type,
        "trade": trade,
        "status": status,
        "phase": phase,
        "version_label": version_label,
        "priority": priority
    }

def extract_version_label(path: str) -> str:
    """Extract version label from filename"""
    try:
        # Remove .pdf extension
        name = path.replace('.pdf', '')
        
        # Try to extract version info after the code
        # E.g., "E2-AS1_4th-Edition-2025" -> "4th Edition 2025"
        patterns = [
            r'_(\d+(?:st|nd|rd|th)-Edition[^_]*)',  # 4th-Edition-2025
            r'Amendment-?(\d+)',  # Amendment-6
            r'Amd(\d+)',  # Amd12
            r'(\d{4})'  # Year
        ]
        
        version_parts = []
        for pattern in patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                version_parts.append(match.group(1).replace('-', ' ').replace('_', ' '))
        
        if version_parts:
            return ' '.join(version_parts)
        
        return None
    except:
        return None

def main():
    """Tag documents from manifest"""
    print("="*80)
    print("DOCUMENT TAGGING FROM MANIFEST")
    print("="*80)
    
    # Load manifest
    with open(MANIFEST_PATH, 'r') as f:
        manifest_entries = [json.loads(line) for line in f if line.strip()]
    
    print(f"\n✅ Loaded {len(manifest_entries)} manifest entries")
    
    # Connect to database
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    
    tagged_count = 0
    missing_count = 0
    doc_type_counts = {}
    
    for entry in manifest_entries:
        supabase_path = entry["supabase_path"]
        
        # Find matching documents
        source_name = supabase_path.replace(".pdf", "")
        
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, source
                FROM documents
                WHERE source = %s OR source LIKE %s
                LIMIT 1;
            """, (source_name, f"%{source_name}%"))
            
            result = cur.fetchone()
            
            if not result:
                print(f"   ⚠️  MISSING IN DB: {supabase_path}")
                missing_count += 1
                continue
            
            doc_id, actual_source = result
            
            # Derive metadata
            metadata = derive_metadata(entry)
            
            # Update document
            cur.execute("""
                UPDATE documents
                SET doc_type = %s,
                    trade = %s,
                    status = %s,
                    phase = %s,
                    version_label = %s,
                    priority = %s
                WHERE source = %s;
            """, (
                metadata["doc_type"],
                metadata["trade"],
                metadata["status"],
                metadata["phase"],
                metadata["version_label"],
                metadata["priority"],
                actual_source
            ))
            
            rows_updated = cur.rowcount
            conn.commit()
            
            tagged_count += rows_updated
            
            # Count by doc_type
            doc_type = metadata["doc_type"]
            doc_type_counts[doc_type] = doc_type_counts.get(doc_type, 0) + 1
            
            print(f"   ✅ TAGGED: {supabase_path:50} | doc_type={metadata['doc_type']:35} | trade={metadata['trade']:25} | status={metadata['status']:10} | priority={metadata['priority']}")
    
    conn.close()
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"TOTAL MANIFEST ENTRIES: {len(manifest_entries)}")
    print(f"DOCS TAGGED: {tagged_count}")
    print(f"DOCS MISSING IN DB: {missing_count}")
    
    print(f"\nCount by doc_type:")
    for doc_type, count in sorted(doc_type_counts.items()):
        print(f"   {doc_type:40}: {count}")

if __name__ == "__main__":
    main()
