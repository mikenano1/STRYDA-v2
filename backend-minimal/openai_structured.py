"""
OpenAI GPT-5 Client for STRYDA Reasoning
Structured JSON responses with Tier-1 citation integration
"""

import os
import json
from typing import Dict, List, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# OpenAI Client Configuration
client = None
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Fallback to available model
API_KEY = os.getenv("OPENAI_API_KEY")

if API_KEY:
    try:
        client = OpenAI(api_key=API_KEY)
        print(f"✅ OpenAI client initialized for model: {MODEL}")
    except Exception as e:
        print(f"❌ OpenAI client initialization failed: {e}")
        client = None
else:
    print("⚠️ No OpenAI API key configured")

# JSON Schema for Structured Response
STRYDA_RESPONSE_SCHEMA = {
    "name": "STRYDAAnswer",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "answer": {"type": "string"},
            "intent": {"type": "string"},
            "citations": {
                "type": "array",
                "items": {
                    "type": "object", 
                    "properties": {
                        "source": {"type": "string"},
                        "section": {"type": "string"},
                        "page": {"type": "string"},
                        "snippet": {"type": "string"}
                    },
                    "required": ["source", "snippet"]
                }
            }
        },
        "required": ["answer", "intent", "citations"]
    }
}

SYSTEM_PROMPT = """You are STRYDA, a NZ building standards assistant. Use ONLY provided Tier-1 snippets for normative statements. If unsure, ask at most 2 concise questions. Keep answers short and practical."""

def generate_structured_response(user_message: str, tier1_snippets: List[Dict], conversation_history: List[Dict] = None) -> Dict[str, Any]:
    """
    Generate structured GPT-5 response with Tier-1 citations
    """
    if not client:
        # Fallback response structure
        return {
            "answer": "I'm currently unable to process your request. Please try again later.",
            "intent": "error_no_llm",
            "citations": tier1_snippets[:3] if tier1_snippets else [],
            "model": "fallback",
            "tokens_used": 0
        }
    
    try:
        # Format Tier-1 snippets for context
        snippet_context = ""
        if tier1_snippets:
            snippet_bullets = []
            for snippet in tier1_snippets:
                source = snippet.get('source', 'Unknown')
                section = snippet.get('section', '')
                content = snippet.get('snippet', snippet.get('content', ''))[:200]
                
                section_text = f" §{section}" if section else ""
                snippet_bullets.append(f"• [{source}{section_text}] {content}")
            
            snippet_context = "\n".join(snippet_bullets[:5])  # Top 5 snippets
        
        # Build messages for structured generation
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        
        # Add conversation history (last 4 messages for context)
        if conversation_history:
            for msg in conversation_history[-4:]:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")[:200]  # Truncate for token management
                })
        
        # Add current user message with Tier-1 context
        user_content = f"""Query: {user_message}

Available Tier-1 building standards:
{snippet_context if snippet_context else "(no specific standards found)"}

Return JSON matching STRYDAAnswer schema with answer, intent, and relevant citations."""
        
        messages.append({"role": "user", "content": user_content})
        
        # Call OpenAI with structured output (adapted for current API)
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=800,
            response_format={"type": "json_object"}  # Request JSON format
        )
        
        # Extract structured response
        response_text = response.choices[0].message.content
        usage = response.usage
        
        try:
            # Parse the JSON response
            structured_data = json.loads(response_text)
            
            # Ensure required fields exist
            if not structured_data.get("answer"):
                structured_data["answer"] = "I need more information to provide a proper answer."
            
            if not structured_data.get("intent"):
                structured_data["intent"] = "general_building"
                
            if not structured_data.get("citations"):
                # Use server-side Tier-1 citations if model didn't provide any
                structured_data["citations"] = [
                    {
                        "source": snippet.get("source", ""),
                        "section": snippet.get("section", ""),
                        "page": str(snippet.get("page", "")),
                        "snippet": snippet.get("snippet", "")[:200]
                    }
                    for snippet in tier1_snippets[:3]
                ]
            
            # Add metadata
            structured_data.update({
                "model": MODEL,
                "tokens_used": usage.total_tokens if usage else 0,
                "tokens_in": usage.prompt_tokens if usage else 0,
                "tokens_out": usage.completion_tokens if usage else 0
            })
            
            return structured_data
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error: {e}")
            # Return structured fallback
            return {
                "answer": response_text,  # Return raw text if JSON parsing fails
                "intent": "unstructured",
                "citations": tier1_snippets[:3] if tier1_snippets else [],
                "model": MODEL,
                "tokens_used": usage.total_tokens if usage else 0
            }
    
    except Exception as e:
        print(f"❌ OpenAI structured generation failed: {e}")
        
        # Return fallback with server-side citations
        return {
            "answer": f"I encountered an issue processing your question: {str(e)[:100]}. Please try rephrasing your query.",
            "intent": "error_llm",
            "citations": tier1_snippets[:3] if tier1_snippets else [],
            "model": "fallback",
            "tokens_used": 0
        }

# Export for use in main app
def get_structured_response():
    return generate_structured_response