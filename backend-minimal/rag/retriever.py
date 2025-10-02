from typing import List, Dict, Any, Optional
from .db import get_conn, search_embeddings
from .llm import embed_text, chat_completion
from .prompt import build_messages

DEFAULT_TOP_K = 6

def retrieve(query: str, top_k: int = DEFAULT_TOP_K, filters=None):
    """
    Retrieve relevant documents for a query
    
    Args:
        query: Search query
        top_k: Number of results
        filters: Optional filters dict
        
    Returns:
        List of document dicts
    """
    conn = get_conn()
    if not conn:
        return []
    
    q_vec = embed_text(query)
    if not q_vec:
        conn.close()
        return []
    
    hits = search_embeddings(conn, q_vec, top_k=top_k, filters=filters or {})
    conn.close()
    return hits

def retrieve_and_answer(
    query: str,
    history: Optional[List[Dict[str, str]]] = None,
    top_k: int = DEFAULT_TOP_K
) -> Dict[str, Any]:
    """
    Retrieve relevant documents and generate answer using RAG
    
    Args:
        query: User's question
        history: Optional conversation history (currently ignored)
        top_k: Number of documents to retrieve
        
    Returns:
        Dict with answer, notes, and citations
    """
    print(f"\n🔍 Processing query: {query[:100]}...")
    
    # Retrieve documents
    docs = retrieve(query, top_k=top_k)
    
    if not docs:
        print("⚠️ No documents found, returning stub")
        return _stub_response()
    
    # Build messages directly with docs (no separate context step)
    messages = build_messages(query, docs, history)
    
    # Generate answer
    answer = chat_completion(messages)
    if not answer:
        print("⚠️ LLM unavailable, returning context only")
        answer = "Based on the retrieved documents, please refer to the citations below for detailed information."
    
    # Format citations
    citations = [
        {
            "doc_id": str(doc.get("id", "")),
            "source": doc.get("source", "Unknown"),
            "page": doc.get("page", "N/A"),
            "score": round(doc.get("score", 0), 3)
        }
        for doc in docs[:3]  # Top 3 citations
    ]
    
    print(f"✅ Generated answer with {len(citations)} citations")
    
    return {
        "answer": answer,
        "notes": ["retrieval", "backend", "rag"],
        "citations": citations
    }

def _stub_response() -> Dict[str, Any]:
    """Fallback stub response when RAG is unavailable"""
    return {
        "answer": "Service temporarily unavailable. RAG system is not configured or offline.",
        "notes": ["stub", "fallback"],
        "citations": [
            {
                "doc_id": "stub",
                "source": "NZMRM COP",
                "page": "N/A",
                "score": 0.0
            }
        ]
    }
