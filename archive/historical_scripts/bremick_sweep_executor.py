#!/usr/bin/env python3
"""
OPERATION BREMICK SWEEP - Background Executor
Moves 287 Bremick PDFs from 'temporary' to 'product-library' bucket
"""
import os
import re
import json
import sys
from datetime import datetime
from pathlib import Path

# Unbuffered output for real-time logging
sys.stdout = open('/app/bremick_sweep.log', 'w', buffering=1)
sys.stderr = sys.stdout

print(f"=" * 80)
print(f"OPERATION BREMICK SWEEP - BACKGROUND EXECUTION")
print(f"Started: {datetime.now().isoformat()}")
print(f"=" * 80)

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
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Load transformation map
with open('/app/bremick_sweep_full_results.json') as f:
    results = json.load(f)

print(f"\n📂 Processing {len(results)} files...\n", flush=True)

# Stats
moved = 0
skipped = 0
errors = 0
error_log = []

for i, r in enumerate(results, 1):
    original = r['original']
    subfolder = r['subfolder']
    
    source_path = original
    dest_folder = f"F_Manufacturers/Fasteners/Bremick/{subfolder}"
    dest_path = f"{dest_folder}/{original}"
    
    try:
        # Download from temporary
        file_data = supabase.storage.from_('temporary').download(source_path)
        
        if file_data:
            # Upload to product-library
            upload_result = supabase.storage.from_('product-library').upload(
                dest_path, 
                file_data,
                {'content-type': 'application/pdf', 'upsert': 'true'}
            )
            moved += 1
            print(f"[{i:3}/{len(results)}] ✅ → {subfolder}/{original[:40]}...", flush=True)
        else:
            errors += 1
            error_log.append(f"Download failed: {original}")
            print(f"[{i:3}/{len(results)}] ❌ Download failed: {original[:40]}...", flush=True)
            
    except Exception as e:
        error_str = str(e)
        if 'Duplicate' in error_str or 'already exists' in error_str.lower():
            skipped += 1
            print(f"[{i:3}/{len(results)}] ⚠️ Exists: {original[:40]}...", flush=True)
        else:
            errors += 1
            error_log.append(f"{original}: {error_str[:80]}")
            print(f"[{i:3}/{len(results)}] ❌ Error: {error_str[:50]}", flush=True)
    
    # Checkpoint every 50 files
    if i % 50 == 0:
        print(f"\n📊 CHECKPOINT [{i}/{len(results)}]: Moved={moved}, Skipped={skipped}, Errors={errors}\n", flush=True)

# Final report
print(f"\n{'='*80}", flush=True)
print(f"OPERATION BREMICK SWEEP - COMPLETE", flush=True)
print(f"{'='*80}", flush=True)
print(f"✅ Moved: {moved}", flush=True)
print(f"⚠️ Skipped (exists): {skipped}", flush=True)
print(f"❌ Errors: {errors}", flush=True)
print(f"Finished: {datetime.now().isoformat()}", flush=True)

# Save report
report = {
    'total': len(results),
    'moved': moved,
    'skipped': skipped,
    'errors': errors,
    'error_log': error_log,
    'completed': datetime.now().isoformat()
}
with open('/app/bremick_sweep_report.json', 'w') as f:
    json.dump(report, f, indent=2)

print(f"\n📋 Report saved to /app/bremick_sweep_report.json", flush=True)
