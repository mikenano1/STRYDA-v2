"""
STRYDA Citation Utilities
Helper functions for determining when citations can be shown to users
"""

import re
from typing import List, Dict

def has_code_signals(question: str) -> bool:
    """
    Check if question contains obvious code/standard references
    """
    q_lower = question.lower()
    
    code_patterns = [
        r'\bnzs\s*\d+',  # NZS 3604, NZS 4229
        r'\b[a-h]\d+/as\d+',  # E2/AS1, H1/AS1, C/AS2
        r'\b[a-h]\d+/vm\d+',  # H1/VM1, B1/VM1
        r'\bclause\s+[\da-h]+',  # clause 7.1, clause E2.3
        r'\bsection\s+[\da-h]+',  # section 5.2
        r'\btable\s+[\d\.]+',  # table 7.1
        r'\b(nzbc|building code|standard|as1|as2|vm1|vm2)\b',
        r'\b(amendment|amdt)\s*\d+',  # amendment 13
    ]
    
    for pattern in code_patterns:
        if re.search(pattern, q_lower):
            return True
    
    return False

def should_allow_citations(
    question: str,
    intent: str,
    citations: List[Dict],
    top_docs: List[Dict]
) -> bool:
    """
    Determine if citations CAN be shown (not whether they SHOULD be auto-shown)
    
    This is a permissive check - returns True if we have good code sources
    that the user MIGHT want to reference, regardless of intent.
    
    Args:
        question: User's question
        intent: Classified intent (compliance_strict, general_help, etc.)
        citations: List of citation objects already built
        top_docs: List of retrieved documents with metadata
    
    Returns:
        True if citations are available and relevant enough to offer to user
    """
    
    # No citations built? Can't show them
    if not citations or len(citations) == 0:
        return False
    
    # Check if we have high-quality code documents
    has_quality_docs = False
    quality_doc_types = [
        "acceptable_solution_current",
        "acceptable_solution_legacy", 
        "verification_method_current",
        "industry_code_of_practice",
        "nz_standard"
    ]
    
    for doc in top_docs[:3]:  # Check top 3 docs only
        doc_type = doc.get('doc_type', '')
        if doc_type in quality_doc_types:
            has_quality_docs = True
            break
    
    # If we have quality docs, allow citations
    if has_quality_docs:
        return True
    
    # Check if question has explicit code signals
    # Even if intent is general_help, if they mention "NZS 3604" they might want clauses
    if has_code_signals(question):
        return True
    
    # Otherwise, don't offer citations
    # (e.g., "How do I stop my deck bouncing?" with no code docs)
    return False

def should_auto_expand_citations(question: str, intent: str) -> bool:
    """
    Determine if citations should be AUTO-EXPANDED (shown by default)
    
    This is more restrictive than should_allow_citations.
    Only auto-expand for clear compliance questions.
    
    Args:
        question: User's question
        intent: Classified intent
    
    Returns:
        True if citations should be expanded by default
    """
    
    # Auto-expand for compliance_strict intent
    if intent == "compliance_strict":
        return True
    
    # Auto-expand if question has very explicit code reference
    q_lower = question.lower()
    
    explicit_patterns = [
        r'\bwhat does\s+(nzs|e\d|h\d|b\d|c/as|f\d|g\d+)\s+(say|require|specify|state)',
        r'\baccording to\s+(nzs|nzbc|code|standard)',
        r'\b(nzs|nzbc)\s+\d+\s+(table|clause|section)',
        r'\b(minimum|maximum)\s+.*\b(nzs|code|as\d)',
    ]
    
    for pattern in explicit_patterns:
        if re.search(pattern, q_lower):
            return True
    
    # Otherwise, collapse by default (let user expand if needed)
    return False
