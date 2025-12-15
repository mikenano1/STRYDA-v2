"""
STRYDA Response Mode Router
Determines whether to use GPT-first or strict compliance mode per turn
"""

import re

def determine_response_mode(question: str, intent: str) -> str:
    """
    Route each question to either 'gpt_first' or 'strict_compliance' mode.
    
    Rules:
    - strict_compliance: ONLY when precision or legal risk exists
    - gpt_first: Default for all other questions
    
    Args:
        question: User's question
        intent: Classified intent (locked for conversation)
    
    Returns:
        "gpt_first" or "strict_compliance"
    """
    
    q_lower = question.lower()
    
    # STRICT COMPLIANCE TRIGGERS (precision/legal risk required)
    strict_patterns = [
        # Explicit requirements
        r'\b(minimum|maximum|required|shall|must)\s+\d+',
        r'\b(what\s+is|what\'s)\s+the\s+(minimum|maximum|required)\b',
        r'\bwhat\s+does\s+(nzs|nzbc|e\d|h\d|b\d|c/as|f\d|g\d+)\s+(say|require|specify|state)\b',
        
        # Consent/Schedule 1
        r'\b(do i need|need)\s+(a\s+)?(consent|building\s+consent)\b',
        r'\b(exempt|exemption|schedule\s*1)\b',
        
        # Spans and structural
        r'\b(span|setback|clearance|spacing)\s+(for|of|with)\b',
        r'\b(max|maximum)\s+span\b',
        r'\bjoist\s+span\b',
        
        # Fire safety
        r'\b(fire\s+rating|frr|fire\s+separation)\b',
        r'\bc/as\d+\b',
        
        # Plumbing/drainage limits
        r'\b(gully\s+trap|waste\s+pipe|cylinder\s+temp|backflow)\b',
        r'\b(fall|gradient)\s+(for|on|of)\s+(pipe|drain|gutter)\b',
        
        # Structural limits
        r'\b(foundation|footing|slab)\s+(depth|thickness|reinforcement)\b',
        r'\b(beam|lintel|bearer)\s+(size|sizing)\b',
    ]
    
    # Check if question matches strict patterns
    for pattern in strict_patterns:
        if re.search(pattern, q_lower):
            return "strict_compliance"
    
    # Intent-based routing (additional safety)
    if intent == "compliance_strict":
        return "strict_compliance"
    
    # Default: GPT can handle naturally
    return "gpt_first"
