#!/usr/bin/env python3
"""
Multi-Turn Chat System with Memory and Enhanced Citations
Implements conversation memory, context-aware retrieval, and bullet-proof citations
"""

import os
import re
import psycopg2
import psycopg2.extras
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv
import time
import json

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
CHAT_MEMORY_BACKEND = os.getenv("CHAT_MEMORY_BACKEND", "db")
CHAT_MAX_TURNS = int(os.getenv("CHAT_MAX_TURNS", "6"))
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "6"))

# In-memory cache for development
memory_cache = {}

class ChatMemory:
    """Chat memory management with DB or in-memory storage"""
    
    @staticmethod
    def save_message(session_id: str, role: str, content: str):
        """Save message to memory backend"""
        if CHAT_MEMORY_BACKEND == "db":
            try:
                conn = psycopg2.connect(DATABASE_URL, sslmode="require")
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO chat_messages (session_id, role, content)
                        VALUES (%s, %s, %s);
                    """, (session_id, role, content))
                    conn.commit()
                conn.close()
            except Exception as e:
                print(f"❌ Failed to save message: {e}")
        else:
            # In-memory fallback
            if session_id not in memory_cache:
                memory_cache[session_id] = []
            memory_cache[session_id].append({
                'role': role,
                'content': content,
                'timestamp': time.time()
            })
    
    @staticmethod
    def get_history(session_id: str, max_turns: int = CHAT_MAX_TURNS) -> List[Dict[str, str]]:
        """Get conversation history for session"""
        if CHAT_MEMORY_BACKEND == "db":
            try:
                conn = psycopg2.connect(DATABASE_URL, sslmode="require")
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                    cur.execute("""
                        SELECT role, content 
                        FROM chat_messages 
                        WHERE session_id = %s
                        ORDER BY created_at DESC
                        LIMIT %s;
                    """, (session_id, max_turns * 2))  # user + assistant pairs
                    
                    messages = cur.fetchall()
                    # Reverse to get chronological order
                    return [dict(msg) for msg in reversed(messages)]
                conn.close()
            except Exception as e:
                print(f"❌ Failed to get history: {e}")
                return []
        else:
            # In-memory fallback
            if session_id not in memory_cache:
                return []
            
            messages = memory_cache[session_id][-max_turns*2:]
            return [{'role': msg['role'], 'content': msg['content']} for msg in messages]

def summarize_for_retrieval(turns: List[str]) -> str:
    """
    Create retrieval query from conversation turns
    Simple join, dedupe, length ≤ 200 chars
    """
    if not turns:
        return ""
    
    # Join turns and extract key terms
    combined = " ".join(turns).lower()
    
    # Extract meaningful terms (remove common words)
    words = re.findall(r'\b[a-z]{3,}\b', combined)
    
    # Remove duplicates while preserving order
    unique_words = []
    seen = set()
    for word in words:
        if word not in seen and word not in ['the', 'and', 'for', 'are', 'what', 'how', 'can', 'you', 'tell', 'about']:
            unique_words.append(word)
            seen.add(word)
    
    # Create query (max 200 chars)
    query = " ".join(unique_words[:20])  # Limit to ~20 terms
    return query[:200]

def retrieve_with_enhanced_citations(query: str, top_k: int = RAG_TOP_K) -> Tuple[List[Dict], float]:
    """
    Retrieve documents with enhanced citations and timing
    Returns: (documents_with_citations, search_time_ms)
    """
    start_time = time.time()
    
    try:
        # Import from existing RAG system that we know works
        from rag.retriever import retrieve
        
        search_start = time.time()
        
        # Use the working retrieve function
        docs = retrieve(query, top_k)
        
        search_time = (time.time() - search_start) * 1000
        
        # Format citations with enhanced metadata
        citations = []
        for doc in docs:
            citation = {
                "source": doc.get("source", "Unknown"),
                "page": doc.get("page", 0), 
                "score": round(float(doc.get("score", 0)), 3),
                "snippet": doc.get("snippet", "") or doc.get("content", "")[:200]
            }
            
            # Add metadata if available
            if doc.get("section"):
                citation["section"] = doc["section"]
            if doc.get("clause"):
                citation["clause"] = doc["clause"]
                
            citations.append(citation)
        
        total_time = (time.time() - start_time) * 1000
        
        print(f"🔍 Retrieval timing: search={search_time:.0f}ms, total={total_time:.0f}ms")
        print(f"📄 Retrieved {len(citations)} documents")
        
        return citations, total_time
        
    except Exception as e:
        print(f"❌ Retrieval failed: {e}")
        return [], 0.0

def build_context_block(citations: List[Dict]) -> str:
    """Build formatted context block for LLM"""
    if not citations:
        return "No relevant documentation found."
    
    context_parts = []
    for i, cite in enumerate(citations, 1):
        source = cite["source"]
        page = cite["page"]
        score = cite["score"]
        snippet = cite["snippet"]
        
        context_parts.append(f"[{i}] Source: {source} p.{page} (score {score})\nSnippet: \"{snippet}\"\n")
    
    return "\n".join(context_parts)

def generate_chat_response(session_id: str, user_message: str) -> Dict[str, Any]:
    """
    Generate multi-turn chat response with memory and citations
    """
    start_time = time.time()
    
    try:
        # Step 1: Save user message
        ChatMemory.save_message(session_id, "user", user_message)
        
        # Step 2: Get conversation history
        history = ChatMemory.get_history(session_id, CHAT_MAX_TURNS)
        
        # Step 3: Build retrieval query from conversation
        user_turns = [msg["content"] for msg in history if msg["role"] == "user"]
        retrieval_query = summarize_for_retrieval(user_turns[-3:])  # Last 3 user turns
        
        if not retrieval_query:
            retrieval_query = user_message
        
        print(f"🔍 Retrieval query: '{retrieval_query}'")
        
        # Step 4: Retrieve with enhanced citations
        citations, retrieval_time = retrieve_with_enhanced_citations(retrieval_query, RAG_TOP_K)
        
        # Step 5: Build context for LLM
        context_block = build_context_block(citations)
        
        # Step 6: Prepare messages for LLM
        system_prompt = """You are STRYDA, a NZ construction compliance assistant.
