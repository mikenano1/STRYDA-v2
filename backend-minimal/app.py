from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict, Any
from rag.retriever import retrieve_and_answer

app = FastAPI(title="STRYDA Backend", version="0.1.0")

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    role: str
    content: str

class AskRequest(BaseModel):
    query: str
    history: Optional[List[Message]] = None

class Citation(BaseModel):
    doc_id: str
    source: str
    page: str | int
    score: float

class AskResponse(BaseModel):
    answer: str
    notes: List[str]
    citations: List[Citation]

@app.get("/health")
def health():
    """Health check endpoint"""
    return {
        "ok": True,
        "version": "v0.1",
        "time": datetime.utcnow().isoformat()
    }

@app.post("/api/ask", response_model=AskResponse)
def ask(req: AskRequest):
    """
    Ask a question using RAG pipeline.
    Falls back to stub if RAG is unavailable.
    """
    # Convert history to dict format if provided
    history_dicts = None
    if req.history:
        history_dicts = [{"role": msg.role, "content": msg.content} for msg in req.history]
    
    # Use RAG pipeline
    result = retrieve_and_answer(req.query, history=history_dicts)
    
    return AskResponse(**result)
