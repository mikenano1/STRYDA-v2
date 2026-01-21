"""
═══════════════════════════════════════════════════════════════════════════════
    STRYDA V3.0 - SOURCE HIERARCHY & CITATION PRIORITY
    
    Priority Order: NZBC > NZ Standards > Industry Codes > Product Manuals
═══════════════════════════════════════════════════════════════════════════════
"""

import re
from typing import List, Dict

# V3.0 Citation Priority Weights
CITATION_PRIORITY = {
    # Level 1: Building Code (Highest Authority)
    "nzbc": 100,
    "building code": 100,
    "c/as": 100,
    "c-as": 100,
    "e2_as1": 100,
    "h1_as1": 100,
    "b1_as1": 100,
    "acceptable solution": 95,
    "verification method": 95,
    
    # Level 2: NZ Standards
    "nzs 3604": 90,
    "nzs 3602": 90,
    "nzs 4229": 90,
    "as/nzs": 90,
    "standards - nzs": 90,
    "standards - as": 90,
    
    # Level 3: MBIE & Industry Codes
    "mbie": 80,
    "worksafe": 80,
    "branz": 75,
    "industry -": 75,
    "code of practice": 75,
    
    # Level 4: Product Manuals (Lowest - but still valid)
    "installation guide": 60,
    "technical data": 60,
    "bpir": 65,
    "codemark": 65,
    "branz appraisal": 70,
    "product guide": 55,
    "brochure": 50,
}

# Span Table Warning Templates
SPAN_TABLE_WARNING = """
⚠️ **SPAN TABLE VERIFICATION REQUIRED**

The span information above is extracted from {source}. 

**IMPORTANT:** Please verify the exact span from the original table grid. AI table-reading is currently in beta and may not capture all conditions (e.g., load combinations, support conditions, ceiling weight).

📖 **Reference:** {citation}
"""

SPAN_TABLE_SOURCES = {
    "nzs_3604": {
        "name": "NZS 3604:2011",
        "tables": {
            "floor_joists": "Table 8.1 - Floor joist spans",
            "ceiling_joists": "Table 10.1 - Ceiling joist/rafter spans",
            "rafters": "Table 10.1 - Rafter spans",
            "lintels": "Table 8.18 - Lintel sizes",
            "purlins": "Table 10.2 - Purlin spans",
        }
    },
    "nzs_4229": {
        "name": "NZS 4229:2013",
        "tables": {
            "masonry": "Section 4 - Masonry tables",
        }
    }
}


def calculate_citation_priority(source: str) -> int:
    """
    Calculate priority score for a citation source.
    Higher score = higher authority = cite first.
    """
    source_lower = source.lower()
    
    # Check each priority pattern
    max_priority = 50  # Default for unknown sources
    
    for pattern, priority in CITATION_PRIORITY.items():
        if pattern in source_lower:
            max_priority = max(max_priority, priority)
    
    return max_priority


def sort_citations_by_priority(citations: List[Dict]) -> List[Dict]:
    """
    Sort citations by V3.0 priority: NZBC > Standards > Industry > Products
    """
    def get_priority(citation):
        source = citation.get("source", "")
        return calculate_citation_priority(source)
    
    # Sort by priority (descending) then by confidence
    return sorted(
        citations, 
        key=lambda c: (get_priority(c), c.get("confidence", 0)),
        reverse=True
    )


def is_span_query(query: str) -> bool:
    """Detect if query is asking about structural spans"""
    span_patterns = [
        r"span\s+(?:for|of|table)",
        r"what\s+span",
        r"maximum\s+span",
        r"joist\s+span",
        r"rafter\s+span",
        r"purlin\s+span",
        r"lintel\s+(?:size|span)",
        r"bearer\s+span",
        r"how\s+far\s+can.*span",
    ]
    
    query_lower = query.lower()
    return any(re.search(p, query_lower) for p in span_patterns)


def get_span_table_warning(query: str, source: str = "NZS 3604:2011") -> str:
    """Generate span table verification warning"""
    
    # Detect specific span type
    query_lower = query.lower()
    span_type = "general"
    table_ref = "relevant span tables"
    
    if "joist" in query_lower or "floor" in query_lower:
        span_type = "floor_joists"
        table_ref = SPAN_TABLE_SOURCES["nzs_3604"]["tables"].get("floor_joists", table_ref)
    elif "rafter" in query_lower or "ceiling" in query_lower:
        span_type = "ceiling_joists"
        table_ref = SPAN_TABLE_SOURCES["nzs_3604"]["tables"].get("ceiling_joists", table_ref)
    elif "lintel" in query_lower:
        span_type = "lintels"
        table_ref = SPAN_TABLE_SOURCES["nzs_3604"]["tables"].get("lintels", table_ref)
    elif "purlin" in query_lower:
        span_type = "purlins"
        table_ref = SPAN_TABLE_SOURCES["nzs_3604"]["tables"].get("purlins", table_ref)
    
    return SPAN_TABLE_WARNING.format(
        source=source,
        citation=table_ref
    )


def apply_v3_citation_hierarchy(docs: List[Dict], query: str) -> tuple:
    """
    Apply V3.0 citation hierarchy to retrieved documents.
    
    Returns:
        Tuple of (sorted_docs, span_warning_if_needed)
    """
    # Sort by citation priority
    sorted_docs = sort_citations_by_priority(docs)
    
    # Check if span warning needed
    span_warning = None
    if is_span_query(query):
        # Find the primary source for the span data
        primary_source = "NZS 3604:2011"
        for doc in sorted_docs:
            if "3604" in doc.get("source", ""):
                primary_source = doc.get("source", primary_source)
                break
        span_warning = get_span_table_warning(query, primary_source)
    
    return sorted_docs, span_warning


# Export the main function
__all__ = [
    'calculate_citation_priority',
    'sort_citations_by_priority',
    'is_span_query',
    'get_span_table_warning',
    'apply_v3_citation_hierarchy',
    'CITATION_PRIORITY'
]
