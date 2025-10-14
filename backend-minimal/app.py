from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
import os
import time
import json
import psycopg2
import psycopg2.extras
import asyncio

# Load environment variables first
load_dotenv()

# Security and rate limiting
limiter = Limiter(key_func=get_remote_address)

# Import validation and modules
from validation import validate_input, validate_output
from rag.retriever import retrieve_and_answer
from profiler import profiler

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")
API_KEY = os.getenv("OPENAI_API_KEY")

# Environment validation (fail fast)
required_env_vars = ["DATABASE_URL"]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]

if missing_vars:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

app = FastAPI(
    title="STRYDA Backend", 
    version="1.4.0",
    docs_url=None,  # Disable docs in production
    redoc_url=None   # Disable redoc in production
)

# Security middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Enhanced CORS for production security
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.emergent.sh",
        "https://onsite-copilot.preview.emergentagent.com",
        "http://localhost:3000",  # Dev only
    ],
    allow_credentials=False,  # Enhanced security
    allow_methods=["GET", "POST"],  # Specific methods only
    allow_headers=["Content-Type", "Authorization"],
)

# Security headers middleware
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Production security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY" 
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Remove server info
    if "server" in response.headers:
        del response.headers["server"]
    
    return response

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
    Enhanced conversational chat with GPT-5 structured JSON output
    """
    import asyncio
    from openai_structured import generate_structured_response
    
    try:
        # Start enhanced profiling
        profiler.reset()
        profiler.start_request()
        
        session_id = req.session_id or "default"
        user_message = req.message
        
        # Step 1: Intent classification with profiling
        with profiler.timer('t_parse'):
            from intent_router import intent_router
            intent, confidence, answer_style = intent_router.classify_intent_and_confidence(user_message)
        
        # Enhanced telemetry
        if os.getenv("ENABLE_TELEMETRY") == "true":
            print(f"[telemetry] chat_request session_id={session_id[:8]}... intent={intent} confidence={confidence:.2f} message_length={len(user_message)}")
        
        # Step 2: Save user message (async-safe)
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
        
        # Step 3: Get conversation history
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
                """, (session_id, 6))
                
                messages = cur.fetchall()
                conversation_history = [dict(msg) for msg in reversed(messages[:-1])]
            conn.close()
        except Exception as e:
            print(f"⚠️ Chat history retrieval failed: {e}")
        
        # Step 4: Enhanced response generation
        tier1_hit = False
        tier1_snippets = []
        
        if intent != "chitchat":
            # Get Tier-1 retrieval for context
            with profiler.timer('t_vector_search'):
                from simple_tier1_retrieval import simple_tier1_retrieval
                docs = simple_tier1_retrieval(user_message, top_k=6)
                tier1_hit = len(docs) > 0
                tier1_snippets = docs
        
        # Step 5: Generate structured response with timeout and retries
        with profiler.timer('t_generate'):
            try:
                structured_response = generate_structured_response(
                    user_message=user_message,
                    tier1_snippets=tier1_snippets,
                    conversation_history=conversation_history
                )
                
                # Strict JSON validation
                required_fields = ['answer', 'intent', 'citations']
                for field in required_fields:
                    if field not in structured_response:
                        raise ValueError(f"Missing required field: {field}")
                
                answer = structured_response.get("answer", "")
                response_intent = structured_response.get("intent", intent)
                response_citations = structured_response.get("citations", [])
                
                # Safety merge: Use server-side citations if model didn't provide
                if not response_citations and tier1_snippets:
                    response_citations = [
                        {
                            "id": f"cite_{doc.get('id', '')[:8]}",
                            "source": doc.get("source", "Unknown"),
                            "page": doc.get("page", 0),
                            "score": doc.get("score", 0.0),
                            "snippet": doc.get("snippet", "")[:200],
                            "section": doc.get("section"),
                            "clause": doc.get("clause")
                        }
                        for doc in tier1_snippets[:3]
                    ]
                
                # Ensure citations are properly formatted
                formatted_citations = []
                for cite in response_citations[:3]:  # Max 3 citations
                    if isinstance(cite, dict):
                        formatted_citation = {
                            "id": cite.get("id", f"cite_{hash(cite.get('source', ''))}"),
                            "source": cite.get("source", "Unknown"),
                            "page": cite.get("page", 0),
                            "score": cite.get("score", 0.0),
                            "snippet": str(cite.get("snippet", ""))[:200],
                            "section": cite.get("section"),
                            "clause": cite.get("clause")
                        }
                        formatted_citations.append(formatted_citation)
                
                model_used = structured_response.get("model", "gpt-4o-mini")
                tokens_used = structured_response.get("tokens_used", 0)
                
            except json.JSONDecodeError as e:
                # Strict JSON enforcement - return 502 for invalid model output
                print(f"❌ JSON parse error from model: {e}")
                return JSONResponse(
                    status_code=502,
                    content={
                        "error": "bad_json",
                        "hint": "model_output_invalid", 
                        "detail": "The AI model returned invalid JSON. Please try again."
                    }
                )
            except Exception as e:
                print(f"❌ Structured generation failed: {e}")
                
                # Fallback with server-side citations
                answer = "I encountered an issue processing your question. Let me provide what I can find in the building standards."
                formatted_citations = [
                    {
                        "id": f"cite_{doc.get('id', '')[:8]}",
                        "source": doc.get("source", "Unknown"),
                        "page": doc.get("page", 0),
                        "score": doc.get("score", 0.0),
                        "snippet": doc.get("snippet", "")[:200],
                        "section": doc.get("section"),
                        "clause": doc.get("clause")
                    }
                    for doc in tier1_snippets[:3]
                ] if tier1_snippets else []
                
                model_used = "fallback"
                tokens_used = 0
        
        # Step 6: Save assistant response
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
        
        # Finish profiling
        profiler.finish_request()
        timing_breakdown = profiler.get_breakdown()
        
        # Enhanced telemetry with GPT-5 metrics
        telemetry_data = {
            "status": "success",
            "intent": response_intent,
            "confidence": confidence,
            "model": model_used,
            "latency_ms": round(timing_breakdown['t_total']),
            "tokens_in": structured_response.get("tokens_in", 0) if 'structured_response' in locals() else 0,
            "tokens_out": structured_response.get("tokens_out", 0) if 'structured_response' in locals() else 0,
            "tier1_hit": tier1_hit,
            "citations_count": len(formatted_citations),
            "timing_breakdown": timing_breakdown
        }
        
        if os.getenv("ENABLE_TELEMETRY") == "true":
            print(f"[telemetry] chat_response_structured {telemetry_data}")
        
        # Step 7: Return structured response
        response = {
            "answer": answer,
            "intent": response_intent,
            "citations": formatted_citations,
            "tier1_hit": tier1_hit,
            "model": model_used,
            "latency_ms": round(timing_breakdown['t_total']),
            "session_id": session_id,
            "notes": ["structured", "tier1", "v1.4"],
            "timestamp": int(time.time())
        }
        
        print(f"✅ Structured chat response ({response_intent}): {len(formatted_citations)} citations, {timing_breakdown['t_total']:.0f}ms, model: {model_used}")
        
        return response
        
    except Exception as e:
        # Enhanced error telemetry
        if os.getenv("ENABLE_TELEMETRY") == "true":
            error_msg = str(e)
            # Mask API key in error logs
            if "sk-" in error_msg:
                error_msg = error_msg.replace(API_KEY[:20] if API_KEY else "", "sk-***")
            
            print(f"[telemetry] chat_error status=error latency_ms={profiler.timers.get('t_total', 0):.0f} error={error_msg[:100]}")
        
        print(f"❌ Enhanced chat error: {e}")
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "hint": "processing_failed",
                "detail": "I'm temporarily unable to process your message. Please try again.",
                "session_id": req.session_id or "default",
                "timestamp": int(time.time())
            }
        )

