"""
STRYDA Quality Audit: Translucent Roofing
=========================================
Displays full directory tree with file counts and compliance checks.
"""

import os
from supabase import create_client
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv("/app/backend-minimal/.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
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
    tree = defaultdict(lambda: {"files": [], "subfolders": defaultdict(list)})
    
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
        subfolder_list = sorted(subfolders.keys())
        for i, subfolder in enumerate(subfolder_list):
            files = subfolders[subfolder]
            is_last_subfolder = (i == len(subfolder_list) - 1) and root_files == 0
            prefix = "└──" if is_last_subfolder else "├──"
            print(f"│   {prefix} 📁 {subfolder}/ ({len(files)} files)")
            for j, f in enumerate(sorted(files)[:5]):
                file_prefix = "    └──" if j == min(4, len(files)-1) else "    ├──"
                print(f"│   │   {file_prefix} 📄 {f}")
            if len(files) > 5:
                print(f"│   │       └── ... and {len(files)-5} more files")
        
        # Print root files
        if root_files > 0:
            print(f"│   └── [Root Files: {root_files}]")
            for i, f in enumerate(sorted(data["files"])[:3]):
                file_prefix = "└──" if i == min(2, root_files-1) else "├──"
                print(f"│       {file_prefix} 📄 {f}")
            if root_files > 3:
                print(f"│           └── ... and {root_files-3} more files")
    
    print(f"\n{'='*70}")
    print(f"📊 TOTAL FILES: {total_files}")
    print("="*70)

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
    
    # Check within Alsynite for product lines
    alsynite_subs = tree.get("Alsynite_One", {}).get("subfolders", {})
    laserlite_in_alsynite = [k for k in alsynite_subs.keys() if "Laserlite" in k]
    topglass_in_alsynite = [k for k in alsynite_subs.keys() if "Topglass" in k]
    
    # Also check as top-level manufacturers
    laserlite_toplevel = "Laserlite_2000" in tree
    topglass_toplevel = "Topglass_Industrial" in tree
    
    if laserlite_in_alsynite and topglass_in_alsynite:
        print(f"   ✅ PASS - Both product lines found as separate subfolders in Alsynite_One:")
        for k in laserlite_in_alsynite + topglass_in_alsynite:
            print(f"      - {k}/ ({len(alsynite_subs[k])} files)")
    elif laserlite_toplevel or topglass_toplevel:
        print(f"   ⚠️ NOTE - Found as top-level manufacturers:")
        if laserlite_toplevel:
            print(f"      - /Laserlite_2000/ exists")
        if topglass_toplevel:
            print(f"      - /Topglass_Industrial/ exists")
    else:
        # Search for keywords in any file paths
        laserlite_files = [f for f in all_files if "laserlite" in f.lower() or "laser" in f.lower()]
        topglass_files = [f for f in all_files if "topglass" in f.lower()]
        
        if laserlite_files or topglass_files:
            print(f"   ⚠️ PARTIAL - Found in file names:")
            print(f"      - Laserlite files: {len(laserlite_files)}")
            print(f"      - Topglass files: {len(topglass_files)}")
        else:
            print(f"   ❌ FAIL - Neither product line found!")
            issues.append("CHECK_B")
    
    # Check C: Is the "Noise Stop Tape" manual present?
    print("\n✅ CHECK C: 'Noise Stop Tape' manual in /Ampelite_NZ/ or /PSP_Limited/?")
    
    ampelite_files = [f for f in all_files if "Ampelite" in f]
    psp_files = [f for f in all_files if "PSP" in f]
    
    noise_in_ampelite = [f for f in ampelite_files if "noise" in f.lower() or "noisestop" in f.lower().replace("_", "")]
    noise_in_psp = [f for f in psp_files if "noise" in f.lower() or "noisestop" in f.lower().replace("_", "")]
    
    # Also check for tape-related files
    tape_files = [f for f in all_files if "tape" in f.lower()]
    
    if noise_in_ampelite:
        print(f"   ✅ PASS - Found in Ampelite_NZ:")
        for f in noise_in_ampelite[:3]:
            print(f"      - {f.split('/')[-1]}")
    elif noise_in_psp:
        print(f"   ✅ PASS - Found in PSP_Limited:")
        for f in noise_in_psp[:3]:
            print(f"      - {f.split('/')[-1]}")
    else:
        # Search broadly
        all_noise = [f for f in all_files if "noise" in f.lower()]
        if all_noise:
            print(f"   ⚠️ PARTIAL - Found elsewhere ({len(all_noise)} files):")
            for f in all_noise[:3]:
                print(f"      - {f}")
        elif tape_files:
            print(f"   ⚠️ PARTIAL - 'Tape' files found ({len(tape_files)}):")
            for f in tape_files[:3]:
                print(f"      - {f}")
        else:
            print(f"   ❌ FAIL - 'Noise Stop Tape' manual NOT found!")
            issues.append("CHECK_C")
    
    # Check for flat structure (no subfolders at all)
    print("\n✅ CHECK D: Structure has proper sub-organization?")
    manufacturers_with_subfolders = sum(1 for m in tree if m != "_root" and tree[m].get("subfolders"))
    total_manufacturers = sum(1 for m in tree if m != "_root")
    
    if manufacturers_with_subfolders == 0:
        print(f"   🚨 CRITICAL: FLAT STRUCTURE - No manufacturer has sub-folders!")
        issues.append("FLAT_STRUCTURE")
    elif manufacturers_with_subfolders < total_manufacturers:
        print(f"   ⚠️ PARTIAL: {manufacturers_with_subfolders}/{total_manufacturers} manufacturers have sub-folders")
        flat_mfrs = [m for m in tree if m != "_root" and not tree[m].get("subfolders")]
        for m in flat_mfrs:
            print(f"      - ⚠️ {m}/ has no sub-organization")
    else:
        print(f"   ✅ PASS - All {total_manufacturers} manufacturers have proper sub-folders")
    
    # Final verdict
    print("\n" + "="*70)
    if issues:
        print(f"⚠️ AUDIT RESULT: {len(issues)} COMPLIANCE ISSUE(S) DETECTED")
        print(f"   Issues: {', '.join(issues)}")
    else:
        print("✅ AUDIT RESULT: ALL CHECKS PASSED")
    print("="*70)
    
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
else:
    print("\n" + "✅"*35)
    print("AUDIT COMPLETE: Structure is compliant!")
    print("✅"*35)
