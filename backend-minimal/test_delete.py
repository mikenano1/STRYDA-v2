import requests
import os
from dotenv import load_dotenv

load_dotenv(override=True)

# URL = "http://localhost:8001" # Internal
URL = "https://strydamaster.preview.emergentagent.com" # External proxy

def test_delete():
    fake_id = "non_existent_session_123"
    print(f"Testing DELETE on {URL}/api/threads/{fake_id}")
    
    try:
        response = requests.delete(f"{URL}/api/threads/{fake_id}")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ DELETE is idempotent (Success on non-existent)")
        elif response.status_code == 404:
            print("❌ DELETE failed (404 Not Found)")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_delete()