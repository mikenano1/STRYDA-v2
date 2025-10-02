from typing import List, Dict, Any

SYSTEM_PROMPT = """You are STRYDA, a NZ construction compliance assistant.
- Answer with short, direct sentences.
- Cite sources with document name and page numbers.
- If uncertain, say so and point to the exact doc/section.
- Never invent citations.
- Use NZ spelling and terminology."""

def build_context(docs: List[Dict[str, Any]]) -> str:
    """
    Build context string from retrieved documents
    
    Args:
        docs: List of document dicts with 'content', 'source', 'page', 'score'
        
    Returns:
        Formatted context string
    """
    if not docs:
        return "No relevant documents found."
    
    context_parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.get('source', 'Unknown')
        page = doc.get('page', 'N/A')
        content = doc.get('content', '').strip()
        score = doc.get('score', 0)
        
        context_parts.append(
            f"[Document {i} - {source}, Page {page}, Relevance: {score:.2f}]\n{content}\n"
        )
    
    return "\n---\n".join(context_parts)

def build_messages(query: str, context_chunks: list, history=None):
    """
    Build chat messages for LLM
    
    Args:
        query: User's question
        context_chunks: List of retrieved document dicts
        history: Optional (ignored for simplicity)
        
    Returns:
        List of message dicts for chat completion
    """
    context_text = "\n\n".join(
        [f"[{i+1}] ({c.get('source','?')} p.{c.get('page','?')}, score={round(c.get('score',0),2)}): {c.get('content','').strip()}"
         for i, c in enumerate(context_chunks)]
    )
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Question: {query}\n\nContext:\n{context_text}\n\nAnswer succinctly with citations [source p.page]."}
    ]
    
    return messages
