"""
STRYDA Numeric Leak Guard (GPT-First Mode Only)
Prevents hard compliance numbers from appearing in GPT-first answers
"""

import re

def check_numeric_leak(answer: str, question: str) -> tuple[bool, str, str]:
    """
    Check if GPT-first answer contains explicit numeric requirements.
    
    Args:
        answer: GPT-generated answer
        question: Original user question
    
    Returns:
        (has_leak: bool, action: str, modified_answer: str)
        action: "ok" | "soften" | "ask_clarify" | "defer_to_strict"
    """
    
    if not answer:
        return (False, "ok", answer)
    
    answer_lower = answer.lower()
    
    # Detect explicit numeric requirements
    numeric_requirement_patterns = [
        r'\bminimum\s+\d+\s*(mm|m|metres|°)',
        r'\bmaximum\s+\d+\s*(mm|m|metres|°)',
        r'\bmust\s+be\s+\d+',
        r'\brequired\s+to\s+be\s+\d+',
        r'\bshall\s+be\s+\d+',
        r'\b\d+:\d+\b',  # Ratios like 1:60, 1:200
    ]
    
    has_numeric_leak = any(re.search(p, answer_lower) for p in numeric_requirement_patterns)
    
    if not has_numeric_leak:
        return (False, "ok", answer)
    
    # Leak detected - determine action
    
    # Check if user question implies they want the actual requirement
    wants_requirement = bool(re.search(
        r'\b(what\s+is|what\'s|tell\s+me)\s+the\s+(exact|specific|code|actual|required)\b',
        question.lower()
    ))
    
    if wants_requirement:
        # User wants precision but didn't phrase it strictly
        # Ask clarifying question
        clarify_question = "Do you want the code minimum or general guidance?"
        return (True, "ask_clarify", f"{answer}\n\n{clarify_question}")
    
    # Otherwise, soften the language
    softened = _soften_numeric_language(answer)
    return (True, "soften", softened)


def _soften_numeric_language(answer: str) -> str:
    """
    Replace hard compliance language with softer, general guidance.
    
    Replacements:
    - "minimum 150mm" → "typically 150mm or more"
    - "maximum 3.6m" → "commonly up to 3.6m"
    - "must be" → "often is"
    - "required to be" → "typically"
    """
    
    softened = answer
    
    # Soften minimum/maximum
    softened = re.sub(
        r'\bminimum\s+(\d+\s*(?:mm|m|metres|°))',
        r'typically \1 or more',
        softened,
        flags=re.IGNORECASE
    )
    
    softened = re.sub(
        r'\bmaximum\s+(\d+\s*(?:mm|m|metres|°))',
        r'commonly up to \1',
        softened,
        flags=re.IGNORECASE
    )
    
    # Soften ratios
    softened = re.sub(
        r'\bmust\s+be\s+(1:\d+)',
        r'typically \1',
        softened,
        flags=re.IGNORECASE
    )
    
    # Soften requirement language
    softened = softened.replace("must be", "often is")
    softened = softened.replace("required to be", "typically")
    softened = softened.replace("shall be", "usually is")
    
    return softened
