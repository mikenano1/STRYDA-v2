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
    Generate structured GPT response with strict JSON validation and resilience
    """
    if not API_KEY:
        print("⚠️ No OpenAI API key - using server-side fallback")
        
        # Intelligent server-side response with Tier-1 citations
        if "hello" in user_message.lower() or "hi" in user_message.lower():
            return {
                "answer": "Kia ora! I'm here to help with building codes and practical guidance. What's on your mind?",
                "intent": "chitchat",
                "citations": [],
                "model": "server_fallback",
                "tokens_used": 0
            }
        elif tier1_snippets:
            # Use Tier-1 content for compliance responses
            primary_snippet = tier1_snippets[0]
            source = primary_snippet.get('source', 'Building Standards')
            content = primary_snippet.get('snippet', '')[:150]
            
            return {
                "answer": f"Based on {source}: {content}... Refer to the citations for specific requirements.",
                "intent": "compliance_strict", 
                "citations": [
                    {
                        "source": doc.get("source", "Unknown"),
                        "section": doc.get("section"),
                        "page": str(doc.get("page", "")),
                        "snippet": doc.get("snippet", "")[:200]
                    }
                    for doc in tier1_snippets[:3]
                ],
                "model": "server_fallback",
                "tokens_used": 0
            }
        else:
            return {
                "answer": "I can help with NZ building standards. Could you be more specific about your building project?",
                "intent": "clarify",
                "citations": [],
                "model": "server_fallback", 
                "tokens_used": 0
            }
    
    # If OpenAI is available, use structured generation (with timeout and retry)
    def make_openai_call():
        from openai import OpenAI
        client = OpenAI(api_key=API_KEY)
        
        # Format context
        snippet_context = ""
        if tier1_snippets:
            snippet_bullets = []
            for snippet in tier1_snippets[:3]:
                source = snippet.get('source', 'Unknown')
                section = snippet.get('section', '')
                content = snippet.get('snippet', snippet.get('content', ''))[:200]
                section_text = f" §{section}" if section else ""
                snippet_bullets.append(f"• [{source}{section_text}] {content}")
            snippet_context = "\n".join(snippet_bullets)
        
        # Build messages for structured generation
        messages = [
            {"role": "system", "content": "You are STRYDA, a NZ building standards assistant. Return only valid JSON with answer, intent, and citations fields."}
        ]
        
        user_content = f"""Query: {user_message}

Available standards:
{snippet_context if snippet_context else "(no specific standards found)"}

Return JSON: {{"answer": "your response", "intent": "chitchat|compliance_strict|clarify", "citations": [...]}}"""

        messages.append({"role": "user", "content": user_content})
        
        # Call OpenAI with structured output
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=messages,
            temperature=0.3,
            max_tokens=600,
            response_format={"type": "json_object"}
        )
        
        return response
    
    try:
        # Execute with timeout and retry
        response = with_timeout_and_retry(make_openai_call, timeout_seconds=20, max_retries=3)
        
        response_text = response.choices[0].message.content
        usage = response.usage
        
        # STRICT JSON parsing
        try:
            structured_data = json.loads(response_text)
            
            # Validate required fields
            required_fields = ['answer', 'intent', 'citations']
            for field in required_fields:
                if field not in structured_data:
                    structured_data[field] = "" if field in ["answer", "intent"] else []
            
            # Add metadata
            structured_data.update({
                "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                "tokens_used": usage.total_tokens if usage else 0,
                "tokens_in": usage.prompt_tokens if usage else 0,
                "tokens_out": usage.completion_tokens if usage else 0
            })
            
            return structured_data
            
        except json.JSONDecodeError as e:
            # Log the invalid output (truncated for safety)
            output_sample = response_text[:1000] if response_text else "empty"
            print(f"❌ JSON parse error: {e}")
            print(f"❌ Model output (first 1k): {output_sample}")
            
            # Return 502 error data structure
            raise ValueError("bad_json")
            
    except Exception as e:
        error_str = str(e)
        
        # Mask API key in error messages
        if API_KEY and API_KEY in error_str:
            error_str = error_str.replace(API_KEY, "sk-***")
        
        print(f"❌ OpenAI call failed: {error_str}")
        
        if "bad_json" in error_str:
            raise ValueError("bad_json")
        
        # Return server-side fallback
        if tier1_snippets:
            return {
                "answer": f"Based on available building standards: {tier1_snippets[0].get('snippet', '')[:100]}... Refer to citations for details.",
                "intent": "compliance_strict",
                "citations": [
                    {
                        "source": doc.get("source", "Unknown"),
                        "section": doc.get("section"),
                        "page": str(doc.get("page", "")),
                        "snippet": doc.get("snippet", "")[:200]
                    }
                    for doc in tier1_snippets[:3]
                ],
                "model": "server_fallback",
                "tokens_used": 0
            }
        
        return {
            "answer": "I encountered an issue processing your question. Please try rephrasing your query.",
            "intent": "error_llm",
            "citations": [],
            "model": "error_fallback",
            "tokens_used": 0
        }

# Export for use in main app
def get_structured_response():
    return generate_structured_response