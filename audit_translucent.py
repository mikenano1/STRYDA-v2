"""
STRYDA Quality Audit: Translucent Roofing
=========================================
Displays full directory tree with file counts and compliance checks.
"""

import os
from supabase import create_client
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
BUCKET = "product-library"
TARGET_PATH = "B_Enclosure/Translucent_Roofing"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def list_all_files(path_prefix):
    """List all files recursively under a path."""
    all_files = []
    offset = 0
    limit = 1000
    
    while True:
        result = supabase.storage.from_(BUCKET).list(
            path_prefix,
            {"limit": limit, "offset": offset}
        )
        if not result:
            break
        
        for item in result:
            item_path = f"{path_prefix}/{item['name']}"
            if item.get('metadata') is None:  # It's a folder
                # Recurse into folder
                sub_files = list_all_files(item_path)
                all_files.extend(sub_files)
            else:
                all_files.append(item_path)
        
        if len(result) < limit:
            break
        offset += limit
    
    return all_files

def build_tree(files):
    """Build a tree structure from file paths."""
    tree = defaultdict(lambda: {"files": [], "subfolders": defaultdict(dict)})
    
    for file_path in files:
        # Remove the base path
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
                if subfolder not in tree[manufacturer]["subfolders"]:
                    tree[manufacturer]["subfolders"][subfolder] = []
                tree[manufacturer]["subfolders"][subfolder].append(filename)
    
    return tree

def print_tree(tree):
    """Print the tree structure with counts."""
    print("\n" + "="*70)
    print("📁 /B_Enclosure/Translucent_Roofing/")
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
        
        # Print subfolders
        for subfolder in sorted(subfolders.keys()):
            files = subfolders[subfolder]
            print(f"│   ├── 📁 {subfolder}/ ({len(files)} files)")
            for f in sorted(files)[:5]:  # Show first 5 files
                print(f"│   │   ├── 📄 {f}")
            if len(files) > 5:
                print(f"│   │   └── ... and {len(files)-5} more files")
        
        # Print root files
        if root_files > 0:
            print(f"│   └── [Root Files: {root_files}]")
            for f in sorted(data["files"])[:3]:
                print(f"│       ├── 📄 {f}")
            if root_files > 3:
                print(f"│       └── ... and {root_files-3} more files")
    
    print(f"\n{'='*70}")
    print(f"📊 TOTAL FILES: {total_files}")
    print("="*70)
    
    return tree

