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
    - GPT-first/hybrid: 1024-1500 tokens (dynamic based on complexity)
    
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
    
    # GPT-first/Hybrid starts with much higher base
    base_tokens = 1024
    
    msg_lower = message.lower()
    
    # Check for calculation/technical keywords that need more tokens
    calc_keywords = [
        'calculate', 'work out', 'formula', 'diagonal',
        'span', 'spacing', 'pitch', 'fall', 'degrees',
        'gradient', 'ratio', 'load', 'bearing',
        'explain', 'describe', 'how to'
    ]
    
    has_calc_words = any(keyword in msg_lower for keyword in calc_keywords)
    
    if has_calc_words:
        base_tokens = 1200  # Need more tokens for technical explanations
    
    # Longer questions often need longer answers
    if len(message) > 140:
        base_tokens += 300
    
    # Clamp between 1024 and 2048
    final_tokens = max(1024, min(2048, base_tokens))
    
    return final_tokens
