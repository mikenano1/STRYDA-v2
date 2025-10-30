"""
Web Search Helper for STRYDA V2
Provides lightweight web search for general/product queries only.
Uses web_search_tool_v2 when available, graceful fallback otherwise.
"""

import os
from typing import List


def web_search(query: str, max_results: int = 3, timeout: float = 6.0) -> List[str]:
    """
    Perform web search and return snippets.
    
    Args:
        query: Search query
        max_results: Maximum number of results to return
        timeout: Request timeout in seconds
    
    Returns:
        List of text snippets from search results
        Returns empty list on any error (graceful fallback)
    """
    try:
        # Check if web search is enabled
        if not os.getenv("ENABLE_WEB_SEARCH", "true").lower() == "true":
            return []
        
        # Placeholder: In production, integrate with web_search_tool_v2
        # For now, return empty list to enable graceful fallback
        # TODO: Integrate with actual web search API
        
        # Example integration point:
        # from web_search_tool_v2 import search
        # results = search(query, max_results=max_results, timeout=timeout)
        # return [r.get("snippet", "") for r in results]
        
        return []
        
    except Exception as e:
        # Never raise - always graceful fallback
        print(f"⚠️ Web search failed (query: {query[:50]}...): {e}")
        return []


def summarize_snippets(snippets: List[str]) -> str:
    """
    Combine web search snippets into a short summary paragraph.
    
    Args:
        snippets: List of text snippets from web search
    
    Returns:
        Combined summary text, or empty string if no snippets
    """
    if not snippets:
        return ""
    
    # Filter out empty snippets
    valid_snippets = [s.strip() for s in snippets if s and s.strip()]
    
    if not valid_snippets:
        return ""
    
    # Join snippets with spacing
    # Limit to reasonable length (avoid token overflow)
    combined = " ".join(valid_snippets[:3])
    
    # Truncate if too long (keep under 500 chars for context)
    if len(combined) > 500:
        combined = combined[:497] + "..."
    
    return combined


def should_use_web_search(intent: str, enable_web_search: bool) -> bool:
    """
    Determine if web search should be used based on intent.
    
    Args:
        intent: Classified intent (compliance_strict, general_help, etc.)
        enable_web_search: Feature flag from environment
    
    Returns:
        True if web search should be attempted
    """
    # Only use web search for general/product queries
    web_search_intents = {"general_help", "product_info"}
    
    # Must be enabled AND correct intent
    return enable_web_search and intent in web_search_intents


# Integration example for app.py:
"""
from web_search import web_search, summarize_snippets, should_use_web_search

# In /api/chat handler:
intent = detect_intent(user_message)
enable_web = os.getenv("ENABLE_WEB_SEARCH", "true").lower() == "true"

web_context = ""
use_web = False

if should_use_web_search(intent, enable_web):
    use_web = True
    snippets = web_search(user_message, max_results=3, timeout=6.0)
    web_context = summarize_snippets(snippets)
    if web_context:
        # Add to prompt context
        context += f"\n\nAdditional web context: {web_context}"

# Log the decision
print(f"[chat] intent={intent} use_web={use_web} model={OPENAI_MODEL} pills={CLAUSE_PILLS}")
"""
