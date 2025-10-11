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

# CORS for development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.emergent.sh",
        "https://onsite-copilot.preview.emergentagent.com",
        "http://localhost:3000",
        "http://localhost:19006",
        "http://localhost:8001",
        "*"  # Allow all for development
    ],
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
    Conversational multi-turn chat with intent routing
    """
    try:
        start_time = time.time()
        session_id = req.session_id or "default"
        user_message = req.message
        
        # Import intent router
        from intent_router import intent_router
        
        # Step 1: Enhanced intent classification
        intent, confidence, answer_style = intent_router.classify_intent_and_confidence(user_message)
        retrieval_params = intent_router.get_retrieval_params(intent, answer_style)
        system_prompt = intent_router.get_system_prompt(intent, answer_style)
        
        # Telemetry with enhanced metrics
        if os.getenv("ENABLE_TELEMETRY") == "true":
            print(f"[telemetry] chat_request session_id={session_id[:8]}... intent={intent} confidence={confidence:.2f} answer_style={answer_style} message_length={len(user_message)}")
        
        # Step 2: Save user message
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
        
        # Step 3: Get conversation history for context
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
                """, (session_id, 10))
                
                messages = cur.fetchall()
                conversation_history = [dict(msg) for msg in reversed(messages[:-1])]
            conn.close()
        except Exception as e:
            print(f"⚠️ Chat history retrieval failed: {e}")
        
        # Step 4: Handle based on intent
        enhanced_citations = []
        used_retrieval = False
        
        if intent == "chitchat":
            # Direct friendly response, no retrieval
            answer = "Hey! I'm here to help with NZ building codes. Ask me anything about flashing, roofing, or building requirements!"
            
        elif intent == "clarify":
            # Educational response with optional light retrieval
            answer = "I can help with NZ building standards! Are you looking for:\n• Specific building code requirements?\n• Metal roofing installation guides?\n• Weatherproofing standards?\n\nWhat's your specific project or question?"
            
        else:
            # general_building or compliance_strict - do full RAG
            used_retrieval = True
            rag_start = time.time()
            result = retrieve_and_answer(user_message, history=conversation_history)
            rag_time = (time.time() - rag_start) * 1000
            
            answer = result.get("answer", "I don't have specific information about that in my current knowledge base.")
            raw_citations = result.get("citations", [])
            
            # Apply citation threshold based on intent
            citation_threshold = retrieval_params["citation_threshold"]
            
            for cite in raw_citations:
                if cite.get("score", 0) >= citation_threshold:
                    citation = {
                        "id": f"cite_{cite.get('doc_id', '')[:8]}",
                        "source": cite.get("source", "Unknown"),
                        "page": cite.get("page", 0),
                        "score": cite.get("score", 0.0),
                        "snippet": cite.get("snippet", "")[:200],
                        "section": cite.get("section"),
                        "clause": cite.get("clause")
                    }
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
        
        # Enhanced telemetry
        if os.getenv("ENABLE_TELEMETRY") == "true":
            print(f"[telemetry] chat_response intent={intent} timing_ms={total_time:.0f} citations_count={len(enhanced_citations)} used_retrieval={used_retrieval}")
        
        # Step 6: Format response
        response = {
            "message": answer,
            "citations": enhanced_citations,
            "session_id": session_id,
            "intent": intent,
            "notes": ["rag", "multi_turn", "conversational"],
            "timestamp": int(time.time()),
            "timing_ms": round(total_time)
        }
        
        print(f"✅ Conversational chat ({intent}): {len(enhanced_citations)} citations, {total_time:.0f}ms")
        
        return response
        
    except Exception as e:
        if os.getenv("ENABLE_TELEMETRY") == "true":
            print(f"[telemetry] chat_error error={str(e)[:50]} session_id={req.session_id or 'default'}")
        
        print(f"❌ Conversational chat error: {e}")
        return {
            "message": "I'm temporarily unable to process your message. Please try again.",
            "citations": [],
            "session_id": req.session_id or "default",
            "intent": "error",
            "notes": ["fallback", "chat", str(e)],
            "timestamp": int(time.time())
        }

