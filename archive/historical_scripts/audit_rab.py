"""
STRYDA Quality Audit: Rigid Air Barriers
========================================
"""

import os
from supabase import create_client
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv("/app/backend-minimal/.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
BUCKET = "product-library"
TARGET_PATH = "B_Enclosure/Rigid_Air_Barriers"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def list_all_files(path_prefix):
    """List all files recursively."""
    all_files = []
    result = supabase.storage.from_(BUCKET).list(path_prefix, {"limit": 1000})
    if not result:
        return all_files
    for item in result:
        item_path = f"{path_prefix}/{item['name']}"
        if item.get('metadata') is None:
            all_files.extend(list_all_files(item_path))
        else:
            all_files.append(item_path)
    return all_files

def build_tree(files):
    """Build tree structure."""
    tree = defaultdict(lambda: {"files": [], "subfolders": defaultdict(list)})
    
    for file_path in files:
        relative = file_path.replace(f"{TARGET_PATH}/", "")
        parts = relative.split("/")
        
        if len(parts) == 1:
            tree["_root"]["files"].append(parts[0])
        else:
            manufacturer = parts[0]
            if len(parts) == 2:
                tree[manufacturer]["files"].append(parts[1])
            else:
                subfolder = parts[1]
                filename = "/".join(parts[2:])
                tree[manufacturer]["subfolders"][subfolder].append(filename)
    
    return tree

def print_tree(tree):
    """Print tree structure."""
    print("\n" + "="*70)
    print("📁 /B_Enclosure/Rigid_Air_Barriers/")
    print("="*70)
    
    total_files = 0
    
    for manufacturer in sorted(tree.keys()):
        if manufacturer == "_root":
            continue
            
        data = tree[manufacturer]
        root_files = len(data.get("files", []))
        subfolders = data.get("subfolders", {})
        
        subfolder_files = sum(len(files) for files in subfolders.values())
        mfr_total = root_files + subfolder_files
        total_files += mfr_total
        
        print(f"\n├── 📂 {manufacturer}/ ({mfr_total} files)")
        
        for subfolder in sorted(subfolders.keys()):
            files = subfolders[subfolder]
            print(f"│   ├── 📁 {subfolder}/ ({len(files)} files)")
            for f in sorted(files)[:3]:
                print(f"│   │   ├── 📄 {f[:55]}...")
            if len(files) > 3:
                print(f"│   │   └── ... and {len(files)-3} more")
    
    print(f"\n{'='*70}")
    print(f"📊 TOTAL FILES: {total_files}")
    print("="*70)

def compliance_checks(tree, all_files):
    """Run compliance checks."""
    print("\n" + "="*70)
    print("🛡️ COMPLIANCE VERIFICATION CHECKS")
    print("="*70)
    
    issues = []
    
    # Check 1: GIB_Weatherline populated
    print("\n✅ CHECK 1: GIB_Weatherline populated?")
    gib = tree.get("GIB_Weatherline", {})
    gib_files = len(gib.get("files", [])) + sum(len(f) for f in gib.get("subfolders", {}).values())
    if gib_files > 0:
        print(f"   ✅ PASS - {gib_files} files found")
        # Check for monolith in 00_General_Resources
        if "00_General_Resources" in gib.get("subfolders", {}):
            monolith = [f for f in gib["subfolders"]["00_General_Resources"] if "Master" in f or "Manual" in f]
            if monolith:
                print(f"   ✅ Rule 8 Monolith: {monolith[0][:50]}...")
    else:
        print(f"   ❌ FAIL - No files found")
        issues.append("GIB_EMPTY")
    
    # Check 2: James_Hardie_RAB populated with separation
    print("\n✅ CHECK 2: James_Hardie_RAB with HomeRAB/RAB Board separation?")
    hardie = tree.get("James_Hardie_RAB", {})
    hardie_subs = hardie.get("subfolders", {})
    hardie_files = len(hardie.get("files", [])) + sum(len(f) for f in hardie_subs.values())
    
    if hardie_files > 0:
        print(f"   ✅ PASS - {hardie_files} files found")
        
        homerab = "HomeRAB_PreClad" in hardie_subs
        rabboard = "RAB_Board" in hardie_subs
        
        if homerab and rabboard:
            print(f"   ✅ Rule 1 Separation:")
            print(f"      - HomeRAB_PreClad/ ({len(hardie_subs.get('HomeRAB_PreClad', []))} files)")
            print(f"      - RAB_Board/ ({len(hardie_subs.get('RAB_Board', []))} files)")
        elif homerab or rabboard:
            print(f"   ⚠️ PARTIAL - Only one product folder found")
        else:
            print(f"   ❌ FAIL - No product separation!")
            issues.append("HARDIE_NO_SEPARATION")
    else:
        print(f"   ❌ FAIL - No files found")
        issues.append("HARDIE_EMPTY")
    
    # Check 3: IBS_RigidRAP has installation docs
    print("\n✅ CHECK 3: IBS_RigidRAP has installation documentation?")
    ibs = tree.get("IBS_RigidRAP", {})
    ibs_subs = ibs.get("subfolders", {})
    ibs_files = len(ibs.get("files", [])) + sum(len(f) for f in ibs_subs.values())
    
    if ibs_files > 0:
        print(f"   ✅ PASS - {ibs_files} files found")
        if "Installation" in ibs_subs:
            print(f"      - Installation/ ({len(ibs_subs['Installation'])} files)")
    else:
        print(f"   ⚠️ WARNING - No files found (website blocked downloads)")
        issues.append("IBS_EMPTY")
    
    # Check 4: Ecoply_Barrier populated with tape system
    print("\n✅ CHECK 4: Ecoply_Barrier populated with Tape_System?")
    ecoply = tree.get("Ecoply_Barrier", {})
    ecoply_subs = ecoply.get("subfolders", {})
    ecoply_files = len(ecoply.get("files", [])) + sum(len(f) for f in ecoply_subs.values())
    
    if ecoply_files > 0:
        print(f"   ✅ PASS - {ecoply_files} files found")
        if "Tape_System" in ecoply_subs:
            print(f"   ✅ Rule 6 Tape System: {len(ecoply_subs['Tape_System'])} files")
    else:
        print(f"   ❌ FAIL - No files found")
        issues.append("ECOPLY_EMPTY")
    
    # Final verdict
    print("\n" + "="*70)
    if issues:
        print(f"⚠️ AUDIT RESULT: {len(issues)} ISSUE(S)")
        for i in issues:
            print(f"   - {i}")
    else:
        print("✅ AUDIT RESULT: ALL CHECKS PASSED")
    print("="*70)
    
    return issues

# Main
print("🔍 STRYDA Quality Audit: Rigid Air Barriers")
print("="*70)

print("\n📥 Fetching files from Supabase Storage...")
all_files = list_all_files(TARGET_PATH)
print(f"   Found {len(all_files)} files")

tree = build_tree(all_files)
print_tree(tree)

issues = compliance_checks(tree, all_files)

if not issues:
    print("\n" + "✅"*35)
    print("AUDIT COMPLETE: ALL COMPLIANCE CHECKS PASSED!")
    print("✅"*35)
