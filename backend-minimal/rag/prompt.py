from typing import List, Dict, Any

SYSTEM_PROMPT = """You are STRYDA, an AI assistant specialized in New Zealand building codes and construction standards. 

Your role is to:
- Provide accurate, cited answers from official NZ building codes and manufacturer specifications
- Always cite the specific document, section, and page when referencing information
- Be concise and practical for on-site use
- If you don't have relevant information in the context, say so clearly

Guidelines:
- Use clear, professional language
- Break down complex requirements into actionable steps
- Highlight safety-critical information
- Cite document sources with page numbers"""

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

def build_messages(
    query: str, 
    context: str, 
    history: List[Dict[str, str]] = None
) -> List[Dict[str, str]]:
    """
    Build chat messages for LLM
    
    Args:
        query: User's question
        context: Retrieved document context
        history: Optional conversation history
        
    Returns:
        List of message dicts for chat completion
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    
    # Add conversation history if provided
    if history:
        for msg in history[-4:]:  # Keep last 4 messages for context
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
    
    # Add current query with context
    user_message = f"""Context from NZ building codes and specifications:

{context}

Question: {query}

Please provide a clear, cited answer based on the context above. Include specific document references and page numbers."""
    
    messages.append({"role": "user", "content": user_message})
    
    return messages
