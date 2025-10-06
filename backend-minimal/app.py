from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
import os
import time
import psycopg2
import psycopg2.extras

# Load environment variables from .env file
load_dotenv()

from rag.retriever import retrieve_and_answer

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI(title="STRYDA Backend", version="0.2.0")

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HistoryItem(BaseModel):
    role: str
    content: str

class AskRequest(BaseModel):
    query: str
    history: Optional[List[HistoryItem]] = None

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant" 
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = None
    session_id: Optional[str] = None

@app.get("/health")
def health():
    return {"ok": True, "version": "v0.2"}

@app.post("/api/ask")
def api_ask(req: AskRequest):
    """
    Process a query using the RAG pipeline
    """
    try:
        # Use the improved retrieve_and_answer function
        result = retrieve_and_answer(req.query, history=req.history)
        
        # Ensure we return the expected format
        response = {
            "answer": result.get("answer", "Unable to process query"),
            "notes": result.get("notes", ["backend"]),
            "citation": result.get("citations", [])  # Note: citations vs citation
        }
        
        return response
        
    except Exception as e:
        return {
            "answer": "Temporary fallback: backend issue.",
            "notes": ["fallback", "backend", str(e)],
            "citation": []
        }

@app.post("/api/chat")
def api_chat(req: ChatRequest):
    """
    Enhanced multi-turn chat with memory, citations, and preferences
    """
    try:
        # Log request for monitoring
        start_time = time.time()
        
        # Step 1: Save user message to memory
        session_id = req.session_id or "default"
        user_message = req.message
        
        # Production telemetry
        if os.getenv("ENABLE_TELEMETRY") == "true":
            print(f"[telemetry] chat_request session_id={session_id[:8]}... message_length={len(user_message)}")
        
        # Save to chat history
        try:
            conn = psycopg2.connect(DATABASE_URL, sslmode="require")
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO chat_messages (session_id, role, content)
                    VALUES (%s, %s, %s);
                """, (session_id, "user", user_message))
                conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️ Chat memory save failed: {e}")
        
        # Step 2: Get conversation context
        conversation_history = []
        try:
            conn = psycopg2.connect(DATABASE_URL, sslmode="require")
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT role, content 
                    FROM chat_messages 
                    WHERE session_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s;
                """, (session_id, 10))  # Last 10 messages
                
                messages = cur.fetchall()
                conversation_history = [dict(msg) for msg in reversed(messages[:-1])]  # Exclude current message
            conn.close()
        except Exception as e:
            print(f"⚠️ Chat history retrieval failed: {e}")
        
        # Step 3: Use existing RAG system for retrieval
        rag_start = time.time()
        result = retrieve_and_answer(user_message, history=conversation_history)
        rag_time = (time.time() - rag_start) * 1000
        
        # Step 4: Format response with enhanced citations
        answer = result.get("answer", "I don't have specific information about that in my current knowledge base.")
        raw_citations = result.get("citations", [])
        
        # Format citations for multi-turn chat
        enhanced_citations = []
        for cite in raw_citations:
            citation = {
                "source": cite.get("source", "Unknown"),
                "page": cite.get("page", 0),
                "score": cite.get("score", 0.0),
                "snippet": cite.get("snippet", "")[:200]
            }
            
            # Add metadata if available
            if cite.get("section"):
                citation["section"] = cite["section"]
            if cite.get("clause"):
                citation["clause"] = cite["clause"]
                
            enhanced_citations.append(citation)
        
        # Step 5: Save assistant response
        try:
            conn = psycopg2.connect(DATABASE_URL, sslmode="require")
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO chat_messages (session_id, role, content)
                    VALUES (%s, %s, %s);
                """, (session_id, "assistant", answer))
                conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️ Assistant message save failed: {e}")
        
        total_time = (time.time() - start_time) * 1000
        
        # Production telemetry
        if os.getenv("ENABLE_TELEMETRY") == "true":
            print(f"[telemetry] chat_response timing_ms={total_time:.0f} citations_count={len(enhanced_citations)} rag_time_ms={rag_time:.0f}")
        
        # Step 6: Format final response
        response = {
            "message": answer,
            "citations": enhanced_citations,
            "session_id": session_id,
            "notes": ["rag", "multi_turn", "enhanced"],
            "timestamp": int(time.time()),
            "timing_ms": round(total_time)
        }
        
        print(f"✅ Multi-turn chat: {len(enhanced_citations)} citations, {total_time:.0f}ms")
        
        return response
        
    except Exception as e:
        # Production error telemetry
        if os.getenv("ENABLE_TELEMETRY") == "true":
            print(f"[telemetry] chat_error error={str(e)[:50]} session_id={req.session_id or 'default'}")
        
        print(f"❌ Multi-turn chat error: {e}")
        return {
            "message": "I'm temporarily unable to process your message. Please try again.",
            "citations": [],
            "session_id": req.session_id or "default",
            "notes": ["fallback", "chat", str(e)],
            "timestamp": int(time.time())
        }

