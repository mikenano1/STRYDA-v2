import re

def generate_snippet(content: str, query: str, max_chars: int = 200) -> str:
    """
    Generate a relevant snippet from document content based on query terms
    Finds best-matching window around query terms
    """
    if not content or not query:
        return content[:max_chars] + "..." if len(content) > max_chars else content
    
    # Extract key terms from query
    query_terms = [term.lower().strip() for term in query.split() if len(term) > 2]
    if not query_terms:
        return content[:max_chars] + "..." if len(content) > max_chars else content
    
    content_lower = content.lower()
    
    # Find positions of query terms
    term_positions = []
    for term in query_terms:
        pos = content_lower.find(term)
        if pos != -1:
            term_positions.append(pos)
    
    if not term_positions:
        # No terms found, return beginning
        return content[:max_chars] + "..." if len(content) > max_chars else content
    
    # Find the best window around the first matching term
    center_pos = min(term_positions)
    
    # Calculate window start and end
    window_start = max(0, center_pos - max_chars // 2)
    window_end = min(len(content), center_pos + max_chars // 2)
    
    snippet = content[window_start:window_end]
    
    # Trim to word boundaries
    if window_start > 0:
        # Find first complete word
        space_pos = snippet.find(' ')
        if space_pos != -1:
            snippet = snippet[space_pos + 1:]
    
    if window_end < len(content):
        # Find last complete word
        space_pos = snippet.rfind(' ')
        if space_pos != -1:
            snippet = snippet[:space_pos]
    
    # Add ellipsis if truncated
    if window_start > 0:
        snippet = "..." + snippet
    if window_end < len(content):
        snippet = snippet + "..."
    
    return snippet[:max_chars] if len(snippet) > max_chars else snippet