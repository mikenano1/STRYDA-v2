"""
STRYDA Quality Audit: Translucent Roofing (Final)
=================================================
"""

import os
import requests
import fitz
from supabase import create_client
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv("/app/backend-minimal/.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
BUCKET = "product-library"
TARGET_PATH = "B_Enclosure/Translucent_Roofing"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def list_all_files(path_prefix):
    """List all files recursively under a path."""
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
    """Build a tree structure from file paths."""
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
        
        for subfolder in sorted(subfolders.keys()):
            files = subfolders[subfolder]
            print(f"│   ├── 📁 {subfolder}/ ({len(files)} files)")
    
    print(f"\n{'='*70}")
    print(f"📊 TOTAL FILES: {total_files}")
    print("="*70)

def check_pdf_for_antinoise(filepath):
    """Check if a PDF contains Anti-Noise Tape content."""
    try:
        result = supabase.storage.from_(BUCKET).create_signed_url(filepath, 60)
        response = requests.get(result['signedURL'], timeout=15)
        
        if response.status_code == 200:
            with open("/tmp/test.pdf", "wb") as f:
                f.write(response.content)
            
            doc = fitz.open("/tmp/test.pdf")
            full_text = ""
            for page in doc:
                full_text += page.get_text().lower()
            
            if 'anti-noise' in full_text or 'antinoise' in full_text:
                return True, "anti-noise"
            elif 'noise' in full_text and 'tape' in full_text:
                return True, "noise tape"
            elif 'foam tape' in full_text:
                return True, "foam tape"
    except:
        pass
    return False, None

def compliance_checks(tree, all_files):
    """Run compliance verification checks."""
    print("\n" + "="*70)
    print("🛡️ COMPLIANCE VERIFICATION CHECKS")
    print("="*70)
    
    issues = []
    
    # Check A
    print("\n✅ CHECK A: /Alsynite_One/00_General_Resources/ exists?")
    alsynite_folders = tree.get("Alsynite_One", {}).get("subfolders", {})
    if "00_General_Resources" in alsynite_folders:
        files = alsynite_folders["00_General_Resources"]
        print(f"   ✅ PASS - Found with {len(files)} files")
    else:
        print(f"   ❌ FAIL")
        issues.append("CHECK_A")
    
    # Check B
    print("\n✅ CHECK B: /Laserlite_2000/ and /Topglass_Industrial/ separated?")
    alsynite_subs = tree.get("Alsynite_One", {}).get("subfolders", {})
    laserlite = [k for k in alsynite_subs.keys() if "Laserlite" in k]
    topglass = [k for k in alsynite_subs.keys() if "Topglass" in k]
    
    if laserlite and topglass:
        print(f"   ✅ PASS - Both product lines clearly separated:")
        print(f"      - {laserlite[0]}/ ({len(alsynite_subs[laserlite[0]])} files)")
        print(f"      - {topglass[0]}/ ({len(alsynite_subs[topglass[0]])} files)")
    else:
        print(f"   ❌ FAIL")
        issues.append("CHECK_B")
    
    # Check C - Deep content scan
    print("\n✅ CHECK C: 'Anti-Noise Tape' content in /Ampelite_NZ/ or /PSP_Suntuf/?")
    print("   🔍 Scanning PDF content for Anti-Noise Tape references...")
    
    ampelite_files = [f for f in all_files if "Ampelite" in f]
    psp_files = [f for f in all_files if "PSP" in f]
    
    found_in = []
    for filepath in ampelite_files + psp_files:
        found, keyword = check_pdf_for_antinoise(filepath)
        if found:
            found_in.append((filepath.split("/")[-1], keyword))
    
    if found_in:
        print(f"   ✅ PASS - Anti-Noise Tape content found in {len(found_in)} documents:")
        for filename, kw in found_in[:4]:
            print(f"      - {filename[:55]}... ({kw})")
        if len(found_in) > 4:
            print(f"      - ... and {len(found_in)-4} more")
    else:
        print(f"   ❌ FAIL - No Anti-Noise Tape content found")
        issues.append("CHECK_C")
    
    # Check D
    print("\n✅ CHECK D: Structure has proper sub-organization?")
    manufacturers = [m for m in tree if m != "_root"]
    with_subfolders = sum(1 for m in manufacturers if tree[m].get("subfolders"))
    
    if with_subfolders == len(manufacturers):
        print(f"   ✅ PASS - All {len(manufacturers)} manufacturers have sub-folders")
    else:
        print(f"   ❌ FAIL")
        issues.append("CHECK_D")
    
    # Final verdict
    print("\n" + "="*70)
    if issues:
        print(f"⚠️ AUDIT RESULT: {len(issues)} COMPLIANCE ISSUE(S)")
    else:
        print("✅ AUDIT RESULT: ALL CHECKS PASSED")
    print("="*70)
    
    return issues

# Main
print("🔍 STRYDA Quality Audit: Translucent Roofing (FINAL)")
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
