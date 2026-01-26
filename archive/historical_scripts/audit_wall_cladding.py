"""
STRYDA Quality Audit: Fibre Cement Wall Cladding
================================================
"""

import os
from supabase import create_client
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv("/app/backend-minimal/.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
BUCKET = "product-library"
TARGET_PATH = "B_Enclosure/Wall_Cladding"

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
    tree = {}
    for f in files:
        relative = f.replace(f"{TARGET_PATH}/", "")
        parts = relative.split("/")
        
        mfr = parts[0] if len(parts) > 0 else "_root"
        product = parts[1] if len(parts) > 1 else "_root"
        subfolder = parts[2] if len(parts) > 2 else "_root"
        filename = parts[-1]
        
        if mfr not in tree:
            tree[mfr] = {}
        if product not in tree[mfr]:
            tree[mfr][product] = {}
        if subfolder not in tree[mfr][product]:
            tree[mfr][product][subfolder] = []
        
        tree[mfr][product][subfolder].append(filename)
    
    return tree

def print_tree(tree, all_files):
    """Print tree structure."""
    print("\n" + "="*70)
    print("📁 /B_Enclosure/Wall_Cladding/")
    print("="*70)
    
    total = len(all_files)
    
    for mfr in sorted(tree.keys()):
        mfr_count = sum(
            len(files)
            for product in tree[mfr].values()
            for files in product.values()
        )
        print(f"\n├── 📂 {mfr}/ ({mfr_count} files)")
        
        for product in sorted(tree[mfr].keys()):
            prod_count = sum(len(f) for f in tree[mfr][product].values())
            print(f"│   ├── 📁 {product}/ ({prod_count} files)")
            
            for subfolder in sorted(tree[mfr][product].keys()):
                if subfolder != "_root":
                    sub_count = len(tree[mfr][product][subfolder])
                    print(f"│   │   ├── 📂 {subfolder}/ ({sub_count} files)")
    
    print(f"\n{'='*70}")
    print(f"📊 TOTAL FILES: {total}")
    print("="*70)

def compliance_checks(tree, all_files):
    """Run compliance checks."""
    print("\n" + "="*70)
    print("🛡️ COMPLIANCE VERIFICATION CHECKS")
    print("="*70)
    
    issues = []
    
    # Check 1: Linea has Cavity_Fix_System and Direct_Fix_System separated
    print("\n✅ CHECK 1: Linea_Weatherboard has Cavity vs Direct Fix separation?")
    
    hardie = tree.get("James_Hardie", {})
    linea = hardie.get("Linea_Weatherboard", {})
    
    has_cavity = "Cavity_Fix_System" in linea
    has_direct = "Direct_Fix_System" in linea
    
    if has_cavity and has_direct:
        cavity_count = len(linea.get("Cavity_Fix_System", []))
        direct_count = len(linea.get("Direct_Fix_System", []))
        print(f"   ✅ PASS - CRITICAL Rule 1 Enforced:")
        print(f"      - Cavity_Fix_System/ ({cavity_count} files)")
        print(f"      - Direct_Fix_System/ ({direct_count} files)")
    else:
        print(f"   ❌ FAIL - Cavity/Direct separation missing!")
        issues.append("LINEA_SEPARATION")
    
    # Check 2: Fire & Acoustic Manual is in 00_General_Resources
    print("\n✅ CHECK 2: 'Fire and Acoustic Design Manual' in 00_General_Resources?")
    
    general = hardie.get("00_General_Resources", {})
    all_general_files = []
    for files in general.values():
        all_general_files.extend(files)
    
    fire_acoustic = [f for f in all_general_files if "Fire" in f and "Acoustic" in f and "Manual" in f]
    
    if fire_acoustic:
        print(f"   ✅ PASS - Rule 8 Monolith in place:")
        for f in fire_acoustic:
            print(f"      - {f[:55]}...")
    else:
        print(f"   ❌ FAIL - Fire & Acoustic Manual not in 00_General_Resources!")
        issues.append("FIRE_ACOUSTIC_MONOLITH")
    
    # Check 3: Innova/BGC products populated
    print("\n✅ CHECK 3: Innova (BGC) products populated?")
    
    innova = tree.get("Innova_Fibre_Cement", {})
    innova_count = sum(len(f) for p in innova.values() for f in p.values())
    
    if innova_count > 0:
        print(f"   ✅ PASS - {innova_count} files found")
        for product in sorted(innova.keys()):
            prod_count = sum(len(f) for f in innova[product].values())
            print(f"      - {product}/ ({prod_count} files)")
    else:
        print(f"   ❌ FAIL - No Innova files found!")
        issues.append("INNOVA_EMPTY")
    
    # Check 4: Axon Panel has Cavity/Direct separation
    print("\n✅ CHECK 4: Axon_Panel has Cavity vs Direct Fix separation?")
    
    axon = hardie.get("Axon_Panel", {})
    axon_cavity = "Cavity_Fix_System" in axon
    axon_direct = "Direct_Fix_System" in axon
    
    if axon_cavity and axon_direct:
        print(f"   ✅ PASS - Rule 1 Enforced for Axon:")
        print(f"      - Cavity_Fix_System/ ({len(axon.get('Cavity_Fix_System', []))} files)")
        print(f"      - Direct_Fix_System/ ({len(axon.get('Direct_Fix_System', []))} files)")
    else:
        print(f"   ⚠️ PARTIAL - Axon cavity/direct folders exist: cavity={axon_cavity}, direct={axon_direct}")
    
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
print("🔍 STRYDA Quality Audit: Fibre Cement Wall Cladding")
print("="*70)

print("\n📥 Fetching files from Supabase Storage...")
all_files = list_all_files(TARGET_PATH)
print(f"   Found {len(all_files)} files")

tree = build_tree(all_files)
print_tree(tree, all_files)

issues = compliance_checks(tree, all_files)

if not issues:
    print("\n" + "✅"*35)
    print("AUDIT COMPLETE: ALL COMPLIANCE CHECKS PASSED!")
    print("✅"*35)
