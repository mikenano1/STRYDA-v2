"""
STRYDA Token Budget Router
Dynamically sets max_tokens based on question complexity to prevent cut-offs while controlling costs
"""

import re

def pick_max_tokens(mode: str, intent: str, message: str) -> int:
    """
    Determine appropriate max_tokens budget based on mode, intent, and message complexity.
    
    Rules:
    - Strict mode: Always 450 tokens (comprehensive answers)
    - GPT-first/hybrid: 120-260 tokens (dynamic based on complexity)
    
    Args:
        mode: "gpt_first" or "strict_compliance"
        intent: Classified intent
        message: User's message
    
    Returns:
        max_tokens value (int)
    """
    
    # Strict compliance always gets full budget
    if mode == "strict_compliance":
        return 450
    
    # GPT-first starts with base budget
    base_tokens = 120
    
    msg_lower = message.lower()
    
    # Check for calculation/technical keywords that need more tokens
    calc_keywords = [
        'calculate', 'work out', 'formula', 'diagonal',
        'span', 'spacing', 'pitch', 'fall', 'degrees',
        'gradient', 'ratio', 'load', 'bearing'
    ]
    
    has_calc_words = any(keyword in msg_lower for keyword in calc_keywords)
    
    if has_calc_words:
        base_tokens = 220  # Need more tokens for technical explanations
    
    # Longer questions often need longer answers
    if len(message) > 140:
        base_tokens += 40
    
    # Clamp between 120 and 260
    final_tokens = max(120, min(260, base_tokens))
    
    return final_tokens
