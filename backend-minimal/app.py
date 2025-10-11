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
        
        # Step 4: Handle based on intent with enhanced styling
        enhanced_citations = []
        used_retrieval = False
        show_sources_button = False
        
        if intent == "chitchat":
            # Friendly conversational response
            answer = "Hey! I'm here to help with NZ building codes and standards. Ask me about flashing, roofing, fasteners, or any building requirements!"
            
        elif intent == "clarify":
            # Educational guidance with targeted questions
            if "stud" in user_message.lower():
                answer = "I can help with stud requirements! Are you asking about:\n• Spacing for wall studs?\n• Sizing for load-bearing walls?\n• Fastening to foundations?\n\nWhat type of construction and wind zone?"
            elif "roofing" in user_message.lower():
                answer = "For roofing guidance, I need to know:\n• What type of roof (metal, membrane, tile)?\n• Roof pitch and wind zone?\n• New construction or repair?\n\nThis helps me give you the right requirements!"
            else:
                answer = "I can help with NZ building standards! To give you the best guidance, could you tell me:\n• What type of building work?\n• Your location's wind zone?\n• Specific component you're working on?"
                
        elif answer_style == "practical_guidance":
            # Step-by-step trade-friendly guidance
            used_retrieval = True
            rag_start = time.time()
            result = retrieve_and_answer(user_message, history=conversation_history)
            
            # Format as practical guidance
            raw_answer = result.get("answer", "")
            answer = f"Here's what you need to check:\n\n{raw_answer}\n\n💡 Key points: Verify your wind zone classification and local council requirements."
            
            # Only show citations if confidence is low or specific compliance mentioned
            raw_citations = result.get("citations", [])
            if confidence < 0.65 or "clause" in user_message.lower():
                show_sources_button = True
                # Store citations for "Show sources" button
                for cite in raw_citations[:3]:
                    if cite.get("score", 0) >= 0.70:
                        enhanced_citations.append({
                            "id": f"cite_{cite.get('doc_id', '')[:8]}",
                            "source": cite.get("source", "Unknown"),
                            "page": cite.get("page", 0),
                            "score": cite.get("score", 0.0),
                            "snippet": cite.get("snippet", "")[:200],
                            "section": cite.get("section"),
                            "clause": cite.get("clause")
                        })
            
        else:
            # compliance_strict or unknown - full RAG with citations
            used_retrieval = True
            rag_start = time.time()
            result = retrieve_and_answer(user_message, history=conversation_history)
            
            answer = result.get("answer", "I don't have specific information about that in my current knowledge base.")
            raw_citations = result.get("citations", [])
            
            # Always include citations for compliance queries (max 3)
            for cite in raw_citations[:3]:
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
        
        # Enhanced telemetry with confidence
        if os.getenv("ENABLE_TELEMETRY") == "true":
            telemetry_data = {
                "intent": intent,
                "confidence": confidence,
                "timing_ms": round(total_time),
                "citations_count": len(enhanced_citations),
                "used_retrieval": used_retrieval,
                "answer_style": answer_style
            }
            print(f"[telemetry] chat_response {telemetry_data}")
        
        # Step 6: Format response with enhanced metadata
        response = {
            "message": answer,
            "citations": enhanced_citations,
            "session_id": session_id,
            "intent": intent,
            "confidence": confidence,
            "answer_style": answer_style,
            "show_sources_button": show_sources_button,
            "notes": ["rag", "multi_turn", "conversational", "v1.2.1"],
            "timestamp": int(time.time()),
            "timing_ms": round(total_time)
        }
        
        print(f"✅ Conversational chat v1.2.1 ({intent}, {answer_style}): {len(enhanced_citations)} citations, {total_time:.0f}ms")
        
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

