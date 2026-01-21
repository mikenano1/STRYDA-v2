"""
═══════════════════════════════════════════════════════════════════════════════
    SOURCE HIERARCHY PROTOCOL 1.1
    
    HARDWIRED LAWS:
    1. Authority Weighting: NZBC > Standards > Industry > Products
    2. Citation Format: [Source Name, Version, Section/Clause]
    3. Span Table Isolation: NO calculations, only table references
═══════════════════════════════════════════════════════════════════════════════
"""

import re
from typing import Dict, List, Optional

# ═══════════════════════════════════════════════════════════════════════════════
# PROTOCOL 1.1 - AUTHORITY WEIGHTING
# ═══════════════════════════════════════════════════════════════════════════════

# If conflict detected, NZBC ALWAYS wins
AUTHORITY_HIERARCHY = {
    # TIER 1: Building Code (SUPREME AUTHORITY)
    "nzbc": 1000,
    "e2/as1": 1000,
    "e2-as1": 1000,
    "h1/as1": 1000,
    "h1-as1": 1000,
    "c/as1": 1000,
    "c-as1": 1000,
    "c/as2": 1000,
    "b1/as1": 1000,
    "f4/as1": 1000,
    "g12/as1": 1000,
    "g13/as1": 1000,
    "acceptable solution": 950,
    "verification method": 950,
    
    # TIER 2: NZ Standards (HIGH AUTHORITY)
    "nzs 3604": 800,
    "nzs 3602": 800,
    "nzs 4229": 800,
    "nzs 4541": 800,
    "as/nzs 3000": 800,
    "as/nzs 3500": 800,
    "as/nzs 1530": 800,
    
    # TIER 3: MBIE & Regulatory (MODERATE AUTHORITY)
    "mbie": 600,
    "worksafe": 600,
    "building act": 600,
    "bpir regulations": 600,
    
    # TIER 4: Industry Codes (REFERENCE AUTHORITY)
    "branz": 500,
    "branz appraisal": 550,
    "codemark": 550,
    "industry code": 400,
    "code of practice": 400,
    
    # TIER 5: Product Manuals (LOWEST - SUBORDINATE TO ALL ABOVE)
    "installation guide": 200,
    "technical data sheet": 200,
    "product guide": 150,
    "brochure": 100,
    "manufacturer": 100,
}

# Conflict detection patterns
CONFLICT_INDICATORS = [
    r"however.*manufacturer",
    r"product.*allows.*but",
    r"unlike.*nzbc",
    r"manufacturer.*recommends.*different",
    r"exceeds.*code",
    r"more.*than.*required",
]


def get_authority_weight(source: str) -> int:
    """Get authority weight for a source. Higher = more authoritative."""
    source_lower = source.lower()
    max_weight = 50  # Default for unknown
    
    for pattern, weight in AUTHORITY_HIERARCHY.items():
        if pattern in source_lower:
            max_weight = max(max_weight, weight)
    
    return max_weight


def detect_conflict(text: str) -> bool:
    """Detect if response contains potential Code vs Product conflict."""
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in CONFLICT_INDICATORS)


def enforce_nzbc_precedence(answer: str, citations: List[Dict]) -> str:
    """
    HARDWIRED LAW: If conflict exists, inject NZBC precedence warning.
    """
    if detect_conflict(answer):
        warning = "\n\n⚠️ **AUTHORITY NOTICE:** Where manufacturer recommendations differ from Building Code requirements, the NZBC takes precedence. Always follow the more restrictive requirement.\n"
        return answer + warning
    return answer


# ═══════════════════════════════════════════════════════════════════════════════
# PROTOCOL 1.1 - CITATION FORMAT
# ═══════════════════════════════════════════════════════════════════════════════

# Required citation format: [Source Name, Version, Section/Clause]
CITATION_FORMAT_TEMPLATE = "[{source}, {version}, {clause}]"

