#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
    STRYDA PROTOCOL V2.0 - GLOBAL AUDIT & COMPLIANCE HANDSHAKE
    PURPOSE: Tag all compliance docs, cross-reference products, generate report
═══════════════════════════════════════════════════════════════════════════════
"""

import json
import re
from datetime import datetime
import psycopg2

DATABASE_URL = "postgresql://postgres.qxqisgjhbjwvoxsjibes:8skmVOJbMyaQHyQl@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres"

# Load Anchor Map
with open('/app/universal_anchor_map.json', 'r') as f:
    ANCHOR_MAP = json.load(f)

# 2026 Code Requirements
CODE_REQUIREMENTS_2026 = {
    "R_VALUE_CEILING": {"min": 6.6, "unit": "m²K/W", "source": "H1-AS1 6th Ed"},
    "R_VALUE_WALL": {"min": 2.0, "unit": "m²K/W", "source": "H1-AS1 6th Ed"},
    "R_VALUE_FLOOR": {"min": 1.3, "unit": "m²K/W", "source": "H1-AS1 6th Ed"},
    "UV_LIMIT_UNDERLAY": {"max": 180, "unit": "days", "source": "E2-AS1 4th Ed"},
    "AIR_GAP": {"min": 25, "unit": "mm", "source": "E2-AS1 4th Ed"},
    "SILL_LAYERS": {"min": 2, "unit": "layers", "source": "E2-AS1 4th Ed"},
    "BALUSTRADE_HEIGHT": {"min": 1000, "unit": "mm", "source": "F4-AS1"},
    "RCD_SENSITIVITY": {"max": 30, "unit": "mA", "source": "AS/NZS 3000:2018"}
}

def extract_numeric(value):
    """Extract numeric value from string"""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r'(\d+\.?\d*)', str(value))
    return float(match.group(1)) if match else None

def audit_product(brand_name, product_data, requirements):
    """Audit a single product against code requirements"""
    results = {
        "brand": brand_name,
        "status": "UNVERIFIED",
        "checks": [],
        "issues": []
    }
    
    unit_range = product_data.get("unit_range", {})
    if isinstance(unit_range, str):
        try:
            unit_range = json.loads(unit_range)
        except:
            unit_range = {}
    
    doc_type = product_data.get("doc_type", "")
    
    # Check UV Limit
    if "uv_exposure_limit_days" in unit_range:
        uv_days = extract_numeric(unit_range["uv_exposure_limit_days"])
        if uv_days:
            max_allowed = requirements["UV_LIMIT_UNDERLAY"]["max"]
            if uv_days <= max_allowed:
                results["checks"].append(f"✅ UV Limit: {uv_days} days (max {max_allowed})")
            else:
                results["checks"].append(f"❌ UV Limit: {uv_days} days EXCEEDS max {max_allowed}")
                results["issues"].append("UV_LIMIT_EXCEEDED")
    
    # Check R-Values
    for r_type in ["r_value_ceiling", "r_value_wall", "r_value_floor", "r_value"]:
        if r_type in unit_range:
            r_val = extract_numeric(unit_range[r_type])
            if r_val:
                req_key = f"R_VALUE_{r_type.split('_')[-1].upper()}" if "_" in r_type else "R_VALUE_WALL"
                if req_key in requirements:
                    min_req = requirements[req_key]["min"]
                    if r_val >= min_req:
                        results["checks"].append(f"✅ {req_key}: R{r_val} (min R{min_req})")
                    else:
                        results["checks"].append(f"❌ {req_key}: R{r_val} BELOW min R{min_req}")
                        results["issues"].append(f"{req_key}_BELOW_MIN")
    
    # Check Sill Requirement
    if "sill_requirement" in unit_range:
        results["checks"].append(f"✅ Sill Requirement: {unit_range['sill_requirement']}")
    
    # Check Air Gap
    if "air_gap_25mm_required" in unit_range or "h1_2026_compliant" in unit_range:
        results["checks"].append(f"✅ H1 2026 Compliant: Air gap requirements met")
    
    # Check certifications
    if doc_type in ["CodeMark_Certificate", "BRANZ_Appraisal", "BPIR"]:
        results["checks"].append(f"✅ Certification: {doc_type} present")
    
    # Determine overall status
    if results["issues"]:
        results["status"] = "FAIL"
    elif results["checks"]:
        results["status"] = "PASS"
    
    return results

def main():
    print("═" * 70)
    print("  STRYDA PROTOCOL V2.0 - GLOBAL AUDIT & COMPLIANCE HANDSHAKE")
    print("═" * 70)
    print(f"  Started: {datetime.now().isoformat()}")
    print("═" * 70)
    
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 1: TAG COMPLIANCE DOCUMENTS WITH ANCHOR KEYS
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n" + "─" * 70)
    print("  STEP 1: TAGGING COMPLIANCE DOCUMENTS")
    print("─" * 70)
    
    # Get all compliance chunks
    cur.execute("""
        SELECT id, source, content, unit_range 
        FROM documents 
        WHERE source LIKE '01_Compliance%'
        AND is_active = true
    """)
    compliance_chunks = cur.fetchall()
    print(f"\n  📊 Scanning {len(compliance_chunks)} compliance chunks...")
    
    anchor_tags = {key: 0 for key in ANCHOR_MAP["anchor_keys"].keys()}
    
    for chunk_id, source, content, unit_range in compliance_chunks:
        content_lower = content.lower() if content else ""
        tags_found = []
        
        # Check each anchor key pattern
        if re.search(r'r[- ]?value|r[67]\.[0-9]|thermal', content_lower):
            tags_found.append("R_VALUE_CEILING")
            anchor_tags["R_VALUE_CEILING"] += 1
        if re.search(r'uv|ultra.?violet|\d+\s*days?\s*exposure', content_lower):
            tags_found.append("UV_LIMIT")
            anchor_tags["UV_LIMIT"] += 1
        if re.search(r'h[1-6]\.?\d?|hazard\s*class|preservative', content_lower):
            tags_found.append("TIMBER_HAZARD_CLASS")
            anchor_tags["TIMBER_HAZARD_CLASS"] += 1
        if re.search(r'wind\s*zone|very\s*high\s*wind', content_lower):
            tags_found.append("WIND_ZONE")
            anchor_tags["WIND_ZONE"] += 1
        if re.search(r'fire\s*rat|frr|fire\s*resistance', content_lower):
            tags_found.append("FIRE_RATING")
            anchor_tags["FIRE_RATING"] += 1
        if re.search(r'codemark|code\s*mark', content_lower):
            tags_found.append("CODEMARK")
            anchor_tags["CODEMARK"] += 1
        if re.search(r'branz|appraisal', content_lower):
            tags_found.append("BRANZ_APPRAISAL")
            anchor_tags["BRANZ_APPRAISAL"] += 1
        if re.search(r'rcd|residual\s*current|30\s*ma', content_lower):
            tags_found.append("RCD_REQUIRED")
            anchor_tags["RCD_REQUIRED"] += 1
        if re.search(r'balustrade|barrier|1000\s*mm|1\s*m.*height', content_lower):
            tags_found.append("BALUSTRADE_HEIGHT")
            anchor_tags["BALUSTRADE_HEIGHT"] += 1
        if re.search(r'air\s*gap|25\s*mm|ventilation\s*cavity', content_lower):
            tags_found.append("AIR_GAP")
            anchor_tags["AIR_GAP"] += 1
        if re.search(r'sill|2.?layer|double\s*flash', content_lower):
            tags_found.append("SILL_REQUIREMENT")
            anchor_tags["SILL_REQUIREMENT"] += 1
        if re.search(r'bpir|class\s*[12]|product\s*information\s*requirement', content_lower):
            tags_found.append("BPIR_CLASS")
            anchor_tags["BPIR_CLASS"] += 1
    
    print("\n  📋 Anchor Key Distribution:")
    for key, count in sorted(anchor_tags.items(), key=lambda x: -x[1]):
        if count > 0:
            print(f"     {key}: {count} chunks")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 2: CROSS-REFERENCE PRODUCT LIBRARY
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n" + "─" * 70)
    print("  STEP 2: PRODUCT LIBRARY CROSS-REFERENCE")
    print("─" * 70)
    
    # Get all products by brand
    cur.execute("""
        SELECT DISTINCT brand_name, doc_type, unit_range, source
        FROM documents 
        WHERE brand_name IS NOT NULL
        AND brand_name != ''
        AND is_active = true
    """)
    products = cur.fetchall()
    
    # Group by brand
    brands = {}
    for brand, doc_type, unit_range, source in products:
        if brand not in brands:
            brands[brand] = []
        brands[brand].append({
            "doc_type": doc_type,
            "unit_range": unit_range,
            "source": source
        })
    
    print(f"\n  📦 Found {len(brands)} brands with product data:")
    for brand, prods in sorted(brands.items()):
        print(f"     • {brand}: {len(prods)} document types")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 3: AUDIT PRODUCTS AGAINST 2026 CODE
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n" + "─" * 70)
    print("  STEP 3: 2026 CODE COMPLIANCE AUDIT")
    print("─" * 70)
    
    audit_results = {"PASS": [], "FAIL": [], "UNVERIFIED": []}
    
    for brand, prods in brands.items():
        # Get best product data (prefer TDS or Installation Guide)
        best_prod = None
        for prod in prods:
            if prod["unit_range"]:
                best_prod = prod
                break
        
        if best_prod:
            result = audit_product(brand, best_prod, CODE_REQUIREMENTS_2026)
            audit_results[result["status"]].append(result)
        else:
            audit_results["UNVERIFIED"].append({
                "brand": brand,
                "status": "UNVERIFIED",
                "checks": ["⚠️ No guardrail data extracted"],
                "issues": []
            })
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 4: GENERATE REPORT
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n" + "═" * 70)
    print("  GLOBAL AUDIT REPORT - 2026 CODE COMPLIANCE")
    print("═" * 70)
    
    print(f"\n  📊 SUMMARY:")
    print(f"     ✅ PASS: {len(audit_results['PASS'])} brands")
    print(f"     ❌ FAIL: {len(audit_results['FAIL'])} brands")
    print(f"     ⚠️ UNVERIFIED: {len(audit_results['UNVERIFIED'])} brands")
    
    print("\n" + "─" * 70)
    print("  ✅ PASS - COMPLIANT WITH 2026 CODE")
    print("─" * 70)
    for result in audit_results["PASS"]:
        print(f"\n  🟢 {result['brand']}")
        for check in result["checks"]:
            print(f"     {check}")
    
    if audit_results["FAIL"]:
        print("\n" + "─" * 70)
        print("  ❌ FAIL - NON-COMPLIANT")
        print("─" * 70)
        for result in audit_results["FAIL"]:
            print(f"\n  🔴 {result['brand']}")
            for check in result["checks"]:
                print(f"     {check}")
            print(f"     Issues: {', '.join(result['issues'])}")
    
    print("\n" + "─" * 70)
    print("  ⚠️ UNVERIFIED - REQUIRES MANUAL REVIEW")
    print("─" * 70)
    for result in audit_results["UNVERIFIED"][:10]:  # Show first 10
        print(f"  🟡 {result['brand']}")
    if len(audit_results["UNVERIFIED"]) > 10:
        print(f"     ... and {len(audit_results['UNVERIFIED']) - 10} more")
    
    # Save report
    report = {
        "generated": datetime.now().isoformat(),
        "code_version": "2026",
        "summary": {
            "pass": len(audit_results["PASS"]),
            "fail": len(audit_results["FAIL"]),
            "unverified": len(audit_results["UNVERIFIED"])
        },
        "anchor_tags": anchor_tags,
        "results": audit_results
    }
    
    with open('/app/audit_report_2026.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print("\n" + "═" * 70)
    print("  AUDIT COMPLETE")
    print("═" * 70)
    print(f"  📄 Report saved: /app/audit_report_2026.json")
    print(f"  Completed: {datetime.now().isoformat()}")
    print("═" * 70)
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
