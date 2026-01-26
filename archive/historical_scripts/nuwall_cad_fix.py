#!/usr/bin/env python3
"""
Nu-Wall CAD File Remediation - Complete VDF and VOC Fix
"""

import os
import re
import requests
import time
from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

from supabase import create_client

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

BASE = 'B_Enclosure/Wall_Cladding/Nu_Wall'

# Complete VDF descriptions (00802 onwards that were missed)
VDF_DESCRIPTIONS = {
    'NW-VDF-00802': 'Internal 90 Deg Corner Using NC107X and NC109X',
    'NW-VDF-00902': 'Typical Inter-Storey or Horizontal Joint',
    'NW-VDF-01002': 'Typical Sill Section NC247 and NC248 Assembly',
    'NW-VDF-01102': 'Typical Jamb Section NC247 and NC248 Assembly',
    'NW-VDF-01202': 'Typical Jamb Section with Negative Detail Filler',
    'NW-VDF-01302': 'Typical Head Section',
    'NW-VDF-01402': 'Soaker Installation to Window Jamb',
    'NW-VDF-01502': 'Typical Head Flashing End Detail',
    'NW-VDF-016A03': 'Typical Soffit Trim',
    'NW-VDF-016B03': 'Typical Raking Soffit',
    'NW-VDF-016C03': 'Typical Inverse Raking Soffit',
    'NW-VDF-01702': 'Typical Pipe Penetration',
    'NW-VDF-01802': 'Typical Apron Roof to Wall Junction',
    'NW-VDF-01902': 'Typical Parapet to Wall',
    'NW-VDF-02002': 'Typical Deck to Wall Junction',
    'NW-VDF-02102': 'Typical Roof and Gutter to Wall Junction',
    'NW-VDF-02202': 'Notching Board Around Window Jamb',
    'NW-VDF-02303': 'Ripped Board to End of Wall Junction',
    'NW-VDF-02403': 'Typical Nu-Wall Fascia to Soffit',
    'NW-VDF-02503': 'Typical Nu-Wall to Fascia Soffit Wall with Alternative',
    'NW-VDF-02603': 'Typical Garage Door Head Jamb Timber Reveal',
    'NW-VDF-026B03': 'Typical Garage Door Head Jamb Nu-Wall Reveal Profile',
    'NW-VDF-02703': 'Typical Nu-Wall to Brick Internal Corner',
    'NW-VDF-02803': 'Typical Nu-Wall to Brick External Corner',
    'NW-VDF-02902': 'Typical Nu-Wall to Brick Horizontal Junction',
    'NW-VDF-03003': 'Typical Nu-Wall to Brick Vertical Junction',
    'NW-VDF-03103': 'Typical Nu-Wall to Concrete Masonry Vertical Junction',
    'NW-VDF-03203': 'Typical Nu-Wall to Concrete Masonry External Corner',
    'NW-VDF-03303': 'Typical Nu-Wall to Concrete Masonry Internal Corner',
}