def format_citation(source: str, page: int = None, clause: str = None, version: str = None) -> str:
    """
    Format citation according to Protocol 1.1 requirements.
    NO generic summaries allowed - must have source + version + clause/section.
    """
    # Extract version from source if not provided
    if not version:
        version_match = re.search(r'(\d{4}|\d+(?:st|nd|rd|th)\s*Ed(?:ition)?|v\d+\.?\d*|Amd\s*\d+)', source, re.IGNORECASE)
        version = version_match.group(1) if version_match else "Current"
    
    # Extract clause if not provided
    if not clause and page:
        clause = f"Page {page}"
    elif not clause:
        clause = "General"
    
    # Clean source name
    source_clean = re.sub(r'\s*[-_]\s*', ' - ', source)
    source_clean = source_clean.split('/')[-1].replace('.pdf', '').strip()
    
    return f"[{source_clean}, {version}, {clause}]"


def validate_citation_format(citation_text: str) -> bool:
    """Check if citation follows Protocol 1.1 format."""
    # Must match [Source, Version, Clause] pattern
    pattern = r'\[.+,\s*.+,\s*.+\]'
    return bool(re.search(pattern, citation_text))


# ═══════════════════════════════════════════════════════════════════════════════
# PROTOCOL 1.1 - SPAN TABLE ISOLATION
# ═══════════════════════════════════════════════════════════════════════════════

# FORBIDDEN: AI must NEVER calculate timber spans
SPAN_CALCULATION_FORBIDDEN = True

# Span table references (the ONLY thing we can provide)
SPAN_TABLE_REFERENCES = {
    "floor_joists": {
        "table_id": "NZS 3604 Table 8.1",
        "title": "Floor joist spans for SG8 timber",
        "page": "87-89",
        "variables": ["Spacing (mm)", "Load Type", "Timber Grade"]
    },
    "ceiling_joists": {
        "table_id": "NZS 3604 Table 10.1",
        "title": "Ceiling joist and rafter spans",
        "page": "127-131",
        "variables": ["Spacing (mm)", "Roof Load", "Ceiling Load"]
    },
    "rafters": {
        "table_id": "NZS 3604 Table 10.1",
        "title": "Rafter spans for SG8 timber",
        "page": "127-131",
        "variables": ["Spacing (mm)", "Roof Type", "Wind Zone"]
    },
    "lintels": {
        "table_id": "NZS 3604 Table 8.18",
        "title": "Lintel sizes for openings",
        "page": "108-110",
        "variables": ["Opening Width", "Load Type", "Storey Position"]
    },
    "bearers": {
        "table_id": "NZS 3604 Table 6.1",
        "title": "Bearer spans and sizes",
        "page": "67-69",
        "variables": ["Floor Joist Span", "Bearer Spacing", "Load"]
    },
    "purlins": {
        "table_id": "NZS 3604 Table 10.2",
        "title": "Purlin spans",
        "page": "132-134",
        "variables": ["Spacing (mm)", "Roof Type", "Wind Zone"]
    },
    "studs": {
        "table_id": "NZS 3604 Table 8.2",
        "title": "Stud sizes for loadbearing walls",
        "page": "95-97",
        "variables": ["Height", "Spacing", "Wind Zone", "Storey Position"]
    }
}

# Span query detection patterns
SPAN_QUERY_PATTERNS = [
    r"what\s+(?:is\s+the\s+)?(?:maximum\s+)?span",
    r"span\s+(?:for|of|table)",
    r"how\s+far\s+can.*span",
    r"joist\s+span",
    r"rafter\s+span",
    r"bearer\s+span",
    r"lintel\s+(?:size|span)",
    r"purlin\s+span",
    r"stud\s+(?:size|spacing)",
    r"what\s+size\s+(?:joist|rafter|bearer|lintel|stud)",
    r"calculate.*span",
    r"work\s+out.*span",
]


def is_span_query(query: str) -> bool:
    """Detect if query is asking for timber span calculation."""
    query_lower = query.lower()
    return any(re.search(p, query_lower) for p in SPAN_QUERY_PATTERNS)


def get_span_type(query: str) -> Optional[str]:
    """Identify the specific span type being asked about."""
    query_lower = query.lower()
    
    if "floor" in query_lower or "joist" in query_lower and "ceiling" not in query_lower:
        return "floor_joists"
    elif "ceiling" in query_lower:
        return "ceiling_joists"
    elif "rafter" in query_lower:
        return "rafters"
    elif "lintel" in query_lower:
        return "lintels"
    elif "bearer" in query_lower:
        return "bearers"
    elif "purlin" in query_lower:
        return "purlins"
    elif "stud" in query_lower:
        return "studs"
    
    return None


