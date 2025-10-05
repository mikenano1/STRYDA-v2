from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
import os
import time

# Load environment variables from .env file
load_dotenv()

from rag.retriever import retrieve_and_answer

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
    Multi-turn chat conversation with memory and enhanced citations
    """
    try:
        import sys
        sys.path.insert(0, '/app/backend-minimal')
        from multi_turn_chat import generate_chat_response
        
        # Generate response with multi-turn awareness
        response = generate_chat_response(
            session_id=req.session_id or "default",
            user_message=req.message
        )
        
        # Ensure backward compatibility - remove timing from client response
        client_response = {
            "message": response.get("message", "Unable to process message"),
            "citations": response.get("citations", []),
            "session_id": response.get("session_id", "default"),
            "notes": response.get("notes", ["backend", "chat"]),
            "timestamp": int(time.time())
        }
        
        return client_response
        
    except Exception as e:
        print(f"❌ Multi-turn chat error: {e}")
        return {
            "message": "I'm temporarily unable to process your message. Please try again.",
            "citations": [],
            "session_id": req.session_id or "default",
            "notes": ["fallback", "chat", str(e)],
            "timestamp": int(time.time())
        }

