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

# Enhanced System Prompts per Intent
SYSTEM_PROMPT_BASE = """You are STRYDA, a NZ building/tradie assistant specializing in building codes and practical guidance.

**Output Format:**
Your response must be valid JSON: {"answer": "...", "intent": "...", "citations": []}

**Citation Rules:**
- If intent == "compliance_strict": Backend provides citations from NZ Building Code (E2/AS1, B1, NZS 3604, etc.). Reference them naturally.
- If intent in {"general_help","product_info","chitchat"}: citations = [] (no citations needed)

**Style Guidelines:**
- Use clear, plain Kiwi-friendly language
- Be concise but complete - aim for 120+ words for substantive queries
- Use bullet points for multi-step guidance
- Include specific numbers, measurements, and practical tips
- Avoid hedging or uncertain language
- Give direct, actionable advice

**Quality Standards:**
- Provide complete, practical answers that a tradie can immediately use
- Include safety considerations when relevant
- Mention common mistakes to avoid
- Give rules of thumb and industry best practices
"""

INTENT_INSTRUCTIONS = {
    "compliance_strict": """
**Compliance Query Instructions:**
- Focus on code requirements, clauses, tables, and figures
- Provide one clear summary paragraph followed by bullet points
- Reference specific clause numbers and page numbers when available
- Never invent citations - only use what's provided in context
- Be precise about requirements and conditions
- Highlight any amendments or special conditions
""",
    "general_help": """
**General Help Instructions:**
- No citations needed - provide practical guidance
- Give step-by-step instructions when applicable
- Include safety notes and common pitfalls
- Mention tools/materials needed
- Provide 2-3 quick tips or pro advice
- Use real-world examples
""",
    "product_info": """
**Product Info Instructions:**
- No citations needed
- Discuss 2-3 product categories or features to consider
- Mention typical price ranges if relevant
- Include durability/warranty considerations
- Suggest where to check specifications
- Focus on what makes a good choice vs poor choice
""",
    "chitchat": """
**Chitchat Instructions:**
- Keep it friendly and brief
- Redirect to building codes or practical guidance if appropriate
- No citations needed
"""
}

def build_system_prompt(intent: str) -> str:
    """Build complete system prompt based on intent"""
    intent_instruction = INTENT_INSTRUCTIONS.get(intent, INTENT_INSTRUCTIONS["general_help"])
    return SYSTEM_PROMPT_BASE + intent_instruction

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

def generate_structured_response(user_message: str, tier1_snippets: List[Dict], conversation_history: List[Dict] = None, intent: str = "general_help") -> Dict[str, Any]:
    """
    Generate structured GPT response with intent-aware prompting and length guards
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
                content = snippet.get('snippet', snippet.get('content', ''))[:200]
                section_text = f" §{section}" if section else ""
                snippet_bullets.append(f"• {source}{section_text}: {content}")
            snippet_context = "\n".join(snippet_bullets)
        
        # Build messages with intent-aware system prompt
        system_prompt = build_system_prompt(intent)
        messages = [
            {"role": "system", "content": system_prompt}
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
        
        # Determine model and appropriate parameters
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        # GPT-5 uses max_completion_tokens and doesn't support temperature
        completion_params = {
            "model": model,
            "messages": messages,
            "timeout": 30  # Increased for GPT-5 reasoning
        }
        
        # Use appropriate parameters based on model
        if "gpt-5" in model.lower() or "o1" in model.lower():
            completion_params["max_completion_tokens"] = 600  # Increased for complete answers
            completion_params["top_p"] = 0.9
            completion_params["presence_penalty"] = 0.1
            completion_params["frequency_penalty"] = 0.0
            # GPT-5 doesn't support temperature parameter, uses default 1
        else:
            completion_params["max_tokens"] = 600
            completion_params["temperature"] = 0.3
        
        # Call OpenAI with proper timeout
        response = client.chat.completions.create(**completion_params)
        
        # Extract response
        answer = response.choices[0].message.content or ""
        usage = response.usage
        
        word_count = len(answer.split())
        print(f"✅ OpenAI response received: {len(answer)} chars, {word_count} words, {usage.total_tokens} tokens")
        
        # Length guard: If response is too short and query is substantial, retry with expansion prompt
        query_word_count = len(user_message.split())
        if word_count < 80 and query_word_count > 5 and snippet_context:
            print(f"⚠️ Response too short ({word_count} words), retrying with expansion prompt...")
            
            # Add expansion instruction
            messages.append({"role": "assistant", "content": answer})
            messages.append({
                "role": "user",
                "content": "Please expand your answer with concrete details, specific measurements, practical examples, and step-by-step guidance. Keep it clear and actionable for a tradie."
            })
            
            # Retry with expansion
            try:
                retry_response = client.chat.completions.create(**completion_params)
                expanded_answer = retry_response.choices[0].message.content or answer
                expanded_word_count = len(expanded_answer.split())
                
                if expanded_word_count > word_count:
                    print(f"✅ Expanded response: {expanded_word_count} words")
                    answer = expanded_answer
                    usage = retry_response.usage
            except Exception as e:
                print(f"⚠️ Expansion failed, using original: {e}")
        
        # Create structured response
        structured_response = {
            "answer": answer,
            "intent": intent,
            "citations": format_tier1_citations(tier1_snippets[:3]) if tier1_snippets else [],
            "model": model,
            "tokens_used": usage.total_tokens,
            "tokens_in": usage.prompt_tokens,
            "tokens_out": usage.completion_tokens
        }
        
        return structured_response
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