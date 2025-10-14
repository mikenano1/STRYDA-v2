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

import asyncio
import signal
from typing import Dict, List, Any, Optional

def with_timeout_and_retry(func, timeout_seconds=20, max_retries=3, backoff_base=0.5):
    """
    Execute function with timeout and exponential backoff retry on 429 errors
    """
    for attempt in range(max_retries):
        try:
            # Create timeout signal
            def timeout_handler(signum, frame):
                raise TimeoutError("Operation timed out")
            
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)
            
            try:
                result = func()
                signal.alarm(0)  # Cancel timeout
                return result
            finally:
                signal.alarm(0)
                
        except TimeoutError:
            print(f"⚠️ Timeout on attempt {attempt + 1}/{max_retries}")
            if attempt == max_retries - 1:
                raise
                
        except Exception as e:
            error_str = str(e)
            
            # Handle 429 rate limit errors
            if "429" in error_str or "overloaded" in error_str.lower():
                if attempt < max_retries - 1:
                    # Jittered exponential backoff
                    import random
                    backoff_time = backoff_base * (2 ** attempt) + random.uniform(0, 0.1)
                    print(f"⚠️ Rate limited, retrying in {backoff_time:.1f}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(backoff_time)
                    continue
            
            # Re-raise non-retriable errors
            raise
    
    raise Exception(f"Max retries ({max_retries}) exceeded")

def generate_structured_response(user_message: str, tier1_snippets: List[Dict], conversation_history: List[Dict] = None) -> Dict[str, Any]:
    """
    Generate structured GPT response with proper async timeout handling
    """
    if not API_KEY:
        print("⚠️ No OpenAI API key - using server-side fallback")
        return create_fallback_response(user_message, tier1_snippets, "no_api_key")
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=API_KEY)
        
        # Format context from Tier-1 snippets
        snippet_context = ""
        if tier1_snippets:
            snippet_bullets = []
            for snippet in tier1_snippets[:3]:
                source = snippet.get('source', 'Unknown')
                section = snippet.get('section', '')
                content = snippet.get('snippet', snippet.get('content', ''))[:150]
                section_text = f" §{section}" if section else ""
                snippet_bullets.append(f"• {source}{section_text}: {content}")
            snippet_context = "\n".join(snippet_bullets)
        
        # Build conversation-aware messages
        messages = [
            {"role": "system", "content": "You are STRYDA, a helpful NZ building assistant. Be conversational and practical. Use provided building standards to give accurate answers."}
        ]
        
        # Add recent conversation context
        if conversation_history:
            for msg in conversation_history[-2:]:  # Last 2 messages for context
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")[:200]
                })
        
        # Add current query with context
        if snippet_context:
            user_content = f"{user_message}\n\nAvailable building standards:\n{snippet_context}"
        else:
            user_content = user_message
            
        messages.append({"role": "user", "content": user_content})
        
        print(f"🔄 Calling OpenAI {os.getenv('OPENAI_MODEL', 'gpt-4o-mini')}...")
        
        # Call OpenAI with proper timeout (no signal handling)
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=messages,
            temperature=0.3,
            max_tokens=500,
            timeout=20  # Simple timeout parameter
        )
        
        # Extract response
        answer = response.choices[0].message.content
        usage = response.usage
        
        print(f"✅ OpenAI response received: {len(answer)} chars, {usage.total_tokens} tokens")
        
        # Create structured response
        structured_response = {
            "answer": answer,
            "intent": classify_intent_from_answer(answer, user_message),
            "citations": format_tier1_citations(tier1_snippets[:3]),
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "tokens_used": usage.total_tokens,
            "tokens_in": usage.prompt_tokens,
            "tokens_out": usage.completion_tokens
        }
        
        return structured_response
        
    except Exception as e:
        error_str = str(e)
        print(f"❌ OpenAI call failed: {error_str}")
        
        # Check specific error types
        if "Incorrect API key" in error_str:
            print("   Root cause: Invalid OpenAI API key")
        elif "429" in error_str:
            print("   Root cause: Rate limit exceeded")
        elif "timeout" in error_str.lower():
            print("   Root cause: Request timeout")
        
        # Return proper fallback
        return create_fallback_response(user_message, tier1_snippets, "openai_failed")

def create_fallback_response(user_message: str, tier1_snippets: List[Dict], reason: str) -> Dict[str, Any]:
    """Create intelligent fallback response"""
    query_lower = user_message.lower()
    
    # Intelligent fallback based on query type
    if any(word in query_lower for word in ['hello', 'hi', 'hey', 'thanks']):
        return {
            "answer": "Kia ora! I'm here to help with NZ building codes and practical guidance. What specific building question can I help you with?",
            "intent": "chitchat",
            "citations": [],
            "model": f"server_intelligent_fallback_{reason}",
            "tokens_used": 0
        }
    elif tier1_snippets:
        # Use first relevant snippet intelligently
        primary_doc = tier1_snippets[0]
        source = primary_doc.get('source', 'building standards')
        
        return {
            "answer": f"Based on {source}, here's what I found: {primary_doc.get('snippet', '')[:200]}... I can provide more specific guidance if you clarify your building situation.",
            "intent": "compliance_strict",
            "citations": format_tier1_citations(tier1_snippets[:3]),
            "model": f"server_intelligent_fallback_{reason}",
            "tokens_used": 0
        }
    else:
        return {
            "answer": "I'd be happy to help with building code questions! Could you be more specific about what you're working on? For example, are you asking about roofing, structural requirements, or weatherproofing?",
            "intent": "clarify",
            "citations": [],
            "model": f"server_intelligent_fallback_{reason}",
            "tokens_used": 0
        }

def classify_intent_from_answer(answer: str, original_query: str) -> str:
    """Classify intent from the answer content"""
    answer_lower = answer.lower()
    query_lower = original_query.lower()
    
    if any(word in answer_lower for word in ['hello', 'hi', 'kia ora', 'help you']):
        return "chitchat"
    elif any(word in answer_lower for word in ['specific', 'precise', 'refer to', 'citation']):
        return "compliance_strict"
    elif '?' in answer:
        return "clarify"
    else:
        return "general_building"

def format_tier1_citations(tier1_snippets: List[Dict]) -> List[Dict]:
    """Format Tier-1 snippets into proper citation structure"""
    citations = []
    
    for doc in tier1_snippets:
        citation = {
            "id": f"cite_{doc.get('id', '')[:8]}",
            "source": doc.get("source", "Unknown"),
            "page": doc.get("page", 0),
            "score": doc.get("score", 0.0),
            "snippet": doc.get("snippet", "")[:200],
            "section": doc.get("section"),
            "clause": doc.get("clause")
        }
        citations.append(citation)
    
    return citations

# Export for use in main app
def get_structured_response():
    return generate_structured_response