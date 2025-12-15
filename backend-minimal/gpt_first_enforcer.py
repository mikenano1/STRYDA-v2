"""
STRYDA GPT-First Output Shape Enforcer
Hard enforcement of minimal, direct answers (no prompt reliance)
"""

import re

def enforce_gpt_first_shape(raw_answer: str, question: str) -> str:
    """
    Enforce 1-2 sentence direct answers for GPT-first mode.
    Remove filler, bullets, and verbose explanations.
    
    Args:
        raw_answer: GPT output
        question: Original question
    
    Returns:
        Enforced minimal answer
    """
    
    if not raw_answer:
        return raw_answer
    
    # Remove markdown bullets
    cleaned = re.sub(r'^\s*[-•*]\s+', '', raw_answer, flags=re.MULTILINE)
    
    # Remove common filler intros
    filler_patterns = [
        r'^When dealing with\s+',
        r'^It\'?s crucial (that|to)\s+',
        r'^Here\'?s how\s+',
        r'^To ensure\s+',
        r'^In order to\s+',
        r'^For proper\s+',
    ]
    
    for pattern in filler_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Split into sentences
    sentences = re.split(r'[.!?]+\s+', cleaned.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Special case: direction/method questions
    q_lower = question.lower()
    is_direction_question = any(phrase in q_lower for phrase in [
        'which way', 'what direction', 'how do i run', 'which direction'
    ])
    
    if is_direction_question and 'underlay' in q_lower:
        # Canned safe template for underlay direction
        if len(sentences) > 0:
            # Use first sentence if it answers direction
            if any(word in sentences[0].lower() for word in ['horizontal', 'vertical', 'parallel', 'perpendicular']):
                return sentences[0] + "."
        
        # Fallback: safe canned answer
        return "Run it horizontally, parallel to the eaves, starting at the bottom and working up."
    
    # Enforce 1-2 sentence max
    if len(sentences) == 0:
        return raw_answer  # Return original if parsing failed
    
    if len(sentences) == 1:
        return sentences[0] + "."
    
    # Two sentences max
    return sentences[0] + ". " + sentences[1] + "."


def remove_bullets_and_formatting(text: str) -> str:
    """Remove markdown bullets and formatting"""
    # Remove bullets
    text = re.sub(r'^\s*[-•*]\s+', '', text, flags=re.MULTILINE)
    
    # Remove bold
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    
    # Remove headings
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    
    # Collapse multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()
