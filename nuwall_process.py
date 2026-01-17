#!/usr/bin/env python3
"""
Nu-Wall Cladding - Full Product Library Processor
==================================================
STRYDA Master Protocol v2.0 Compliant

Product Systems Identified:
- HOC: Horizontal On Cavity
- VDF: Vertical Direct Fix  
- VOC: Vertical On Cavity
- SS200: Panel System

Folder Structure:
B_Enclosure/Wall_Cladding/Nu_Wall/
├── 00_General_Resources/           ← BPIR, Product Statements, Care guides
├── BRANZ_Appraisals/               ← All BRANZ appraisals and certificates
├── Horizontal_On_Cavity/           ← HOC system CAD details
├── Vertical_Direct_Fix/            ← VDF system CAD details
├── Vertical_On_Cavity/             ← VOC system (if present)
├── SS200_Panel/                    ← SS200 system CAD details
├── Colour_Finish/                  ← Dulux, Interpon colour guides
└── Accessories/                    ← Alibat, NC247T, etc.
"""

import os
import re
import sys
import requests
import time
import fitz  # PyMuPDF

sys.path.insert(0, '/app/backend-minimal')

from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

from supabase import create_client

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
BUCKET_SOURCE = 'temporary'
BUCKET_DEST = 'product-library'
BASE_PATH = 'B_Enclosure/Wall_Cladding/Nu_Wall'

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def extract_cad_title(content):
    """Extract drawing title from CAD PDF"""
    try:
        doc = fitz.open(stream=content, filetype='pdf')
        if doc.page_count == 0:
            return None
        
        page = doc[0]
        text = page.get_text()
        doc.close()
        
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        # Look for descriptive title patterns
        for line in lines:
            # Skip short lines, drawing numbers, scales
            if len(line) < 15 or re.match(r'^(NW-|1:|[A-Z]{2,3}-\d)', line):
                continue
            
            # Look for typical CAD title patterns
            if any(kw in line.lower() for kw in [
                'typical', 'installation', 'base channel', 'corner', 'junction',
                'soffit', 'jamb', 'head', 'sill', 'parapet', 'penetration',
                'flashing', 'deck', 'roof', 'wall', 'window', 'door', 'garage',
                'batten', 'trim', 'raking', 'inverse', 'cavity', 'storey'
            ]):
                # Clean up the title
                title = re.sub(r'\s+', ' ', line).strip()
                title = title[:80]
                return title
        
        return None
    except:
        return None


def clean_filename(text):
    """Clean text for use in filename"""
    if not text:
        return None
    cleaned = re.sub(r'[<>:"/\\|?*]', '', text)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = cleaned.strip(' -–.')
    return cleaned[:80]


def get_drawing_number(filename):
    """Extract drawing number from filename"""
    # Pattern: nw-hoc-00102, nw-vdf-00202, nw-ss200-00101
    match = re.search(r'(nw-(?:hoc|vdf|voc|ss200)-\d+[a-z]?\d*)', filename.lower())
    if match:
        return match.group(1).upper()
    
    # Pattern: nw-v015c
    match = re.search(r'(nw-v\d+[a-z]?)', filename.lower())
    if match:
        return match.group(1).upper()
    
    return None


def determine_destination(filename):
    """Determine folder based on filename"""
    name_lower = filename.lower()
    
    # CAD Details by system
    if 'nw-hoc-' in name_lower:
        return f'{BASE_PATH}/Horizontal_On_Cavity/CAD_Details'
    elif 'nw-vdf-' in name_lower:
        return f'{BASE_PATH}/Vertical_Direct_Fix/CAD_Details'
    elif 'nw-voc-' in name_lower:
        return f'{BASE_PATH}/Vertical_On_Cavity/CAD_Details'
    elif 'nw-ss200-' in name_lower:
        return f'{BASE_PATH}/SS200_Panel/CAD_Details'
    elif 'nw-v0' in name_lower:
        return f'{BASE_PATH}/00_General_Resources/CAD_Details'
    
    # BRANZ Appraisals
    elif 'branz' in name_lower:
        return f'{BASE_PATH}/BRANZ_Appraisals'
    
    # BPIR
    elif 'bpis' in name_lower or 'bpir' in name_lower:
        return f'{BASE_PATH}/00_General_Resources'
    
    # Dulux/Interpon colour guides
    elif 'dulux' in name_lower or 'interpon' in name_lower:
        return f'{BASE_PATH}/Colour_Finish'
    
    # Accessories
    elif 'alibat' in name_lower or 'nc247' in name_lower:
        return f'{BASE_PATH}/Accessories'
    
    # Maintenance
    elif 'maintenance' in name_lower or 'care' in name_lower:
        return f'{BASE_PATH}/00_General_Resources'
    
    # Product statements, guides
    elif any(x in name_lower for x in ['product-statement', 'colour-and-texture', 'general-product']):
        return f'{BASE_PATH}/00_General_Resources'
    
    # Nu-Wall specific docs
    elif 'nu-wall' in name_lower or 'nu_wall' in name_lower:
        return f'{BASE_PATH}/00_General_Resources'
    
    # Default
    else:
        return f'{BASE_PATH}/00_General_Resources'


