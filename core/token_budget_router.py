"""
STRYDA Token Budget Router
Dynamically sets max_tokens based on question complexity to prevent cut-offs while controlling costs

CHANGELOG:
- v1.2 (June 2025): CRITICAL FIX - Increased max from 3000→4500 for compliance queries
- v1.2: Added fire safety, boundary, combustible keywords for extended responses
- v1.1 (June 2025): Increased base tokens from 1200→1600, max from 2048→3000 to prevent cut-offs
- v1.1: Added safety/compliance keywords for F4, variations, amendments
"""

import re

def pick_max_tokens(mode: str, intent: str, message: str) -> int:
    """
    Determine appropriate max_tokens budget based on mode, intent, and message complexity.
    
    Rules:
    - Strict mode: Always 4500 tokens (comprehensive compliance answers)
    - Fire/Boundary queries: 4500 tokens (MUST complete safety warnings)
    - GPT-first/hybrid: 2000-4500 tokens (dynamic based on complexity)
    
    Args:
        mode: "gpt_first" or "strict_compliance"
        intent: Classified intent
        message: User's message
    
    Returns:
        max_tokens value (int)
    """
    
    msg_lower = message.lower()
    
    # CRITICAL: Fire safety and boundary queries ALWAYS get maximum tokens
    # These queries MUST complete their warnings - truncation is a liability risk
    fire_boundary_keywords = [
        'boundary', 'property line', 'site boundary', 'fire', 'combustible',
        'polystyrene', 'eps', 'styrodrain', 'c/as1', 'c/as2', 'cas1', 'cas2',
        'fire rating', 'fire spread', 'non-combustible', 'flame', 'ignition',
        'basement', 'retaining wall', 'below ground', 'above ground'
    ]
    
    has_fire_boundary = any(keyword in msg_lower for keyword in fire_boundary_keywords)
    
    if has_fire_boundary:
        # Fire/boundary queries get MAXIMUM tokens - no truncation allowed
        return 4500
    
    # Strict compliance always gets full budget
    if mode == "strict_compliance":
        return 4500
    
    # Compliance-related intents get high budget
    if intent in ("compliance_strict", "implicit_compliance"):
        return 4000
    
    # GPT-first/Hybrid starts with higher base
    base_tokens = 2000
    
    # Check for calculation/technical keywords that need more tokens
    calc_keywords = [
        'calculate', 'work out', 'formula', 'diagonal',
        'span', 'spacing', 'pitch', 'fall', 'degrees',
        'gradient', 'ratio', 'load', 'bearing',
        'explain', 'describe', 'how to', 'what is the maximum',
        'what is the minimum', 'how high', 'how far'
    ]
    
    # Table-related keywords that need comprehensive responses
    table_keywords = [
        'stud', 'joist', 'bearer', 'lintel', 'rafter',
        'table 8', 'table 7', 'table 6', 'table 5',
        'wind zone', 'sg8', 'sg10', 'sg6',
        'loadbearing', 'non-loadbearing', 'single storey', 'top storey',
        'loaded dimension', 'maximum span'
    ]
    
    # Safety and compliance keywords (F4, variations, amendments)
    safety_compliance_keywords = [
        'balustrade', 'barrier', 'deck', 'handrail', 'guardrail',
        'height', 'falling', 'safety', 'f4', 'clause f4',
        'variation', 'amendment', 'minor variation', 'change to plans',
        'building consent', 'approved plans', 'consent process',
        'nzbc', 'building code', 'acceptable solution', 'verification method'
    ]
    
    has_calc_words = any(keyword in msg_lower for keyword in calc_keywords)
    has_table_words = any(keyword in msg_lower for keyword in table_keywords)
    has_safety_words = any(keyword in msg_lower for keyword in safety_compliance_keywords)
    
    if has_calc_words or has_table_words or has_safety_words:
        base_tokens = 3000  # Increased for technical/safety/compliance explanations
    
    # Longer questions often need longer answers
    if len(message) > 100:
        base_tokens += 400
    if len(message) > 200:
        base_tokens += 600
    
    # Clamp between 2000 and 4500
    final_tokens = max(2000, min(4500, base_tokens))
    
    return final_tokens
