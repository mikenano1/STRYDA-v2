"""
Gemini Client for STRYDA Reasoning (via Emergent)
Structured JSON responses with Tier-1 citation integration
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Emergent Imports
try:
    from emergentintegrations.llm.chat import LlmChat, UserMessage
except ImportError:
    print("CRITICAL: emergentintegrations not installed")
    LlmChat = None

load_dotenv(override=True)

# Configuration
MODEL = os.getenv("GEMINI_PRO_MODEL", "gemini-1.5-pro")  # Strict/Reasoning model
FALLBACK_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")  # Fast fallback
API_KEY = os.getenv("EMERGENT_LLM_KEY")

print(f"🤖 Primary model: {MODEL}, Fallback: {FALLBACK_MODEL}")

if not API_KEY:
    print("⚠️ No EMERGENT_LLM_KEY configured")

def extract_final_text(response) -> tuple[str, int, dict]:
    """
    Extract final assistant text from Response object.
    Supports OpenAI-compatible responses from LiteLLM/Emergent.
    """
    try:
        # LiteLLM ModelResponse mimics OpenAI structure
        if hasattr(response, 'choices') and len(response.choices) > 0:
            content = response.choices[0].message.content
            if content:
                return content, len(content), {"extraction_path": "choices[0].message.content"}
        
        # Fallback for direct text
        if hasattr(response, 'content'):
             return str(response.content), len(str(response.content)), {"extraction_path": "content"}

    except Exception as e:
        print(f"⚠️ extract_final_text error: {e}")
    
    return "", 0, {"extraction_path": "<none>"}


def build_system_prompt(intent: str) -> str:
    """Build complete system prompt based on intent"""
    # ... (Same as before) ...
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

**Term Translation:** If a user asks for the "Matrix" or "Flashing Matrix" in context of E2/AS1, they are referring to **Table 7 (E2/AS1 4th Ed)** or the **flashing selection tables**. Do not state it doesn't exist; retrieve Table 7.

IMPORTANT: For H1/AS1 inquiries, the Schedule Method is no longer permitted for new consents (since Nov 2025). Recommend Calculation or Modelling methods.

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

    intent_instruction = INTENT_INSTRUCTIONS.get(intent, INTENT_INSTRUCTIONS["general_help"])
    return SYSTEM_PROMPT_BASE + intent_instruction


async def generate_structured_response(user_message: str, tier1_snippets: List[Dict], conversation_history: List[Dict] = None, intent: str = "general_help") -> Dict[str, Any]:
    """
    Generate structured Gemini response with intent-aware prompting.
    Async function.
    """
    if not API_KEY:
        print("⚠️ No Emergent API key - using server-side fallback")
        return create_fallback_response(user_message, tier1_snippets, "no_api_key")
    
    try:
        # Format context from Tier-1 snippets
        snippet_context = ""
        if tier1_snippets:
            snippet_bullets = []
            for snippet in tier1_snippets[:3]:
                source = snippet.get('source', 'Unknown')
                section = snippet.get('section', '')
                content = snippet.get('snippet', snippet.get('content', ''))[:300] # Expanded context
                section_text = f" §{section}" if section else ""
                snippet_bullets.append(f"• {source}{section_text}: {content}")
            snippet_context = "\n".join(snippet_bullets)
        
        # Build messages
        system_prompt = build_system_prompt(intent)
        
        # Construct message history manually for LlmChat initialization
        messages_payload = [
            {"role": "system", "content": system_prompt}
        ]
        
        if conversation_history:
            for msg in conversation_history[-3:]:  # Last 3 messages
                messages_payload.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")[:500]
                })
        
        # Add current query with context
        if snippet_context:
            user_content = f"{user_message}\n\nAvailable building standards:\n{snippet_context}"
        else:
            user_content = user_message
            
        messages_payload.append({"role": "user", "content": user_content})
        
        # Determine model
        if intent in ["general_help", "product_info", "chitchat"]:
            model = FALLBACK_MODEL  # Flash for speed
            max_tokens = 1024  # Increased for Gemini Flash
        else:
            model = MODEL  # Pro for strict compliance
            max_tokens = 2048 # Increased for Gemini Pro
            
        print(f"🔄 Calling Gemini ({model}) for intent={intent}...")
        
        # Initialize LlmChat
        chat_client = LlmChat(
            api_key=API_KEY,
            session_id="temp_structured",
            system_message="", # Already in messages_payload
            initial_messages=messages_payload
        )
        chat_client.with_model("gemini", model)
        chat_client.with_params(max_tokens=max_tokens, temperature=0.2)
        
        # Execute via internal method to get full object, or use send_message
        # Using _execute_completion to get usage stats if possible, but LlmChat hides it mostly.
        # Actually, let's just use _execute_completion.
        response = await chat_client._execute_completion(messages_payload)
        
        # Extract text
        final_text, raw_len, extraction_meta = extract_final_text(response)
        
        # Usage stats
        usage = response.usage if hasattr(response, 'usage') else None
        tokens_in = usage.prompt_tokens if usage else 0
        tokens_out = usage.completion_tokens if usage else 0
        
        print(f"📥 Gemini Response: {raw_len} chars, {tokens_out} tokens out")

        # Parse JSON
        json_ok = False
        answer = ""
        
        if final_text:
            # 1. Try to clean markdown code blocks often returned by Gemini
            cleaned_text = final_text.replace("```json", "").replace("```", "").strip()
            
            try:
                parsed = json.loads(cleaned_text)
                if isinstance(parsed, dict) and "answer" in parsed:
                    answer = parsed.get("answer", "")
                    json_ok = True
            except json.JSONDecodeError:
                # Fallback regex
                import re
                json_match = re.search(r'\{[\s\S]*"answer"[\s\S]*\}', cleaned_text)
                if json_match:
                    try:
                        parsed = json.loads(json_match.group(0))
                        answer = parsed.get("answer", "")
                        json_ok = True
                    except:
                        pass
        
        if not answer:
             answer = final_text.strip()
             print(f"⚠️ JSON parse failed, using raw text")

        return {
            "answer": answer,
            "intent": intent,
            "citations": format_tier1_citations(tier1_snippets[:3]) if tier1_snippets else [],
            "model": model,
            "tokens_used": (tokens_in + tokens_out),
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "raw_len": raw_len,
            "json_ok": json_ok
        }

    except Exception as e:
        print(f"❌ Gemini API error: {e}")
        return create_fallback_response(user_message, tier1_snippets, "gemini_failed")

def create_fallback_response(user_message: str, tier1_snippets: List[Dict], reason: str) -> Dict[str, Any]:
    """Create intelligent fallback response"""
    # (Same as before, simplified)
    if tier1_snippets:
        primary_doc = tier1_snippets[0]
        source = primary_doc.get('source', 'building standards')
        return {
            "answer": f"Based on {source}, here's what I found: {primary_doc.get('snippet', '')[:200]}...",
            "intent": "compliance_strict",
            "citations": format_tier1_citations(tier1_snippets[:3]),
            "model": f"fallback_{reason}",
            "tokens_used": 0
        }
    else:
        return {
            "answer": "I'm having trouble connecting to the brain. Please try again in a moment.",
            "intent": "general_help",
            "citations": [],
            "model": f"fallback_{reason}",
            "tokens_used": 0
        }

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

def get_structured_response():
    return generate_structured_response
