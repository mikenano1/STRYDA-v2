import os
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Global client variable
client = None
_api_key = os.getenv("OPENAI_API_KEY")

def init_openai_client():
    """Initialize OpenAI client with error handling"""
    global client
    if not _api_key:
        print("⚠️ No OpenAI API key configured")
        return
    
    try:
        # Import OpenAI and create client
        import openai
        client = openai.OpenAI(api_key=_api_key)
        
        # Test the client with a simple call
        test_response = client.models.list()
        print("✅ OpenAI LLM client initialized and tested")
        return True
    except Exception as e:
        print(f"❌ OpenAI client initialization failed: {e}")
        client = None
        return False

# Initialize on import
init_openai_client()

def embed_text(text: str, model: str = "text-embedding-3-small") -> Optional[List[float]]:
    """
    Generate embedding for text using OpenAI
    """
    if not client:
        print("❌ OpenAI client not available - trying to reinitialize...")
        if not init_openai_client():
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
    """
    if not client:
        print("❌ OpenAI client not available - trying to reinitialize...")
        if not init_openai_client():
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
