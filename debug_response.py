#!/usr/bin/env python3
"""Debug response structure"""

import requests
import json

BACKEND_URL = "https://codequery-4.preview.emergentagent.com"
API_ENDPOINT = f"{BACKEND_URL}/api/chat"

query = "nzs 3604 stud spacing requirements"

print(f"Testing query: {query}\n")

response = requests.post(
    API_ENDPOINT,
    json={"message": query, "session_id": "debug_test"},
    timeout=30
)

print(f"Status: {response.status_code}")
print(f"\nResponse keys: {list(response.json().keys())}")
print(f"\nFull response structure:")
print(json.dumps(response.json(), indent=2)[:2000])
