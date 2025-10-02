from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(title="STRYDA Backend", version="0.1.0")

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AskRequest(BaseModel):
    query: str

class AskResponse(BaseModel):
    answer: str
    notes: list[str]
    citation: str

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
    Stub endpoint - returns canned response.
    Future: will query RAG system with building code context.
    """
    return AskResponse(
        answer="Coming soon - this is a backend stub response for your query.",
        notes=["demo", "backend"],
        citation="NZMRM COP X.Y"
    )
