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
    Multi-turn chat conversation with RAG context and history
    """
    try:
        # Convert chat history to the format expected by retrieve_and_answer
        history = []
        if req.conversation_history:
            for msg in req.conversation_history[-5:]:  # Keep last 5 messages for context
                history.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # Process the message using RAG
        result = retrieve_and_answer(req.message, history=history)
        
        # Format response for chat interface
        response = {
            "message": result.get("answer", "Unable to process message"),
            "role": "assistant",
            "citations": result.get("citations", []),
            "session_id": req.session_id or "default",
            "notes": result.get("notes", ["backend", "chat"]),
            "timestamp": int(time.time())
        }
        
        return response
        
    except Exception as e:
        return {
            "message": "I'm temporarily unable to process your message. Please try again.",
            "role": "assistant", 
            "citations": [],
            "session_id": req.session_id or "default",
            "notes": ["fallback", "chat", str(e)],
            "timestamp": int(time.time())
        }

