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
    - GPT-first/hybrid: 1024-2048 tokens (dynamic based on complexity)
    
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
    
    # GPT-first/Hybrid starts with higher base
    base_tokens = 1200  # Increased from 1024
    
    msg_lower = message.lower()
    
    # Check for calculation/technical keywords that need more tokens
    calc_keywords = [
        'calculate', 'work out', 'formula', 'diagonal',
        'span', 'spacing', 'pitch', 'fall', 'degrees',
        'gradient', 'ratio', 'load', 'bearing',
        'explain', 'describe', 'how to'
    ]
    
    # Table-related keywords that need comprehensive responses
    table_keywords = [
        'stud', 'joist', 'bearer', 'lintel', 'rafter',
        'table 8', 'table 7', 'table 6', 'table 5',
        'wind zone', 'sg8', 'sg10', 'sg6',
        'loadbearing', 'non-loadbearing', 'single storey', 'top storey',
        'loaded dimension', 'maximum span'
    ]
    
    has_calc_words = any(keyword in msg_lower for keyword in calc_keywords)
    has_table_words = any(keyword in msg_lower for keyword in table_keywords)
    
    if has_calc_words or has_table_words:
        base_tokens = 1500  # Increased for technical/table explanations
    
    # Longer questions often need longer answers
    if len(message) > 100:
        base_tokens += 200
    if len(message) > 200:
        base_tokens += 300
    
    # Clamp between 1200 and 2048
    final_tokens = max(1200, min(2048, base_tokens))
    
    return final_tokens
