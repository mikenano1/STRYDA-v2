from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
import os
import time
import json
import psycopg2
import psycopg2.extras

# Load environment variables from .env file
load_dotenv()

from rag.retriever import retrieve_and_answer
from profiler import profiler

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
    Optimized conversational chat with profiling and hybrid retrieval (v1.3.3)
    """
    # Import optimization modules
    from profiler import profiler
    from hybrid_retrieval import hybrid_retrieval_optimized
    
    try:
        # Start profiling
        profiler.reset()
        profiler.start_request()
        
        session_id = req.session_id or "default"
        user_message = req.message
        
        # Step 1: Intent classification with profiling
        with profiler.timer('t_parse'):
            from intent_router import intent_router
            intent, confidence, answer_style = intent_router.classify_intent_and_confidence(user_message)
            retrieval_params = intent_router.get_retrieval_params(intent, answer_style)
        
        # Enhanced telemetry
        if os.getenv("ENABLE_TELEMETRY") == "true":
            print(f"[telemetry] chat_request session_id={session_id[:8]}... intent={intent} confidence={confidence:.2f} answer_style={answer_style}")
        
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
                """, (session_id, 10))
                
                messages = cur.fetchall()
                conversation_history = [dict(msg) for msg in reversed(messages[:-1])]
            conn.close()
        except Exception as e:
            print(f"⚠️ Chat history retrieval failed: {e}")
        
        # Step 4: Handle based on intent with optimized retrieval
        enhanced_citations = []
        used_retrieval = False
        cache_hit = False
        top_sources = []
        
        if intent == "chitchat":
            # Direct friendly response
            answer = "Kia ora! I'm here to help with building codes and practical guidance. What's on your mind?"
            
        elif intent == "clarify":
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
• Specific component you're working on?

Examples:
• 'Reroofing Colorsteel in high wind zone'
• 'Internal wall framing for kitchen extension'"""
                
        elif answer_style == "practical_guidance":
            # Optimized retrieval for how-to
            used_retrieval = True
            
            with profiler.timer('t_hybrid_keyword'):
                # Use working Tier-1 retrieval (no Decimal issues)
                from simple_tier1_retrieval import simple_tier1_retrieval
                docs = simple_tier1_retrieval(user_message, top_k=6)
            
            with profiler.timer('t_merge_relevance'):
                # Extract top sources for telemetry
                top_sources = [doc.get('source', '') for doc in docs[:3]]
                
                # Format practical guidance with Tier-1 content
                if docs:
                    tier1_content = docs[0].get('content', '')[:200] + "..."
                    answer = f"""Here's the guidance you need:

Based on the building standards:
{tier1_content}

💡 Key points: Check your specific wind zone and verify requirements with your local building consent authority."""
                else:
                    answer = "I can provide guidance on that. Could you be more specific about your building project and wind zone?"
            
            # Show citations for compliance-related queries or low confidence
            if confidence < 0.65 or "clause" in user_message.lower() or any(term in user_message.lower() for term in ['minimum', 'maximum', 'requirement']):
                enhanced_citations = []
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
            
        else:
            # compliance_strict or unknown - use working Tier-1 retrieval
            used_retrieval = True
            
            with profiler.timer('t_embed_query'):
                # Use working Tier-1 retrieval for compliance queries
                from simple_tier1_retrieval import simple_tier1_retrieval
                
            with profiler.timer('t_vector_search'):
                docs = simple_tier1_retrieval(user_message, top_k=6)
            
            with profiler.timer('t_merge_relevance'):
                # Process results for compliance
                top_sources = [doc.get('source', '') for doc in docs[:3]]
                
                # Generate compliance answer with citations
                if docs:
                    primary_source = docs[0].get('source', '')
                    primary_content = docs[0].get('content', '')[:150] + "..."
                    
                    answer = f"""Based on {primary_source}:

{primary_content}

Refer to the citations below for specific requirements and full details."""
                else:
                    answer = "I don't have specific information about that in my current knowledge base. Could you rephrase or ask about a specific building code section?"
                
                # Always include citations for compliance queries (max 3)
                enhanced_citations = []
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
        
        # Finish profiling
        profiler.finish_request()
        timing_breakdown = profiler.get_breakdown()
        
        # Enhanced telemetry with profiling
        tier1_hit = any(any(t1 in cite.get("source", "") for t1 in ["NZS 3604", "E2/AS1", "B1/AS1"]) 
                       for cite in enhanced_citations)
        
        telemetry = profiler.get_telemetry(
            intent=intent,
            confidence=confidence,
            citations_count=len(enhanced_citations),
            cache_hit=cache_hit,
            top_sources=top_sources
        )
        telemetry['tier1_hit'] = tier1_hit
        telemetry['used_retrieval'] = used_retrieval
        
        if os.getenv("ENABLE_TELEMETRY") == "true":
            print(f"[telemetry] chat_response_v133 {telemetry}")
        
        # Format response
        response = {
            "message": answer,
            "citations": enhanced_citations,
            "session_id": session_id,
            "intent": intent,
            "confidence": confidence,
            "answer_style": answer_style,
            "notes": ["rag", "multi_turn", "optimized", "v1.3.3"],
            "timestamp": int(time.time()),
            "timing_ms": round(timing_breakdown['t_total']),
            "timing_breakdown": timing_breakdown
        }
        
        print(f"✅ Optimized chat v1.3.3 ({intent}): {len(enhanced_citations)} citations, {timing_breakdown['t_total']:.0f}ms")
        
        return response
        
    except Exception as e:
        if os.getenv("ENABLE_TELEMETRY") == "true":
            print(f"[telemetry] chat_error error={str(e)[:50]} session_id={req.session_id or 'default'}")
        
        print(f"❌ Optimized chat error: {e}")
        return {
            "message": "I'm temporarily unable to process your message. Please try again.",
            "citations": [],
            "session_id": req.session_id or "default",
            "intent": "error",
            "notes": ["fallback", "chat", str(e)],
            "timestamp": int(time.time())
        }

