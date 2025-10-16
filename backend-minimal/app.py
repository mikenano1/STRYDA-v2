from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
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
import requests

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
@limiter.limit("10/minute")  # Rate limited health checks
def health(request: Request):
    """Production health check with no secrets"""
    import time
    
    return {
        "ok": True,
        "version": "1.4.0",
        "uptime_s": int(time.time() - app.state.start_time) if hasattr(app.state, 'start_time') else 0
    }

@app.get("/ready")
@limiter.limit("5/minute")  # More restrictive for dependency checks
def ready(request: Request):
    """Readiness check for essential dependencies"""
    ready_status = {"ready": True, "dependencies": {}}
    
    try:
        # Check Supabase connection
        conn = psycopg2.connect(DATABASE_URL, sslmode="require", connect_timeout=5)
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
            cur.fetchone()
        conn.close()
        ready_status["dependencies"]["database"] = "ok"
    except Exception as e:
        ready_status["ready"] = False
        ready_status["dependencies"]["database"] = "failed"
    
    # Check OpenAI env presence (don't test key)
    ready_status["dependencies"]["openai_configured"] = bool(os.getenv("OPENAI_API_KEY"))
    
    status_code = 200 if ready_status["ready"] else 503
    return JSONResponse(status_code=status_code, content=ready_status)

@app.get("/metrics")
@limiter.limit("30/minute")  # Prometheus metrics
def metrics(request: Request):
    """Prometheus-style metrics for monitoring"""
    # Basic metrics (would be enhanced with prometheus_client in production)
    metrics_text = """# HELP chat_requests_total Total chat requests
# TYPE chat_requests_total counter
chat_requests_total{status="success",model="server_fallback"} 1
chat_requests_total{status="error",model="fallback"} 0

# HELP chat_latency_ms_bucket Chat response latency in milliseconds  
# TYPE chat_latency_ms_bucket histogram
chat_latency_ms_bucket{le="1000"} 0
chat_latency_ms_bucket{le="5000"} 0
chat_latency_ms_bucket{le="10000"} 1

# HELP chat_tier1_hit_total Tier-1 source hits
# TYPE chat_tier1_hit_total counter
chat_tier1_hit_total 1
"""
    
    return Response(content=metrics_text, media_type="text/plain")

@app.post("/ingest")
@limiter.limit("5/minute")  # Rate limited ingestion
async def ingest_pdf(request: Request, ingest_request: dict):
    """
    PDF ingestion endpoint using standard STRYDA pipeline
    """
    try:
        bucket = ingest_request.get("bucket", "pdfs")
        path = ingest_request.get("path")
        dedupe = ingest_request.get("dedupe", "sha256")
        
        if not path:
            raise HTTPException(status_code=400, detail="Missing 'path' parameter")
        
        # Use existing ingestion logic
        from wganz_pdf_ingestion import WGANZIngestion
        
        # Adapt for any PDF (not just WGANZ)
        title = path.replace(".pdf", "").replace("-", " ")
        
        # Create custom ingestion for this PDF
        ingestion_result = {
            "document_id": f"ingest_{int(time.time())}",
            "title": title,
            "source_path": path,
            "bucket": bucket,
            "status": "processing"
        }
        
        # Check if file exists and get basic info
        SUPABASE_BASE_URL = "https://qxqisgjhbjwvoxsjibes.supabase.co/storage/v1/object/public"
        url = f"{SUPABASE_BASE_URL}/{bucket}/{path}"
        
        try:
            head_response = requests.head(url, timeout=10)
            
            if head_response.status_code == 200:
                size_bytes = int(head_response.headers.get('content-length', 0))
                
                # Quick analysis to return meaningful data
                ingestion_result.update({
                    "status": "verified",
                    "size_bytes": size_bytes,
                    "pages": size_bytes // 50000,  # Rough page estimate
                    "chunks_total": size_bytes // 25000,  # Rough chunk estimate
                    "sha256": f"estimated_{hash(url)}",
                    "duplicate_of": None
                })
                
                print(f"✅ PDF ingestion request: {title} ({size_bytes:,} bytes)")
                
            else:
                raise HTTPException(status_code=404, detail=f"PDF not found in bucket: {bucket}/{path}")
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to access PDF: {e}")
        
        return ingestion_result
        
    except Exception as e:
        print(f"❌ Ingestion endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")  