def compliance_checks(tree, all_files):
    """Run compliance verification checks."""
    print("\n" + "="*70)
    print("🛡️ COMPLIANCE VERIFICATION CHECKS")
    print("="*70)
    
    issues = []
    
    # Check A: Does /Alsynite_One/00_General_Resources/ exist?
    print("\n✅ CHECK A: /Alsynite_One/00_General_Resources/ exists?")
    alsynite_folders = tree.get("Alsynite_One", {}).get("subfolders", {})
    if "00_General_Resources" in alsynite_folders:
        files = alsynite_folders["00_General_Resources"]
        print(f"   ✅ PASS - Found with {len(files)} files:")
        for f in files[:3]:
            print(f"      - {f}")
    else:
        print(f"   ❌ FAIL - Folder NOT found!")
        print(f"   📁 Available Alsynite_One subfolders: {list(alsynite_folders.keys())}")
        issues.append("CHECK_A")
    
    # Check B: Are /Laserlite_2000/ and /Topglass_Industrial/ clearly separated?
    print("\n✅ CHECK B: /Laserlite_2000/ and /Topglass_Industrial/ separated?")
    
    laserlite_exists = "Laserlite_2000" in tree or any("Laserlite_2000" in f for f in all_files)
    topglass_exists = "Topglass_Industrial" in tree or any("Topglass_Industrial" in f for f in all_files)
    
    # Check within Alsynite for product lines
    alsynite_subs = tree.get("Alsynite_One", {}).get("subfolders", {})
    laserlite_in_alsynite = any("Laserlite" in k for k in alsynite_subs.keys())
    topglass_in_alsynite = any("Topglass" in k for k in alsynite_subs.keys())
    
    if laserlite_in_alsynite and topglass_in_alsynite:
        print(f"   ✅ PASS - Both product lines found as separate subfolders in Alsynite_One:")
        for k in alsynite_subs.keys():
            if "Laserlite" in k or "Topglass" in k:
                print(f"      - {k}/ ({len(alsynite_subs[k])} files)")
    elif laserlite_exists or topglass_exists:
        print(f"   ⚠️ PARTIAL - Found as separate manufacturers (acceptable):")
        print(f"      - Laserlite_2000: {'Found' if laserlite_exists else 'Not Found'}")
        print(f"      - Topglass_Industrial: {'Found' if topglass_exists else 'Not Found'}")
    else:
        print(f"   ❌ FAIL - Neither product line clearly separated!")
        issues.append("CHECK_B")
    
    # Check C: Is the "Noise Stop Tape" manual present?
    print("\n✅ CHECK C: 'Noise Stop Tape' manual in /Ampelite_NZ/ or /PSP_Limited/?")
    
    noise_stop_files = [f for f in all_files if "noise" in f.lower() or "stop" in f.lower() or "tape" in f.lower()]
    
    ampelite_files = [f for f in all_files if "Ampelite" in f]
    psp_files = [f for f in all_files if "PSP" in f]
    
    noise_in_ampelite = [f for f in ampelite_files if "noise" in f.lower() or "tape" in f.lower()]
    noise_in_psp = [f for f in psp_files if "noise" in f.lower() or "tape" in f.lower()]
    
    if noise_in_ampelite:
        print(f"   ✅ PASS - Found in Ampelite_NZ:")
        for f in noise_in_ampelite:
            print(f"      - {f.split('/')[-1]}")
    elif noise_in_psp:
        print(f"   ✅ PASS - Found in PSP_Limited:")
        for f in noise_in_psp:
            print(f"      - {f.split('/')[-1]}")
    elif noise_stop_files:
        print(f"   ⚠️ PARTIAL - Found elsewhere:")
        for f in noise_stop_files[:3]:
            print(f"      - {f}")
    else:
        print(f"   ❌ FAIL - 'Noise Stop Tape' manual NOT found!")
        # Search for any tape-related files
        tape_files = [f for f in all_files if "tape" in f.lower()]
        if tape_files:
            print(f"   📋 Tape-related files found: {tape_files}")
        issues.append("CHECK_C")
    
    # Final verdict
    print("\n" + "="*70)
    if issues:
        print(f"⚠️ AUDIT RESULT: {len(issues)} COMPLIANCE ISSUE(S) DETECTED")
        print(f"   Issues: {', '.join(issues)}")
    else:
        print("✅ AUDIT RESULT: ALL CHECKS PASSED")
    print("="*70)
    
    # Check for flat structure (no subfolders)
    is_flat = all(len(tree.get(m, {}).get("subfolders", {})) == 0 for m in tree if m != "_root")
    if is_flat:
        print("\n🚨 CRITICAL: FLAT STRUCTURE DETECTED - No sub-organization!")
        issues.append("FLAT_STRUCTURE")
    
    return issues

# Main execution
print("🔍 STRYDA Quality Audit: Translucent Roofing")
print("="*70)
print(f"Target: /{TARGET_PATH}/")
print("="*70)

print("\n📥 Fetching file list from Supabase Storage...")
all_files = list_all_files(TARGET_PATH)
print(f"   Found {len(all_files)} files total")

tree = build_tree(all_files)
print_tree(tree)

issues = compliance_checks(tree, all_files)

if issues:
    print("\n" + "🚨"*35)
    print("ACTION REQUIRED: Structure needs correction!")
    print("🚨"*35)
