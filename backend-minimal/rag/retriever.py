from typing import List, Dict, Any, Optional
from .db import get_conn, search_embeddings
from .llm import get_embedding, chat_completion
from .prompt import build_context, build_messages

def retrieve_and_answer(
    query: str,
    history: Optional[List[Dict[str, str]]] = None,
    top_k: int = 6
) -> Dict[str, Any]:
    """
    Retrieve relevant documents and generate answer using RAG
    
    Args:
        query: User's question
        history: Optional conversation history
        top_k: Number of documents to retrieve
        
    Returns:
        Dict with answer, notes, and citations
    """
    print(f"\n🔍 Processing query: {query[:100]}...")
    
    # 1. Get database connection
    conn = get_conn()
    if not conn:
        print("⚠️ Database unavailable, returning stub")
        return _stub_response()
    
    # 2. Generate query embedding
    query_embedding = get_embedding(query)
    if not query_embedding:
        print("⚠️ Embedding unavailable, returning stub")
        conn.close()
        return _stub_response()
    
    # 3. Search for relevant documents
    docs = search_embeddings(conn, query_embedding, top_k=top_k)
    conn.close()
    
    if not docs:
        print("⚠️ No documents found, returning stub")
        return _stub_response()
    
    # 4. Build context and messages
    context = build_context(docs)
    messages = build_messages(query, context, history)
    
    # 5. Generate answer
    answer = chat_completion(messages)
    if not answer:
        print("⚠️ LLM unavailable, returning context only")
        answer = "Based on the retrieved documents, please refer to the citations below for detailed information."
    
    # 6. Format citations
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
