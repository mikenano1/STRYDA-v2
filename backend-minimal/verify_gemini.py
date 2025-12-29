
import os
import sys
import traceback

print(f"Python executable: {sys.executable}")
print(f"Python path: {sys.path}")

try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
    print("Dotenv loaded.")
except ImportError:
    print("Dotenv not found.")

try:
    print("Attempting to import emergentintegrations...")
    from emergentintegrations import EmergentLLM
    print("Import successful.")
except ImportError as e:
    print(f"CRITICAL: emergentintegrations library not found! Error: {e}")
    traceback.print_exc()
    sys.exit(1)

api_key = os.getenv("EMERGENT_LLM_KEY")
model_strict = os.getenv("GEMINI_PRO_MODEL")
model_hybrid = os.getenv("GEMINI_MODEL")

print(f"DEBUG: Key found: {bool(api_key)}")
print(f"DEBUG: Model Strict: {model_strict}")
print(f"DEBUG: Model Hybrid: {model_hybrid}")

if not api_key:
    print("CRITICAL: No EMERGENT_LLM_KEY found in environment.")
    sys.exit(1)

# Initialize Client
try:
    client = EmergentLLM(api_key=api_key)
    print("SUCCESS: Client initialized.")
except Exception as e:
    print(f"CRITICAL: Client init failed: {e}")
    sys.exit(1)

# Test Generation (Strict Model)
print(f"Testing generation with {model_strict}...")
try:
    response = client.chat.completions.create(
        model=model_strict,
        messages=[{"role": "user", "content": "Hello"}]
    )
    print("SUCCESS: Strict Model Response:")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"ERROR: Strict Model generation failed: {e}")

# Test Generation (Hybrid Model)
print(f"Testing generation with {model_hybrid}...")
try:
    response = client.chat.completions.create(
        model=model_hybrid,
        messages=[{"role": "user", "content": "Hello"}]
    )
    print("SUCCESS: Hybrid Model Response:")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"ERROR: Hybrid Model generation failed: {e}")
