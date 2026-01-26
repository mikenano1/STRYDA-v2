#!/usr/bin/env python3
"""
Simple STRYDA Backend - Fallback Mode
Provides basic endpoints for testing as requested by user
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os

# Create FastAPI app
app = FastAPI(title="STRYDA.ai Simple Backend", version="v0.2")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class AskRequest(BaseModel):
    query: str

class AskResponse(BaseModel):
    answer: str
    notes: str
    citation: str

class HealthResponse(BaseModel):
    ok: bool
    version: str

# Health endpoint as requested by user
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint returning exactly what user requested"""
    return HealthResponse(ok=True, version="v0.2")

# Ask endpoint as requested by user  
@app.post("/api/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """Simple ask endpoint with fallback response as requested"""
    return AskResponse(
        answer=f"This is a fallback response to your question: '{request.query}'. The STRYDA.ai system is currently in fallback mode and providing basic responses.",
        notes="System is operating in fallback mode. For comprehensive NZ Building Code guidance, please ensure the full system is operational.",
        citation="STRYDA.ai Fallback System v0.2"
    )

# Root endpoint
@app.get("/")
async def root():
    return {"message": "STRYDA.ai Simple Backend v0.2 - Fallback Mode"}

@app.get("/api/")
async def api_root():
    return {"message": "STRYDA.ai Backend API v0.2 - Fallback Mode"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)