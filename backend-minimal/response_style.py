"""
STRYDA Response Style Layer
Transforms LLM answers into conversational, practical Kiwi builder language
"""

import re
from typing import Optional

def apply_answer_style(raw_answer: str, intent: str, user_message: str) -> str:
    """
    Transform raw LLM answer into human, conversational style.
    
    Rules:
    - Start with direct answer (1-2 sentences)
    - Use bullets for details/tips
    - No AI waffle ("As an AI...", "I don't have access to...")
    - Plain NZ English, like a competent tradie
    - Citations stay separate (no clause spam in body)
    - Remove dangling headings (Task 3.5)
    - Truncate at last full stop (Task 3.5)
    
    Args:
        raw_answer: Original LLM response
        intent: Intent classification (compliance_strict, general_help, etc.)
        user_message: Original user question
    
    Returns:
        Cleaned, conversational answer
    """
    
    if not raw_answer or len(raw_answer.strip()) < 10:
        return raw_answer
    
    # Step 1: Remove AI waffle and disclaimers
    cleaned = _remove_ai_waffle(raw_answer)
    
    # Step 2: Apply intent-specific tone
    styled = _apply_intent_tone(cleaned, intent)
    
    # Step 3: Ensure concise structure (direct answer + optional bullets)
    structured = _ensure_concise_structure(styled, intent)
    
    # Step 4: Remove excessive clause references from body (citations handle this)
    final = _declutter_clause_spam(structured)
    
    # Step 5: Remove dangling headings and truncate properly (Task 3.5)
    final = _remove_dangling_headings(final)
    final = _truncate_at_last_sentence(final)
    
    return final.strip()


def _remove_ai_waffle(text: str) -> str:
    """Remove AI-sounding disclaimers and formal language"""
    
    # Patterns to remove entirely
    remove_patterns = [
        r"As an AI language model,?\s*",
        r"I('m| am) (an AI|not able to|unable to|a language model)",
        r"I don't have access to real-time",
        r"I cannot (access|provide|guarantee)",
        r"Please note that",
        r"It'?s important to note that",
        r"It should be noted that",
        r"Keep in mind that",
        r"Bear in mind that",
        r"For more information,?\s*consult",
        r"Always consult (a|an|the) (professional|engineer|expert)",
        r"This is for informational purposes only",
        r"Disclaimer:",
    ]
    
    cleaned = text
    for pattern in remove_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    
    # Replace overly formal phrases
    replacements = {
        r"\bHowever,\b": "But",
        r"\bTherefore,\b": "So",
        r"\bAdditionally,\b": "Also",
        r"\bFurthermore,\b": "Plus",
        r"\bNevertheless,\b": "Still",
        r"\bConsequently,\b": "So",
        r"\bin accordance with\b": "per",
        r"\bprior to\b": "before",
        r"\bsubsequent to\b": "after",
        r"\butilise\b": "use",
        r"\bfacilitate\b": "help",
        r"\bimplement\b": "do",
    }
    
    for formal, casual in replacements.items():
        cleaned = re.sub(formal, casual, cleaned, flags=re.IGNORECASE)
    
    return cleaned


def _apply_intent_tone(text: str, intent: str) -> str:
    """Apply appropriate tone based on intent"""
    
    if intent == "compliance_strict":
        # Confident, clear, but still conversational
        # Already has code context, just keep it clean
        return text
    
    elif intent == "implicit_compliance":
        # Check if we need to mention code alignment
        if not re.search(r"\b(code|standard|nzs|nzbc|requirement)\b", text, re.I):
            # Add a light code reference if missing
            text = text.rstrip()
            if not text.endswith("."):
                text += "."
            text += " Make sure it lines up with the building code."
        return text
    
    elif intent == "general_help":
        # Most conversational - remove any remaining formality
        text = text.replace("optimal", "best")
        text = text.replace("ensure that", "make sure")
        text = text.replace("ensure", "make sure")
        text = text.replace("verify", "check")
        return text
    
    elif intent == "product_info":
        # Practical product guidance
        return text
    
    elif intent == "council_process":
        # Step-by-step, simple
        return text
    
    return text


def _ensure_concise_structure(text: str, intent: str) -> str:
    """
    Restructure to: direct answer + optional bullets
    
    Target structure:
    - First 1-2 sentences: Direct answer
    - Then: Bullet points for details (if needed)
    - Optional final line: "Check the code clauses for exact wording."
    """
    
    lines = text.split("\n")
    
    # Remove excessive blank lines
    cleaned_lines = []
    prev_blank = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if not prev_blank:
                cleaned_lines.append("")
                prev_blank = True
        else:
            cleaned_lines.append(stripped)
            prev_blank = False
    
    # Join back
    text = "\n".join(cleaned_lines).strip()
    
    # If text is already short and punchy, return as-is
    if len(text) < 200 and text.count("\n") <= 3:
        return text
    
    # For longer answers, try to extract key points
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    
    if len(paragraphs) > 3:
        # Take first paragraph as direct answer
        direct_answer = paragraphs[0]
        
        # Condense remaining paragraphs into bullets
        bullets = []
        for para in paragraphs[1:4]:  # Max 3 bullet points
            # Take first sentence of each paragraph
            first_sentence = para.split(".")[0].strip()
            if first_sentence and len(first_sentence) > 10:
                bullets.append(f"- {first_sentence}")
        
        if bullets:
            return f"{direct_answer}\n\n" + "\n".join(bullets)
        else:
            return direct_answer
    
    return text


def _declutter_clause_spam(text: str) -> str:
    """
    Remove excessive inline clause references.
    Citations/pills will show these, so we don't need them cluttering the answer.
    
    Keep first mention of a standard, remove repeats.
    """
    
    # Pattern for clause references like "E2/AS1 clause 4.2.1" or "NZS 3604 Table 7.1"
    clause_pattern = r'\b([A-H]\d+/AS\d+|NZS\s*\d+)\s+(clause|table|section)\s+[\d\.]+\b'
    
    # Find all clause mentions
    mentions = list(re.finditer(clause_pattern, text, re.IGNORECASE))
    
    # If more than 2 mentions, keep only first 2
    if len(mentions) > 2:
        # Remove mentions beyond the first 2
        for match in reversed(mentions[2:]):
            start, end = match.span()
            # Replace with just the standard name (keep first part)
            replacement = match.group(1)
            text = text[:start] + replacement + text[end:]
    
    return text


def add_citation_hint(answer: str, intent: str, has_citations: bool) -> str:
    """
    Optionally add a final line hinting at citations if appropriate.
    
    Only for compliance intents where citations are available.
    """
    
    if not has_citations:
        return answer
    
    # Only add for compliance intents
    if intent not in ["compliance_strict", "implicit_compliance"]:
        return answer
    
    # Check if answer already mentions checking clauses/code
    if re.search(r"\b(check|see|refer to|view|clauses?|citations?)\b", answer, re.I):
        return answer  # Already has a reference
    
    # Add gentle hint
    answer = answer.rstrip()
    if not answer.endswith("."):
        answer += "."
    
    # Random variation to keep it natural
    import random
    hints = [
        " Check the code clauses if you need the exact wording.",
        " The code clauses have the exact requirements if you need them.",
        " View the clauses for the full technical detail.",
    ]
    
    return answer + hints[hash(answer) % len(hints)]
