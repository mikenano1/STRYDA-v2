#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
    SECTOR F: CERTIFICATION LOCKDOWN
    Automated CodeMark & BRANZ Appraisal Verification System
═══════════════════════════════════════════════════════════════════════════════
"""

import os
import re
import json
import csv
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
import psycopg2

DATABASE_URL = "postgresql://postgres.qxqisgjhbjwvoxsjibes:8skmVOJbMyaQHyQl@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres"

# ═══════════════════════════════════════════════════════════════════════════════
# SECTOR F: CERTIFICATION ANCHOR KEYS
# ═══════════════════════════════════════════════════════════════════════════════

CERTIFICATION_ANCHORS = {
    "CodeMark_ID": {
        "description": "CodeMark certificate identification number",
        "format": "CMxxxxxxx or similar",
        "patterns": [
            r"CodeMark.*?([A-Z]{2,3}[-\s]?\d{4,8})",
            r"CM[-\s]?(\d{4,8})",
            r"certificate.*?number.*?([A-Z0-9]{6,12})",
        ],
        "validation": "must_be_active"
    },
    "BRANZ_Appraisal_Number": {
        "description": "BRANZ Appraisal certificate number",
        "format": "Appraisal No. XXX",
        "patterns": [
            r"Appraisal\s*(?:No\.?|Number)?\s*(\d{3,4})",
            r"BRANZ\s*(?:Appraisal)?\s*#?(\d{3,4})",
            r"Technical\s*Appraisal\s*(\d{3,4})",
        ],
        "validation": "must_be_active"
    },
    "Certification_Expiry_Date": {
        "description": "Expiry date of certification",
        "format": "YYYY-MM-DD or Month YYYY",
        "patterns": [
            r"(?:valid|expires?|expiry).*?(\d{1,2}[-/]\d{1,2}[-/]\d{4})",
            r"(?:valid|expires?).*?(?:until|to).*?(\w+\s+\d{4})",
            r"(\d{4}[-/]\d{2}[-/]\d{2})",
            r"(?:November|December|January|February|March|April|May|June|July|August|September|October)\s+\d{4}",
        ],
        "validation": "must_be_future"
    },
    "Appraisal_Scope_Limitations": {
        "description": "Restrictions on where/how product can be used",
        "format": "Text description",
        "patterns": [
            r"(?:scope|limitation|condition|restriction)s?[:\s]+([^.]+\.)",
            r"(?:not\s+suitable|excluded|limited\s+to)[:\s]+([^.]+\.)",
            r"(?:wind\s+zone|fire\s+rating|exposure)[:\s]+([^.]+\.)",
        ],
        "validation": "must_flag_if_restricted"
    }
}

# Known CodeMark patterns by brand
KNOWN_CODEMARK_BRANDS = {
    "Kingspan": ["CM", "CodeMark"],
    "James Hardie": ["CM", "JH"],
    "GIB": ["CodeMark", "CM"],
    "Knauf": ["CM"],
    "Bradford": ["CM"],
}

# Known BRANZ Appraisal patterns
KNOWN_BRANZ_BRANDS = {
    "Marshall": [621, 750],  # Known appraisal numbers
    "Masons": [],
    "Kingspan": [1020, 1021],
    "GIB": [105, 445, 500],
}


def extract_codemark_id(content: str) -> Optional[str]:
    """Extract CodeMark ID from document content"""
    for pattern in CERTIFICATION_ANCHORS["CodeMark_ID"]["patterns"]:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1) if match.lastindex else match.group(0)
    return None


def extract_branz_number(content: str) -> Optional[str]:
    """Extract BRANZ Appraisal number from document content"""
    for pattern in CERTIFICATION_ANCHORS["BRANZ_Appraisal_Number"]["patterns"]:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1) if match.lastindex else match.group(0)
    return None


def extract_expiry_date(content: str) -> Optional[Tuple[str, bool]]:
    """
    Extract expiry date and check if expired.
    Returns: (date_string, is_expired)
    """
    content_lower = content.lower()
    
    # Look for expiry patterns
    date_patterns = [
        (r"(?:valid\s+until|expires?)\s*[:\s]*(\d{1,2})[/-](\d{1,2})[/-](\d{4})", "dmy"),
        (r"(?:valid\s+until|expires?)\s*[:\s]*(\d{4})[/-](\d{2})[/-](\d{2})", "ymd"),
        (r"(?:expiry|valid\s+until)\s*[:\s]*(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})", "my"),
        (r"(\d{4})[/-](\d{2})[/-](\d{2})", "ymd"),  # Generic date
    ]
    
    for pattern, fmt in date_patterns:
        match = re.search(pattern, content_lower)
        if match:
            try:
                if fmt == "dmy":
                    d, m, y = match.groups()
                    exp_date = date(int(y), int(m), int(d))
                elif fmt == "ymd":
                    y, m, d = match.groups()
                    exp_date = date(int(y), int(m), int(d))
                elif fmt == "my":
                    month_names = {"january": 1, "february": 2, "march": 3, "april": 4,
                                   "may": 5, "june": 6, "july": 7, "august": 8,
                                   "september": 9, "october": 10, "november": 11, "december": 12}
                    m = month_names.get(match.group(1), 1)
                    y = int(match.group(2))
                    exp_date = date(y, m, 28)  # End of month approximation
                
                is_expired = exp_date < date.today()
                return (exp_date.isoformat(), is_expired)
            except:
                pass
    
    return None


def extract_scope_limitations(content: str) -> Optional[str]:
    """Extract scope limitations or conditions"""
    limitations = []
    
    # Patterns for limitations
    limit_patterns = [
        r"(?:limitation|condition|restriction)[s]?[:\s]+([^.]{20,200}\.)",
        r"(?:not\s+suitable\s+for|excluded\s+from|limited\s+to)[:\s]+([^.]{10,150}\.)",
        r"(?:wind\s+zone\s+(?:high|very\s+high|extra\s+high)|SED\s+zone|fire\s+zone)\s*[:\s]+([^.]{10,100}\.)",
        r"conditional.*?(?:upon|requires?)[:\s]+([^.]{10,150}\.)",
    ]
    
    for pattern in limit_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        limitations.extend(matches[:2])  # Max 2 per pattern
    
    if limitations:
        return " | ".join(set(limitations[:3]))  # Max 3 total
    return None


def determine_certification_status(codemark: Optional[str], branz: Optional[str], 
                                    expiry: Optional[Tuple], limitations: Optional[str]) -> str:
    """Determine overall certification status"""
    
    if not codemark and not branz:
        return "MISSING"
    
    if expiry and expiry[1]:  # is_expired
        return "EXPIRED"
    
    if limitations and any(word in limitations.lower() for word in ["not suitable", "excluded", "limited to", "conditional"]):
        return "CONDITIONAL"
    
    return "ACTIVE"


def scan_library_certifications():
    """Scan entire library for certification data"""
    
    print("═" * 70)
    print("  SECTOR F: CERTIFICATION LOCKDOWN")
    print("  Scanning entire library for CodeMark & BRANZ data...")
    print("═" * 70)
    
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Get all unique products with their content
    cur.execute("""
        SELECT DISTINCT 
            brand_name,
            source,
            doc_type,
            string_agg(DISTINCT content, ' ') as full_content
        FROM documents 
        WHERE is_active = true
        AND brand_name IS NOT NULL
        GROUP BY brand_name, source, doc_type
        ORDER BY brand_name, source
    """)
    
    products = cur.fetchall()
    print(f"\n📊 Found {len(products)} unique product documents to scan")
    
    results = []
    stats = {"ACTIVE": 0, "EXPIRED": 0, "CONDITIONAL": 0, "MISSING": 0}
    
    for brand, source, doc_type, content in products:
        if not content:
            continue
        
        # Extract certification data
        codemark_id = extract_codemark_id(content)
        branz_number = extract_branz_number(content)
        expiry_data = extract_expiry_date(content)
        scope_limits = extract_scope_limitations(content)
        
        # Determine status
        expiry_date = expiry_data[0] if expiry_data else None
        is_expired = expiry_data[1] if expiry_data else False
        status = determine_certification_status(codemark_id, branz_number, expiry_data, scope_limits)
        
        stats[status] += 1
        
        # Extract product name from source
        product_name = source.split("/")[-1].replace(".pdf", "").strip()
        
        results.append({
            "brand": brand or "Unknown",
            "product": product_name[:50],
            "source": source,
            "doc_type": doc_type or "Unknown",
            "codemark_id": codemark_id or "",
            "branz_number": branz_number or "",
            "expiry_date": expiry_date or "",
            "is_expired": "YES" if is_expired else ("NO" if expiry_date else "UNKNOWN"),
            "scope_limitations": scope_limits or "",
            "status": status,
            "bpir_status": "DECLARED" if doc_type in ["BPIR", "BPIR_Summary"] else "UNDECLARED"
        })
    
    cur.close()
    conn.close()
    
    return results, stats


def update_anchor_map():
    """Update universal_anchor_map.json with Sector F anchors"""
    
    anchor_map_path = "/app/protocols/universal_anchor_map.json"
    
    with open(anchor_map_path, 'r') as f:
        anchor_map = json.load(f)
    
    # Add Sector F certification anchors to anchor_definitions
    if "anchor_definitions" not in anchor_map:
        anchor_map["anchor_definitions"] = {}
    
    anchor_map["anchor_definitions"]["CodeMark_ID"] = {
        "description": "CodeMark certificate identification number",
        "unit": "certificate_id",
        "compliance_sources": ["MBIE", "CodeMark Scheme"],
        "product_categories": ["all"],
        "validation_rule": "has_valid_codemark AND not_expired",
        "format": "CMxxxxxxx or alphanumeric"
    }
    
    anchor_map["anchor_definitions"]["BRANZ_Appraisal_Number"] = {
        "description": "BRANZ Technical Appraisal certificate number",
        "unit": "appraisal_number",
        "compliance_sources": ["BRANZ"],
        "product_categories": ["all"],
        "validation_rule": "has_valid_appraisal AND not_expired",
        "format": "3-4 digit number"
    }
    
    anchor_map["anchor_definitions"]["Certification_Expiry_Date"] = {
        "description": "Expiry date of CodeMark or BRANZ certification",
        "unit": "date",
        "compliance_sources": ["Certificate document"],
        "product_categories": ["all"],
        "validation_rule": "expiry_date > today",
        "format": "YYYY-MM-DD"
    }
    
    anchor_map["anchor_definitions"]["Appraisal_Scope_Limitations"] = {
        "description": "Restrictions on where/how the certified product can be used",
        "unit": "text",
        "compliance_sources": ["CodeMark Certificate", "BRANZ Appraisal"],
        "product_categories": ["all"],
        "validation_rule": "must_flag_if_restricted",
        "examples": ["Wind Zone Limited", "Not for Fire-rated assemblies", "External use only"]
    }
    
    # Update sectors if present
    if "sectors" in anchor_map:
        anchor_map["sectors"]["F_Certification"] = {
            "governing_docs": ["MBIE CodeMark Scheme", "BRANZ Appraisal Program", "BPIR Regs 2022"],
            "anchors": [
                "CodeMark_ID",
                "BRANZ_Appraisal_Number",
                "Certification_Expiry_Date",
                "Appraisal_Scope_Limitations",
                "CODEMARK_CERTIFICATE",
                "GREENTAG_LEVEL",
                "EPD_REFERENCE",
                "WARRANTY_YEARS"
            ]
        }
    
    # Update protocol version
    anchor_map["protocol_version"] = "3.1-F"
    anchor_map["last_updated"] = datetime.now().isoformat()
    
    with open(anchor_map_path, 'w') as f:
        json.dump(anchor_map, f, indent=2)
    
    print("\n✅ Updated universal_anchor_map.json with Sector F anchors")


def generate_master_register(results: List[Dict], stats: Dict):
    """Generate Compliance_Master_Register.csv"""
    
    csv_path = "/app/protocols/Compliance_Master_Register.csv"
    
    # Sort by status priority: EXPIRED > CONDITIONAL > MISSING > ACTIVE
    status_priority = {"EXPIRED": 0, "CONDITIONAL": 1, "MISSING": 2, "ACTIVE": 3}
    results_sorted = sorted(results, key=lambda x: (status_priority.get(x["status"], 4), x["brand"], x["product"]))
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "brand", "product", "doc_type", "codemark_id", "branz_number",
            "expiry_date", "is_expired", "status", "bpir_status", "scope_limitations", "source"
        ])
        writer.writeheader()
        writer.writerows(results_sorted)
    
    print(f"\n✅ Generated {csv_path}")
    print(f"   Total records: {len(results)}")
    
    return csv_path


def main():
    print("═" * 70)
    print("  SECTOR F: CERTIFICATION LOCKDOWN")
    print("  Automated CodeMark & BRANZ Verification System")
    print("═" * 70)
    print(f"  Started: {datetime.now().isoformat()}")
    print("═" * 70)
    
    # Step 1: Update Anchor Map
    print("\n" + "─" * 70)
    print("  STEP 1: UPDATING ANCHOR MAP")
    print("─" * 70)
    update_anchor_map()
    
    # Step 2: Scan Library
    print("\n" + "─" * 70)
    print("  STEP 2: SCANNING LIBRARY FOR CERTIFICATIONS")
    print("─" * 70)
    results, stats = scan_library_certifications()
    
    # Step 3: Generate Master Register
    print("\n" + "─" * 70)
    print("  STEP 3: GENERATING MASTER REGISTER")
    print("─" * 70)
    csv_path = generate_master_register(results, stats)
    
    # Step 4: Summary Report
    print("\n" + "═" * 70)
    print("  SECTOR F CERTIFICATION AUDIT - SUMMARY")
    print("═" * 70)
    
    print(f"\n  📊 CERTIFICATION STATUS:")
    print(f"     ✅ ACTIVE: {stats['ACTIVE']} products")
    print(f"     ⚠️ CONDITIONAL: {stats['CONDITIONAL']} products (scope limitations)")
    print(f"     ❌ EXPIRED: {stats['EXPIRED']} products")
    print(f"     ❓ MISSING: {stats['MISSING']} products (no certification found)")
    
    # Flag critical issues
    expired = [r for r in results if r["status"] == "EXPIRED"]
    conditional = [r for r in results if r["status"] == "CONDITIONAL"]
    
    if expired:
        print(f"\n  🚨 EXPIRED CERTIFICATIONS ({len(expired)}):")
        for r in expired[:5]:
            print(f"     • {r['brand']} - {r['product'][:40]}... (Expired: {r['expiry_date']})")
        if len(expired) > 5:
            print(f"     ... and {len(expired) - 5} more")
    
    if conditional:
        print(f"\n  ⚠️ CONDITIONAL CERTIFICATIONS ({len(conditional)}):")
        for r in conditional[:5]:
            print(f"     • {r['brand']} - {r['product'][:40]}...")
            if r['scope_limitations']:
                print(f"       Limitation: {r['scope_limitations'][:80]}...")
        if len(conditional) > 5:
            print(f"     ... and {len(conditional) - 5} more")
    
    print("\n" + "═" * 70)
    print(f"  ✅ SECTOR F LOCKDOWN COMPLETE")
    print(f"  📄 Master Register: {csv_path}")
    print(f"  Completed: {datetime.now().isoformat()}")
    print("═" * 70)


if __name__ == "__main__":
    main()
