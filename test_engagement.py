#!/usr/bin/env python3
"""Quick test for engagement endpoint"""

import requests
import json

BASE_URL = "http://localhost:5000"
API_KEY = "test-key"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

payload = {
    "customer_id": "C000001"
}

print("Testing /api/v1/predict/engagement endpoint...")
print(f"Payload: {payload}\n")

try:
    response = requests.post(
        f"{BASE_URL}/api/v1/predict/engagement",
        json=payload,
        headers=headers,
        timeout=10
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
