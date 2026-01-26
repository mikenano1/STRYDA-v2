"""
STRYDA Response Mode Router
Determines whether to use GPT-first or strict compliance mode per turn

PRIMARY SIGNAL: User phrasing (demands precision)
SECONDARY SIGNAL: Intent (support only, never forces strict)
"""

import re

def determine_response_mode(question: str, intent: str) -> tuple[str, str]:
    """
    Route each question to either 'gpt_first' or 'strict_compliance' mode.
    
    CRITICAL: Phrasing is PRIMARY. Intent is SECONDARY support only.
    Intent alone NEVER triggers strict_compliance.
    
    Args:
        question: User's question
        intent: Classified intent (support signal only)
    
    Returns:
        (mode: str, trigger_reason: str)
        mode: "gpt_first" or "strict_compliance"
        trigger_reason: why this mode was selected
    """
    
    q_lower = question.lower()
    
    # STRICT COMPLIANCE TRIGGERS (phrasing only)
    # ONLY for legal/consent questions that need citations
    
    # 1. Consent/Schedule 1 (legal risk - need citations)
    if re.search(r'\b(do i need|need)\s+(a\s+)?(consent|building\s+consent)\b', q_lower):
        return ("strict_compliance", "consent_query")
    
    if re.search(r'\b(exempt|exemption|schedule\s*1)\b', q_lower):
        return ("strict_compliance", "exemption_query")
    
    # 2. Explicit "what does code say" (user wants citations)
    if re.search(r'\bwhat\s+does\s+(nzs|nzbc|e\d|h\d|b\d|c/as|f\d|g\d+)\s+(say|require|specify)\b', q_lower):
        return ("strict_compliance", "code_lookup")
    
    # 3. User explicitly asks for code/standard reference
    if re.search(r'\b(according to|per|under)\s+(nzs|nzbc|code|e\d|h\d|b\d)\b', q_lower):
        return ("strict_compliance", "code_reference")
    
    # DEFAULT: Hybrid mode (full retrieval + natural synthesis, no citations)
    # This includes: pitch questions, timber lists, spans, etc.
    return ("gpt_first", "default")
