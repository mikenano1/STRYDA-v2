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
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")  # Primary model - production stable
FALLBACK_MODEL = os.getenv("OPENAI_MODEL_FALLBACK", "gpt-4o-mini")  # Fallback if primary fails
API_KEY = os.getenv("OPENAI_API_KEY")

print(f"🤖 Primary model: {MODEL}, Fallback: {FALLBACK_MODEL}")

if API_KEY:
    try:
        client = OpenAI(api_key=API_KEY)
        print(f"✅ OpenAI client initialized")
    except Exception as e:
        print(f"❌ OpenAI client initialization failed: {e}")
        client = None
else:
    print("⚠️ No OpenAI API key configured")


def extract_final_text(response) -> tuple[str, int, dict]:
    """
    Extract final assistant text from OpenAI response, supporting GPT-5/o1 reasoning outputs.
    
    Returns:
        (final_text, raw_len, meta_additions) where:
        - final_text: Assistant's final/output text only (no reasoning)
        - raw_len: Character count of extracted text
        - meta_additions: Dict with extraction_path for debugging
    """
    try:
        payload = response.model_dump()
        
        # 1️⃣ GPT-5 / o1 reasoning model output path
        if "output" in payload and payload["output"]:
            for part in payload["output"][0].get("content", []):
                part_type = part.get("type", "")
                # Skip reasoning/thoughts parts, extract only output_text
                if part_type in ("reasoning", "thoughts"):
                    continue
                if part_type in ("output_text", "text"):
                    text = part.get("text") or part.get("value") or ""
                    if text.strip():
                        return text, len(text), {"extraction_path": "output[0].content[output_text]"}
        
        # 2️⃣ GPT-5 Responses API compatibility (output_text field)
        if hasattr(response, "output_text") and response.output_text:
            text = str(response.output_text)
            return text, len(text), {"extraction_path": "output_text"}
        
        # 3️⃣ Standard GPT-4 path (choices[0].message.content)
        choices = payload.get("choices", [])
        if choices:
            msg = choices[0].get("message", {})
            content = msg.get("content")
            
            # String content
            if isinstance(content, str) and content.strip():
                return content, len(content), {"extraction_path": "choices[0].message.content"}
            
            # Array content (multi-part messages)
            if isinstance(content, list):
                text_parts = []
                for part in content:
                    if isinstance(part, dict):
                        part_type = part.get("type", "")
                        # Skip reasoning, extract only text/output_text
                        if part_type in ("reasoning", "thoughts"):
                            continue
                        if part_type in ("text", "output_text") and "text" in part:
                            text_parts.append(part["text"])
                
                if text_parts:
                    joined = " ".join(text_parts)
                    return joined, len(joined), {"extraction_path": "choices[0].message.content[list]"}
    
    except Exception as e:
        print(f"⚠️ extract_final_text error: {e}")
    
    # Default: No text found
    return "", 0, {"extraction_path": "<none>"}

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

