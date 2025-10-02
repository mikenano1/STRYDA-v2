from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from rag.retriever import retrieve
from rag.prompt import build_messages
from rag.llm import chat

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

@app.get("/health")
def health():
    return {"ok": True, "version": "v0.2"}

@app.post("/api/ask")
def api_ask(req: AskRequest):
    try:
        ctx = retrieve(req.query, top_k=6)
        if not ctx:
            return {
                "answer": "Temporary fallback: no retrieval context found.",
                "notes": ["fallback", "backend"],
                "citation": []
            }
        messages = build_messages(req.query, ctx, history=req.history)
        answer = chat(messages)
        if not answer:
            answer = "Temporary fallback: LLM unavailable."
        cites = [
            {
                "doc_id": str(c.get("id")),
                "source": c.get("source"),
                "page": c.get("page"),
                "score": float(c.get("score", 0))
            }
            for c in ctx
        ]
        return {"answer": answer, "notes": ["retrieval", "backend"], "citation": cites}
    except Exception as e:
        return {
            "answer": "Temporary fallback: backend issue.",
            "notes": ["fallback", "backend", str(e)],
            "citation": []
        }