- Be concise and practical. Use NZ terminology.
- Prefer citing NZ Building Code and NZ Metal Roofing.
- If unsure, say so and point to the nearest relevant section.
- Cite like: [Source p.Page]. Never invent citations."""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent conversation history (compact)
        if len(history) > 2:
            recent_history = history[-4:]  # Last 4 messages (2 turns)
            for msg in recent_history[:-1]:  # Exclude current user message
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"][:200]  # Truncate for token management
                })
        
        # Add current user message with context
        user_content = f"Question: {user_message}\n\nAvailable documentation:\n{context_block}"
        messages.append({"role": "user", "content": user_content})
        
        # Step 7: Generate response
        llm_start = time.time()
        
        try:
            from rag.llm import chat_completion
            
            answer = chat_completion(
                messages=messages,
                model="gpt-4o-mini",
                temperature=0.2,
                max_tokens=500
            )
            
            llm_time = (time.time() - llm_start) * 1000
            
            if not answer:
                answer = "I'm having trouble accessing my knowledge base right now. Could you try rephrasing your question?"
                notes = ["fallback", "llm_error"]
            else:
                notes = ["rag", "multi_turn"]
            
        except Exception as e:
            print(f"❌ LLM call failed: {e}")
            answer = "I'm temporarily unable to process your question. Please try again."
            notes = ["fallback", "llm_error"]
            llm_time = 0
        
        # Step 8: Save assistant response
        ChatMemory.save_message(session_id, "assistant", answer)
        
        total_time = (time.time() - start_time) * 1000
        
        print(f"⏱️ Total timing: retrieval={retrieval_time:.0f}ms, llm={llm_time:.0f}ms, total={total_time:.0f}ms")
        
        # Step 9: Format response
        response = {
            "message": answer,
            "citations": citations if citations else [],
            "session_id": session_id,
            "notes": notes,
            "timing": {
                "retrieval_ms": round(retrieval_time),
                "llm_ms": round(llm_time),
                "total_ms": round(total_time)
            }
        }
        
        return response
        
    except Exception as e:
        print(f"❌ Chat generation failed: {e}")
        return {
            "message": "I encountered an error processing your message. Please try again.",
            "citations": [],
            "session_id": session_id,
            "notes": ["fallback", "system_error"]
        }

if __name__ == "__main__":
    # Test the system
    print("🧪 Testing multi-turn chat system...")
    
    # Test 1: Single turn
    print("\nTest 1: Single turn")
    response1 = generate_chat_response("test_session", "What is apron flashing minimum cover?")
    print(f"Response: {response1['message'][:100]}...")
    print(f"Citations: {len(response1['citations'])}")
    
    # Test 2: Multi-turn follow-up
    print("\nTest 2: Multi-turn follow-up")
    response2 = generate_chat_response("test_session", "What about very high wind zones?")
    print(f"Response: {response2['message'][:100]}...")
    print(f"Citations: {len(response2['citations'])}")
    
    print(f"\n✅ Multi-turn chat system tested")