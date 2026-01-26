
import os
import sys
import asyncio
from dotenv import load_dotenv

# Force reload of .env
load_dotenv(override=True)

try:
    from emergentintegrations.llm.chat import LlmChat, UserMessage
except ImportError:
    print("CRITICAL: emergentintegrations.llm.chat not found!")
    sys.exit(1)

api_key = os.getenv("EMERGENT_LLM_KEY")
# Clean up model names (remove 'gemini/' prefix if user added it, though LlmChat adds it)
model_strict = os.getenv("GEMINI_PRO_MODEL", "gemini-1.5-pro")
model_hybrid = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

print(f"DEBUG: Key found: {bool(api_key)}")
print(f"DEBUG: Model Strict: {model_strict}")
print(f"DEBUG: Model Hybrid: {model_hybrid}")

if not api_key:
    print("CRITICAL: No EMERGENT_LLM_KEY found.")
    sys.exit(1)

async def test_models():
    # Test Strict
    print(f"\nTesting Strict Model: {model_strict}")
    try:
        # Note: LlmChat expects initial_messages to be a list of dicts
        client = LlmChat(
            api_key=api_key, 
            session_id="test-strict", 
            system_message="You are a helpful assistant.",
            initial_messages=[] 
        )
        client.with_model("gemini", model_strict)
        
        response = await client.send_message(UserMessage(text="Hello, strictly speaking, who are you?"))
        print(f"SUCCESS Strict: {response[:100]}...")
    except Exception as e:
        print(f"ERROR Strict: {e}")

    # Test Hybrid
    print(f"\nTesting Hybrid Model: {model_hybrid}")
    try:
        client = LlmChat(
            api_key=api_key, 
            session_id="test-hybrid", 
            system_message="You are a helpful assistant.",
            initial_messages=[]
        )
        client.with_model("gemini", model_hybrid)
        
        response = await client.send_message(UserMessage(text="Hello, quickly, who are you?"))
        print(f"SUCCESS Hybrid: {response[:100]}...")
    except Exception as e:
        print(f"ERROR Hybrid: {e}")

if __name__ == "__main__":
    asyncio.run(test_models())