# Complete VOC descriptions
VOC_DESCRIPTIONS = {
    'NW-VOC-00103': 'Batten Layout for Vertical Cladding Over Drained Vented Cavity',
    'NW-VOC-00202': 'Typical Installation Timber Cavity Batten to Timber Frame',
    'NW-VOC-00302': 'Typical Installation Timber Cavity Batten to Steel Frame',
    'NW-VOC-00402': 'Typical Installation Alibat to Timber Frame',
    'NW-VOC-00502': 'Typical Base Channel Fixing',
    'NW-VOC-00602': 'Typical Base Channel Over Timber Floor',
    'NW-VOC-00702': 'Typical Base Channel Over Waterproof Deck',
    'NW-VOC-007B02': 'Typical Base Channel Over Concrete Slab',
    'NW-VOC-00802': 'Pre-Fabricated 90 Deg Base Channel Corner',
    'NW-VOC-00902': 'Typical Corner NC107X and NC109X Assembly',
    'NW-VOC-010': 'One Piece External Corner Negative Detail',
    'NW-VOC-01102': 'External 90 Deg Corner Using NC251 Box Assembly',
    'NW-VOC-01202': 'External 90 Deg Corner Using NC252 Negative Detail Assembly',
    'NW-VOC-01302': 'Internal 90 Deg Corner Using NC107X and NC109X',
    'NW-VOC-01402': 'Internal 90 Deg Corner Using NC253 Negative Detail',
    'NW-VOC-01502': 'Typical Inter-Storey or Horizontal Joint',
    'NW-VOC-01602': 'Typical Sill Section NC247 and NC248 Assembly',
    'NW-VOC-01702': 'Typical Jamb Section NC247 and NC248 Assembly',
    'NW-VOC-01802': 'Typical Jamb Section with Negative Detail Filler',
    'NW-VOC-01902': 'Typical Head Section',
    'NW-VOC-02002': 'Soaker Installation to Window Jamb',
    'NW-VOC-02102': 'Typical Head Flashing End Detail',
    'NW-VOC-022A03': 'Typical Soffit Trim',
    'NW-VOC-022B03': 'Typical Raking Soffit',
    'NW-VOC-022C03': 'Typical Inverse Raking Soffit',
    'NW-VOC-02302': 'Typical Pipe Penetration',
    'NW-VOC-023B02': 'Typical Large Pipe Penetration with Cowel',
    'NW-VOC-02402': 'Typical Apron Roof to Wall Junction',
    'NW-VOC-02502': 'Typical Parapet to Wall',
    'NW-VOC-02602': 'Typical Deck to Wall Junction',
    'NW-VOC-02702': 'Typical Roof and Gutter to Wall Junction',
    'NW-VOC-02802': 'Notching Board Around Window Jamb',
    'NW-VOC-02903': 'Ripped Board to End of Wall Junction',
    'NW-VOC-03003': 'Typical Nu-Wall Fascia to Soffit',
    'NW-VOC-030B03': 'Typical Nu-Wall Fascia to Soffit Optional Cavity Closure',
    'NW-VOC-03103': 'Typical Nu-Wall to Fascia Soffit Wall with Alternative',
    'NW-VOC-03203': 'Typical Garage Door Head and Jamb Timber Reveal',
    'NW-VOC-032B03': 'Typical Garage Door Head and Jamb Nu-Wall Reveal Profile',
    'NW-VOC-03303': 'Typical Nu-Wall to Brick Internal Corner',
    'NW-VOC-03403': 'Typical Nu-Wall to Brick External Corner',
    'NW-VOC-03502': 'Typical Nu-Wall to Brick Horizontal Junction',
    'NW-VOC-03603': 'Typical Nu-Wall to Brick Vertical Junction',
    'NW-VOC-03703': 'Typical Nu-Wall to Concrete Masonry Vertical Junction',
    'NW-VOC-03803': 'Typical Nu-Wall to Concrete Masonry External Corner',
    'NW-VOC-03903': 'Typical Nu-Wall to Concrete Masonry Internal Corner',
    'NW-VOC-04003': 'Typical Nu-Wall Irregular External Corner Flashing',
    'NW-VOC-04103': 'Typical Nu-Wall Irregular Internal Corner Flashing',
    'NW-VOC-04202': 'Typical Nu-Wall Irregular Internal Corner Flashing Profiles',
    'NW-VOC-04302': 'Vertical Join Mixed Cladding',
    'NW-VOC-043B02': 'Vertical Join Mixed Cladding NC105X NC103',
}

# Combine all
ALL_DESCRIPTIONS = {**VDF_DESCRIPTIONS, **VOC_DESCRIPTIONS}

def rename_file(old_path, new_filename):
    """Download, re-upload with new name, delete old"""
    try:
        signed = supabase.storage.from_('product-library').create_signed_url(old_path, 60)
        response = requests.get(signed['signedURL'], timeout=60)
        
        if response.status_code == 200:
            content = response.content
            folder = '/'.join(old_path.split('/')[:-1])
            new_path = f'{folder}/{new_filename}'
            
            supabase.storage.from_('product-library').upload(
                new_path, content,
                {'content-type': 'application/pdf', 'upsert': 'true'}
            )
            supabase.storage.from_('product-library').remove([old_path])
            return True
    except:
        pass
    return False

print('=' * 80)
print('NU-WALL CAD FILE REMEDIATION - VDF & VOC')
print('=' * 80)

folders = [
    (f'{BASE}/Vertical_Direct_Fix/CAD_Details', 'VDF'),
    (f'{BASE}/Vertical_On_Cavity/CAD_Details', 'VOC'),
]

stats = {'renamed': 0, 'skipped': 0, 'failed': 0}

for folder, system in folders:
    print(f'\n📁 {system} System')
    print('-' * 60)
    
    try:
        result = supabase.storage.from_('product-library').list(folder)
        files = sorted([f['name'] for f in result if f.get('name')])
        
        for filename in files:
            # Check if file has generic name
            if 'Nu-Wall cladding vertical' not in filename:
                stats['skipped'] += 1
                continue
            
            # Extract drawing number
            match = re.search(r'(NW-[A-Z0-9]+)', filename)
            if not match:
                continue
            
            dwg_num = match.group(1)
            
            # Get proper description
            if dwg_num not in ALL_DESCRIPTIONS:
                print(f'   ⚠️ No mapping for {dwg_num}')
                stats['failed'] += 1
                continue
            
            description = ALL_DESCRIPTIONS[dwg_num]
            new_filename = f'Nu-Wall - {dwg_num} - {description}.pdf'
            old_path = f'{folder}/{filename}'
            
            if rename_file(old_path, new_filename):
                print(f'   ✅ {dwg_num}: {description[:45]}')
                stats['renamed'] += 1
            else:
                print(f'   ❌ Failed: {dwg_num}')
                stats['failed'] += 1
            
            time.sleep(0.15)
            
    except Exception as e:
        print(f'   Error: {e}')

print(f'\n{"=" * 80}')
print('SUMMARY')
print('=' * 80)
print(f'✅ Renamed: {stats["renamed"]}')
print(f'⏭️ Already correct: {stats["skipped"]}')
print(f'❌ Failed: {stats["failed"]}')
