import os
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = None
_api_key = os.getenv("OPENAI_API_KEY")

if _api_key:
    client = OpenAI(api_key=_api_key)
    print("✅ OpenAI LLM client initialized")
else:
    print("⚠️ No OpenAI API key configured")

def embed_text(text: str, model: str = "text-embedding-3-small") -> Optional[List[float]]:
    """
    Generate embedding for text using OpenAI
    
    Args:
        text: Text to embed
        model: Embedding model to use
        
    Returns:
        Embedding vector or None if unavailable
    """
    if not client:
        print("❌ OpenAI client not available")
        return None
    
    try:
        response = client.embeddings.create(
            input=text,
            model=model
        )
        embedding = response.data[0].embedding
        print(f"✅ Generated embedding ({len(embedding)} dimensions)")
        return embedding
    except Exception as e:
        print(f"❌ Embedding generation failed: {e}")
        return None

# Alias for backwards compatibility
get_embedding = embed_text

def chat_completion(
    messages: List[dict], 
    model: str = "gpt-4o-mini",
    temperature: float = 0.3,
    max_tokens: int = 500
) -> Optional[str]:
    """
    Generate chat completion using OpenAI
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Model to use for completion
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        
    Returns:
        Generated text or None if unavailable
    """
    if not client:
        print("❌ OpenAI client not available")
        return None
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        answer = response.choices[0].message.content
        print(f"✅ Generated completion ({len(answer)} chars)")
        return answer
    except Exception as e:
        print(f"❌ Chat completion failed: {e}")
        return None

# Alias for simpler naming
chat = chat_completion
