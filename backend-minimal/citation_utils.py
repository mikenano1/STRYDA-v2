"""
STRYDA Citation Utilities
Helper functions for determining when citations can be shown to users
"""

import re
from typing import List, Dict

def has_code_signals(question: str) -> bool:
    """
    Check if question contains obvious code/standard references
    
    EXCLUDES timber treatment grades (H3, H3.1, H3.2, H4) which are 
    product specifications, not building code clauses.
    """
    q_lower = question.lower()
    
    code_patterns = [
        r'\bnzs\s*\d+',  # NZS 3604, NZS 4229
        r'\b[abcefg]\d+/as\d+',  # E2/AS1, C/AS2, etc. (excludes H3/H4 treatment)
        r'\bh1/as\d+',  # H1/AS1 (energy code, not H1 treatment)
        r'\b[a-h]\d+/vm\d+',  # H1/VM1, B1/VM1
        r'\bclause\s+[a-z]?\d+',  # clause 7.1, clause E2.3
        r'\bsection\s+[a-z]?\d+',  # section 5.2
        r'\btable\s+[\d\.]+',  # table 7.1
        r'\b(nzbc|building code|standard|as1|as2|vm1|vm2)\b',
        r'\b(amendment|amdt)\s*\d+',  # amendment 13
        # Explicit exclusion: NOT H3, H3.1, H3.2, H4 (timber treatment)
    ]
    
    # Check if it's a timber treatment question (NOT a code reference)
    timber_treatment_pattern = r'\bh[34](\.\d)?(?!\s*/\s*as)'
    if re.search(timber_treatment_pattern, q_lower):
        # If ONLY timber treatment mentioned (no other code), return False
        has_other_code = any(re.search(p, q_lower) for p in code_patterns[:-1])  # Exclude amendment pattern
        if not has_other_code:
            return False  # Timber treatment alone is NOT a code signal
    
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
    
    STRICT RULES (Task 2):
    - Must have citations built (not empty array)
    - Must have quality code documents in top results
    - For product_info/general_help: extra strict (must have code signals OR quality docs)
    - For compliance intents: normal permissive rules
    
    This prevents empty citation pills and ensures only real code sources trigger displays.
    
    Args:
        question: User's question
        intent: Classified intent (compliance_strict, general_help, etc.)
        citations: List of citation objects already built
        top_docs: List of retrieved documents with metadata
    
    Returns:
        True if citations are available and relevant enough to offer to user
    """
    
    # RULE 1: No citations built? Can't show them (prevents empty pills)
    if not citations or len(citations) == 0:
        return False
    
    # RULE 2: Check if we have high-quality code documents
    has_quality_docs = False
    quality_doc_types = [
        "acceptable_solution_current",
        "acceptable_solution_legacy", 
        "verification_method_current",
        "industry_code_of_practice",
        "nz_standard",
        "nzbc_clauses"  # Added for NZBC direct clause references
    ]
    
    quality_doc_count = 0
    for doc in top_docs[:4]:  # Check top 4 docs (increased from 3)
        doc_type = doc.get('doc_type', '')
        if doc_type in quality_doc_types:
            has_quality_docs = True
            quality_doc_count += 1
    
    # RULE 3: For compliance intents, be permissive
    if intent in ["compliance_strict", "implicit_compliance"]:
        # If we have quality docs, always allow
        if has_quality_docs:
            return True
        # Even without quality doc_type, if question has code signals, allow
        if has_code_signals(question):
            return True
        # No quality docs and no code signals → don't show
        return False
    
    # RULE 4: For general_help / product_info / council_process, be STRICT
    # Only allow citations when:
    # (a) We have quality code documents, AND
    # (b) Question has code signals OR at least 2 quality docs OR brand explicitly named
    if intent in ["general_help", "product_info", "council_process"]:
        # Must have quality docs as baseline
        if not has_quality_docs:
            # ADDITIONAL CHECK (Task 3.3): Block manufacturer manuals for non-brand questions
            # Check if docs are manufacturer/handbook only
            all_non_code = all(
                doc.get('doc_type', '').startswith('manufacturer_') or 
                doc.get('doc_type', '') in ['handbook_guide', 'unknown']
                for doc in top_docs[:3]
            )
            
            if all_non_code:
                # Check if brand is explicitly mentioned
                brands = ['ardex', 'gib', 'james hardie', 'resene', 'pink batts', 
                         'metalcraft', 'colorsteel', 'placemakers', 'bunnings']
                has_brand = any(brand in q_lower for brand in brands)
                
                if not has_brand:
                    # No quality docs, only manuals, no brand mentioned → hide
                    return False
            
            # No quality docs at all → hide
            return False
        
        # Check if question has code signals
        has_signals = has_code_signals(question)
        
        # If explicit code signals, allow
        if has_signals:
            return True
        
        # If 2+ quality docs (strong code match), allow
        if quality_doc_count >= 2:
            return True
        
        # Otherwise, don't show (e.g., "deck bouncing" shouldn't show citations)
        return False
    
    # RULE 5: Fallback for unknown intents - require quality docs
    return has_quality_docs

def should_auto_expand_citations(question: str, intent: str) -> bool:
    """
    Determine if citations should be AUTO-EXPANDED (shown by default)
    
    Enhanced to detect compliance-type questions even without explicit code references.
    Auto-expand for:
    - compliance_strict intent
    - Questions with explicit code references
    - Questions about requirements (min/max/span/fall/clearance/spacing)
    - Questions using requirement language
    
    Args:
        question: User's question
        intent: Classified intent
    
    Returns:
        True if citations should be expanded by default
    """
    
    # Auto-expand for compliance_strict intent
    if intent == "compliance_strict":
        return True
    
    # Auto-expand for implicit_compliance with strong compliance signals
    if intent == "implicit_compliance":
        q_lower = question.lower()
        # Check if asking about specific requirements
        if re.search(r'\b(minimum|maximum|required|span|fall|clearance|spacing|height|width|depth|thickness|cover)\b', q_lower):
            return True
    
    q_lower = question.lower()
    
    # Pattern 1: Explicit code references
    explicit_code_patterns = [
        r'\bwhat does\s+(nzs|e\d|h\d|b\d|c/as|f\d|g\d+)\s+(say|require|specify|state)',
        r'\baccording to\s+(nzs|nzbc|code|standard)',
        r'\bper\s+(nzs|nzbc|code|e\d|h\d)',
        r'\b(nzs|nzbc)\s+\d+\s+(table|clause|section)',
    ]
    
    for pattern in explicit_code_patterns:
        if re.search(pattern, q_lower):
            return True
    
    # Pattern 2: Requirement questions (min/max/span/fall/clearance) + code context
    has_requirement_term = bool(re.search(
        r'\b(?:what(?:\'s| is)?|what(?:\'s| is)?\s+the)\s+(?:minimum|maximum|required|max|min)\b',
        q_lower
    ))
    
    has_measurement_term = bool(re.search(
        r'\b(span|fall|clearance|spacing|height|width|depth|thickness|cover|distance|gap)\b',
        q_lower
    ))
    
    # If asking "what's the minimum X" or "what's the max span", auto-expand
    if has_requirement_term or has_measurement_term:
        # Check if it's a building/construction context (not just "what's the minimum age")
        has_building_context = bool(re.search(
            r'\b(gutter|joist|stud|beam|wall|roof|floor|deck|cladding|'
            r'slab|footing|pile|frame|batten|lining|insulation|'
            r'ground|building|structure|foundation)\b',
            q_lower
        ))
        
        if has_building_context:
            return True
    
    # Pattern 3: Questions about code requirements (even without naming the standard)
    requirement_language_patterns = [
        r'\bwhat(?:\'s| is)?\s+(?:required|needed|necessary)\b',
        r'\bdo i need\b.*\b(?:code|comply|requirement)',
        r'\brequirement for\b',
        r'\bcode require',
    ]
    
    for pattern in requirement_language_patterns:
        if re.search(pattern, q_lower):
            return True
    
    # Otherwise, collapse by default (let user expand if needed)
    return False