def generate_new_filename(orig_filename, content=None):
    """Generate Protocol v2.0 compliant filename"""
    name_lower = orig_filename.lower()
    dwg_num = get_drawing_number(orig_filename)
    
    # For CAD files, try to extract title
    if dwg_num and content:
        title = extract_cad_title(content)
        if title:
            clean_title = clean_filename(title)
            return f'Nu-Wall - {dwg_num} - {clean_title}.pdf'
    
    # For non-CAD files, apply naming rules
    
    # BRANZ Appraisals
    if 'branz-appraisal-550' in name_lower:
        return 'Nu-Wall - BRANZ Appraisal 550 - Horizontal On Cavity Aug 2025.pdf'
    elif 'branz-appraisal-556' in name_lower:
        return 'Nu-Wall - BRANZ Appraisal 556 - Vertical Direct Fix Aug 2025.pdf'
    elif 'branz-appraisal-870' in name_lower:
        return 'Nu-Wall - BRANZ Appraisal 870 - Vertical On Cavity Aug 2025.pdf'
    elif 'branz-em7' in name_lower or 'e2-vm2' in name_lower:
        if 'nu-wall' in name_lower:
            return 'Nu-Wall - BRANZ E2-VM2 Report and Certificate.pdf'
        else:
            return 'Nu-Wall - BRANZ EM7 E2-VM2 Certificate Apr 2023.pdf'
    
    # BPIR
    elif 'bpis' in name_lower or 'bpir' in name_lower:
        return 'Nu-Wall - BPIR Statement Jun 2024.pdf'
    
    # Product Statements
    elif 'general-product-statement' in name_lower:
        return 'Nu-Wall - General Product Statement Sep 2023.pdf'
    
    # Care and Maintenance
    elif 'care-and-maintenance' in name_lower:
        return 'Nu-Wall - Care and Maintenance Guide.pdf'
    
    # Colour guides
    elif 'colour-and-texture' in name_lower:
        return 'Nu-Wall - Colour and Texture Guide.pdf'
    
    # NZS 4284 Test
    elif 'nzs-4284' in name_lower:
        return 'Nu-Wall - NZS 4284 Commercial Facade Test Aug 2014.pdf'
    
    # Batten set
    elif 'batten-full-pdf-set' in name_lower:
        return 'Nu-Wall - Batten System Full Detail Set.pdf'
    
    # Maintenance Joint
    elif 'maintenance-joint-specification' in name_lower:
        return 'Nu-Wall - Maintenance Joint Specification Guide.pdf'
    elif 'maintenance-joint-one-pager' in name_lower:
        return 'Nu-Wall - Maintenance Joint Summary.pdf'
    
    # Alibat
    elif 'alibat' in name_lower:
        return 'Nu-Wall - Alibat Fastening Bulletin May 2024.pdf'
    
    # NC247T
    elif 'nc247t' in name_lower:
        return 'Nu-Wall - NC247T Product Information.pdf'
    
    # Dulux documents
    elif 'dulux-colour-selector-commercial' in name_lower:
        return 'Dulux - Commercial Colour Selector Duratec 2022.pdf'
    elif 'dulux-colour-selector-residential' in name_lower:
        return 'Dulux - Residential Colour Selector 2022.pdf'
    elif 'dulux-premium-architectural' in name_lower:
        return 'Dulux - Premium Architectural Colour Selector 2023.pdf'
    elif 'dulux-powder-warranty' in name_lower:
        return 'Dulux - Powder Warranty Solutions Brochure.pdf'
    elif 'dulux-sunscreen' in name_lower:
        return 'Dulux - Sunscreen Powdercoating Guide.pdf'
    
    # Interpon
    elif 'interpon-care' in name_lower:
        return 'Interpon - Care and Maintenance NZ.pdf'
    elif 'interpon-colors' in name_lower:
        return 'Interpon - Colors of New Zealand Nov 2021.pdf'
    
    # NW-V files (general details)
    elif 'nw-v015' in name_lower:
        return 'Nu-Wall - Detail V015 - General.pdf'
    elif 'nw-v016' in name_lower:
        return 'Nu-Wall - Detail V016 - General.pdf'
    elif 'nw-v017' in name_lower:
        return 'Nu-Wall - Detail V017 - General.pdf'
    
    # Default - clean up original name
    else:
        clean_name = orig_filename.replace('-', ' ').replace('_', ' ')
        clean_name = re.sub(r'\s+', ' ', clean_name).strip()
        clean_name = clean_name.replace('.pdf', '')
        return f'Nu-Wall - {clean_name}.pdf'


