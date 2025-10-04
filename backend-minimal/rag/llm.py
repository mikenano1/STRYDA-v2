import os
import asyncio
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize emergentintegrations
from emergentintegrations.llm.chat import LlmChat, UserMessage

# Global client
chat_client = None
_api_key = os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY")

if _api_key:
    chat_client = LlmChat(
        api_key=_api_key,
        session_id="rag-pipeline",
        system_message="You are a helpful assistant for New Zealand building codes and construction."
    ).with_model("openai", "gpt-4o-mini")
    print("✅ Emergent LLM client initialized")
else:
    print("⚠️ No LLM API key configured (EMERGENT_LLM_KEY or OPENAI_API_KEY)")

async def embed_text_async(text: str, model: str = "text-embedding-3-small") -> Optional[List[float]]:
    """
    Generate embedding for text using emergentintegrations
    """
    if not chat_client:
        print("❌ LLM client not available")
        return None
    
    try:
        # Create a temporary embedding client for this specific request
        embedding_client = LlmChat(
            api_key=_api_key,
            session_id="embedding-pipeline",
            system_message=""
        ).with_model("openai", model)
        
        # Use a simple approach to get embeddings through the client
        # Note: This is a workaround as emergentintegrations may not have direct embedding support
        # We'll need to implement this differently
        
        # For now, let's use the OpenAI client approach but with proper error handling
        from openai import OpenAI
        openai_client = OpenAI(api_key=_api_key)
        
        response = openai_client.embeddings.create(
            input=text,
            model=model
        )
        embedding = response.data[0].embedding
        print(f"✅ Generated embedding ({len(embedding)} dimensions)")
        return embedding
        
    except Exception as e:
        print(f"❌ Embedding generation failed: {e}")
        return None

def embed_text(text: str, model: str = "text-embedding-3-small") -> Optional[List[float]]:
    """
    Synchronous wrapper for embed_text_async
    """
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(embed_text_async(text, model))
    except RuntimeError:
        # No event loop, create a new one
        return asyncio.run(embed_text_async(text, model))

# Alias for backwards compatibility
get_embedding = embed_text

async def chat_completion_async(
    messages: List[dict], 
    model: str = "gpt-4o-mini",
    temperature: float = 0.3,
    max_tokens: int = 500
) -> Optional[str]:
    """
    Generate chat completion using emergentintegrations
    """
    if not chat_client:
        print("❌ LLM client not available")
        return None
    
    try:
        # Configure the client for this request
        configured_client = chat_client.with_model("openai", model)
        
        # Convert messages to UserMessage format
        # Take the last user message (assuming that's what we want to respond to)
        user_content = ""
        for msg in messages:
            if msg.get("role") == "user":
                user_content = msg.get("content", "")
            elif msg.get("role") == "system":
                # Update system message if provided
                configured_client = LlmChat(
                    api_key=_api_key,
                    session_id="rag-pipeline",
                    system_message=msg.get("content", "")
                ).with_model("openai", model)
        
        if not user_content:
            print("❌ No user message found")
            return None
        
        user_message = UserMessage(text=user_content)
        response = await configured_client.send_message(user_message)
        
        print(f"✅ Generated completion ({len(response)} chars)")
        return response
        
    except Exception as e:
        print(f"❌ Chat completion failed: {e}")
        return None

def chat_completion(
    messages: List[dict], 
    model: str = "gpt-4o-mini",
    temperature: float = 0.3,
    max_tokens: int = 500
) -> Optional[str]:
    """
    Synchronous wrapper for chat_completion_async
    """
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(chat_completion_async(messages, model, temperature, max_tokens))
    except RuntimeError:
        # No event loop, create a new one
        return asyncio.run(chat_completion_async(messages, model, temperature, max_tokens))

# Alias for simpler naming
chat = chat_completion
