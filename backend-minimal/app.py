from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
import os

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

