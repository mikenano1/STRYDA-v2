"""
STRYDA Token Budget Router
Dynamically sets max_tokens based on question complexity to prevent cut-offs while controlling costs
"""

import re

def pick_max_tokens(mode: str, intent: str, message: str) -> int:
    """
    Determine appropriate max_tokens budget based on mode, intent, and message complexity.
    
    Rules:
    - Strict mode: Always 2048 tokens (comprehensive answers)
    - GPT-first/hybrid: 800-1024 tokens (dynamic based on complexity)
    
    Args:
        mode: "gpt_first" or "strict_compliance"
        intent: Classified intent
        message: User's message
    
    Returns:
        max_tokens value (int)
    """
    
    # Strict compliance always gets full budget
    if mode == "strict_compliance":
        return 2048
    
    # GPT-first starts with base budget
    base_tokens = 800
    
    msg_lower = message.lower()
    
    # Check for calculation/technical keywords that need more tokens
    calc_keywords = [
        'calculate', 'work out', 'formula', 'diagonal',
        'span', 'spacing', 'pitch', 'fall', 'degrees',
        'gradient', 'ratio', 'load', 'bearing'
    ]
    
    has_calc_words = any(keyword in msg_lower for keyword in calc_keywords)
    
    if has_calc_words:
        base_tokens = 1000  # Need more tokens for technical explanations
    
    # Longer questions often need longer answers
    if len(message) > 140:
        base_tokens += 100
    
    # Clamp between 800 and 1024
    final_tokens = max(800, min(1024, base_tokens))
    
    return final_tokens