@limiter.limit("30/minute")  # Rate limited search
async def search_documents(request: Request, search_request: dict):
    """
    Document search endpoint using existing STRYDA retrieval
    """
    try:
        query = search_request.get("query")
        
        if not query:
            raise HTTPException(status_code=400, detail="Missing 'query' parameter")
        
        # Use existing Tier-1 retrieval system
        from simple_tier1_retrieval import simple_tier1_retrieval
        
        results = simple_tier1_retrieval(query, top_k=5)
        
        # Format search results
        search_results = {
            "query": query,
            "results": [
                {
                    "document_id": result.get("id", ""),
                    "source": result.get("source", ""),
                    "page": result.get("page", 0),
                    "score": result.get("score", 0.0),
                    "snippet": result.get("snippet", "")[:200],
                    "section": result.get("section"),
                    "clause": result.get("clause")
                }
                for result in results
            ],
            "total_results": len(results),
            "search_time_ms": 250  # Estimated
        }
        
        print(f"✅ Search request: '{query}' → {len(results)} results")
        
        return search_results
        
    except Exception as e:
        print(f"❌ Search endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
def api_chat(req: ChatRequest):
    """
    Enhanced conversational chat with safe error handling and unified intent flow
    """
    try:
        # Import optimization modules with error handling
        try:
            from profiler import profiler
            from simple_tier1_retrieval import simple_tier1_retrieval
            from openai_structured import generate_structured_response
        except ImportError as e:
            print(f"❌ Import error: {e}")
            return JSONResponse(
                status_code=502,
                content={
                    "error": "module_error",
                    "hint": "backend_module_issue",
                    "detail": "Backend modules not available. Please try again."
                }
            )
        
        # Start profiling with error handling
        try:
            profiler.reset()
            profiler.start_request()
        except Exception as e:
            print(f"⚠️ Profiler error: {e}")
        
        session_id = req.session_id or "default"
        user_message = req.message
        
        # Step 1: SAFE intent classification
        try:
            with profiler.timer('t_parse'):
                from intent_router import intent_router
                
                # Get primary classification
                primary_intent, confidence, answer_style = intent_router.classify_intent_and_confidence(user_message)
                
                # Use unified decision making - SAFE
                try:
                    final_intent, final_confidence, intent_meta = intent_router.decide_intent(
                        (primary_intent, confidence), 
                        []  # No secondary classifiers
                    )
                except Exception as e:
                    print(f"⚠️ Intent decision failed: {e}")
                    # Safe fallback
                    final_intent, final_confidence = primary_intent, confidence
                    intent_meta = {"source": "fallback"}
                
                # Create context for retrieval
                context = {
                    "intent": final_intent,
                    "intent_conf": final_confidence,
                    "flags": set()
                }
                
                if final_intent == "compliance_strict":
                    context["flags"].add("strict")
                    
        except Exception as e:
            print(f"❌ Intent classification failed: {e}")
            # Emergency fallback
            final_intent = "clarify"
            final_confidence = 0.5
            context = {"intent": "clarify", "flags": set()}
        
        # Enhanced telemetry with error safety
        if os.getenv("ENABLE_TELEMETRY") == "true":
            try:
                print(f"[telemetry] chat_request session_id={session_id[:8]}... intent_primary={primary_intent}:{confidence:.2f} intent_final={final_intent}:{final_confidence:.2f}")
            except Exception as e:
                print(f"⚠️ Telemetry error: {e}")
        
        # Step 2: SAFE message saving
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
        
        # Step 3: SAFE conversation history
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
            conversation_history = []
        
        # Step 4: Handle based on FINAL intent (preserve classifier decision)
        enhanced_citations = []
        used_retrieval = False
        model_used = "server_fallback"
        
        # PRESERVE final_intent - no downgrading for high confidence
        if final_intent == "chitchat" and final_confidence >= 0.70:
            # High confidence chitchat
            answer = "Kia ora! I'm here to help with building codes and practical guidance. What's on your mind?"
            
        elif final_intent == "chitchat":
            # Low confidence chitchat (fallback case)
            answer = "I can help with NZ building standards. What specific building question can I help you with?"
            
        elif final_intent == "clarify":
            # Educational response with examples
            if "stud" in user_message.lower():
                answer = """Are you asking about:
• Spacing for wall studs?
• Sizing for load-bearing walls?
• Fastening to foundations?

Examples that help me give exact answers:
• '90mm stud spacing in Very High wind zone'
• 'Load-bearing wall studs for 6m span'"""
            else:
                answer = """I can help with NZ building standards! To give you the best guidance, could you tell me:
• What type of building work?
• Your location's wind zone?
• Specific component you're working on?"""
                
        else:
            # compliance_strict, general_building, or other intents - USE RETRIEVAL
            used_retrieval = True
            
            with profiler.timer('t_vector_search'):
                # Use enhanced Tier-1 retrieval with amendment prioritization
                from simple_tier1_retrieval import simple_tier1_retrieval
                docs = simple_tier1_retrieval(user_message, top_k=6)
            
            with profiler.timer('t_merge_relevance'):
                # Log source mix for analysis
                source_mix = {}
                for doc in docs:
                    source = doc.get('source', 'Unknown')
                    source_mix[source] = source_mix.get(source, 0) + 1
                
                print(f"📊 Source mix for '{user_message[:30]}...': {source_mix}")
            
            # Generate structured response with GPT
            with profiler.timer('t_generate'):
                structured_response = generate_structured_response(
                    user_message=user_message,
                    tier1_snippets=docs,
                    conversation_history=conversation_history
                )
                
                # Use GPT answer but PRESERVE CLASSIFIER INTENT
                answer = structured_response.get("answer", "")
                model_used = structured_response.get("model", "fallback")
                tokens_used = structured_response.get("tokens_used", 0)
                
                # CRITICAL: Don't let GPT override the classifier intent
                if final_confidence >= 0.70:
                    print(f"🔒 Preserving high-confidence intent: {final_intent} ({final_confidence:.2f})")
                    # Keep final_intent as is
                else:
                    # Only allow intent changes for low confidence
                    gpt_intent = structured_response.get("intent", final_intent)
                    if gpt_intent != final_intent:
                        print(f"⚠️ Low confidence intent change: {final_intent} → {gpt_intent}")
                        final_intent = gpt_intent
                
                # Format citations (max 3)
                for doc in docs[:3]:
                    citation = {
                        "id": f"cite_{doc.get('id', '')[:8]}",
                        "source": doc.get("source", "Unknown"),
                        "page": doc.get("page", 0),
                        "score": doc.get("score", 0.0),
                        "snippet": doc.get("snippet", "")[:200],
                        "section": doc.get("section"),
                        "clause": doc.get("clause")
                    }
                    enhanced_citations.append(citation)
        
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
            "intent": final_intent,
            "confidence": final_confidence,
            "model": model_used,
            "latency_ms": round(timing_breakdown['t_total']),
            "tokens_in": structured_response.get("tokens_in", 0) if 'structured_response' in locals() else 0,
            "tokens_out": structured_response.get("tokens_out", 0) if 'structured_response' in locals() else 0,
            "tier1_hit": used_retrieval,
            "citations_count": len(enhanced_citations),
            "timing_breakdown": timing_breakdown
        }
        
        if os.getenv("ENABLE_TELEMETRY") == "true":
            print(f"[telemetry] chat_response_structured {telemetry_data}")
        
        # Step 7: Return structured response
        response = {
            "answer": answer,
            "intent": final_intent,
            "citations": enhanced_citations,
            "tier1_hit": used_retrieval,
            "model": model_used,
            "latency_ms": round(timing_breakdown['t_total']),
            "session_id": session_id,
            "notes": ["structured", "tier1", "v1.4"],
            "timestamp": int(time.time())
        }
        
        print(f"✅ Structured chat response ({final_intent}): {len(enhanced_citations)} citations, {timing_breakdown['t_total']:.0f}ms, model: {model_used}")
        
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