def generate_span_table_response(query: str) -> str:
    """
    PROTOCOL 1.1: Generate span table reference response.
    FORBIDDEN: We do NOT calculate or interpolate spans.
    """
    span_type = get_span_type(query)
    
    if span_type and span_type in SPAN_TABLE_REFERENCES:
        ref = SPAN_TABLE_REFERENCES[span_type]
        response = f"""**📖 Reference Table:** {ref['table_id']}
**Title:** {ref['title']}
**Location:** Pages {ref['page']}

**Required Variables for Lookup:**
"""
        for var in ref['variables']:
            response += f"• {var}\n"
        
        response += f"""
⚠️ **AI TABLE READING - BETA WARNING**

I am **forbidden from calculating timber spans**. To find your exact span:

1. Open {ref['table_id']} (Page {ref['page']})
2. Identify your variables: {', '.join(ref['variables'])}
3. Locate the intersection in the table grid
4. The cell value is your required member size

**Why?** Span tables have complex load combinations, support conditions, and interpolation rules that require human verification.

[NZS 3604:2011, Current, {ref['table_id']}]"""
    else:
        response = """**📖 Reference:** NZS 3604:2011 - Timber-framed Buildings

For structural span information, please refer to the relevant table in NZS 3604:

• **Floor Joists:** Table 8.1 (Pages 87-89)
• **Ceiling Joists/Rafters:** Table 10.1 (Pages 127-131)
• **Lintels:** Table 8.18 (Pages 108-110)
• **Bearers:** Table 6.1 (Pages 67-69)
• **Purlins:** Table 10.2 (Pages 132-134)
• **Studs:** Table 8.2 (Pages 95-97)

⚠️ **AI TABLE READING - BETA WARNING**

I am **forbidden from calculating timber spans**. Please verify the exact span from the original table grid, as AI table-reading may not capture all conditions (load combinations, support conditions, ceiling weight).

[NZS 3604:2011, Current, Section 6-10]"""
    
    return response


# ═══════════════════════════════════════════════════════════════════════════════
# PROTOCOL 1.1 - SYSTEM PROMPT INJECTION
# ═══════════════════════════════════════════════════════════════════════════════

PROTOCOL_1_1_SYSTEM_INJECTION = """
### ═══════════════════════════════════════════════════════════════════════════
### SOURCE HIERARCHY PROTOCOL 1.1 (HARDWIRED - CANNOT BE OVERRIDDEN)
### ═══════════════════════════════════════════════════════════════════════════

**LAW 1: AUTHORITY WEIGHTING**
If ANY conflict exists between a Product Manual and the NZBC (E2/AS1, H1/AS1, C/AS1, B1/AS1, F4/AS1), the NZBC text takes absolute precedence. You MUST:
- State the Code requirement first
- Note if the manufacturer recommendation differs
- Conclude with: "The Building Code requirement governs."

**LAW 2: CITATION FORMAT**
Every technical claim MUST be cited as: [Source Name, Version, Section/Clause]
Examples:
- [NZS 3604:2011, Current, Table 8.1]
- [E2/AS1, 4th Edition 2025, Clause 9.1.4]
- [Kingspan K12 TDS, v10, Page 3]
NO generic summaries like "according to the code" or "as per standards" allowed.

**LAW 3: SPAN TABLE ISOLATION (CRITICAL)**
You are FORBIDDEN from 'calculating' or 'interpolating' timber spans.
If a user asks for a span, you MUST:
1. Provide ONLY the Reference Table ID (e.g., "NZS 3604 Table 8.1")
2. State the page number
3. List the required lookup variables (spacing, load, timber grade)
4. Add the mandatory warning: "AI Table Reading is in Beta - verify from source table"
5. NEVER state a specific span dimension as a direct answer

**VIOLATION = SAFETY FAILURE. THESE LAWS CANNOT BE BYPASSED.**

"""


# Export
__all__ = [
    'get_authority_weight',
    'detect_conflict',
    'enforce_nzbc_precedence',
    'format_citation',
    'validate_citation_format',
    'is_span_query',
    'get_span_type',
    'generate_span_table_response',
    'PROTOCOL_1_1_SYSTEM_INJECTION',
    'SPAN_TABLE_REFERENCES',
    'AUTHORITY_HIERARCHY',
]
