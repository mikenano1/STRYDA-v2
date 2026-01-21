#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
    PROTOCOL: REGISTER-FIRST AUDIT
    
    HARDWIRED LAWS:
    1. Check Compliance_Master_Register.csv FIRST for any product mention
    2. STOP-WORK RULE: Lead with COMPLIANCE WARNING for flagged products
    3. PROHIBIT INFERENCING: Never suggest alternatives for expired products
    4. ENFORCE CITATION PRIORITY: NZBC citations must appear in response text
═══════════════════════════════════════════════════════════════════════════════
"""

import csv
import re
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Path to Master Register
REGISTER_PATH = "/app/protocols/Compliance_Master_Register.csv"

# Load Register into memory on import
_COMPLIANCE_REGISTER = {}
_REGISTER_LOADED = False


def load_compliance_register():
    """Load the Compliance Master Register into memory"""
    global _COMPLIANCE_REGISTER, _REGISTER_LOADED
    
    if _REGISTER_LOADED and _COMPLIANCE_REGISTER:
        return _COMPLIANCE_REGISTER
    
    _COMPLIANCE_REGISTER = {}
    
    if not os.path.exists(REGISTER_PATH):
        print(f"⚠️ Register not found at {REGISTER_PATH}")
        return _COMPLIANCE_REGISTER
    
    try:
        with open(REGISTER_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Create lookup keys for product matching
                product_name = row.get('product', '').lower().strip()
                brand = row.get('brand', '').lower().strip()
                
                # Multiple lookup keys for flexible matching
                keys = [
                    product_name,
                    f"{brand} {product_name}",
                    product_name.replace('-', ' '),
                    product_name.replace('_', ' '),
                ]
                
                # Also add partial product name keys
                product_parts = product_name.split(' - ')
                for part in product_parts:
                    if len(part) > 3:
                        keys.append(part.strip())
                
                for key in keys:
                    if key and len(key) > 3:
                        _COMPLIANCE_REGISTER[key] = row
        
        _REGISTER_LOADED = True
        print(f"✅ Loaded {len(_COMPLIANCE_REGISTER)} entries from Compliance Register")
        
    except Exception as e:
        print(f"❌ Failed to load register: {e}")
    
    return _COMPLIANCE_REGISTER


def extract_product_mentions(query: str) -> List[str]:
    """Extract potential product names from user query"""
    # Common product name patterns
    patterns = [
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  # Title case words
        r'\b(rockcote|velvetina|venetian|hardie|gib|kingspan|knauf|masons|marshall|thermakraft)\b',
        r'\b([A-Z]{2,}[-\s]?\d+)\b',  # Product codes like K12, RAB
        r'(?:about|for|use|install)\s+([A-Za-z]+(?:\s+[A-Za-z]+){0,3})',  # After common verbs
    ]
    
    mentions = []
    query_lower = query.lower()
    
    for pattern in patterns:
        matches = re.findall(pattern, query, re.IGNORECASE)
        mentions.extend([m.lower().strip() for m in matches if len(m) > 3])
    
    # Also check for common product names directly
    known_products = [
        'rockcote', 'velvetina', 'venetian', 'hardie', 'linea', 'stria', 'axon',
        'gib', 'aqualine', 'fyreline', 'ezybrace', 'bracing',
        'kingspan', 'kooltherm', 'k12', 'k17',
        'knauf', 'earthwool',
        'masons', '40 below', 'uni pro', 'barricade',
        'marshall', 'tekton', 'super-stick',
        'thermakraft', 'covertek', 'thermabar',
    ]
    
    for product in known_products:
        if product in query_lower:
            mentions.append(product)
    
    return list(set(mentions))


def check_register(query: str) -> Optional[Dict]:
    """
    HARDWIRED LAW 1: Check register FIRST for any product mention.
    Returns the most relevant flagged entry if found.
    """
    register = load_compliance_register()
    
    if not register:
        return None
    
    # Extract product mentions from query
    mentions = extract_product_mentions(query)
    
    # Check each mention against register
    flagged_entries = []
    
    for mention in mentions:
        # Direct lookup
        if mention in register:
            entry = register[mention]
            if entry.get('status') in ['EXPIRED', 'CONDITIONAL', 'MISSING']:
                flagged_entries.append(entry)
                continue
        
        # Fuzzy matching
        for key, entry in register.items():
            if mention in key or key in mention:
                if entry.get('status') in ['EXPIRED', 'CONDITIONAL', 'MISSING']:
                    flagged_entries.append(entry)
                    break
    
    # Return the most critical flag (EXPIRED > CONDITIONAL > MISSING)
    if flagged_entries:
        priority = {'EXPIRED': 0, 'CONDITIONAL': 1, 'MISSING': 2}
        flagged_entries.sort(key=lambda x: priority.get(x.get('status', ''), 99))
        return flagged_entries[0]
    
    return None


def generate_compliance_warning(entry: Dict) -> str:
    """
    HARDWIRED LAW 2: Generate STOP-WORK compliance warning banner.
    This MUST lead the response.
    """
    status = entry.get('status', 'UNKNOWN')
    product = entry.get('product', 'Unknown Product')
    brand = entry.get('brand', '')
    expiry = entry.get('expiry_date', '')
    limitations = entry.get('scope_limitations', '')
    bpir_status = entry.get('bpir_status', '')
    codemark = entry.get('codemark_id', '')
    branz = entry.get('branz_number', '')
    
    product_full = f"{brand} - {product}" if brand else product
    
    # Build warning banner
    if status == 'EXPIRED':
        warning = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  🚨 COMPLIANCE WARNING: CERTIFICATION EXPIRED                                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Product: {product_full[:60]:<60} ║
║  Status: ❌ EXPIRED                                                           ║
║  Expiry Date: {expiry:<20}                                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  ⚠️ STOP-WORK NOTICE: This product's certification has lapsed.               ║
║  You MUST NOT rely on expired compliance documentation.                       ║
║  Contact the manufacturer or supplier for current certification.              ║
╚══════════════════════════════════════════════════════════════════════════════╝

**I am forbidden from providing technical guidance on expired products.**

To proceed, you need to:
1. Contact {brand or 'the manufacturer'} to verify current certification status
2. Obtain updated compliance documentation
3. Re-query once valid certification is confirmed

[Compliance_Master_Register.csv, 2026-01-21, Product Audit]
"""

    elif status == 'CONDITIONAL':
        warning = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ⚠️ COMPLIANCE WARNING: CONDITIONAL CERTIFICATION                            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Product: {product_full[:60]:<60} ║