def download_from_temp(filename):
    """Download file from temporary bucket"""
    try:
        signed = supabase.storage.from_(BUCKET_SOURCE).create_signed_url(filename, 120)
        if signed and signed.get('signedURL'):
            response = requests.get(signed['signedURL'], timeout=120)
            if response.status_code == 200:
                return response.content
    except Exception as e:
        print(f'    ❌ Download error: {str(e)[:50]}')
    return None


def upload_to_dest(content, folder, filename):
    """Upload to product-library bucket"""
    path = f'{folder}/{filename}'
    try:
        supabase.storage.from_(BUCKET_DEST).upload(
            path, content,
            {'content-type': 'application/pdf', 'upsert': 'true'}
        )
        return True
    except Exception as e:
        if 'Duplicate' in str(e) or 'already exists' in str(e).lower():
            return True
        print(f'    ❌ Upload error: {str(e)[:50]}')
        return False


def main():
    print('=' * 80)
    print('NU-WALL CLADDING - FULL LIBRARY PROCESSOR')
    print('STRYDA Master Protocol v2.0')
    print('=' * 80)
    
    # Get files from temporary
    result = supabase.storage.from_(BUCKET_SOURCE).list('')
    files = sorted([f['name'] for f in result if f.get('name')])
    
    print(f'\n📂 Found {len(files)} files to process\n')
    
    stats = {
        'processed': 0,
        'skipped_dup': 0,
        'failed': 0
    }
    
    processed = []
    seen_names = set()
    
    for orig_filename in files:
        # Skip duplicates with (1), (2) suffix
        if re.search(r'\(\d+\)\.pdf$', orig_filename):
            print(f'🚫 Skipping duplicate: {orig_filename}')
            stats['skipped_dup'] += 1
            processed.append(orig_filename)
            continue
        
        print(f'\n📄 {orig_filename}')
        
        # Download
        content = download_from_temp(orig_filename)
        if not content:
            stats['failed'] += 1
            continue
        
        # Generate new filename
        new_filename = generate_new_filename(orig_filename, content)
        
        # Skip if we've already processed same name
        if new_filename.lower() in seen_names:
            print(f'   ⏭️ Duplicate name, skipping')
            stats['skipped_dup'] += 1
            processed.append(orig_filename)
            continue
        
        seen_names.add(new_filename.lower())
        
        # Determine destination folder
        dest_folder = determine_destination(orig_filename)
        
        print(f'   → {new_filename}')
        print(f'   → {dest_folder}/')
        
        # Upload
        if upload_to_dest(content, dest_folder, new_filename):
            print(f'   ✅ Done ({len(content):,} bytes)')
            stats['processed'] += 1
            processed.append(orig_filename)
        else:
            stats['failed'] += 1
        
        time.sleep(0.2)
    
    # Cleanup
    print(f'\n🧹 Cleaning up {len(processed)} files from temporary...')
    for f in processed:
        try:
            supabase.storage.from_(BUCKET_SOURCE).remove([f])
        except:
            pass
    
    # Summary
    print(f'\n{"=" * 80}')
    print('PROCESSING SUMMARY')
    print('=' * 80)
    print(f'✅ Processed: {stats["processed"]}')
    print(f'🚫 Skipped duplicates: {stats["skipped_dup"]}')
    print(f'❌ Failed: {stats["failed"]}')
    
    return stats['failed'] == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
