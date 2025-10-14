"""
STRYDA Backend Hardening - Input Validation & Security
Production-ready validation schemas and error handling
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from fastapi import HTTPException
import re

class ChatRequest(BaseModel):
    """Validated chat request with security constraints"""
    session_id: Optional[str] = Field(None, max_length=100, pattern=r'^[a-zA-Z0-9_-]*$')
    message: str = Field(..., min_length=1, max_length=4000)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Message cannot be empty or whitespace only')
        
        # Security: Basic content validation
        v_clean = v.strip()
        if len(v_clean) > 4000:
            raise ValueError('Message too long (max 4000 characters)')
            
        return v_clean
    
    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v):
        if v is None:
            return None
        
        # Security: Alphanumeric session IDs only
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Invalid session ID format')
            
        return v

class Citation(BaseModel):
    """Validated citation structure"""
    source: str = Field(..., min_length=1)
    section: Optional[str] = Field(None, max_length=200)
    page: Optional[str] = Field(None, max_length=20)
    snippet: str = Field(..., min_length=1, max_length=200)
    
    @validator('snippet')
    def validate_snippet(cls, v):
        if len(v) > 200:
            # Truncate at word boundary
            truncated = v[:200]
            last_space = truncated.rfind(' ')
            if last_space > 150:
                return truncated[:last_space] + "..."
            return truncated + "..."
        return v

class ChatResponse(BaseModel):
    """Strict response schema for /api/chat"""
    answer: str = Field(..., min_length=1)
    intent: str = Field(..., pattern=r'^(chitchat|compliance_strict|clarify|general_building|error)$')
    citations: List[Citation] = Field(default_factory=list, max_items=3)
    tier1_hit: bool = Field(default=False)
    model: str = Field(..., min_length=1)
    latency_ms: int = Field(..., ge=0)
    session_id: str = Field(..., min_length=1)
    timestamp: int = Field(..., ge=0)

def validate_input(request_data: dict) -> ChatRequest:
    """Validate input with proper error messages"""
    try:
        return ChatRequest(**request_data)
    except Exception as e:
        # Map validation errors to appropriate HTTP codes
        error_str = str(e)
        
        if "empty" in error_str or "whitespace" in error_str:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        elif "too long" in error_str or "max_length" in error_str:
            raise HTTPException(status_code=413, detail="Message too long (max 4000 characters)")
        elif "session" in error_str:
            raise HTTPException(status_code=400, detail="Invalid session ID format")
        else:
            raise HTTPException(status_code=400, detail="Invalid request format")

def validate_output(response_data: dict) -> dict:
    """Validate output structure before sending"""
    try:
        validated = ChatResponse(**response_data)
        return validated.dict()
    except Exception as e:
        print(f"❌ Response validation failed: {e}")
        
        # Return minimal valid response
        return {
            "answer": "I encountered an issue generating a proper response. Please try again.",
            "intent": "error",
            "citations": [],
            "tier1_hit": False,
            "model": "validation_fallback", 
            "latency_ms": 0,
            "session_id": response_data.get("session_id", "unknown"),
            "timestamp": int(time.time())
        }

# Export validation functions
def get_input_validator():
    return validate_input

def get_output_validator():
    return validate_output