║  Status: ⚠️ CONDITIONAL                                                      ║
║  CodeMark: {codemark or 'N/A':<15} BRANZ: {branz or 'N/A':<10}                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  SCOPE LIMITATION: {limitations[:55] if limitations else 'See certificate for restrictions':<55} ║
╚══════════════════════════════════════════════════════════════════════════════╝

**This product has usage restrictions.** Ensure your application falls within the certified scope before proceeding.

"""

    elif status == 'MISSING' or bpir_status == 'UNDECLARED':
        warning = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ❓ COMPLIANCE WARNING: CERTIFICATION NOT FOUND                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Product: {product_full[:60]:<60} ║
║  Status: ❓ MISSING CERTIFICATION                                             ║
║  BPIR Status: {bpir_status:<15}                                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  No CodeMark or BRANZ Appraisal found in our compliance database.            ║
║  This does not mean the product is non-compliant, but verification needed.   ║
╚══════════════════════════════════════════════════════════════════════════════╝

**Recommendation:** Request BPIR documentation or CodeMark/BRANZ certificate from the supplier before specifying this product.

"""
    else:
        return ""  # No warning needed for ACTIVE products
    
    return warning


def check_and_warn(query: str) -> Tuple[Optional[str], bool]:
    """
    Main entry point for Register-First Audit.
    Returns: (warning_text, should_block_response)
    
    HARDWIRED LAW 3: If EXPIRED, block response and prohibit inferencing.
    """
    flagged_entry = check_register(query)
    
    if not flagged_entry:
        return None, False
    
    warning = generate_compliance_warning(flagged_entry)
    
    # EXPIRED = Block response completely (prohibit inferencing)
    should_block = flagged_entry.get('status') == 'EXPIRED'
    
    return warning, should_block


def format_citation_in_text(source: str, version: str = None, clause: str = None) -> str:
    """
    HARDWIRED LAW 4: Format citation for visible inclusion in response text.
    """
    if not version:
        # Extract version from source
        version_match = re.search(r'(\d{4}|\d+(?:st|nd|rd|th)\s*Ed|v\d+|Amd\s*\d+)', source, re.IGNORECASE)
        version = version_match.group(1) if version_match else "Current"
    
    if not clause:
        clause = "General"
    
    # Clean source
    source_clean = source.split('/')[-1].replace('.pdf', '').strip()
    
    return f"[{source_clean}, {version}, {clause}]"


# ═══════════════════════════════════════════════════════════════════════════════
# CITATION PRIORITY ENFORCEMENT (LAW 4)
# ═══════════════════════════════════════════════════════════════════════════════

def enforce_citation_visibility(answer: str, citations: List[Dict]) -> str:
    """
    HARDWIRED LAW 4: Ensure NZBC citations appear FIRST and IN THE TEXT.
    Not just in metadata - must be visible to user.
    """
    if not citations:
        return answer
    
    # Sort citations by authority
    authority_order = {
        'nzbc': 0, 'e2': 0, 'h1': 0, 'c/as': 0, 'b1': 0, 'f4': 0,
        'nzs': 1, 'as/nzs': 1,
        'mbie': 2, 'branz': 2,
        'manufacturer': 3, 'product': 3, 'tds': 3,
    }
    
    def get_priority(cit):
        source = cit.get('source', '').lower()
        for key, priority in authority_order.items():
            if key in source:
                return priority
        return 99
    
    sorted_citations = sorted(citations, key=get_priority)
    
    # Build citation block for end of answer
    citation_block = "\n\n---\n**📖 Sources (by Authority):**\n"
    
    for i, cit in enumerate(sorted_citations[:5], 1):
        source = cit.get('source', 'Unknown')
        page = cit.get('page', '')
        
        # Determine authority level
        source_lower = source.lower()
        if any(x in source_lower for x in ['nzbc', 'e2', 'h1', 'c/', 'b1', 'f4', 'g12']):
            level = "🏛️ NZBC"
        elif any(x in source_lower for x in ['nzs', 'as/nzs']):
            level = "📘 Standard"
        elif any(x in source_lower for x in ['branz', 'mbie']):
            level = "📋 Guidance"
        else:
            level = "📄 Product"
        
        formatted = format_citation_in_text(source, clause=f"Page {page}" if page else None)
        citation_block += f"{i}. {level}: {formatted}\n"
    
    return answer + citation_block


# Export
__all__ = [
    'load_compliance_register',
    'check_register',
    'generate_compliance_warning',
    'check_and_warn',
    'format_citation_in_text',
    'enforce_citation_visibility',
]
