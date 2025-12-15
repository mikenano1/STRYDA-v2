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
    # When user asks for specific factual information that needs accurate retrieval
    
    # 1. List/catalogue questions (need comprehensive retrieval)
    if re.search(r'\b(list|what are|all the|types of)\b.*\b(timber|treatment|grade|type)', q_lower):
        return ("strict_compliance", "catalogue_query")
    
    # 2. Specific pitch/angle requirements
    if re.search(r'\b(pitch|angle|degrees?)\b.*\b(require|change|underlay|roof)', q_lower):
        return ("strict_compliance", "pitch_requirement")
    
    # 3. Numeric requirements
    if re.search(r'\b(minimum|maximum|required|must|shall)\s+\d+', q_lower):
        return ("strict_compliance", "numeric_requirement")
    
    if re.search(r'\bwhat\s+is\s+the\s+(minimum|maximum|required)\b', q_lower):
        return ("strict_compliance", "explicit_requirement")
    
    # 4. Code requirement questions
    if re.search(r'\bwhat\s+does\s+(nzs|nzbc|e\d|h\d|b\d|c/as|f\d|g\d+)\s+(say|require|specify)\b', q_lower):
        return ("strict_compliance", "code_lookup")
    
    # 5. Consent/Schedule 1
    if re.search(r'\b(do i need|need)\s+(a\s+)?(consent|building\s+consent)\b', q_lower):
        return ("strict_compliance", "consent_query")
    
    if re.search(r'\b(exempt|exemption|schedule\s*1)\b', q_lower):
        return ("strict_compliance", "exemption_query")
    
    # 6. Specific numeric limits (spans, setbacks, FRR)
    if re.search(r'\b(span|setback|clearance)\s+(for|of)\b', q_lower) and re.search(r'\b\d+x\d+\b', q_lower):
        return ("strict_compliance", "structural_sizing")
    
    if re.search(r'\bmax\s+span\b', q_lower):
        return ("strict_compliance", "span_lookup")
    
    # DEFAULT: GPT can handle naturally
    # Intent does NOT override this
    return ("gpt_first", "default")