def store_reasoning_trace(response_obj, user_message: str, intent: str, model: str, final_text: str, extraction_meta: dict, fallback_used: bool):
    """
    Store full GPT-5/o1 reasoning response for deferred parsing.
    Non-blocking - will not interrupt user flow if DB fails.
    """
    try:
        import psycopg2
        import json
        
        DATABASE_URL = os.getenv("DATABASE_URL")
        if not DATABASE_URL:
            return
        
        # Get response dump
        reasoning_dump = response_obj.model_dump() if hasattr(response_obj, 'model_dump') else {}
        reasoning_trace_size = len(json.dumps(reasoning_dump))
        
        # Get usage stats
        usage = response_obj.usage if hasattr(response_obj, 'usage') else None
        tokens_total = usage.total_tokens if usage else 0
        tokens_in = usage.prompt_tokens if usage else 0
        tokens_out = usage.completion_tokens if usage else 0
        
        # Prepare metadata
        metadata = {
            "extraction_path": extraction_meta.get("extraction_path", "<unknown>"),
            "raw_len": len(final_text),
            "tokens_used": tokens_total,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "finish_reason": reasoning_dump.get("choices", [{}])[0].get("finish_reason", "unknown") if reasoning_dump.get("choices") else "unknown"
        }
        
        # Insert into database
        conn = psycopg2.connect(DATABASE_URL, sslmode="require", connect_timeout=5)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO reasoning_responses 
            (session_id, query, intent, model, reasoning_trace, final_answer, metadata, fallback_used, response_time_ms)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            "default",  # Session ID will be added later
            user_message[:500],
            intent,
            model,
            json.dumps(reasoning_dump),
            final_text[:1000] if final_text else "",
            json.dumps(metadata),
            fallback_used,
            int(tokens_total * 50)  # Rough estimate
        ))
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"🧠 Stored reasoning trace ({reasoning_trace_size:,} bytes) model={model} fallback={fallback_used}")
        
        if fallback_used:
            print(f"⚙️ Live answer served from fallback model (reasoning trace captured for {model})")
            
    except Exception as db_error:
        # Non-blocking: don't interrupt user flow
        print(f"⚠️ Reasoning trace storage failed (non-blocking): {db_error}")

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
        
        # GPT-5/o1 reasoning models have restricted parameters
        completion_params = {
            "model": model,
            "messages": messages,
            "timeout": 30  # Increased for reasoning models
        }
        
        # Use appropriate parameters based on model type
        if "gpt-5" in model.lower() or "o1" in model.lower():
            # GPT-5/o1 reasoning models: Only max_completion_tokens supported
            # CRITICAL: Balance between reasoning space and response time
            # 2500 tokens allows reasoning while avoiding timeout (30s limit)
            completion_params["max_completion_tokens"] = 2500
            completion_params["timeout"] = 45  # Increased timeout for reasoning models
            # No temperature, top_p, presence_penalty, frequency_penalty
            print(f"🤖 Using GPT-5/o1 with max_completion_tokens=2500, timeout=45s")
        else:
            # Standard models: Full parameter set
            completion_params["max_tokens"] = 600
            completion_params["temperature"] = 0.3
            print(f"🤖 Using standard model with full parameters")
        
        # Call OpenAI with proper timeout and error handling
        try:
            response = client.chat.completions.create(**completion_params)
        except Exception as api_error:
            print(f"❌ OpenAI API error: {api_error}")
            # Return safe fallback with metadata
            return {
                "answer": "I encountered a technical issue. Please try again shortly.",
                "intent": intent,
                "citations": [],
                "model": model,
                "tokens_used": 0,
                "tokens_in": 0,
                "tokens_out": 0,
                "raw_len": 0,
                "json_ok": False,
                "retry_reason": "api_error",
                "answer_words": 9,
                "extraction_path": "<error>",
                "fallback_used": False
            }
        
        # Step 1: Extract final text using robust helper
        final_text, raw_len, extraction_meta = extract_final_text(response)
        usage = response.usage
        
        print(f"📥 Raw response: {raw_len} chars, {usage.total_tokens} tokens (path: {extraction_meta.get('extraction_path')})")
        
        # Store GPT-5 reasoning trace immediately (before retry/fallback)
        use_gpt5_experimental = os.getenv("USE_GPT5_EXPERIMENTAL", "false").lower() == "true"
        if model.startswith("gpt-5") or use_gpt5_experimental:
            store_reasoning_trace(response, user_message, intent, model, final_text, extraction_meta, fallback_used=False)
        
        # Step 2: If empty, retry with strict instruction
        retry_reason = ""
        fallback_used = False
        
        if not final_text or raw_len == 0:
            print(f"⚠️ Empty response detected (raw_len={raw_len}), retrying with strict instructions...")
            retry_reason = "reasoning_retry"
            
            # Add strict instruction
            messages.append({
                "role": "user",
                "content": "Return the final answer as JSON in assistant content. No hidden reasoning."
            })
            
            try:
                retry_response = client.chat.completions.create(**completion_params)
                final_text, raw_len, extraction_meta = extract_final_text(retry_response)
                usage = retry_response.usage
                print(f"🔄 Retry response: {raw_len} chars (path: {extraction_meta.get('extraction_path')})")
            except Exception as e:
                print(f"⚠️ Retry failed: {e}")
        
        # Step 3: If still empty, fallback to different model
        if not final_text or raw_len == 0:
            fallback_model = os.getenv("OPENAI_MODEL_FALLBACK", "gpt-4o-mini")
            print(f"⚠️ Still empty (raw_len={raw_len}), switching to fallback model: {fallback_model}")
            fallback_used = True
            retry_reason = "fallback_model"
            
            # Update params for fallback model
            completion_params["model"] = fallback_model
            # Ensure correct parameters for fallback (standard model)
            if "max_completion_tokens" in completion_params:
                completion_params["max_tokens"] = completion_params.pop("max_completion_tokens")
            if "temperature" not in completion_params:
                completion_params["temperature"] = 0.3
            
            try:
                fallback_response = client.chat.completions.create(**completion_params)
                final_text, raw_len, extraction_meta = extract_final_text(fallback_response)
                usage = fallback_response.usage
                print(f"🔄 Fallback response: {raw_len} chars from {fallback_model} (path: {extraction_meta.get('extraction_path')})")
            except Exception as e:
                print(f"❌ Fallback also failed: {e}")
                final_text = "I apologize, but I'm having difficulty generating a response. Please try again."
                raw_len = len(final_text)
        
        # Step 4: Run JSON extraction on final_text (3-stage: direct → regex → raw)
        json_ok = False
        answer = ""
        
        if final_text:
            try:
                # Attempt 1: Direct JSON parse
                parsed = json.loads(final_text)
                if isinstance(parsed, dict) and "answer" in parsed:
                    answer = parsed.get("answer", "")
                    json_ok = True
                    print(f"✅ JSON parsed directly")
            except json.JSONDecodeError:
                # Attempt 2: Extract JSON block with regex
                import re
                json_match = re.search(r'\{[\s\S]*"answer"[\s\S]*\}', final_text)
                if json_match:
                    try:
                        parsed = json.loads(json_match.group(0))
                        answer = parsed.get("answer", "")
                        json_ok = True
                        if not retry_reason:
                            retry_reason = "regex_extraction"
                        print(f"✅ JSON extracted via regex")
                    except:
                        pass
            
            # Fallback: Use raw text as answer
            if not answer:
                answer = final_text.strip()
                if not retry_reason:
                    retry_reason = "raw_fallback"
                print(f"⚠️ JSON parse failed, using raw text: {len(answer)} chars")
        
        word_count = len(answer.split())
        print(f"📊 Final answer: {len(answer)} chars, {word_count} words, json_ok={json_ok}")
        
        # Step 5: Length guard (if still too short after all retries)
        query_word_count = len(user_message.split())
        if word_count < 80 and query_word_count > 5 and snippet_context and not fallback_used:
            print(f"⚠️ Response too short ({word_count} words), retrying with expansion prompt...")
            retry_reason = "length_guard"
            
            # Add expansion instruction
            messages.append({"role": "assistant", "content": answer})
            messages.append({
                "role": "user",
                "content": "Please expand your answer with concrete details, specific measurements, practical examples, and step-by-step guidance. Keep it clear and actionable for a tradie."
            })
            
            # Retry with expansion
            try:
                retry_response = client.chat.completions.create(**completion_params)
                retry_raw = retry_response.choices[0].message.content or answer
                
                # Try parsing retry response
                try:
                    retry_parsed = json.loads(retry_raw)
                    expanded_answer = retry_parsed.get("answer", retry_raw)
                except:
                    expanded_answer = retry_raw.strip()
                
                expanded_word_count = len(expanded_answer.split())
                
                if expanded_word_count > word_count:
                    print(f"✅ Expanded response: {expanded_word_count} words")
                    answer = expanded_answer
                    usage = retry_response.usage
                    word_count = expanded_word_count
            except Exception as e:
                print(f"⚠️ Expansion failed, using original: {e}")
        
        # Create structured response with metadata
        structured_response = {
            "answer": answer,
            "intent": intent,
            "citations": format_tier1_citations(tier1_snippets[:3]) if tier1_snippets else [],
            "model": model,
            "tokens_used": usage.total_tokens,
            "tokens_in": usage.prompt_tokens,
            "tokens_out": usage.completion_tokens,
            # Metadata for logging
            "raw_len": raw_len,
            "json_ok": json_ok,
            "retry_reason": retry_reason,
            "answer_words": word_count,
            "extraction_path": extraction_meta.get("extraction_path", "<unknown>"),
            "fallback_used": fallback_used
        }
        
        # Store reasoning trace for GPT-5/experimental models
        use_gpt5_experimental = os.getenv("USE_GPT5_EXPERIMENTAL", "false").lower() == "true"
        if (model.startswith("gpt-5") or use_gpt5_experimental) and hasattr(response, 'model_dump'):
            try:
                import psycopg2
                import json
                import time
                
                DATABASE_URL = os.getenv("DATABASE_URL")
                if DATABASE_URL:
                    # Calculate response time (approximate from current request)
                    response_time_ms = int(usage.total_tokens * 50)  # Rough estimate
                    
                    # Prepare reasoning trace record
                    reasoning_dump = response.model_dump()
                    reasoning_trace_size = len(json.dumps(reasoning_dump))
                    
                    record_data = {
                        "query": user_message[:500],  # Limit query size
                        "intent": intent,
                        "model": model,
                        "reasoning_trace": json.dumps(reasoning_dump),
                        "final_answer": answer or "",
                        "metadata": json.dumps({
                            "extraction_path": extraction_meta.get("extraction_path", "<unknown>"),
                            "raw_len": raw_len,
                            "json_ok": json_ok,
                            "retry_reason": retry_reason,
                            "answer_words": word_count,
                            "tokens_used": usage.total_tokens,
                            "tokens_in": usage.prompt_tokens,
                            "tokens_out": usage.completion_tokens
                        }),
                        "fallback_used": fallback_used,
                        "response_time_ms": response_time_ms
                    }
                    
                    # Insert into database (non-blocking)
                    conn = psycopg2.connect(DATABASE_URL, sslmode="require", connect_timeout=5)
                    cur = conn.cursor()
                    cur.execute("""
                        INSERT INTO reasoning_responses 
                        (session_id, query, intent, model, reasoning_trace, final_answer, metadata, fallback_used, response_time_ms)
                        VALUES (%(session_id)s, %(query)s, %(intent)s, %(model)s, %(reasoning_trace)s::jsonb, 
                                %(final_answer)s, %(metadata)s::jsonb, %(fallback_used)s, %(response_time_ms)s);
                    """, {
                        "session_id": "default",  # Will be passed from caller later
                        **record_data
                    })
                    conn.commit()
                    cur.close()
                    conn.close()
                    
                    print(f"🧠 Stored reasoning trace ({reasoning_trace_size:,} bytes) model={model} fallback={fallback_used}")
                    
                    if fallback_used:
                        print(f"⚙️ Live answer served from fallback model (reasoning trace captured for GPT-5)")
                        
            except Exception as db_error:
                # Don't block user response if DB fails
                print(f"⚠️ Reasoning trace storage failed (non-blocking): {db_error}")
        
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